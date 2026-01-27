"""Client package for the Wahoo SYSTM GraphQL API."""

from wahoo_systm_mcp.client.api import (
    CHANNEL_ID_TO_NAME,
    FULL_FRONTAL_ID,
    HALF_MONTY_ID,
    AuthenticationError,
    WahooAPIError,
    WahooClient,
)
from wahoo_systm_mcp.client.config import (
    DEFAULT_API_URL,
    DEFAULT_APP_PLATFORM,
    DEFAULT_APP_VERSION,
    DEFAULT_LOCALE,
    DEFAULT_TIMEOUT,
    ClientConfig,
)

__all__ = [
    "CHANNEL_ID_TO_NAME",
    "DEFAULT_API_URL",
    "DEFAULT_APP_PLATFORM",
    "DEFAULT_APP_VERSION",
    "DEFAULT_LOCALE",
    "DEFAULT_TIMEOUT",
    "FULL_FRONTAL_ID",
    "HALF_MONTY_ID",
    "AuthenticationError",
    "ClientConfig",
    "WahooAPIError",
    "WahooClient",
]
