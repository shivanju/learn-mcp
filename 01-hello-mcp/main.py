"""
01-hello-mcp: The simplest possible MCP server.

An MCP server is just a Python process that speaks the MCP protocol.
Claude (the client) starts this process and communicates over stdio.

This server exposes two tools: `greet` and `add`
"""

from mcp.server.fastmcp import FastMCP

# FastMCP handles all the JSON-RPC protocol boilerplate.
# The string becomes the server's name — Claude sees this.
mcp = FastMCP("hello-mcp")


# @mcp.tool() registers this function as an MCP tool.
# Type hints → auto-generated JSON schema (so Claude knows what args to pass)
# Docstring → tool description (so Claude knows when to use it)
@mcp.tool()
def greet(name: str) -> str:
    """Greet a person by name. Returns a friendly greeting message."""
    return f"Hello, {name}! This response came from a Python process running on your machine."


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together and return the result."""
    return a + b


# mcp.run() starts the server on stdio.
# Claude Code will launch this process and pipe JSON-RPC messages to it.
if __name__ == "__main__":
    mcp.run()
