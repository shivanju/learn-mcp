"""
02-pacman: A read-only Arch Linux package query MCP server.

New concepts vs 01-hello-mcp:
- Input validation with meaningful errors
- Subprocess calls from within a tool
- Structured return types (list, dict)
- A flexible tool that lets Claude decide the args based on user intent
"""

import shlex
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pacman")

# Only these flag prefixes are allowed — enforces read-only at the tool level.
ALLOWED_PREFIXES = {"-Q", "-h", "--help", "--query"}


def _run(args: list[str]) -> str:
    """Run pacman with given args and return stdout as a string."""
    result = subprocess.run(
        ["pacman"] + args,
        capture_output=True,
        text=True,
    )
    # pacman exits non-zero when a package isn't found etc.
    if result.returncode != 0 and result.stderr:
        raise ValueError(result.stderr.strip())
    return result.stdout.strip()


def _validate(args: list[str]) -> None:
    """Reject anything that isn't a query operation."""
    if not args:
        raise ValueError("No arguments provided.")
    first = args[0]
    if not any(first.startswith(p) for p in ALLOWED_PREFIXES):
        raise ValueError(
            f"Only read-only query flags are allowed (e.g. -Q, -Qi, -Qs, -Ql, -Qo, -Qdt). "
            f"Got: '{first}'"
        )


@mcp.tool()
def pacman_query(args: list[str]) -> str | list[str]:
    """
    Run a read-only pacman query and return the output.

    Only -Q (query) operations are permitted — no installs, removals, or syncs.

    Common usage patterns:
    - List all installed packages:       ["-Q"]
    - Search installed packages:         ["-Qs", "<term>"]
    - Full info on a package:            ["-Qi", "<package>"]
    - Files owned by a package:          ["-Ql", "<package>"]
    - Which package owns a file:         ["-Qo", "<file_path>"]
    - Orphaned packages:                 ["-Qdt"]
    - Explicitly installed packages:     ["-Qe"]
    - List foreign (AUR) packages:       ["-Qm"]

    Args:
        args: pacman arguments as a list, e.g. ["-Qi", "git"]

    Returns:
        Raw pacman output as a string.

    Raises:
        ValueError: if non-query flags are used, or if pacman returns an error.
    """
    _validate(args)
    return _run(args)


if __name__ == "__main__":
    mcp.run()
