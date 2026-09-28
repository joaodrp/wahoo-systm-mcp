"""Wahoo SYSTM clients for the people signed in to the remote server."""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token

from wahoo_systm_mcp.client import InvalidCredentialsError, WahooClient
from wahoo_systm_mcp.remote.oauth import WahooAccessToken

if TYPE_CHECKING:
    from collections.abc import Callable

# Sign in to Wahoo again after this long, in case its session token has expired
SESSION_MAX_AGE = 60 * 60

RECONNECT_MESSAGE = (
    "Wahoo SYSTM no longer accepts the email and password this connector signed in with. "
    "Disconnect and reconnect it in Claude's connector settings."
)


@dataclass
class _Session:
    client: WahooClient
    password_digest: bytes
    signed_in_at: float


class UserClients:
    """A signed-in WahooClient per user, kept for the lifetime of the server instance.

    Each user has their own client: WahooClient caches the rider profile, so sharing one
    between users would leak data. Clients sign in with the Wahoo credentials carried by the
    request's access token, on first use and again after SESSION_MAX_AGE or a password change.
    """

    def __init__(
        self,
        client_factory: Callable[[], WahooClient] = WahooClient,
        *,
        session_max_age: float = SESSION_MAX_AGE,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._client_factory = client_factory
        self._session_max_age = session_max_age
        self._clock = clock
        self._sessions: dict[str, _Session] = {}
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def get(self) -> WahooClient:
        """Return the signed-in client for the user whose access token made this request."""
        token = get_access_token()
        if not isinstance(token, WahooAccessToken):
            msg = "Not signed in"
            raise ToolError(msg)
        try:
            return await self._client_for(token.email, token.password.get_secret_value())
        except InvalidCredentialsError as e:
            raise ToolError(RECONNECT_MESSAGE) from e

    async def _client_for(self, email: str, password: str) -> WahooClient:
        digest = hashlib.sha256(password.encode()).digest()
        async with self._locks[email]:
            session = self._sessions.get(email)
            if (
                session is not None
                and session.password_digest == digest
                and self._clock() - session.signed_in_at < self._session_max_age
            ):
                return session.client

            # Sign the existing client in again rather than replacing it, as other requests
            # for this user may still be using it
            client = session.client if session is not None else self._client_factory()
            try:
                await client.authenticate(email, password)
            except BaseException:
                self._sessions.pop(email, None)
                await client.close()
                raise
            self._sessions[email] = _Session(client, digest, self._clock())
            return client

    async def close(self) -> None:
        sessions = list(self._sessions.values())
        self._sessions.clear()
        for session in sessions:
            await session.client.close()
