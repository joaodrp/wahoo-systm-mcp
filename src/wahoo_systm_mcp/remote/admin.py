"""Manage who can sign in to the Lambda-hosted server.

Run with `uv run python -m wahoo_systm_mcp.remote.admin <command>` (or `just users <command>`).

The allowlist and the token signing secret are SecureString parameters in SSM Parameter Store,
in the region of your default AWS profile (the one `sam deploy` uses). Lambda reads them once
per cold start, so every change here also recycles the function's running instances.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from wahoo_systm_mcp.remote.settings import (
    DEFAULT_SSM_PREFIX,
    SSM_ALLOWED_EMAILS,
    SSM_SIGNING_SECRET,
    SettingsError,
    parse_allowed_emails,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from botocore.client import BaseClient

FUNCTION_NAME = "wahoo-systm-mcp"  # FunctionName in template.yaml

USAGE = """commands:
  list                 Show the Wahoo SYSTM emails allowed to sign in
  allow EMAIL...       Allow emails to sign in (creates the signing secret the first time)
  deny EMAIL...        Stop emails signing in (signs them out everywhere)
  sign-out-all         Replace the signing secret (signs everyone out)"""


class Admin:
    """Reads and writes the server's SSM parameters, and recycles the function after changes."""

    def __init__(
        self,
        ssm: BaseClient,
        lambda_client: BaseClient,
        prefix: str = DEFAULT_SSM_PREFIX,
        out: Callable[[str], None] = print,
    ) -> None:
        self._ssm = ssm
        self._lambda = lambda_client
        self._prefix = prefix
        self._out = out

    def list(self) -> None:
        emails = self._load_emails()
        for email in sorted(emails):
            self._out(email)
        if not emails:
            self._out("No emails allowed yet. Add one with: allow <email>")

    def allow(self, emails: Sequence[str]) -> None:
        added = parse_allowed_emails(",".join(emails))
        current = self._load_emails()
        self._save_emails(current | added)
        for email in sorted(added):
            self._out(
                f"{email} already can sign in." if email in current else f"{email} can sign in."
            )
        self._recycle()

    def deny(self, emails: Sequence[str]) -> None:
        removed = parse_allowed_emails(",".join(emails))
        current = self._load_emails()
        unknown = sorted(removed - current)
        if unknown:
            msg = f"Not on the allowlist: {', '.join(unknown)}"
            raise SettingsError(msg)
        remaining = current - removed
        self._save_emails(remaining)
        for email in sorted(removed):
            self._out(f"{email} can no longer sign in.")
        if not remaining:
            self._out("Nobody can sign in now.")
        self._recycle()

    def sign_out_all(self) -> None:
        self._put(SSM_SIGNING_SECRET, _new_signing_secret())
        self._out("Replaced the signing secret: everyone has to connect again.")
        self._recycle()

    def _load_emails(self) -> frozenset[str]:
        value = self._get(SSM_ALLOWED_EMAILS)
        return parse_allowed_emails(value) if value else frozenset()

    def _save_emails(self, emails: frozenset[str]) -> None:
        if self._get(SSM_SIGNING_SECRET) is None:
            self._put(SSM_SIGNING_SECRET, _new_signing_secret())
        # A JSON array rather than a comma-separated list, as SSM values can't be empty
        self._put(SSM_ALLOWED_EMAILS, json.dumps(sorted(emails)))

    def _get(self, name: str) -> str | None:
        try:
            response = self._ssm.get_parameter(Name=f"{self._prefix}/{name}", WithDecryption=True)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ParameterNotFound":
                return None
            raise
        return response["Parameter"]["Value"]

    def _put(self, name: str, value: str) -> None:
        self._ssm.put_parameter(
            Name=f"{self._prefix}/{name}", Value=value, Type="SecureString", Overwrite=True
        )

    def _recycle(self) -> None:
        """Change the function's configuration so Lambda starts instances that re-read SSM."""
        try:
            self._lambda.update_function_configuration(
                FunctionName=FUNCTION_NAME,
                Description=f"Settings updated {datetime.now(UTC).isoformat(timespec='seconds')}",
            )
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != "ResourceNotFoundException":
                raise
            self._out(f"{FUNCTION_NAME} isn't deployed yet; deploy it next.")
            return
        self._out(f"Recycled {FUNCTION_NAME} so it picks up the change.")


def _new_signing_secret() -> str:
    return secrets.token_hex(32)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m wahoo_systm_mcp.remote.admin",
        description="Manage who can sign in to the Lambda-hosted Wahoo SYSTM MCP server.",
        epilog=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", choices=["list", "allow", "deny", "sign-out-all"])
    parser.add_argument("emails", nargs="*", metavar="EMAIL")
    parser.add_argument("--prefix", default=DEFAULT_SSM_PREFIX, help="SSM parameter path")
    args = parser.parse_args(argv)
    if args.command in ("allow", "deny") and not args.emails:
        parser.error(f"{args.command} needs at least one email")

    session = boto3.session.Session()
    print(f"Region: {session.region_name}")
    admin = Admin(session.client("ssm"), session.client("lambda"), args.prefix)
    try:
        if args.command == "list":
            admin.list()
        elif args.command == "allow":
            admin.allow(args.emails)
        elif args.command == "deny":
            admin.deny(args.emails)
        else:
            admin.sign_out_all()
    except SettingsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
