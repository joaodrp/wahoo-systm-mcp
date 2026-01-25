"""Wahoo SYSTM MCP Server."""

from wahoo_systm_mcp.client import WahooClient
from wahoo_systm_mcp.server import mcp

__version__ = "1.0.0"
__all__ = ["WahooClient", "mcp", "__version__"]
