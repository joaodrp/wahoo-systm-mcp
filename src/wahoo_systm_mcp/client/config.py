"""Configuration for the Wahoo SYSTM API client."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_API_URL = "https://api.thesufferfest.com/graphql"
DEFAULT_APP_VERSION = "7.101.1-web.3480-7-g4802ce80"
DEFAULT_APP_PLATFORM = "web"
DEFAULT_LOCALE = "en"
DEFAULT_TIMEOUT = 30.0


@dataclass(frozen=True, slots=True)
class ClientConfig:
    """Runtime configuration for WahooClient."""

    api_url: str = DEFAULT_API_URL
    app_version: str = DEFAULT_APP_VERSION
    install_id: str | None = None
    app_platform: str = DEFAULT_APP_PLATFORM
    default_locale: str = DEFAULT_LOCALE
    timeout: float = DEFAULT_TIMEOUT

    @classmethod
    def from_env(cls) -> ClientConfig:
        """Build configuration from environment variables."""
        return cls(
            app_version=os.environ.get("WAHOO_APP_VERSION", DEFAULT_APP_VERSION),
            install_id=os.environ.get("WAHOO_INSTALL_ID"),
            default_locale=os.environ.get("WAHOO_LOCALE", DEFAULT_LOCALE),
        )
