# 🎨 flow-py: Google Flow for AI Agents (`google-flow-api`)

> **The Unofficial Multi-Agent Automation Engine, CLI, MCP Server & Universal Skill for Google Flow.**  
> Offload production-grade image generation (Nano Banana 2, Nano Banana Pro, Imagen 3) and cinematic video generation (Gemini Omni Flash 1.1) to Google Flow directly from any AI Agent — with zero token waste and native original quality.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: >=3.10](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Ready](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Universal Skill](https://img.shields.io/badge/Skill-Universal%20Standard-purple.svg)](SKILL.md)
[![Security Policy](https://img.shields.io/badge/Security-Threat%20Model%20Included-red.svg)](SECURITY.md)

---

## 🤖 Multi-Agent Compatibility Matrix

`google-flow-api` is built from the ground up to integrate natively into every major AI coding and automation agent:

| Agent / Harness | Integration Mechanism | Configuration File |
| :--- | :--- | :--- |
| **Claude Code** (Anthropic) | Native CLI / `CLAUDE.md` | [`CLAUDE.md`](CLAUDE.md) |
| **OpenAI Codex** | Subprocess CLI / `AGENTS.md` | [`AGENTS.md`](AGENTS.md) |
| **OpenClaw** | Autonomous Skill Runner | [`SKILL.md`](SKILL.md) |
| **Hermes Agent** (Nous Research) | CLI `--json` Envelopes | [`SKILL.md`](SKILL.md) |
| **OpenCode** | Skill / MCP Stdio Server | [`AGENTS.md`](AGENTS.md) / `google-flow mcp` |
| **Google Antigravity** | Native Workspace Skill | `~/.gemini/config/skills/google-flow/` |
| **Cursor / Windsurf / Claude Desktop** | Model Context Protocol (MCP) | `claude_desktop_config.json` |

---

## ✨ Key Capabilities

- **🤫 Silent Background Engine (Headless-by-Default)**: Operates 100% invisibly in the background with zero window popups (parity with `/notebooklm`). Chrome runs in `--headless=new` with Full HD viewport and WebGL acceleration. Use `--head` whenever you want visual inspection.
- **⚡ Sub-Second Preflight Auth Check (`auth-check`)**: Instantly verifies authenticated state and canvas readiness in sub-second JSON response without opening windows.
- **🛑 Safe Lifecycle Control (`google-flow stop`)**: Safely shuts down the background headless browser daemon and frees RAM/CPU, isolating port 9222 and never touching your personal browsing windows.
- **🎯 Deterministic JSON Output (`--json`)**: All automated commands output structured JSON to `stdout` with predictable exit codes (`0` for success, `1` for error).
- **👤 Multi-Reference Character Consistency**: Pass reference images (front, side, profile) to maintain character facial identity across different scenes.
- **🎬 Native Video Support (Gemini Omni Flash 1.1)**: Text-to-Video and Image-to-Video with strictly validated durations (`4s`, `6s`, `8s`, `10s`) and native 720p MP4 download.
- **🔄 Concurrent Batch & Carousels (`batch`)**: Dispatches multi-slide prompts with a 3-second interval, generating 8-10 slides in parallel in ~1 minute.
- **🔌 OpenAI-Compatible REST API (`google-flow serve`)**: Local FastAPI endpoint emulating `POST /v1/images/generations` for **n8n**, **Dify**, **LangChain**, or custom applications.
- **💎 Dual-Detection Asset Downloader**: Extracts full 1K/2K resolution images directly from the WebGL canvas and network responses.

---

## 📦 Installation & Quickstart

### Prerequisites
- Python 3.10+
- Google Chrome installed locally
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

```bash
# Clone repository
git clone https://github.com/twofxz/flow-py.git
cd flow-py

# Install dependencies and dev tools
uv sync --extra dev
```

---

## 🔐 One-Time Authentication

Authenticate your Google account once in a dedicated, isolated browser profile:

```bash
uv run google-flow login
```
1. A Chrome window opens at `https://flow.google.com`.
2. Sign into your Google account and accept terms of service if visiting for the first time.
3. Press `[ENTER]` in the terminal when you see the Flow canvas.
4. Your authenticated session is permanently stored in `~/.google-flow/chrome_profile/` with restricted permissions (`0600`).

### Verify Authentication State
```bash
uv run google-flow auth-check --json
```
```json
{
  "authenticated": true,
  "status": "ready",
  "url": "https://flow.google.com/project/01caca8b-...",
  "session": "default",
  "profile_dir": "C:\\Users\\...\\.google-flow\\chrome_profile"
}
```

---

## 💻 CLI Commands & Recipes

### 1. Text-to-Image (T2I)
```bash
uv run google-flow generate \
  --prompt "Cinematic photo of an astronaut discovering ancient ruins on Mars, volumetric light, 8k" \
  --model "Nano Banana 2" \
  --ratio "16:9" \
  --resolution "1K" \
  --output-dir "./output" \
  --filename "mars_ruins.jpeg"
```

### 2. Image-to-Image & Character Consistency (I2I)
```bash
uv run google-flow generate \
  --prompt "The character in casual clothing having a coffee in a vibrant Parisian cafe" \
  --reference "./assets/character_face.jpeg" \
  --model "Nano Banana 2" \
  --ratio "9:16" \
  --output-dir "./output" \
  --filename "character_paris.jpeg"
```

### 3. Video Generation (Gemini Omni Flash 1.1)
```bash
# Text-to-Video (T2V) - 6 seconds
uv run google-flow video \
  --prompt "Cinematic aerial tracking shot orbiting a lighthouse during a storm, rough waves crashing" \
  --duration 6 \
  --ratio "16:9" \
  --output-dir "./output" \
  --filename "stormy_lighthouse.mp4"

# Image-to-Video (I2V) - 4 seconds
uv run google-flow video \
  --prompt "The character smiles gently and turns their head towards the camera" \
  --reference "./output/mars_ruins.jpeg" \
  --duration 4 \
  --ratio "16:9" \
  --output-dir "./output"
```

### 4. Batch Carousel Generation (Instagram / LinkedIn)
```bash
uv run google-flow batch \
  --manifest "./carousel_prompts.json" \
  --reference "./assets/spokesperson.jpeg" \
  --ratio "3:4" \
  --delay 3.0 \
  --output-dir "./output/carousel"
```

---

## 🔌 Model Context Protocol (MCP) Setup

Connect Google Flow directly to Claude Desktop, Cursor, OpenCode, or Windsurf:

```bash
uv run google-flow mcp
```

### Configuration (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "google-flow": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/google-flow-api", "google-flow", "mcp"]
    }
  }
}
```

---

## 🐍 Python SDK Usage

```python
from flow_api import FlowClient, FlowEditor, FlowDownloader

client = FlowClient(download_dir="./output_images", headless=True)
try:
    client.start_browser_if_needed()
    page = client.connect()
    client.ensure_canvas()

    editor = FlowEditor(page)
    editor.submit_prompt(
        prompt="Cyberpunk flying taxi soaring between holographic skyscrapers, heavy rain",
        model="Nano Banana 2",
        aspect_ratio="16:9"
    )
    editor.wait_for_generation(timeout=90)

    downloader = FlowDownloader(page, client.download_dir)
    saved_path = downloader.download_current(resolution="1K")
    print(f"✅ Image saved: {saved_path}")
finally:
    client.close()
```

---

## 🌐 OpenAI-Compatible Server (for n8n, Dify, LangChain)

```bash
uv run google-flow serve --port 8000
```

Send standard OpenAI image generation requests:
```bash
curl http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Futuristic electric supercar on a scenic coastal highway at sunset",
    "size": "1792x1024"
  }'
```

---

## 🧪 Testing

Run the automated test suite:
```bash
uv run pytest
```

---

## 🛡️ Security & Privacy

`google-flow-api` strictly isolates credentials in `~/.google-flow/` and contains **zero telemetry or third-party relays**. For detailed security guidelines, threat modeling, and CI/CD best practices, please read [`SECURITY.md`](SECURITY.md).

---

## 📄 License

MIT License - Copyright (c) 2026 Gabriel Siqueira.

*Disclaimer: This is an independent open-source automation engine for research and automation purposes. It is not affiliated with, endorsed by, or sponsored by Google.*
