# 🎨 Google Flow API (`google-flow-api`)

> **The ultimate multi-agent automation engine, CLI, and MCP Server for Google Flow media generation.**
> Generates production-grade images (Nano Banana 2 / Pro) and native videos (Gemini Omni Flash 1.1) with full character consistency and original resolution downloads.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: >=3.9](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Ready](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Agents: Claude | Codex | Antigravity | OpenCode](https://img.shields.io/badge/Agents-Claude%20%7C%20Codex%20%7C%20AGY%20%7C%20OpenCode-blueviolet.svg)](#-multi-agent-setup-claude-codex-antigravity-cursor-opencode)

---

## ✨ Features

- **🤖 Multi-Agent Ready (Claude, Codex, Antigravity, OpenCode, Cursor)**: Plug directly via native **MCP Protocol**, **Skill markdown**, or **CLI**.
- **⚡ Fast CLI (`google-flow generate` & `google-flow video`)**: Instant generation in 20-30s with structured JSON output.
- **🎬 Native Video Support (Gemini Omni Flash 1.1)**: Text-to-Video and Image-to-Video with strictly validated durations (`4s`, `6s`, `8s`, `10s`) and native 720p MP4 download.
- **👤 Hyper-Consistent Characters (Multi-Reference)**: Upload up to 3 reference images (front, left profile, right profile) attached directly as ProseMirror chips.
- **🔄 Concurrent Batch & Carousels (`batch`)**: Dispatches multi-slide prompts with a 3-second interval, generating 8-10 slides in parallel in ~1 minute.
- **🔌 OpenAI Compatible Server (`google-flow serve`)**: Local FastAPI endpoint emulating `POST /v1/images/generations` for **n8n**, **Dify**, **LangChain**, or custom frontends.
- **💎 Native Original Quality**: Injected CDP downloads preserving full uncompressed 1K/2K images and 720p MP4 videos.
- **🌐 Cross-Platform Auto-Detection**: Dynamic `ChromeResolver` for Windows, macOS, and Linux with persistent Google account authentication.
- **🛡️ Safety & Policy Guard**: Proactively catches Google Flow community guideline warnings, daily quota caps, and content blocks.

---

## 📦 Installation

```bash
git clone https://github.com/gabrielsiqueira/google-flow-api.git
cd google-flow-api

# Install in editable mode
pip install -e .

# Or with uv (recommended)
uv sync
```

---

## 🔑 One-Time Login Setup

Run the interactive onboarding command to log into your Google Account:
```bash
google-flow login
```
1. A dedicated browser window will open in `https://flow.google.com`.
2. Log into your Google Account and accept terms of service if this is your first visit.
3. Press `[ENTER]` in your terminal to confirm.
Your authenticated profile will be saved permanently in `~/.google-flow/profile`.

To verify your connection anytime:
```bash
google-flow status
```

---

## 🤖 Multi-Agent Setup (Claude, Codex, Antigravity, Cursor, OpenCode)

### 1. Claude Desktop & Claude Code (MCP)
Add `google-flow` to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-flow": {
      "command": "uv",
      "args": ["run", "--with", "mcp", "google-flow", "mcp"]
    }
  }
}
```
*Claude will now have access to `generate_image`, `generate_video`, `generate_batch`, and `flow_status` tools!*

### 2. Cursor & OpenCode
Add to your Cursor MCP settings (`Settings > MCP`):
- **Name**: `google-flow`
- **Type**: `command`
- **Command**: `uv run --with mcp google-flow mcp`

### 3. Antigravity & Codex
Copy the skill folder into your agent directory:
- **Antigravity**: `~/.gemini/config/skills/google-flow-media/`
- **Codex**: `~/.codex/skills/google-flow-media/`

The agent will automatically discover the skill and use `google-flow` commands seamlessly.

---

## 💻 CLI Usage

### Generate 16:9 Widescreen Image
```bash
google-flow generate \
  --prompt "Photoreal cinematic shot of a vintage Porsche 911 in Tokyo rain at midnight, reflections on wet asphalt..." \
  --ratio 16:9 \
  --resolution 1K
```

### Character Consistency (Image-to-Image / Multi-Reference)
```bash
google-flow generate \
  --prompt "Photoreal cinematic action shot, the same young man from reference playing tennis on a clay court..." \
  --reference-image "./assets/character.jpg" \
  --filename "character_tennis.jpeg" \
  --resolution 1K
```

> [!CAUTION]
> **Safety Filter Notice (Zero Celebrity Names)**: Google Flow blocks any generation containing the name of a real famous person/celebrity. Even if the reference image is of a celebrity, always refer to them anonymously (e.g. *"This character"*, *"The person in the attached reference image"*). Never include real names in prompts.

### Generate Video (Text-to-Video & Image-to-Video)
The Google Flow UI strictly supports **`4s`**, **`6s`**, **`8s`**, and **`10s`** with model `Gemini Omni Flash 1.1`:

```bash
# Text-to-Video (T2V) - 4 seconds
google-flow video \
  --prompt "Cinematic dynamic shot of a matte-black sports car speeding on wet asphalt highway at night..." \
  --duration 4 \
  --ratio 16:9 \
  --filename "carro_noturno.mp4"

# Image-to-Video (I2V) from Reference Image - 8 seconds
google-flow video \
  --prompt "Cinematic tracking shot, the same character from reference running along a scenic park pathway..." \
  --duration 8 \
  --reference-image "./assets/character.jpg" \
  --filename "personagem_correndo_8s.mp4"
```

### Generate Batch / Carousel Concurrently (Turbo 3s Dispatch)
```bash
google-flow batch \
  --manifest "./prompts.json" \
  --reference "./character.jpg" \
  --ratio 3:4 \
  --delay 3.0 \
  --output-dir "./output_carousel"
```

---

## 🐍 Python API Usage

```python
from flow_api import FlowClient, FlowEditor, FlowDownloader

# Connect to the persistent Flow session
client = FlowClient(download_dir="./output_images")
page = client.connect()

try:
    editor = FlowEditor(page)
    editor.submit_prompt(
        prompt="A sleek matte-black quadcopter drone hovering over the Amazon rainforest at sunrise...",
        model="Nano Banana 2",
        aspect_ratio="16:9"
    )
    editor.wait_for_generation()

    downloader = FlowDownloader(page, client.download_dir)
    image_path = downloader.download_current(resolution="1K")
    print(f"Native image saved to: {image_path}")
finally:
    client.close()
```

---

## 🌐 OpenAI-Compatible Server (for n8n, Dify, LangChain)

Start the local server:
```bash
google-flow serve --port 8000
```

Now you can send standard OpenAI image requests:
```bash
curl http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Cyberpunk high-speed bullet train crossing snowy Alps...",
    "size": "1792x1024"
  }'
```

---

## 🛠️ Environment Variables

| Variable | Description | Default |
|---|---|---|
| `FLOW_CHROME_BIN` | Custom path to Chrome/Chromium executable | Auto-detected |
| `FLOW_HOME` | Configuration and profile directory | `~/.google-flow` |
| `FLOW_DOWNLOAD_DIR` | Directory for downloaded media assets | `~/Downloads/google_flow_assets` |
| `FLOW_CDP_PORT` | Port for Chrome DevTools Protocol | `9222` |

---

## 📄 License & Disclaimer

**MIT License** - Copyright (c) 2026 Gabriel Siqueira.

*Disclaimer: This is an independent automation project for personal and research purposes. It is not officially affiliated with, endorsed by, or sponsored by Google.*
