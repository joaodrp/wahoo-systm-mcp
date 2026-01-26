"""Server lifecycle hooks and shared context helpers."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from wahoo_systm_mcp.client import WahooClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastmcp import Context, FastMCP


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, WahooClient]]:
    """Initialize shared resources for the server lifetime.

    Credentials are validated in entry points before the server starts.
    """
    username = os.environ["WAHOO_USERNAME"]
    password = os.environ["WAHOO_PASSWORD"]
    client = WahooClient()
    await client.authenticate(username, password)
    try:
        yield {"client": client}
    finally:
        await client.close()


def get_client(ctx: Context) -> WahooClient:
    """Get the authenticated WahooClient from context."""
    client: WahooClient = ctx.lifespan_context["client"]
    return client
