"""Server lifecycle hooks and shared context helpers."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Protocol

from wahoo_systm_mcp.client import WahooClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastmcp import Context, FastMCP


class ClientSource(Protocol):
    """Provides the WahooClient for the user making the current request."""

    async def get(self) -> WahooClient: ...


class StaticClient:
    """A single client shared by every request (stdio and single-user HTTP)."""

    def __init__(self, client: WahooClient) -> None:
        self._client = client

    async def get(self) -> WahooClient:
        return self._client


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[dict[str, ClientSource]]:
    """Initialize shared resources for the server lifetime.

    Credentials are validated in entry points before the server starts.
    """
    username = os.environ["WAHOO_USERNAME"]
    password = os.environ["WAHOO_PASSWORD"]
    client = WahooClient()
    await client.authenticate(username, password)
    try:
        yield {"clients": StaticClient(client)}
    finally:
        await client.close()


async def get_client(ctx: Context) -> WahooClient:
    """Get the authenticated WahooClient for the current request's user."""
    clients: ClientSource = ctx.lifespan_context["clients"]
    return await clients.get()
