"""Tests for the multi-user remote server: settings, OAuth sign-in, and per-user clients."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from fastmcp.exceptions import ToolError
from pydantic import SecretStr

from wahoo_systm_mcp.client import InvalidCredentialsError, WahooAPIError
from wahoo_systm_mcp.client.models import UserPlanItem
from wahoo_systm_mcp.remote import oauth
from wahoo_systm_mcp.remote.app import create_remote_app
from wahoo_systm_mcp.remote.clients import RECONNECT_MESSAGE, UserClients
from wahoo_systm_mcp.remote.oauth import (
    MAX_FAILED_LOGINS,
    Sealer,
    WahooAccessToken,
    WahooOAuthProvider,
    _Login,
    wahoo_login,
)
from wahoo_systm_mcp.remote.settings import (
    CLAUDE_REDIRECT_URI,
    RemoteSettings,
    SettingsError,
    parse_allowed_emails,
    parse_redirect_uris,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastmcp.server.http import StarletteWithLifespan

PUBLIC_URL = "https://abc123.lambda-url.us-west-2.on.aws"
MCP_URL = f"{PUBLIC_URL}/mcp"
SECRET = "0123456789abcdef" * 4
ALICE = "alice@example.com"
BOB = "bob@example.com"
PASSWORDS = {ALICE: "alice-password", BOB: "bob-password"}
MCP_HEADERS = {"Accept": "application/json, text/event-stream"}


def make_settings(**overrides: object) -> RemoteSettings:
    values: dict[str, Any] = {
        "public_url": PUBLIC_URL,
        "signing_secret": SECRET,
        "allowed_emails": frozenset({ALICE, BOB}),
    }
    values.update(overrides)
    return RemoteSettings(**values)


# =============================================================================
# Fake Wahoo SYSTM
# =============================================================================


class FakeWahoo:
    """Stands in for Wahoo SYSTM: checks passwords and hands out fake clients."""

    def __init__(self) -> None:
        self.passwords = dict(PASSWORDS)
        self.down = False
        self.clients: list[FakeClient] = []

    async def verify_login(self, email: str, password: str) -> None:
        if self.down:
            msg = "API request timed out"
            raise WahooAPIError(msg)
        if self.passwords.get(email) != password:
            msg = "Authentication failed: Invalid credentials"
            raise InvalidCredentialsError(msg)

    def new_client(self) -> FakeClient:
        client = FakeClient(self)
        self.clients.append(client)
        return client


class FakeClient:
    def __init__(self, wahoo: FakeWahoo) -> None:
        self.wahoo = wahoo
        self.email: str | None = None
        self.logins = 0
        self.closed = False

    async def authenticate(self, email: str, password: str) -> None:
        await self.wahoo.verify_login(email, password)
        self.email = email
        self.logins += 1

    async def get_calendar(self, start: str, end: str, time_zone: str) -> list[UserPlanItem]:
        # The plan name identifies whose client answered
        item = {
            "day": 1,
            "plannedDate": start,
            "rank": 1,
            "agendaId": "agenda1",
            "status": "scheduled",
            "type": "workout",
            "prospects": [],
            "plan": {"id": "p", "name": f"plan of {self.email}", "color": "", "category": ""},
        }
        return [UserPlanItem.model_validate(item)]

    async def close(self) -> None:
        self.closed = True


# =============================================================================
# Settings
# =============================================================================


class TestSettings:
    def test_parse_emails_json(self) -> None:
        assert parse_allowed_emails('["A@Example.com", "b@example.com"]') == {
            "a@example.com",
            "b@example.com",
        }

    def test_parse_emails_comma_separated(self) -> None:
        assert parse_allowed_emails(" a@example.com, B@example.com ,") == {
            "a@example.com",
            "b@example.com",
        }

    def test_parse_emails_rejects_invalid(self) -> None:
        with pytest.raises(SettingsError, match="not-an-email"):
            parse_allowed_emails("a@example.com,not-an-email")

    def test_parse_emails_rejects_non_strings(self) -> None:
        with pytest.raises(SettingsError, match="JSON array of strings"):
            parse_allowed_emails("[1, 2]")

    def test_parse_emails_empty_array(self) -> None:
        assert parse_allowed_emails("[]") == frozenset()

    def test_redirect_uris_default_to_claude(self) -> None:
        assert parse_redirect_uris(None) == (CLAUDE_REDIRECT_URI,)
        assert parse_redirect_uris(" a , b ") == ("a", "b")

    def test_short_secret_rejected(self) -> None:
        with pytest.raises(SettingsError, match="at least 32"):
            make_settings(signing_secret="short")

    def test_plain_http_rejected_except_localhost(self) -> None:
        with pytest.raises(SettingsError, match="https"):
            make_settings(public_url="http://example.com")
        assert make_settings(public_url="http://localhost:8000/").public_url == (
            "http://localhost:8000"
        )

    def test_from_env(self) -> None:
        settings = RemoteSettings.from_env(
            {
                "MCP_SIGNING_SECRET": SECRET,
                "MCP_ALLOWED_EMAILS": "Alice@example.com",
                "HTTP_PORT": "9000",
                "OAUTH_REDIRECT_URIS": "http://localhost:6274/oauth/callback",
            }
        )
        assert settings.public_url == "http://localhost:9000"
        assert settings.allowed_emails == {ALICE}
        assert settings.redirect_uris == ("http://localhost:6274/oauth/callback",)

    def test_from_env_requires_secret_and_emails(self) -> None:
        with pytest.raises(SettingsError, match="MCP_ALLOWED_EMAILS"):
            RemoteSettings.from_env({"MCP_SIGNING_SECRET": SECRET})

    def test_from_ssm(self) -> None:
        ssm = MagicMock()
        ssm.get_parameters.return_value = {
            "Parameters": [
                {"Name": "/p/SIGNING_SECRET", "Value": SECRET},
                {"Name": "/p/ALLOWED_EMAILS", "Value": json.dumps([ALICE])},
                {"Name": "/p/PUBLIC_URL", "Value": f"{PUBLIC_URL}/"},
            ],
            "InvalidParameters": [],
        }
        settings = RemoteSettings.from_ssm(ssm, "/p", env={})

        ssm.get_parameters.assert_called_once_with(
            Names=["/p/SIGNING_SECRET", "/p/ALLOWED_EMAILS", "/p/PUBLIC_URL"],
            WithDecryption=True,
        )
        assert settings.public_url == PUBLIC_URL
        assert settings.allowed_emails == {ALICE}
        assert settings.redirect_uris == (CLAUDE_REDIRECT_URI,)

    def test_from_ssm_missing_parameters(self) -> None:
        ssm = MagicMock()
        ssm.get_parameters.return_value = {
            "Parameters": [],
            "InvalidParameters": ["/p/SIGNING_SECRET"],
        }
        with pytest.raises(SettingsError, match="/p/SIGNING_SECRET"):
            RemoteSettings.from_ssm(ssm, "/p", env={})


# =============================================================================
# Sealer
# =============================================================================


def sample_login(exp: float = 9e9) -> _Login:
    return _Login(
        client_id="c",
        redirect_uri=CLAUDE_REDIRECT_URI,
        redirect_uri_explicit=True,
        code_challenge="cc",
        state=None,
        scopes=[],
        resource=None,
        exp=exp,
    )


class TestSealer:
    def test_round_trip(self) -> None:
        sealer = Sealer(SECRET)
        sealed = sealer.seal(oauth._LOGIN, sample_login())
        assert sealer.open(oauth._LOGIN, sealed, _Login) == sample_login()

    def test_contents_are_encrypted(self) -> None:
        sealed = Sealer(SECRET).seal(oauth._LOGIN, sample_login())
        assert CLAUDE_REDIRECT_URI.encode() not in base64.urlsafe_b64decode(sealed + "==")

    def test_rejects_other_kind(self) -> None:
        sealer = Sealer(SECRET)
        sealed = sealer.seal(oauth._LOGIN, sample_login())
        assert sealer.open(oauth._CODE, sealed, _Login) is None

    def test_rejects_other_secret(self) -> None:
        sealed = Sealer(SECRET).seal(oauth._LOGIN, sample_login())
        assert Sealer(SECRET[::-1]).open(oauth._LOGIN, sealed, _Login) is None

    def test_rejects_tampering(self) -> None:
        sealer = Sealer(SECRET)
        raw = bytearray(base64.urlsafe_b64decode(sealer.seal(oauth._LOGIN, sample_login()) + "=="))
        raw[20] ^= 1
        tampered = base64.urlsafe_b64encode(bytes(raw)).decode().rstrip("=")
        assert sealer.open(oauth._LOGIN, tampered, _Login) is None

    @pytest.mark.parametrize("value", ["", "a", "!!!", "é", "a.b.c"])
    def test_rejects_garbage(self, value: str) -> None:
        assert Sealer(SECRET).open(oauth._LOGIN, value, _Login) is None

    def test_rejects_expired(self) -> None:
        sealer = Sealer(SECRET)
        sealed = sealer.seal(oauth._LOGIN, sample_login(exp=1))
        assert sealer.open(oauth._LOGIN, sealed, _Login) is None


# =============================================================================
# OAuth flow, end to end through the ASGI app
# =============================================================================


def pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).decode().rstrip("=")


def query(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


class Server:
    """The remote app on an in-process HTTP client, with helpers for each OAuth step."""

    def __init__(self, http: httpx.AsyncClient, wahoo: FakeWahoo) -> None:
        self.http = http
        self.wahoo = wahoo

    async def register(
        self, method: str = "none", redirect_uris: list[str] | None = None
    ) -> httpx.Response:
        return await self.http.post(
            "/register",
            json={
                "redirect_uris": redirect_uris or [CLAUDE_REDIRECT_URI],
                "token_endpoint_auth_method": method,
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "client_name": "Claude",
            },
        )

    async def client(self, method: str = "none") -> dict[str, Any]:
        response = await self.register(method)
        assert response.status_code == 201, response.text
        return response.json()

    async def authorize(
        self, client: dict[str, Any], challenge: str, resource: str = MCP_URL
    ) -> httpx.Response:
        return await self.http.get(
            "/authorize",
            params={
                "response_type": "code",
                "client_id": client["client_id"],
                "redirect_uri": CLAUDE_REDIRECT_URI,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": "state-123",
                "resource": resource,
            },
        )

    async def login_request(self, client: dict[str, Any], challenge: str) -> str:
        response = await self.authorize(client, challenge)
        assert response.status_code == 302, response.text
        location = response.headers["location"]
        assert location.startswith(f"{PUBLIC_URL}/login?")
        return query(location)["request"]

    async def submit_login(self, request: str, email: str, password: str) -> httpx.Response:
        return await self.http.post(
            "/login", data={"request": request, "email": email, "password": password}
        )

    async def code(self, client: dict[str, Any], email: str) -> tuple[str, str]:
        verifier, challenge = pkce()
        request = await self.login_request(client, challenge)
        response = await self.submit_login(request, email, PASSWORDS[email])
        assert response.status_code == 302, response.text
        params = query(response.headers["location"])
        assert response.headers["location"].startswith(f"{CLAUDE_REDIRECT_URI}?")
        assert params["state"] == "state-123"
        return params["code"], verifier

    async def token(self, client: dict[str, Any], **form: str) -> httpx.Response:
        data = {"client_id": client["client_id"], **form}
        if client.get("client_secret"):
            data["client_secret"] = client["client_secret"]
        return await self.http.post("/token", data=data)

    async def connect(self, email: str, method: str = "none") -> tuple[dict[str, Any], dict]:
        client = await self.client(method)
        code, verifier = await self.code(client, email)
        response = await self.token(
            client,
            grant_type="authorization_code",
            code=code,
            code_verifier=verifier,
            redirect_uri=CLAUDE_REDIRECT_URI,
        )
        assert response.status_code == 200, response.text
        return client, response.json()

    async def call_tool(
        self, access_token: str | None, name: str, arguments: dict[str, Any]
    ) -> httpx.Response:
        headers = dict(MCP_HEADERS)
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return await self.http.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
            headers=headers,
        )

    async def calendar(self, access_token: str) -> httpx.Response:
        args = {"start_date": "2026-09-01", "end_date": "2026-09-07"}
        return await self.call_tool(access_token, "get_calendar", args)


@pytest.fixture
def wahoo() -> FakeWahoo:
    return FakeWahoo()


def make_app(wahoo: FakeWahoo, settings: RemoteSettings | None = None) -> StarletteWithLifespan:
    return create_remote_app(
        settings or make_settings(),
        verify_login=wahoo.verify_login,
        clients=UserClients(client_factory=wahoo.new_client),  # type: ignore[arg-type]
    )


@asynccontextmanager
async def serve(wahoo: FakeWahoo, settings: RemoteSettings | None = None) -> AsyncIterator[Server]:
    """Run the app's lifespan and an HTTP client for it (in the test's own task, as anyio needs)."""
    app = make_app(wahoo, settings)
    async with (
        app.lifespan(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=PUBLIC_URL) as http,
    ):
        yield Server(http, wahoo)


class TestDiscovery:
    async def test_protected_resource_metadata(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            response = await server.http.get("/.well-known/oauth-protected-resource/mcp")
            assert response.status_code == 200
            assert response.json()["resource"] == MCP_URL
            assert response.json()["authorization_servers"] == [f"{PUBLIC_URL}/"]

    async def test_authorization_server_metadata(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            response = await server.http.get("/.well-known/oauth-authorization-server")
            metadata = response.json()
            assert metadata["authorization_endpoint"] == f"{PUBLIC_URL}/authorize"
            assert metadata["registration_endpoint"] == f"{PUBLIC_URL}/register"
            assert "revocation_endpoint" not in metadata

    async def test_mcp_requires_token(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            response = await server.calendar("")
            assert response.status_code == 401
            assert "oauth-protected-resource/mcp" in response.headers["www-authenticate"]

    async def test_mcp_rejects_bad_token(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            response = await server.calendar("not-a-token")
            assert response.status_code == 401


class TestRegistration:
    async def test_public_client(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            client = await server.client()
            assert "client_secret" not in client
            assert client["redirect_uris"] == [CLAUDE_REDIRECT_URI]
            # The ID is sealed, not a random UUID the server would have to remember
            assert len(client["client_id"]) > 60

    async def test_confidential_client_gets_derived_secret(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            client = await server.client("client_secret_post")
            assert client["client_secret"]
            assert client["client_secret_expires_at"] == 0

    async def test_rejects_other_redirect_uris(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            response = await server.register(redirect_uris=["https://evil.example/callback"])
            assert response.status_code == 400
            assert response.json()["error"] == "invalid_redirect_uri"

    async def test_rejects_unsupported_auth_method(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            response = await server.register("private_key_jwt")
            assert response.status_code == 400
            assert response.json()["error"] == "invalid_client_metadata"

    async def test_unknown_client(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            _, challenge = pkce()
            response = await server.authorize({"client_id": "made-up"}, challenge)
            assert response.status_code == 400


class TestSignIn:
    async def test_login_page(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            client = await server.client()
            request = await server.login_request(client, pkce()[1])

            response = await server.http.get("/login", params={"request": request})

            assert response.status_code == 200
            assert "Connect <strong>claude.ai</strong> to your Wahoo SYSTM account" in response.text
            assert 'name="password"' in response.text
            csp = response.headers["content-security-policy"]
            assert "form-action 'self' https://claude.ai" in csp
            assert "frame-ancestors 'none'" in csp
            assert response.headers["cache-control"] == "no-store"

    async def test_rejects_wrong_resource(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            client = await server.client()
            response = await server.authorize(
                client, pkce()[1], resource="https://other.example/mcp"
            )
            assert response.status_code == 302
            params = query(response.headers["location"])
            assert params["error"] == "invalid_request"
            assert params["state"] == "state-123"

    @pytest.mark.parametrize("request_value", ["", "garbage"])
    async def test_expired_or_invalid_request(self, wahoo: FakeWahoo, request_value: str) -> None:
        async with serve(wahoo) as server:
            response = await server.http.get("/login", params={"request": request_value})
            assert response.status_code == 400
            assert "expired" in response.text

    async def test_email_not_allowed(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            request = await server.login_request(await server.client(), pkce()[1])
            response = await server.submit_login(request, "mallory@example.com", "whatever")
            assert response.status_code == 403
            assert "mallory@example.com isn&#x27;t allowed" in response.text

    async def test_missing_fields(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            request = await server.login_request(await server.client(), pkce()[1])
            response = await server.submit_login(request, ALICE, "")
            assert response.status_code == 400

    async def test_wrong_password_keeps_email(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            request = await server.login_request(await server.client(), pkce()[1])
            response = await server.submit_login(request, "  Alice@Example.com ", "wrong")
            assert response.status_code == 401
            assert "didn&#x27;t accept" in response.text
            assert f'value="{ALICE}"' in response.text

    async def test_too_many_failures(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            request = await server.login_request(await server.client(), pkce()[1])
            for _ in range(MAX_FAILED_LOGINS):
                assert (await server.submit_login(request, ALICE, "wrong")).status_code == 401
            response = await server.submit_login(request, ALICE, PASSWORDS[ALICE])
            assert response.status_code == 429
            # Other accounts aren't affected
            assert (await server.submit_login(request, BOB, PASSWORDS[BOB])).status_code == 302

    async def test_wahoo_unreachable(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            request = await server.login_request(await server.client(), pkce()[1])
            wahoo.down = True
            response = await server.submit_login(request, ALICE, PASSWORDS[ALICE])
            assert response.status_code == 502


class TestTokens:
    async def test_code_exchange_and_tool_call(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            _, tokens = await server.connect(ALICE)
            assert tokens["token_type"] == "Bearer"
            assert tokens["expires_in"] == 3600
            # The Wahoo password is inside, but encrypted
            assert PASSWORDS[ALICE].encode() not in base64.urlsafe_b64decode(
                tokens["access_token"] + "=="
            )

            response = await server.calendar(tokens["access_token"])

            assert response.status_code == 200, response.text
            assert f"plan of {ALICE}" in response.text
            assert [c.email for c in wahoo.clients] == [ALICE]

    async def test_each_user_gets_their_own_client(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            _, alice = await server.connect(ALICE)
            _, bob = await server.connect(BOB)

            alice_response = await server.calendar(alice["access_token"])
            bob_response = await server.calendar(bob["access_token"])
            await server.calendar(alice["access_token"])

            assert f"plan of {ALICE}" in alice_response.text
            assert ALICE not in bob_response.text
            assert f"plan of {BOB}" in bob_response.text
            assert sorted(c.email or "" for c in wahoo.clients) == [ALICE, BOB]
            assert all(c.logins == 1 for c in wahoo.clients)

    async def test_wrong_verifier(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            client = await server.client()
            code, _ = await server.code(client, ALICE)
            response = await server.token(
                client,
                grant_type="authorization_code",
                code=code,
                code_verifier=pkce()[0],
                redirect_uri=CLAUDE_REDIRECT_URI,
            )
            assert response.status_code == 401
            assert response.json()["error"] == "invalid_grant"

    async def test_code_is_bound_to_client(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            code, verifier = await server.code(await server.client(), ALICE)
            response = await server.token(
                await server.client(),
                grant_type="authorization_code",
                code=code,
                code_verifier=verifier,
                redirect_uri=CLAUDE_REDIRECT_URI,
            )
            assert response.json()["error"] == "invalid_grant"

    async def test_confidential_client_needs_secret(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            client = await server.client("client_secret_post")
            code, verifier = await server.code(client, ALICE)
            response = await server.token(
                {**client, "client_secret": "wrong"},
                grant_type="authorization_code",
                code=code,
                code_verifier=verifier,
                redirect_uri=CLAUDE_REDIRECT_URI,
            )
            assert response.status_code == 401

            _, tokens = await server.connect(ALICE, "client_secret_post")
            assert tokens["access_token"]

    async def test_refresh(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            client, tokens = await server.connect(ALICE)

            response = await server.token(
                client, grant_type="refresh_token", refresh_token=tokens["refresh_token"]
            )

            assert response.status_code == 200, response.text
            refreshed = response.json()
            assert refreshed["refresh_token"] != tokens["refresh_token"]
            assert (await server.calendar(refreshed["access_token"])).status_code == 200

    async def test_refresh_after_password_change(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            client, tokens = await server.connect(ALICE)
            wahoo.passwords[ALICE] = "changed"

            response = await server.token(
                client, grant_type="refresh_token", refresh_token=tokens["refresh_token"]
            )

            assert response.status_code == 401
            assert response.json()["error"] == "invalid_grant"

    async def test_refresh_token_is_not_an_access_token(self, wahoo: FakeWahoo) -> None:
        async with serve(wahoo) as server:
            _, tokens = await server.connect(ALICE)
            assert (await server.calendar(tokens["refresh_token"])).status_code == 401

    async def test_removed_email_is_signed_out(self, wahoo: FakeWahoo) -> None:
        # Two instances with the same secret, the second after ALICE left the allowlist
        before = make_app(wahoo)
        after = make_app(wahoo, make_settings(allowed_emails=frozenset({BOB})))
        async with (
            before.lifespan(before),
            after.lifespan(after),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=before), base_url=PUBLIC_URL
            ) as http_before,
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=after), base_url=PUBLIC_URL
            ) as http_after,
        ):
            client, tokens = await Server(http_before, wahoo).connect(ALICE)
            server_after = Server(http_after, wahoo)

            assert (await server_after.calendar(tokens["access_token"])).status_code == 401
            response = await server_after.token(
                client, grant_type="refresh_token", refresh_token=tokens["refresh_token"]
            )
            assert response.json()["error"] == "invalid_grant"


class TestProviderDirectly:
    async def test_exchange_rejects_foreign_types(self) -> None:
        from mcp.server.auth.provider import AuthorizationCode, RefreshToken, TokenError

        provider = WahooOAuthProvider(make_settings())
        client = MagicMock()
        code = AuthorizationCode(
            code="c",
            scopes=[],
            expires_at=9e9,
            client_id="c",
            code_challenge="x",
            redirect_uri=CLAUDE_REDIRECT_URI,  # type: ignore[arg-type]
            redirect_uri_provided_explicitly=True,
        )
        with pytest.raises(TokenError):
            await provider.exchange_authorization_code(client, code)
        with pytest.raises(TokenError):
            await provider.exchange_refresh_token(
                client, RefreshToken(token="t", client_id="c", scopes=[]), []
            )
        await provider.revoke_token(RefreshToken(token="t", client_id="c", scopes=[]))

    async def test_wahoo_login_closes_client(self) -> None:
        with patch.object(oauth, "WahooClient") as client_class:
            client = client_class.return_value
            client.authenticate = AsyncMock(side_effect=InvalidCredentialsError("nope"))
            client.close = AsyncMock()
            with pytest.raises(InvalidCredentialsError):
                await wahoo_login(ALICE, "pw")
            client.close.assert_awaited_once()


# =============================================================================
# UserClients
# =============================================================================


def access_token(email: str, password: str) -> WahooAccessToken:
    return WahooAccessToken(
        token="t", client_id="c", scopes=[], email=email, password=SecretStr(password)
    )


class TestUserClients:
    @pytest.fixture
    def clock(self) -> list[float]:
        return [1000.0]

    @pytest.fixture
    def clients(self, wahoo: FakeWahoo, clock: list[float]) -> UserClients:
        return UserClients(wahoo.new_client, session_max_age=3600, clock=lambda: clock[0])  # type: ignore[arg-type]

    async def get(self, clients: UserClients, token: WahooAccessToken | None) -> FakeClient:
        with patch("wahoo_systm_mcp.remote.clients.get_access_token", return_value=token):
            return cast("FakeClient", await clients.get())

    async def test_reuses_client(self, clients: UserClients, wahoo: FakeWahoo) -> None:
        first = await self.get(clients, access_token(ALICE, PASSWORDS[ALICE]))
        second = await self.get(clients, access_token(ALICE, PASSWORDS[ALICE]))
        assert first is second
        assert first.logins == 1

    async def test_signs_in_again_after_max_age(
        self, clients: UserClients, clock: list[float]
    ) -> None:
        first = await self.get(clients, access_token(ALICE, PASSWORDS[ALICE]))
        clock[0] += 3600
        second = await self.get(clients, access_token(ALICE, PASSWORDS[ALICE]))
        assert second is first
        assert first.logins == 2

    async def test_signs_in_again_with_new_password(
        self, clients: UserClients, wahoo: FakeWahoo
    ) -> None:
        first = await self.get(clients, access_token(ALICE, PASSWORDS[ALICE]))
        wahoo.passwords[ALICE] = "new-password"
        second = await self.get(clients, access_token(ALICE, "new-password"))
        assert second is first
        assert first.logins == 2

    async def test_rejected_credentials(self, clients: UserClients, wahoo: FakeWahoo) -> None:
        with pytest.raises(ToolError, match="reconnect"):
            await self.get(clients, access_token(ALICE, "wrong"))
        assert wahoo.clients[0].closed
        assert RECONNECT_MESSAGE.startswith("Wahoo SYSTM no longer accepts")

    async def test_wahoo_down_is_not_a_reconnect(
        self, clients: UserClients, wahoo: FakeWahoo
    ) -> None:
        wahoo.down = True
        with pytest.raises(WahooAPIError, match="timed out"):
            await self.get(clients, access_token(ALICE, PASSWORDS[ALICE]))

    async def test_needs_signed_in_user(self, clients: UserClients) -> None:
        with pytest.raises(ToolError, match="Not signed in"):
            await self.get(clients, None)

    async def test_close(self, clients: UserClients, wahoo: FakeWahoo) -> None:
        await self.get(clients, access_token(ALICE, PASSWORDS[ALICE]))
        await self.get(clients, access_token(BOB, PASSWORDS[BOB]))
        await clients.close()
        assert all(c.closed for c in wahoo.clients)


# =============================================================================
# Lambda entry point
# =============================================================================


class TestLambdaApp:
    def test_create_app_reads_ssm(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from wahoo_systm_mcp.remote import lambda_app

        ssm = MagicMock()
        ssm.get_parameters.return_value = {
            "Parameters": [
                {"Name": "/custom/SIGNING_SECRET", "Value": SECRET},
                {"Name": "/custom/ALLOWED_EMAILS", "Value": json.dumps([ALICE])},
                {"Name": "/custom/PUBLIC_URL", "Value": f"{PUBLIC_URL}/"},
            ],
        }
        monkeypatch.setenv("SSM_PREFIX", "/custom")
        monkeypatch.setattr(lambda_app.boto3, "client", MagicMock(return_value=ssm))

        app = lambda_app.create_app()

        lambda_app.boto3.client.assert_called_once_with("ssm")  # type: ignore[attr-defined]
        assert app.state.path == "/mcp"
