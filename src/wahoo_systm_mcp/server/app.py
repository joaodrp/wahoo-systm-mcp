"""FastMCP server entrypoint for Wahoo SYSTM tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from wahoo_systm_mcp.server.lifecycle import app_lifespan
from wahoo_systm_mcp.server.register import register_tools

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractAsyncContextManager

    from fastmcp.server.auth import AuthProvider


def create_server(
    lifespan: Callable[[FastMCP], AbstractAsyncContextManager[Any]] = app_lifespan,
    auth: AuthProvider | None = None,
) -> FastMCP:
    """Build a server with all tools; the lifespan must yield {"clients": ClientSource}."""
    server = FastMCP("wahoo-systm", lifespan=lifespan, auth=auth)
    register_tools(server)
    return server


mcp = create_server()
