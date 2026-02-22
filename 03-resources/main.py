"""
03-resources: Introducing the MCP Resources primitive.

Resources expose *data* via URIs — like a read-only filesystem for the AI.
The client can list available resources and fetch them by URI.

Two flavours shown here:
  - Static resource:   fixed URI, always the same data source
  - Dynamic resource:  URI template with {param}, resolved at read time

Compare with tools (02-pacman): tools are actions Claude *calls*.
Resources are data Claude *reads* — no side effects, just content.
"""

import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("system-info")


# --- Static resources ---
# @mcp.resource("uri") registers a fixed URI.
# The function is called when the client reads that URI.
# The docstring becomes the resource description the client sees when listing.

@mcp.resource("system://os-release")
def os_release() -> str:
    """Current OS identity — contents of /etc/os-release."""
    return Path("/etc/os-release").read_text()


@mcp.resource("system://pacman-log")
def pacman_log() -> str:
    """Last 100 lines of the pacman package manager log."""
    lines = Path("/var/log/pacman.log").read_text().splitlines()
    return "\n".join(lines[-100:])


@mcp.resource("system://memory")
def memory_info() -> str:
    """Current memory usage — contents of /proc/meminfo."""
    return Path("/proc/meminfo").read_text()


# --- Dynamic resource (template) ---
# URI templates use {param} placeholders.
# FastMCP maps the placeholder to the function argument by name.
# The client can pass any value — e.g. system://journal/nginx

@mcp.resource("system://journal/{service}")
def journal(service: str) -> str:
    """
    Last 50 log lines for a systemd service.
    URI: system://journal/{service}  e.g. system://journal/sshd
    """
    result = subprocess.run(
        ["journalctl", "-u", service, "-n", "50", "--no-pager"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(f"Could not fetch journal for '{service}': {result.stderr.strip()}")
    return result.stdout


if __name__ == "__main__":
    mcp.run()
