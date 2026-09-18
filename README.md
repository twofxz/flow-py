# 🎨 Google Flow API (`google-flow-api`)

> An unofficial, ultra-fast Python API, CLI, and OpenAI-compatible server for Google Flow media generation (Nano Banana 2 & Veo).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: >=3.9](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ Features

- **🚀 Programmatic Python API**: Simple, high-level client to generate and retrieve native original assets.
- **⚡ Fast CLI (`flow generate`)**: One-liner command generation with structured JSON response.
- **🔌 OpenAI Compatible (`flow serve`)**: Spin up a local server emulating `POST /v1/images/generations` to seamlessly plug Google Flow into **n8n**, **Dify**, **LangChain**, or existing web UIs!
- **💎 Native Original Quality**: Retrieves true native 1K/2K resolution without browser-scaled compression.
- **🔒 Persistent Authentication**: Log in once with your Google account; session stays saved locally.
- **🛡️ Strict Model Guard**: Automatic enforcement of high-fidelity models (`Nano Banana 2` / `Nano Banana Pro`).

---

## 📦 Installation

```bash
git clone https://github.com/seu-usuario/google-flow-api.git
cd google-flow-api
pip install -e .
# or with uv
uv sync
```

---

## 🔑 One-Time Login Setup

Run the setup command to log into your Google Account:
```bash
flow login
```
A browser window will open. Log into your Google Account. Your session profile will be saved permanently in `~/.google-flow/profile`.

---

## 💻 CLI Usage

### Generate 16:9 Widescreen Image
```bash
flow generate \
  --prompt "Photoreal cinematic shot of a vintage Porsche 911 in Tokyo rain at midnight..." \
  --ratio 16:9 \
  --resolution 1K
```

### Generate Image from Reference (Image-to-Image / Character Consistency)
```bash
flow generate \
  --prompt "Photoreal cinematic action shot, the same character from reference playing tennis..." \
  --reference-image "./assets/character.jpg" \
  --filename "character_tennis.jpeg" \
  --resolution 1K
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
flow serve --port 8000
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

## 📄 License
MIT License. Created by Gabriel Siqueira.
