---
name: google-flow
description: Programmatically generate, edit, download, and batch high-resolution images (Nano Banana 2, Nano Banana Pro, Imagen 3) and cinematic videos (Gemini Omni Flash 1.1) via Google Flow. Use when creating visual assets, marketing carousels, character-consistent imagery, and videos without paying for third-party image APIs or burning vision model tokens.
---

# Google Flow Automation Skill

Use the `google-flow` CLI to generate and manage high-resolution media deterministically. All automation subcommands run **headless by default** and return structured JSON on `stdout`.

---

## 1. Setup & Authentication

Requires Python 3.10+ and Google Chrome installed locally.

```bash
# Clone and install dependencies
git clone https://github.com/gabriel-siqueira/google-flow-api.git
cd google-flow-api
uv sync --extra dev
```

### Preflight Authentication Check
Always verify session readiness before starting generative workflows:
```bash
uv run google-flow auth-check --json
```

- If `.authenticated == true`: Session is valid and ready for generation.
- If `.authenticated == false`: Run the one-time interactive login:
  ```bash
  uv run google-flow login
  ```
  Log in with your Google account in the Chrome window that opens, accept the Google Flow terms, and press `[ENTER]` in the terminal.

---

## 2. Operating Invariants for AI Agents

1. **Preflight First**: Always run `google-flow auth-check --json` before issuing generation tasks. If the exit code is non-zero, instruct the user to run `google-flow login`.
2. **Headless Execution**: Do not pass `--head` unless the user explicitly asks to debug the browser interface visually.
3. **Parse JSON Output**: All generation commands print a JSON object on completion containing `"downloaded_file"` with the exact local path of the saved asset.
4. **Isolated Sessions in Concurrency**: If running multiple agents or parallel tasks, append `--session <agent_id>` to prevent browser tab collisions.
5. **Video Durations**: Video generation strictly supports durations of **4, 6, 8, or 10** seconds.
6. **Graceful Shutdown**: When finished with a large batch or when cleaning up resources, execute `uv run google-flow stop`.

---

## 3. Core Commands & Recipes

### A. Text-to-Image (T2I)
Generate high-resolution images using Nano Banana 2 or Nano Banana Pro:
```bash
uv run google-flow generate \
  --prompt "Cinematic hyper-realistic photo of an astronaut on Mars, volumetric lighting, 8k" \
  --model "Nano Banana 2" \
  --ratio "16:9" \
  --resolution "1K" \
  --output-dir "./output" \
  --filename "mars_astronaut.jpeg"
```

**Output JSON**:
```json
{
  "success": true,
  "session": "default",
  "model": "Nano Banana 2",
  "ratio": "16:9",
  "reference": null,
  "downloaded_file": "./output/mars_astronaut.jpeg",
  "output_dir": "./output"
}
```

---

### B. Image-to-Image (I2I & Character Consistency)
Generate new scenes while preserving character face and style using a reference image:
```bash
uv run google-flow generate \
  --prompt "The character running in a futuristic neon city at night, rain reflections" \
  --reference "./references/character.jpeg" \
  --model "Nano Banana 2" \
  --ratio "9:16" \
  --output-dir "./output" \
  --filename "character_night_run.jpeg"
```

---

### C. Text-to-Video & Image-to-Video (Gemini Omni Flash 1.1)
Generate native MP4 video clips with camera movement direction:
```bash
uv run google-flow video \
  --prompt "Slow cinematic drone pull-back revealing a misty pine forest at sunrise" \
  --duration 6 \
  --ratio "16:9" \
  --output-dir "./output" \
  --filename "forest_sunrise.mp4"
```

For **Image-to-Video (I2V)**, add `--reference`:
```bash
uv run google-flow video \
  --prompt "The person looks up towards the sky and smiles gently" \
  --reference "./output/mars_astronaut.jpeg" \
  --duration 4 \
  --ratio "16:9" \
  --output-dir "./output"
```

---

### D. Batch Carousel Generation (Instagram / LinkedIn)
Render an entire slide deck concurrently with smart staggering:
```bash
uv run google-flow batch \
  --manifest "./carousel_prompts.json" \
  --reference "./references/spokesperson.jpeg" \
  --ratio "3:4" \
  --delay 3.0 \
  --output-dir "./output/carousel"
```

`carousel_prompts.json` format:
```json
[
  { "slide": 1, "prompt": "Cover slide: Protagonist looking confident in modern startup office", "filename": "slide_01.jpeg" },
  { "slide": 2, "prompt": "Protagonist pointing at a high-tech holographic dashboard", "filename": "slide_02.jpeg" },
  { "slide": 3, "prompt": "Protagonist shaking hands with an international client", "filename": "slide_03.jpeg" }
]
```

---

## 4. MCP Server Integration (Model Context Protocol)

To connect Google Flow directly to Claude Desktop, Cursor, OpenCode, or Windsurf:

```bash
uv run google-flow mcp
```

### Configuration snippet (`mcpServers` in `claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "google-flow": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/google-flow-api", "google-flow", "mcp"]
    }
  }
}
```

Exposed MCP Tools:
- `generate_image(prompt, ratio, model, reference_image, resolution)`
- `generate_video(prompt, duration, ratio, reference_image)`
- `check_status()`
