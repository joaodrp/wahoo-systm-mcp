"""Configuration for the remote server, from environment variables or SSM Parameter Store."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from botocore.client import BaseClient

CLAUDE_REDIRECT_URI = "https://claude.ai/api/mcp/auth_callback"
DEFAULT_SSM_PREFIX = "/wahoo-systm-mcp"
MIN_SIGNING_SECRET_LENGTH = 32

# Names under the SSM prefix. SIGNING_SECRET and ALLOWED_EMAILS are SecureStrings managed with
# `python -m wahoo_systm_mcp.remote.admin`; PUBLIC_URL is a String written by template.yaml.
SSM_SIGNING_SECRET = "SIGNING_SECRET"  # noqa: S105 - a parameter name
SSM_ALLOWED_EMAILS = "ALLOWED_EMAILS"
SSM_PUBLIC_URL = "PUBLIC_URL"

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SettingsError(ValueError):
    """Raised when the remote server's configuration is missing or invalid."""


def normalize_email(email: str) -> str:
    """Lowercase and trim an email address, as used for the allowlist and sign-in."""
    return email.strip().lower()


def parse_allowed_emails(value: str) -> frozenset[str]:
    """Parse an allowlist: a JSON array (as stored in SSM) or a comma-separated list."""
    text = value.strip()
    if text.startswith("["):
        items = json.loads(text)
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            msg = "The allowed emails must be a JSON array of strings"
            raise SettingsError(msg)
    else:
        items = re.split(r"[,\s]+", text)
    emails = frozenset(normalize_email(item) for item in items if item.strip())
    invalid = sorted(email for email in emails if not _EMAIL.match(email))
    if invalid:
        msg = f"Not valid email addresses: {', '.join(invalid)}"
        raise SettingsError(msg)
    return emails


def parse_redirect_uris(value: str | None) -> tuple[str, ...]:
    """Parse a comma-separated list of OAuth redirect URIs, defaulting to claude.ai's."""
    uris = tuple(uri.strip() for uri in (value or "").split(",") if uri.strip())
    return uris or (CLAUDE_REDIRECT_URI,)


@dataclass(frozen=True, slots=True)
class RemoteSettings:
    """What the remote server needs besides the code: where it lives and who may sign in."""

    # Public origin, e.g. the Lambda function URL; OAuth metadata embeds absolute URLs
    public_url: str
    # Seals client IDs, codes and tokens (which carry each user's Wahoo credentials)
    signing_secret: str
    # Emails of the Wahoo SYSTM accounts that may sign in
    allowed_emails: frozenset[str]
    # Redirect URIs OAuth clients may register, e.g. claude.ai's connector callback
    redirect_uris: tuple[str, ...] = (CLAUDE_REDIRECT_URI,)

    def __post_init__(self) -> None:
        if len(self.signing_secret) < MIN_SIGNING_SECRET_LENGTH:
            msg = f"The signing secret must be at least {MIN_SIGNING_SECRET_LENGTH} characters"
            raise SettingsError(msg)
        if not self.public_url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            msg = f"The public URL must use https (or be localhost): {self.public_url}"
            raise SettingsError(msg)
        object.__setattr__(self, "public_url", self.public_url.rstrip("/"))

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> RemoteSettings:
        """Build settings for a local test of the remote setup (see .env.example)."""
        env = os.environ if env is None else env
        secret = env.get("MCP_SIGNING_SECRET", "")
        emails = env.get("MCP_ALLOWED_EMAILS", "")
        if not secret or not emails:
            msg = "Set MCP_SIGNING_SECRET and MCP_ALLOWED_EMAILS to run the multi-user server"
            raise SettingsError(msg)
        port = env.get("HTTP_PORT", "8000")
        return cls(
            public_url=env.get("PUBLIC_URL") or f"http://localhost:{port}",
            signing_secret=secret,
            allowed_emails=parse_allowed_emails(emails),
            redirect_uris=parse_redirect_uris(env.get("OAUTH_REDIRECT_URIS")),
        )

    @classmethod
    def from_ssm(
        cls, ssm: BaseClient, prefix: str = DEFAULT_SSM_PREFIX, env: Mapping[str, str] | None = None
    ) -> RemoteSettings:
        """Build settings on Lambda, from SSM parameters under `prefix` (read once per cold start).

        Args:
            ssm: A boto3 SSM client.
            prefix: The SSM path holding the parameters.
            env: Environment for OAUTH_REDIRECT_URIS (defaults to os.environ).

        """
        env = os.environ if env is None else env
        names = [SSM_SIGNING_SECRET, SSM_ALLOWED_EMAILS, SSM_PUBLIC_URL]
        response = ssm.get_parameters(Names=[f"{prefix}/{n}" for n in names], WithDecryption=True)
        if response.get("InvalidParameters"):
            missing = ", ".join(response["InvalidParameters"])
            msg = (
                f"Missing SSM parameters: {missing}. Allow an email first with "
                "`uv run python -m wahoo_systm_mcp.remote.admin allow <email>`."
            )
            raise SettingsError(msg)
        values = {p["Name"][len(prefix) + 1 :]: p["Value"] for p in response["Parameters"]}
        return cls(
            public_url=values[SSM_PUBLIC_URL],
            signing_secret=values[SSM_SIGNING_SECRET],
            allowed_emails=parse_allowed_emails(values[SSM_ALLOWED_EMAILS]),
            redirect_uris=parse_redirect_uris(env.get("OAUTH_REDIRECT_URIS")),
        )
