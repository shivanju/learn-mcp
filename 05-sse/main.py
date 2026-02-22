"""
05-sse: MCP server over SSE (Server-Sent Events) transport.

The ONLY code difference from 02-pacman is the last line:
    stdio:  mcp.run()               → Claude Code spawns and owns this process
    SSE:    mcp.run(transport="sse") → YOU own this process, clients just connect

Everything else — tools, resources, prompts — works identically.
The transport is purely an operational concern, not a code concern.

Operational model:
    1. You start this server manually (or via systemd)
    2. It listens on http://localhost:8000/sse
    3. Any MCP client connects to that URL
    4. Server keeps running when clients disconnect
    5. Multiple clients can connect simultaneously
"""

import subprocess

from mcp.server.fastmcp import FastMCP

# host/port are configurable — useful when running multiple SSE servers
mcp = FastMCP("pacman-sse", host="127.0.0.1", port=8000)

ALLOWED_PREFIXES = {"-Q", "-h", "--help", "--query"}


def _run(args: list[str]) -> str:
    result = subprocess.run(["pacman"] + args, capture_output=True, text=True)
    if result.returncode != 0 and result.stderr:
        raise ValueError(result.stderr.strip())
    return result.stdout.strip()


def _validate(args: list[str]) -> None:
    if not args:
        raise ValueError("No arguments provided.")
    first = args[0]
    if not any(first.startswith(p) for p in ALLOWED_PREFIXES):
        raise ValueError(
            f"Only read-only query flags are allowed (e.g. -Q, -Qi, -Qs, -Ql, -Qo, -Qdt). "
            f"Got: '{first}'"
        )


@mcp.tool()
def pacman_query(args: list[str]) -> str:
    """
    Run a read-only pacman query and return the output.
    Only -Q (query) operations are permitted.

    Common usage:
    - List all installed:     ["-Q"]
    - Search installed:       ["-Qs", "<term>"]
    - Package details:        ["-Qi", "<package>"]
    - Files owned by pkg:     ["-Ql", "<package>"]
    - Owner of a file:        ["-Qo", "<path>"]
    - Orphaned packages:      ["-Qdt"]
    """
    _validate(args)
    return _run(args)


if __name__ == "__main__":
    # transport="sse" is the only line that differs from the stdio version.
    # FastMCP starts a uvicorn HTTP server. SSE endpoint: /sse
    mcp.run(transport="sse")
