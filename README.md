# learn-mcp

A hands-on, project-by-project guide to understanding and building MCP (Model Context Protocol) servers — aimed at software engineers who are new to MCP and want to use it in their day-to-day workflow.

Each project is self-contained, builds on the previous one, and introduces exactly one or two new concepts. No fluff.

---

## What is MCP?

MCP (Model Context Protocol) is an open standard by Anthropic that lets AI models like Claude connect to external tools and data sources in a standardised way. Think of it as USB-C for AI — a universal connector.

Three primitives an MCP server can expose:

| Primitive | What it is | Analogy |
|-----------|-----------|---------|
| **Tool** | A function Claude can call | API endpoint |
| **Resource** | Data Claude can read via a URI | File / database record |
| **Prompt** | A reusable conversation template | Slash command / macro |

---

## Prerequisites

- **Python 3.11+** (projects use 3.14)
- **uv** — [install](https://docs.astral.sh/uv/getting-started/installation/)
- **Claude Code** — [install](https://claude.ai/code)
- An Arch Linux machine (projects 02–04 use `pacman`/`journalctl`; concepts are portable)

---

## Projects

### 01 — hello-mcp
**Concepts:** FastMCP basics, `@mcp.tool()`, type hints → JSON schema, docstring → tool description, stdio transport, registering with Claude Code.

The simplest possible MCP server. Two tools: `greet(name)` and `add(a, b)`. Goal is understanding the full lifecycle — write a function, decorate it, wire it to Claude.

### 02 — pacman
**Concepts:** Flexible tool design, input validation, subprocess calls, structured error responses.

A read-only Arch Linux package query server. One flexible tool (`pacman_query`) that accepts pacman `-Q` flags directly — Claude decides what args to pass based on your intent. Enforces read-only at the tool level.

### 03 — resources
**Concepts:** `@mcp.resource()` decorator, static resources (fixed URI), dynamic resources (URI templates with `{param}`).

Exposes live system data as MCP resources: OS release info, pacman log, memory stats, and per-service systemd journal output. Shows how resources differ from tools — data Claude reads vs actions Claude calls.

### 04 — prompts
**Concepts:** `@mcp.prompt()` decorator, single-string vs multi-message return, dynamic data gathering inside the prompt handler.

Three practical prompts for an Arch Linux machine: `system_health`, `disk_audit`, and `troubleshoot(symptom)`. Each gathers live system data at invocation time and injects it into a pre-structured conversation — so Claude starts with full context, no manual copy-pasting.

### 05 — sse
**Concepts:** SSE transport (`mcp.run(transport="sse")`), independent server lifecycle, URL-based registration, running as a background process / systemd user service.

The same pacman tool from project 02, but over SSE. Shows the one-line code change and the entirely different operational model: you own the process, Claude just connects to it. Server survives session close/reopen and can serve multiple clients simultaneously.

---

## Transports at a glance

| | stdio | SSE |
|---|---|---|
| Who starts the server | Claude Code (subprocess) | You |
| Server lifetime | = Claude Code session | Independent |
| Multiple clients | No | Yes |
| Registration | `claude mcp add name python main.py` | `claude mcp add name --transport sse http://localhost:PORT/sse` |
| On session close | Server killed ("N servers failed" — normal) | Server keeps running |
| Best for | Personal tools tied to one user | Shared/persistent servers |

---

## Setup pattern (every project)

```bash
mkdir XX-project && cd XX-project
uv init --no-readme
uv add mcp
# write main.py
claude mcp add server-name .venv/bin/python main.py
```

Add to `pyproject.toml` so pyright (nvim LSP) finds the venv:

```toml
[tool.pyright]
venvPath = "."
venv = ".venv"
```

---

## Key things learned

- `@mcp.tool()` — type hints become the JSON schema Claude uses to call the function; docstring becomes the description Claude reads to decide *when* to use it
- `@mcp.resource("uri://{param}")` — URI templates auto-map `{param}` to the function argument
- `@mcp.prompt()` returning `list[UserMessage | AssistantMessage]` — the middle `AssistantMessage` primes Claude's role before it responds
- `mcp.run()` is a blocking asyncio loop reading newline-delimited JSON-RPC from stdin
- MCP servers registered mid-session are not available until the next session start
- `claude mcp add` writes to `~/.claude.json` under the current project path as key; scope is local by default

---

## Public MCP servers worth knowing

Official reference implementations: [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)

Notable ones: `filesystem`, `github`, `postgres`, `sqlite`, `brave-search`, `slack`, `puppeteer`, `memory`

Install any of them (most are Node.js):
```bash
claude mcp add github npx -- @modelcontextprotocol/server-github
```
