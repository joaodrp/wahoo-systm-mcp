"""FastMCP server entrypoint for Wahoo SYSTM tools."""

from fastmcp import FastMCP

from wahoo_systm_mcp.server.lifecycle import app_lifespan
from wahoo_systm_mcp.server.register import register_tools

mcp = FastMCP("wahoo-systm", lifespan=app_lifespan)
register_tools(mcp)
