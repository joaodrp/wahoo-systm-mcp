"""Entry point for running the MCP server (stdio)."""

from __future__ import annotations

import os
import sys

from wahoo_systm_mcp.server.app import mcp


def main() -> None:
    """Run the MCP server over stdio transport."""
    if not os.environ.get("WAHOO_USERNAME") or not os.environ.get("WAHOO_PASSWORD"):
        print(
            "Error: Missing Wahoo SYSTM credentials. "
            "Set WAHOO_USERNAME and WAHOO_PASSWORD environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)
    mcp.run()


if __name__ == "__main__":
    main()
