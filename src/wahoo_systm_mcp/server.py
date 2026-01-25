"""FastMCP server with Wahoo SYSTM tools."""

from collections.abc import AsyncIterator
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.server.lifespan import lifespan


@lifespan
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Initialize shared resources for the server lifetime."""
    # TODO: Initialize WahooClient and authenticate
    yield {"client": None}


mcp = FastMCP("wahoo-systm", lifespan=app_lifespan)


@mcp.tool
async def get_rider_profile(ctx: Context) -> str:
    """Get the rider's 4DP profile (NM, AC, MAP, FTP) and rider type."""
    # POC: validate tool registration and context access works
    _ = ctx.lifespan_context["client"]
    return "POC: Tool registration and lifespan context working"
