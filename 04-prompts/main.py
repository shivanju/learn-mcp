"""
04-prompts: Introducing the MCP Prompts primitive.

Prompts are reusable conversation starters — templates that pre-load
context so you don't have to describe your situation every time.

Key difference from tools and resources:
  - Tool     → Claude calls a function, gets a result (action)
  - Resource → Claude reads data from a URI (passive data)
  - Prompt   → YOU invoke a template, conversation is pre-structured (context injection)

Two return styles shown here:
  - str              → becomes a single user message (simple)
  - list[Message]    → full multi-turn conversation setup (rich)

These three prompts gather live system data inside the handler itself,
so the conversation starts with real context already loaded — no manual
copy-pasting of logs or stats.
"""

import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import AssistantMessage, UserMessage

mcp = FastMCP("local-assistant")


# --- Helpers ---

def _run(cmd: list[str], fallback: str = "(unavailable)") -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    except Exception:
        return fallback


# --- Prompts ---
# @mcp.prompt() registers a prompt. Docstring = description shown to the client.
# Args with type hints become the prompt's required parameters.
# Return value becomes the injected message(s).

@mcp.prompt()
def system_health() -> list[UserMessage | AssistantMessage]:
    """
    Snapshot current system health and ask Claude to flag anything concerning.
    Gathers: uptime, load, memory, disk, failed systemd services.
    No arguments needed — invoke and go.
    """
    uptime   = _run(["uptime", "-p"])
    load     = _run(["cat", "/proc/loadavg"])
    memory   = _run(["free", "-h"])
    disk     = _run(["df", "-h", "--output=source,size,used,avail,pcent,target", "-x", "tmpfs", "-x", "devtmpfs"])
    failed   = _run(["systemctl", "--failed", "--no-pager"]) or "None"

    context = f"""\
Here is the current state of my Arch Linux system:

## Uptime
{uptime}

## Load Average (1m 5m 15m / running/total / last-pid)
{load}

## Memory
{memory}

## Disk
{disk}

## Failed systemd Services
{failed}
"""
    return [
        UserMessage(context),
        AssistantMessage("I have your system snapshot. Let me analyse it."),
        UserMessage("What looks concerning? Flag anything that needs attention, ordered by severity."),
    ]


@mcp.prompt()
def disk_audit() -> list[UserMessage | AssistantMessage]:
    """
    Audit disk usage — filesystems, largest directories in home, pacman cache.
    Use this when disk is filling up and you want to know where to look.
    No arguments needed.
    """
    df      = _run(["df", "-h", "--output=source,size,used,avail,pcent,target", "-x", "tmpfs", "-x", "devtmpfs"])
    home    = _run(["du", "-sh", "--exclude=.git",
                    *[str(p) for p in sorted(Path.home().iterdir())]])
    cache   = _run(["du", "-sh", "/var/cache/pacman/pkg"])
    journal = _run(["journalctl", "--disk-usage"])

    context = f"""\
I want to audit disk usage on my Arch Linux machine.

## Filesystem Overview
{df}

## Home Directory Breakdown (~/)
{home}

## Pacman Package Cache
{cache}

## systemd Journal Size
{journal}
"""
    return [
        UserMessage(context),
        AssistantMessage("I can see your disk usage breakdown. Let me identify where space is going."),
        UserMessage("Where should I clean up first? Give me concrete, safe commands I can run."),
    ]


@mcp.prompt()
def troubleshoot(symptom: str) -> list[UserMessage | AssistantMessage]:
    """
    Structured troubleshooting session. Describe a symptom, get a context-loaded debug session.
    Auto-fetches: recent errors, failed services, top CPU/memory processes, load.

    Args:
        symptom: What you're experiencing, e.g. "system feels sluggish" or "wifi keeps dropping"
    """
    errors   = _run(["journalctl", "-p", "err..emerg", "-n", "40", "--no-pager"])
    failed   = _run(["systemctl", "--failed", "--no-pager"]) or "None"
    cpu_top  = _run(["ps", "aux", "--sort=-%cpu"])
    mem_top  = _run(["ps", "aux", "--sort=-%mem"])
    load     = _run(["uptime"])
    memory   = _run(["free", "-h"])

    # Trim ps output to top 10 lines
    cpu_top = "\n".join(cpu_top.splitlines()[:11])
    mem_top = "\n".join(mem_top.splitlines()[:11])

    context = f"""\
I'm troubleshooting an issue on my Arch Linux machine.

## Symptom
{symptom}

## System Load
{load}

## Memory
{memory}

## Recent Errors (journal)
{errors}

## Failed systemd Services
{failed}

## Top Processes by CPU
{cpu_top}

## Top Processes by Memory
{mem_top}
"""
    return [
        UserMessage(context),
        AssistantMessage(
            "I have the system context. Based on the symptom and the data above, "
            "let me work through what's likely causing this."
        ),
        UserMessage("What's causing the issue and what should I do to fix it?"),
    ]


if __name__ == "__main__":
    mcp.run()
