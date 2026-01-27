"""Wahoo SYSTM MCP Server."""

from importlib.metadata import version

from wahoo_systm_mcp.client import WahooClient
from wahoo_systm_mcp.server import mcp

__version__ = version("wahoo-systm-mcp")
__all__ = ["WahooClient", "mcp", "__version__"]
