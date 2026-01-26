"""HTTP server entrypoint for Wahoo SYSTM MCP."""

from __future__ import annotations

import os
import sys

from wahoo_systm_mcp.server.app import mcp
from wahoo_systm_mcp.server.config import HTTP_HOST, HTTP_PORT, HTTP_TRANSPORT


def main() -> None:
    """Run the MCP server over HTTP transport."""
    if not os.environ.get("WAHOO_USERNAME") or not os.environ.get("WAHOO_PASSWORD"):
        print(
            "Error: Missing Wahoo SYSTM credentials. "
            "Set WAHOO_USERNAME and WAHOO_PASSWORD environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)
    mcp.run(transport=HTTP_TRANSPORT, host=HTTP_HOST, port=HTTP_PORT)


if __name__ == "__main__":
    main()
