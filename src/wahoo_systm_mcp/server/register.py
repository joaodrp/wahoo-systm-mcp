"""Register MCP tools for the server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from wahoo_systm_mcp.tools import calendar, library, profile

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_tools(app: FastMCP) -> None:
    """Register all tools with the provided FastMCP app."""
    calendar.register(app)
    library.register(app)
    profile.register(app)
