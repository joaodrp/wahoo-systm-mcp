"""OAuth authorization server where each person signs in with their own Wahoo SYSTM account.

claude.ai custom connectors (which also serve the mobile app) only support OAuth or no auth, so
this is a minimal authorization server: /authorize redirects to a sign-in page, which checks the
email against the allowlist and the password with Wahoo SYSTM before issuing a code.

Everything is stateless so it runs on Lambda without a database: client IDs, sign-in requests,
codes and tokens are claims sealed with AES-GCM under a key derived from the signing secret.
Codes and tokens carry the user's Wahoo email and password, so the tools can sign in to Wahoo
for them; the password is never stored, and only this server can read it. The trade-offs:

- A single token can't be revoked. Removing an email from the allowlist signs that person out,
  and replacing the signing secret signs out everyone.
- Codes can't be marked as used, so they're short-lived and bound to PKCE instead.
- Anyone holding both a token and the signing secret can read the password inside the token.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import logging
import os
import time
from typing import TYPE_CHECKING, Literal, TypeVar
from urllib.parse import urlencode, urlsplit

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastmcp.server.auth import AccessToken, OAuthProvider
from mcp.server.auth.provider import (
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    RefreshToken,
    RegistrationError,
    TokenError,
    construct_redirect_uri,
)
from mcp.server.auth.settings import ClientRegistrationOptions
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyUrl, BaseModel, ConfigDict, SecretStr, ValidationError
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route

from wahoo_systm_mcp.client import InvalidCredentialsError, WahooAPIError, WahooClient
from wahoo_systm_mcp.remote.settings import normalize_email

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request

    from wahoo_systm_mcp.remote.settings import RemoteSettings

logger = logging.getLogger(__name__)

LOGIN_PATH = "/login"
ACCESS_TOKEN_TTL = 60 * 60  # 1 hour
REFRESH_TOKEN_TTL = 90 * 24 * 60 * 60  # 90 days, renewed on every refresh
# Codes can't be marked as used without storage, so they're short-lived and PKCE-bound instead
CODE_TTL = 2 * 60
LOGIN_FORM_TTL = 10 * 60
# Failed sign-ins per email before a cool-down. Per instance on Lambda, so it only slows down
# password guessing through this server; the allowlist keeps it to known accounts.
MAX_FAILED_LOGINS = 5
FAILED_LOGIN_WINDOW = 15 * 60

AuthMethod = Literal["none", "client_secret_post", "client_secret_basic"]
_NONCE_SIZE = 12
# Associated data for each kind of sealed value, so one can't be passed off as another. Bump the
# version if a model below changes incompatibly: older values then simply fail to open.
_CLIENT = b"wahoo-systm-mcp/v1/client"
_LOGIN = b"wahoo-systm-mcp/v1/login"
_CODE = b"wahoo-systm-mcp/v1/code"
_ACCESS = b"wahoo-systm-mcp/v1/access"
_REFRESH = b"wahoo-systm-mcp/v1/refresh"


async def wahoo_login(email: str, password: str) -> None:
    """Check an email and password by signing in to Wahoo SYSTM.

    Raises:
        InvalidCredentialsError: If Wahoo SYSTM rejects them.
        WahooAPIError: If Wahoo SYSTM can't be reached or returns an error.

    """
    client = WahooClient()
    try:
        await client.authenticate(email, password)
    finally:
        await client.close()


# =============================================================================
# Sealed values
# =============================================================================


class _Sealed(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class _Client(_Sealed):
    """A dynamically registered OAuth client; the sealed value is its client ID."""

    redirect_uris: list[str]
    auth_method: AuthMethod
    scope: str | None = None


class _Login(_Sealed):
    """An authorization request, round-tripped through the sign-in form."""

    client_id: str
    redirect_uri: str
    redirect_uri_explicit: bool
    code_challenge: str
    state: str | None
    scopes: list[str]
    resource: str | None
    exp: float


class _Grant(_Sealed):
    """What access and refresh tokens carry: the signed-in user and their Wahoo credentials."""

    client_id: str
    scopes: list[str]
    resource: str | None
    email: str
    password: str
    exp: float


class _Code(_Grant):
    redirect_uri: str
    redirect_uri_explicit: bool
    code_challenge: str


_SealedT = TypeVar("_SealedT", bound=_Sealed)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class Sealer:
    """Encrypts and authenticates small JSON claims (AES-256-GCM)."""

    def __init__(self, secret: str) -> None:
        key = secret.encode()
        self._aead = AESGCM(hmac.new(key, b"seal", hashlib.sha256).digest())
        self._mac_key = hmac.new(key, b"mac", hashlib.sha256).digest()

    def seal(self, kind: bytes, value: _Sealed) -> str:
        nonce = os.urandom(_NONCE_SIZE)
        body = value.model_dump_json().encode()
        return _b64encode(nonce + self._aead.encrypt(nonce, body, kind))

    def open(self, kind: bytes, sealed: str, model: type[_SealedT]) -> _SealedT | None:
        """Return the sealed value, or None if it was tampered with, is another kind or expired."""
        try:
            raw = _b64decode(sealed)
            body = self._aead.decrypt(raw[:_NONCE_SIZE], raw[_NONCE_SIZE:], kind)
            value = model.model_validate_json(body)
        except (ValueError, InvalidTag, ValidationError):
            return None
        expires = getattr(value, "exp", None)
        if expires is not None and expires < time.time():
            return None
        return value

    def mac(self, value: str) -> str:
        return _b64encode(hmac.new(self._mac_key, value.encode(), hashlib.sha256).digest())


# =============================================================================
# Provider
# =============================================================================


class WahooAuthorizationCode(AuthorizationCode):
    email: str
    password: SecretStr


class WahooRefreshToken(RefreshToken):
    email: str
    password: SecretStr
    resource: str | None = None


class WahooAccessToken(AccessToken):
    """An access token for a signed-in user; tools use `email` and `password` to reach Wahoo."""

    email: str
    password: SecretStr


class WahooOAuthProvider(OAuthProvider):
    """Stateless OAuth server whose sign-in page checks credentials with Wahoo SYSTM."""

    def __init__(
        self,
        settings: RemoteSettings,
        verify_login: Callable[[str, str], Awaitable[None]] = wahoo_login,
    ) -> None:
        super().__init__(
            base_url=settings.public_url,
            client_registration_options=ClientRegistrationOptions(enabled=True),
        )
        self._public_url = settings.public_url
        self._allowed_emails = settings.allowed_emails
        # Normalized the way the SDK parses redirect URIs, so they compare equal
        self._redirect_uris = [str(AnyUrl(uri)) for uri in settings.redirect_uris]
        self._sealer = Sealer(settings.signing_secret)
        self._verify_login = verify_login
        self._failed_logins: dict[str, list[float]] = {}

    def get_routes(self, mcp_path: str | None = None) -> list[Route]:
        routes = super().get_routes(mcp_path)
        routes.append(Route(LOGIN_PATH, self._handle_login, methods=["GET", "POST"]))
        return routes

    # --- Clients -------------------------------------------------------------

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        # The SDK has filled in a random client ID and secret, and returns this same object to
        # the client. They're replaced with a sealed ID and a secret derived from it, so neither
        # needs to be stored.
        uris = [str(uri) for uri in client_info.redirect_uris or []]
        disallowed = [uri for uri in uris if uri not in self._redirect_uris]
        if disallowed:
            msg = f"redirect_uri not allowed: {', '.join(disallowed)}"
            raise RegistrationError(error="invalid_redirect_uri", error_description=msg)
        method = client_info.token_endpoint_auth_method
        if method not in ("none", "client_secret_post", "client_secret_basic"):
            msg = f"token_endpoint_auth_method not supported: {method}"
            raise RegistrationError(error="invalid_client_metadata", error_description=msg)

        client = _Client(redirect_uris=uris, auth_method=method, scope=client_info.scope)
        client_id = self._sealer.seal(_CLIENT, client)
        client_info.client_id = client_id
        client_info.client_secret = self._client_secret(client_id, method)
        client_info.client_secret_expires_at = None if method == "none" else 0

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        client = self._sealer.open(_CLIENT, client_id, _Client)
        if client is None:
            return None
        uris = [uri for uri in client.redirect_uris if uri in self._redirect_uris]
        if not uris:
            return None
        return OAuthClientInformationFull(
            client_id=client_id,
            client_secret=self._client_secret(client_id, client.auth_method),
            redirect_uris=[AnyUrl(uri) for uri in uris],
            token_endpoint_auth_method=client.auth_method,
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope=client.scope,
        )

    def _client_secret(self, client_id: str, method: AuthMethod) -> str | None:
        return None if method == "none" else self._sealer.mac(f"client-secret:{client_id}")

    # --- Authorization -------------------------------------------------------

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        resource_url = str(self._resource_url).rstrip("/")
        if params.resource is not None and params.resource.rstrip("/") != resource_url:
            msg = f"This server only issues tokens for {resource_url}"
            raise AuthorizeError(error="invalid_request", error_description=msg)
        login = _Login(
            client_id=client.client_id or "",
            redirect_uri=str(params.redirect_uri),
            redirect_uri_explicit=params.redirect_uri_provided_explicitly,
            code_challenge=params.code_challenge,
            state=params.state,
            scopes=params.scopes or [],
            resource=params.resource,
            exp=time.time() + LOGIN_FORM_TTL,
        )
        query = urlencode({"request": self._sealer.seal(_LOGIN, login)})
        return f"{self._public_url}{LOGIN_PATH}?{query}"

    async def _handle_login(self, request: Request) -> Response:
        """GET shows the sign-in form for a request from authorize(); POST checks it."""
        params = await request.form() if request.method == "POST" else request.query_params
        sealed = params.get("request")
        login = self._sealer.open(_LOGIN, sealed, _Login) if isinstance(sealed, str) else None
        client = await self.get_client(login.client_id) if login else None
        if (
            login is None
            or client is None
            or login.redirect_uri not in [str(uri) for uri in client.redirect_uris or []]
        ):
            body = "<p>This sign-in link has expired. Start connecting again from Claude.</p>"
            return self._page(body, status_code=400)
        assert isinstance(sealed, str)  # noqa: S101 - login was opened from it

        if request.method == "GET":
            return self._login_page(sealed, login)

        email_value = params.get("email")
        password_value = params.get("password")
        email = normalize_email(email_value) if isinstance(email_value, str) else ""
        password = password_value if isinstance(password_value, str) else ""
        failure = await self._check_credentials(email, password)
        if failure is not None:
            status_code, message = failure
            return self._login_page(sealed, login, message, email, status_code)

        code = _Code(
            client_id=login.client_id,
            scopes=login.scopes,
            resource=login.resource,
            email=email,
            password=password,
            redirect_uri=login.redirect_uri,
            redirect_uri_explicit=login.redirect_uri_explicit,
            code_challenge=login.code_challenge,
            exp=time.time() + CODE_TTL,
        )
        target = construct_redirect_uri(
            login.redirect_uri, code=self._sealer.seal(_CODE, code), state=login.state
        )
        return RedirectResponse(target, status_code=302, headers={"Cache-Control": "no-store"})

    async def _check_credentials(self, email: str, password: str) -> tuple[int, str] | None:
        """Return (HTTP status, message) when sign-in fails, or None when it succeeds."""
        if not email or not password:
            return 400, "Enter your Wahoo SYSTM email and password."
        if email not in self._allowed_emails:
            return 403, (
                f"{email} isn't allowed to use this server. "
                "Ask the person who runs it to add your Wahoo SYSTM email."
            )
        now = time.monotonic()
        recent = [t for t in self._failed_logins.get(email, []) if now - t < FAILED_LOGIN_WINDOW]
        self._failed_logins[email] = recent
        if len(recent) >= MAX_FAILED_LOGINS:
            return 429, "Too many failed attempts. Try again in 15 minutes."
        try:
            await self._verify_login(email, password)
        except InvalidCredentialsError:
            recent.append(now)
            return 401, "Wahoo SYSTM didn't accept that email and password."
        except WahooAPIError as e:
            logger.warning("Wahoo SYSTM sign-in failed: %s", e.message)
            return 502, "Couldn't reach Wahoo SYSTM. Try again in a minute."
        self._failed_logins.pop(email, None)
        return None

    # --- Tokens --------------------------------------------------------------

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> WahooAuthorizationCode | None:
        code = self._sealer.open(_CODE, authorization_code, _Code)
        if code is None or code.client_id != client.client_id or not self._allowed(code.email):
            return None
        return WahooAuthorizationCode(
            code=authorization_code,
            scopes=code.scopes,
            expires_at=code.exp,
            client_id=code.client_id,
            code_challenge=code.code_challenge,
            redirect_uri=AnyUrl(code.redirect_uri),
            redirect_uri_provided_explicitly=code.redirect_uri_explicit,
            resource=code.resource,
            email=code.email,
            password=SecretStr(code.password),
        )

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,  # noqa: ARG002 - checked by load_authorization_code
        authorization_code: AuthorizationCode,
    ) -> OAuthToken:
        if not isinstance(authorization_code, WahooAuthorizationCode):
            msg = "Unknown authorization code"
            raise TokenError(error="invalid_grant", error_description=msg)
        return self._issue_tokens(
            client_id=authorization_code.client_id,
            scopes=authorization_code.scopes,
            resource=authorization_code.resource,
            email=authorization_code.email,
            password=authorization_code.password.get_secret_value(),
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> WahooRefreshToken | None:
        grant = self._sealer.open(_REFRESH, refresh_token, _Grant)
        if grant is None or grant.client_id != client.client_id or not self._allowed(grant.email):
            return None
        return WahooRefreshToken(
            token=refresh_token,
            client_id=grant.client_id,
            scopes=grant.scopes,
            expires_at=int(grant.exp),
            email=grant.email,
            password=SecretStr(grant.password),
            resource=grant.resource,
        )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,  # noqa: ARG002 - checked by load_refresh_token
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        if not isinstance(refresh_token, WahooRefreshToken):
            msg = "Unknown refresh token"
            raise TokenError(error="invalid_grant", error_description=msg)
        password = refresh_token.password.get_secret_value()
        # Check the credentials still work, so a changed Wahoo password makes Claude ask the user
        # to connect again. Other errors (Wahoo unreachable) fail this refresh without ending the
        # grant, so it can be retried.
        try:
            await self._verify_login(refresh_token.email, password)
        except InvalidCredentialsError as e:
            msg = "Wahoo SYSTM no longer accepts this sign-in; connect again"
            raise TokenError(error="invalid_grant", error_description=msg) from e
        return self._issue_tokens(
            client_id=refresh_token.client_id,
            scopes=scopes,
            resource=refresh_token.resource,
            email=refresh_token.email,
            password=password,
        )

    async def load_access_token(self, token: str) -> WahooAccessToken | None:
        grant = self._sealer.open(_ACCESS, token, _Grant)
        if grant is None or not self._allowed(grant.email):
            return None
        return WahooAccessToken(
            token=token,
            client_id=grant.client_id,
            scopes=grant.scopes,
            expires_at=int(grant.exp),
            resource=grant.resource,
            claims={"sub": grant.email},
            email=grant.email,
            password=SecretStr(grant.password),
        )

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        """Tokens can't be revoked individually (the revocation endpoint is disabled)."""

    def _allowed(self, email: str) -> bool:
        return email in self._allowed_emails

    def _issue_tokens(
        self,
        *,
        client_id: str,
        scopes: list[str],
        resource: str | None,
        email: str,
        password: str,
    ) -> OAuthToken:
        now = time.time()

        def grant(ttl: int) -> _Grant:
            return _Grant(
                client_id=client_id,
                scopes=scopes,
                resource=resource,
                email=email,
                password=password,
                exp=now + ttl,
            )

        return OAuthToken(
            access_token=self._sealer.seal(_ACCESS, grant(ACCESS_TOKEN_TTL)),
            token_type="Bearer",  # noqa: S106 - not a password
            expires_in=ACCESS_TOKEN_TTL,
            refresh_token=self._sealer.seal(_REFRESH, grant(REFRESH_TOKEN_TTL)),
            scope=" ".join(scopes) if scopes else None,
        )

    # --- Pages ---------------------------------------------------------------

    def _login_page(
        self,
        sealed: str,
        login: _Login,
        error: str | None = None,
        email: str = "",
        status_code: int = 200,
    ) -> Response:
        e = html.escape
        host = urlsplit(login.redirect_uri).hostname or login.redirect_uri
        error_html = f'<p class="error" role="alert">{e(error)}</p>' if error else ""
        body = f"""<p>Connect <strong>{e(host)}</strong> to your Wahoo SYSTM account.</p>
    <form method="post" action="{LOGIN_PATH}">
      <input type="hidden" name="request" value="{e(sealed)}">
      <label for="email">Wahoo SYSTM email</label>
      <input id="email" name="email" type="email" value="{e(email)}" autocomplete="username"
        autocapitalize="none" spellcheck="false" required{"" if email else " autofocus"}>
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password"
        required{" autofocus" if email else ""}>
      {error_html}
      <button type="submit">Sign in and allow access</button>
    </form>
    <p class="note">Your password is checked with Wahoo SYSTM, then kept only inside the
      encrypted tokens Claude holds for this connection, so it can sign in to Wahoo for you.
      It isn't saved on this server.</p>"""
        return self._page(body, status_code)

    def _page(self, body: str, status_code: int = 200) -> Response:
        # The sign-in form redirects to the client, and Chrome applies form-action to that too
        targets = " ".join(
            sorted({f"{urlsplit(u).scheme}://{urlsplit(u).netloc}" for u in self._redirect_uris})
        )
        headers = {
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                f"default-src 'none'; style-src 'unsafe-inline'; form-action 'self' {targets}; "
                "frame-ancestors 'none'; base-uri 'none'"
            ),
            "Referrer-Policy": "no-referrer",
            "X-Frame-Options": "DENY",
        }
        return HTMLResponse(_PAGE.format(body=body), status_code=status_code, headers=headers)


_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wahoo SYSTM MCP sign-in</title>
<style>
  :root {{ color-scheme: light dark; --bg: #f5f6f8; --card: #fff; --text: #16181d;
    --muted: #626873; --accent: #1f5fd1; --error: #b91c1c; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg: #121417; --card: #1d2025;
    --text: #e9ebef; --muted: #9ba1ab; --accent: #6b9cf5; --error: #f87171; }} }}
  body {{ margin: 0; min-height: 100vh; display: grid; place-items: center;
    background: var(--bg); color: var(--text); font: 16px/1.5 system-ui, sans-serif; }}
  main {{ width: min(380px, calc(100vw - 32px)); background: var(--card); border-radius: 12px;
    padding: 24px; box-sizing: border-box; }}
  h1 {{ font-size: 20px; margin: 0 0 8px; }}
  label {{ display: block; margin-top: 16px; font-weight: 600; }}
  input[type=email], input[type=password] {{ width: 100%; box-sizing: border-box;
    margin-top: 6px; padding: 10px 12px; font: inherit; border: 1px solid var(--muted);
    border-radius: 8px; background: transparent; color: inherit; }}
  button {{ width: 100%; margin-top: 16px; padding: 12px; font: inherit; font-weight: 600;
    border: 0; border-radius: 8px; background: var(--accent); color: #fff; }}
  .error {{ color: var(--error); margin: 8px 0 0; }}
  .note {{ color: var(--muted); font-size: 14px; margin: 16px 0 0; }}
</style>
</head>
<body><main><h1>Wahoo SYSTM MCP</h1>{body}</main></body>
</html>
"""
