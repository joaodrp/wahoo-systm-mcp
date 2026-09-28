"""HTTP server entrypoint for Wahoo SYSTM MCP."""

from __future__ import annotations

import os
import sys

from wahoo_systm_mcp.server.app import mcp
from wahoo_systm_mcp.server.config import HTTP_HOST, HTTP_PORT, HTTP_TRANSPORT


def main() -> None:
    """Run the MCP server over HTTP transport.

    With MCP_SIGNING_SECRET set, runs the multi-user server that AWS Lambda hosts: OAuth
    sign-in with each person's own Wahoo SYSTM account. Otherwise serves the single
    WAHOO_USERNAME account without authentication.
    """
    if os.environ.get("MCP_SIGNING_SECRET"):
        _run_multi_user()
        return
    if not os.environ.get("WAHOO_USERNAME") or not os.environ.get("WAHOO_PASSWORD"):
        print(
            "Error: Missing Wahoo SYSTM credentials. "
            "Set WAHOO_USERNAME and WAHOO_PASSWORD environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)
    mcp.run(transport=HTTP_TRANSPORT, host=HTTP_HOST, port=HTTP_PORT)


def _run_multi_user() -> None:
    import uvicorn  # noqa: PLC0415 - only needed in this mode

    from wahoo_systm_mcp.remote.app import create_remote_app  # noqa: PLC0415
    from wahoo_systm_mcp.remote.settings import RemoteSettings, SettingsError  # noqa: PLC0415

    try:
        settings = RemoteSettings.from_env()
    except SettingsError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Multi-user server: {settings.public_url}/mcp", file=sys.stderr)
    uvicorn.run(create_remote_app(settings), host=HTTP_HOST, port=HTTP_PORT)


if __name__ == "__main__":
    main()
