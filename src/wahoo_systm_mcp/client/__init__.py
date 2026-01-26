"""Client package for the Wahoo SYSTM GraphQL API."""

from wahoo_systm_mcp.client.api import (  # noqa: F401
    CHANNEL_ID_TO_NAME,
    FULL_FRONTAL_ID,
    HALF_MONTY_ID,
    AuthenticationError,
    WahooAPIError,
    WahooClient,
)
from wahoo_systm_mcp.client.config import (  # noqa: F401
    DEFAULT_API_URL,
    DEFAULT_APP_PLATFORM,
    DEFAULT_APP_VERSION,
    DEFAULT_LOCALE,
    DEFAULT_TIMEOUT,
    ClientConfig,
)

__all__ = [
    "CHANNEL_ID_TO_NAME",
    "FULL_FRONTAL_ID",
    "HALF_MONTY_ID",
    "AuthenticationError",
    "WahooAPIError",
    "WahooClient",
    "ClientConfig",
    "DEFAULT_API_URL",
    "DEFAULT_APP_PLATFORM",
    "DEFAULT_APP_VERSION",
    "DEFAULT_LOCALE",
    "DEFAULT_TIMEOUT",
]
