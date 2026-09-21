# Claude Code Guide: google-flow-api

This file contains conventions, developer commands, and architecture rules for Claude Code when working in this repository.

---

## Project Overview

`google-flow-api` is an unofficial, production-grade automation engine, CLI, and MCP Server for **Google Flow** (Nano Banana 2, Nano Banana Pro, and Gemini Omni Flash 1.1).

It is built for AI agents and developers who need programmatic, high-resolution media generation with zero vision token consumption.

---

## Development Environment & Commands

The project uses `uv` for fast, reproducible dependency management.

```bash
# Setup environment & install dev dependencies (including pytest)
uv sync --extra dev

# Run test suite
uv run pytest

# Execute single test file
uv run pytest tests/test_auth_check.py -v

# Run the CLI
uv run google-flow --help
uv run google-flow auth-check --json

# Run MCP server locally
uv run google-flow mcp

# Start OpenAI-compatible FastAPI server
uv run google-flow serve --port 8000

# Terminate background browser daemon
uv run google-flow stop
```

---

## Core Architecture

```
flow_api/
├── cli.py         # Terminal CLI entry point (argparse, JSON envelopes, exit codes)
├── client.py      # FlowClient: Headless Chromium lifecycle, CDP attachment, tab concurrency
├── editor.py      # FlowEditor: DOM interaction, prompt submission, model selection, watchers
├── downloader.py  # FlowDownloader: Dual-detection high-resolution extractor (1K/2K and MP4)
├── mcp_server.py  # FastMCP server for Claude Desktop, Cursor, OpenCode, Windsurf
└── server.py      # FastAPI OpenAI-compatible REST server (/v1/images/generations)
tests/             # Pytest test suite validating auth checks, CLI flags, headless & lifecycle
```

---

## Operational Rules & Invariants for Claude

1. **Headless by Default**:
   - Every automation command (`generate`, `video`, `batch`, `auth-check`, `status`) must default to headless execution.
   - Only the interactive onboarding command (`google-flow login`) or an explicit `--head` flag should launch a visible GUI.
   - Do not steal focus or disturb the user's desktop workspace.

2. **JSON-First Output Envelope**:
   - In automated commands, return structured JSON payloads to `stdout` with clear status indicators:
     - Success: `{"success": true, "downloaded_file": "...", ...}`
     - Failure: `{"success": false, "error": "..."}` with non-zero exit code (`sys.exit(1)`).

3. **Sub-second Preflight Checks**:
   - Before triggering long-running generative actions, encourage agents to run:
     `uv run google-flow auth-check --json`
   - Keep the preflight check ultra-fast by verifying local CDP connectivity and page state without unnecessary page reloads.

4. **Cross-Platform Discipline (Windows, macOS, Linux)**:
   - On Windows, detached browser spawning uses PowerShell / WMI (`Win32_Process`) to decouple from terminal Job Objects.
   - On Linux/macOS, use `start_new_session=True` and `pkill`.
   - Always use `os.path.join` or `pathlib.Path` for file system paths.

5. **Concurrency & Session Isolation**:
   - When multiple agents or subagents run concurrently, pass `--session <unique_id>` to ensure separate project contexts, cache files, and lock files.
