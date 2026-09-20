# Google Flow Headless & Silent Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform `google-flow-api` into an invisible, daemonized background engine inspired by `/notebooklm`, running Chrome in `--headless=new` mode by default, with dedicated visible login (`--head`), sub-second `auth check`, and process lifecycle management (`stop`/`down`).

**Architecture:** A dual-mode execution model where Chrome runs persistently in modern headless mode (`--headless=new`, 1920x1080 Full HD viewport, WebGL/GPU enabled) for all generation and download tasks, while isolating GUI visibility strictly to `google-flow login` or explicit `--head` debugging flags.

**Tech Stack:** Python 3.10+, Playwright (CDP attach), Chrome DevTools Protocol, FastMCP / MCPServer, FastAPI, Windows WMI / POSIX subprocess.

**Spec:** [notebooklm-like silent automation specification](README.md)

## Global Constraints
- Chrome must run invisibly by default with `--headless=new`, without flashing or stealing OS focus.
- The Full HD viewport (`1920x1080`) must be strictly enforced in headless mode to prevent responsive hamburger menu collapses.
- `google-flow login` must be the only command that opens a visible GUI window by default.
- Every generation command (`generate`, `video`, `batch`) must accept an optional `--head` flag for visual debugging.
- Process lifecycle management (`google-flow stop`) must gracefully terminate background instances on port 9222 without touching the user's personal Chrome browser.
- All changes must be synchronized across `google-flow-api`, `.gemini/config/skills/google-flow-media/`, and `.codex/skills/google-flow-media/`.

---

### Task 1: Headless Configuration & Viewport Enforcement in FlowClient

**Files:**
- Modify: `flow_api/client.py`
- Test: `tests/test_headless_client.py`

**Interfaces:**
- Consumes: `find_chrome_executable()`, `FLOW_BASE_URL`, `DEFAULT_PROFILE`
- Produces: `FlowClient(headless: bool = True, ...)` supporting `--headless=new`, `1920x1080`, WebGL flags, and CDP viewport management.

- [ ] **Step 1: Write the test for headless launch flags and connection**

```python
# tests/test_headless_client.py
import pytest
from flow_api.client import FlowClient

def test_headless_flags_configuration():
    client = FlowClient(headless=True)
    assert client.headless is True
    client_visible = FlowClient(headless=False)
    assert client_visible.headless is False
```

- [ ] **Step 2: Run test to verify it fails or needs implementation**

Run: `uv run python -m pytest tests/test_headless_client.py`

- [ ] **Step 3: Implement headless flag support and 1920x1080 viewport in `flow_api/client.py`**
Add `headless: bool = True` to `FlowClient.__init__` and incorporate:
```python
flags = [
    f'--remote-debugging-port={self.cdp_port}',
    f'--user-data-dir="{DEFAULT_PROFILE}"',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--window-size=1920,1080'
]
if self.headless:
    flags.extend([
        '--headless=new',
        '--enable-gpu',
        '--use-gl=angle'
    ])
```

- [ ] **Step 4: Run test and verify it passes**

Run: `uv run python -m pytest tests/test_headless_client.py`

- [ ] **Step 5: Commit changes**

```bash
git add flow_api/client.py tests/test_headless_client.py
git commit -m "feat: add modern headless=new and Full HD viewport support to FlowClient"
```

---

### Task 2: Implement Process Lifecycle & Daemon Management (`google-flow stop` / `down`)

**Files:**
- Modify: `flow_api/client.py`
- Modify: `flow_api/cli.py`
- Test: `tests/test_lifecycle.py`

**Interfaces:**
- Consumes: port 9222 socket check, process enumeration filtered strictly by profile path or executable path.
- Produces: `FlowClient.stop_background_process()` and CLI command `google-flow stop`.

- [ ] **Step 1: Write test for process stop and port cleanup**

```python
# tests/test_lifecycle.py
from flow_api.client import FlowClient

def test_stop_non_running_graceful():
    client = FlowClient()
    # Stopping when not running should not raise an exception
    stopped = client.stop_background_process()
    assert isinstance(stopped, bool)
```

- [ ] **Step 2: Run test to verify**

Run: `uv run python -m pytest tests/test_lifecycle.py`

- [ ] **Step 3: Implement `stop_background_process` in `client.py` and register `stop` in `cli.py`**
Safely identify Chrome PIDs bound to the Flow profile or port 9222 and terminate them without killing the user's main personal Chrome.

- [ ] **Step 4: Verify test passes**

Run: `uv run python -m pytest tests/test_lifecycle.py`

- [ ] **Step 5: Commit changes**

```bash
git add flow_api/client.py flow_api/cli.py tests/test_lifecycle.py
git commit -m "feat: add process stop and lifecycle management to FlowClient and CLI"
```

---

### Task 3: Dual-Mode CLI Enforcement (Visible `login` vs Headless `generate/video/batch/status`)

**Files:**
- Modify: `flow_api/cli.py`
- Test: `tests/test_cli_modes.py`

**Interfaces:**
- Consumes: `FlowClient(headless=...)`
- Produces: CLI argument `--head` on `generate`, `video`, `batch`, `status`; default `headless=False` strictly on `login`.

- [ ] **Step 1: Write test checking CLI argument defaults**

```python
# tests/test_cli_modes.py
from flow_api.cli import build_parser

def test_cli_parser_defaults():
    parser = build_parser()
    args_gen = parser.parse_args(["generate", "--prompt", "test"])
    assert getattr(args_gen, "head", False) is False
    args_gen_head = parser.parse_args(["generate", "--prompt", "test", "--head"])
    assert args_gen_head.head is True
```

- [ ] **Step 2: Run test to verify**

Run: `uv run python -m pytest tests/test_cli_modes.py`

- [ ] **Step 3: Refactor CLI parser into `build_parser()` and attach `--head` flag to all runner commands**
Enforce `FlowClient(headless=not args.head)` for runners, and `FlowClient(headless=False)` for `login`.

- [ ] **Step 4: Run test and verify pass**

Run: `uv run python -m pytest tests/test_cli_modes.py`

- [ ] **Step 5: Commit changes**

```bash
git add flow_api/cli.py tests/test_cli_modes.py
git commit -m "feat: enforce headless by default with --head override across CLI commands"
```

---

### Task 4: Sub-Second `auth check` Command (NotebookLM Parity)

**Files:**
- Modify: `flow_api/cli.py`
- Modify: `flow_api/client.py`
- Test: `tests/test_auth_check.py`

**Interfaces:**
- Consumes: `client.check_auth_status()`
- Produces: CLI subcommand `auth-check` returning clean JSON envelope (`{"status": "ready"|"auth_required", "authenticated": bool, "headless": bool}`).

- [ ] **Step 1: Write test for auth-check JSON output structure**

```python
# tests/test_auth_check.py
from flow_api.client import FlowClient

def test_auth_status_schema():
    client = FlowClient()
    # Test checking auth structure returns dict with authenticated key
    assert hasattr(client, "check_auth_status")
```

- [ ] **Step 2: Run test**

Run: `uv run python -m pytest tests/test_auth_check.py`

- [ ] **Step 3: Implement `auth-check` subcommand in `cli.py`**
Return structured JSON instantly, matching `/notebooklm` standard.

- [ ] **Step 4: Verify test passes**

Run: `uv run python -m pytest tests/test_auth_check.py`

- [ ] **Step 5: Commit changes**

```bash
git add flow_api/cli.py flow_api/client.py tests/test_auth_check.py
git commit -m "feat: add fast JSON auth-check matching notebooklm standard"
```

---

### Task 5: End-to-End Live Validation (Silent Image & Video Generation in Headless Mode)

**Files:**
- Test Script: `tests/test_live_headless_generation.py`
- Outputs: `~/Downloads/google_flow_assets/`

**Interfaces:**
- Consumes: running background headless Chrome on port 9222.
- Produces: verified 1K image and 720p MP4 video generated without any visible browser window.

- [ ] **Step 1: Execute `google-flow stop` to ensure clean state**
- [ ] **Step 2: Run `google-flow generate` in pure headless mode without `--head`**
Verify the terminal outputs progress cleanly and the JPEG file is saved `> 200 KB` without any window popping up.
- [ ] **Step 3: Run `google-flow video` in pure headless mode with `--duration 4`**
Verify the MP4 file is downloaded and verified `> 500 KB`.
- [ ] **Step 4: Verify MCP server executes in headless mode**
- [ ] **Step 5: Commit verification results**

---

### Task 6: Skill Documentation & Multi-Agent Synchronization

**Files:**
- Modify: `README.md`
- Modify: `~/.gemini/config/skills/google-flow-media/SKILL.md`
- Modify: `~/.codex/skills/google-flow-media/SKILL.md`

**Interfaces:**
- Consumes: updated engine and CLI options.
- Produces: updated documentation reflecting silent/headless operation, `--head` debugging, and parity with `/notebooklm`.

- [ ] **Step 1: Update README.md with headless architecture details and `auth-check` / `stop` commands**
- [ ] **Step 2: Synchronize updated `flow_api` to Antigravity and Codex skill paths**
- [ ] **Step 3: Update `SKILL.md` in both locations to instruct agents on silent background execution**
- [ ] **Step 4: Commit and finalize release**
