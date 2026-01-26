"""Server configuration derived from environment variables."""

from __future__ import annotations

import os
from typing import Literal, cast

Transport = Literal["stdio", "http", "sse", "streamable-http"]

HTTP_HOST = os.environ.get("HTTP_HOST", "127.0.0.1")
HTTP_PORT = int(os.environ.get("HTTP_PORT", "8000"))
HTTP_TRANSPORT = cast("Transport", os.environ.get("HTTP_TRANSPORT", "http"))
