"""ASGI app for the multi-user remote server."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from wahoo_systm_mcp.remote.clients import UserClients
from wahoo_systm_mcp.remote.oauth import WahooOAuthProvider, wahoo_login
from wahoo_systm_mcp.server.app import create_server

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable

    from fastmcp import FastMCP
    from fastmcp.server.http import StarletteWithLifespan

    from wahoo_systm_mcp.remote.settings import RemoteSettings
    from wahoo_systm_mcp.server.lifecycle import ClientSource

MCP_PATH = "/mcp"


def create_remote_app(
    settings: RemoteSettings,
    *,
    verify_login: Callable[[str, str], Awaitable[None]] = wahoo_login,
    clients: UserClients | None = None,
) -> StarletteWithLifespan:
    """Build the app: OAuth endpoints, the sign-in page, and the MCP endpoint at /mcp."""
    user_clients = clients or UserClients()

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[dict[str, ClientSource]]:
        try:
            yield {"clients": user_clients}
        finally:
            await user_clients.close()

    provider = WahooOAuthProvider(settings, verify_login=verify_login)
    server = create_server(lifespan=lifespan, auth=provider)
    # Stateless with plain JSON responses: any instance can serve any request, and there are no
    # sessions or SSE streams to keep (a Lambda instance only runs while handling a request)
    return server.http_app(path=MCP_PATH, stateless_http=True, json_response=True)
