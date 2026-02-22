# CLAUDE.md — learn-mcp

This repo is a structured, hands-on learning series for MCP (Model Context Protocol). Each subdirectory is an independent project with its own `uv` environment.

## Repo structure

```
learn-mcp/
├── 01-hello-mcp/   stdio, @mcp.tool(), basics
├── 02-pacman/      stdio, input validation, subprocess
├── 03-resources/   stdio, @mcp.resource(), static + dynamic URIs
├── 04-prompts/     stdio, @mcp.prompt(), multi-message, live data gathering
└── 05-sse/         SSE transport, independent lifecycle
```

## Conventions used across all projects

**Project setup:**
```bash
uv init --no-readme
uv add mcp
```

**Every `pyproject.toml` has this for pyright LSP support:**
```toml
[tool.pyright]
venvPath = "."
venv = ".venv"
```

**Entry point is always `main.py`** (uv's default, not `server.py`).

**Run a server manually:**
```bash
uv run main.py                        # stdio (for testing)
uv run main.py   # transport="sse"   # SSE servers
```

## MCP server registrations

All servers are registered in `~/.claude.json` under the `learn-mcp` project scope. To inspect:

```python
import json
data = json.load(open('/home/shivanju/.claude.json'))
for path, config in data.get('projects', {}).items():
    servers = config.get('mcpServers', {})
    if servers:
        print(path, servers)
```

To add a new project's server:
```bash
claude mcp add <name> /abs/path/to/.venv/bin/python /abs/path/to/main.py
```

For SSE:
```bash
claude mcp add <name> --transport sse http://localhost:PORT/sse
```

## MCP primitives — quick reference

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import UserMessage, AssistantMessage

mcp = FastMCP("server-name")           # stdio
mcp = FastMCP("name", host="127.0.0.1", port=8000)  # SSE

@mcp.tool()
def my_tool(arg: str) -> str:          # type hints → JSON schema
    """Docstring → description Claude reads."""
    ...

@mcp.resource("scheme://path")         # static URI
def my_resource() -> str: ...

@mcp.resource("scheme://path/{param}") # dynamic URI template
def my_resource(param: str) -> str: ...

@mcp.prompt()
def my_prompt(arg: str) -> list[UserMessage | AssistantMessage]:
    return [
        UserMessage("context..."),
        AssistantMessage("primes Claude's role..."),
        UserMessage("actual question"),
    ]

mcp.run()                              # stdio (default)
mcp.run(transport="sse")              # SSE
```

## When adding a new project

1. `mkdir NN-name && cd NN-name`
2. `uv init --no-readme && uv add mcp`
3. Write `main.py`
4. Add `[tool.pyright]` block to `pyproject.toml`
5. Register: `claude mcp add name .venv/bin/python main.py`
6. Verify: `claude mcp list` + inspect `~/.claude.json`
7. New sessions pick up the server on next start

## Important behaviours

- MCP servers registered mid-session are NOT available until the next session
- Closing a session kills all stdio servers → "N servers failed" on exit is normal, not an error
- SSE servers must be started manually before registering; they persist across sessions
- `claude mcp add` scopes to the CWD's project by default (`-s user` for user-wide)
- Stale entries in `~/.claude.json` are best cleaned up via Python `json` manipulation, not `claude mcp remove` (which targets the current session's project scope)
