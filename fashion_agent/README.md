# Local Fashion AI Agent

A fully local, agent-controlled toolkit for a **Lenovo/ThinkPad P51** (NVIDIA
Quadro M1200, **4 GB VRAM**, 16 GB RAM). You talk to it in plain English; it
picks a tool and runs it on your machine:

- **Search** the internet with cited results (and a working **offline mode**).
- **Generate outfits** on your photos (e.g. put a saree on yourself) while
  keeping your **face, pose, and background** intact.
- **Post-process** images and **assemble videos** (slideshow + crossfades + music).
- **Remember** your preferences privately, on disk.

This is a corrected, hardware-honest reworking of a popular ChatGPT/Gemini-style
scaffold. See **[What was fixed](#what-was-fixed-vs-the-original-scaffold)** for
the specific bugs that were repaired.

---

## The one rule that makes this work on 4 GB

> **The LLM runs on the CPU. The GPU is reserved for Stable Diffusion.**

A 4 GB card cannot hold an 8B chat model *and* a Stable Diffusion pipeline at
once. So we run the language model on the CPU (slower, but fine for tool-picking
and summarizing) and give the whole GPU to image generation. The tools are
sequenced so the two never fight for VRAM.

### Honest expectations on this hardware
- **Text/agent replies:** a few seconds (3B model on CPU).
- **Outfit image (SD 1.5 + inpaint, `--lowvram`):** ~1–3 minutes each.
- **Clothing mask (CPU):** ~10–60 seconds the first time (model downloads once).
- **Video:** FFmpeg slideshows are fast. **True AI video generation is NOT
  included** — the lightest credible models need ~8 GB+ VRAM, which this GPU
  does not have. This is a deliberate, honest omission, not a missing feature.

---

## Architecture

```
You (natural language)
        |
        v
   agent.py  ── asks local LLM (Ollama, CPU) for ONE tool + JSON args
        |        (robust parser tolerates <think> tags & prose)
        |
        +── search_web / search_local_docs   (SearXNG online | TF-IDF offline)
        +── create_outfit                     (mask -> Stable Diffusion inpaint)
        +── enhance/resize/watermark/batch     (ImageMagick)
        +── create_video/transitions/audio     (FFmpeg)
        +── remember / recall                  (local JSON memory)
        |
        v
   results saved to disk under fashion_agent/
```

---

## Prerequisites

| Component | Purpose | Runs on |
|-----------|---------|---------|
| **Ollama** | local LLM server | CPU |
| **Stable Diffusion WebUI Forge** | image generation/inpaint | **GPU** |
| **FFmpeg** | video assembly | CPU |
| **ImageMagick** | image post-processing | CPU |
| **Python 3.10+** | the agent itself | CPU |
| **SearXNG** (optional, Docker) | private web search | CPU |

> Forge is recommended over AUTOMATIC1111 here because its backend is optimized
> for low VRAM. **Do not use Fooocus** — it does not expose the ControlNet
> inpainting API this agent calls.

---

## Setup — step by step

### 1. Install the system tools

**Linux (Debian/Ubuntu):**
```bash
sudo apt update
sudo apt install -y ffmpeg imagemagick python3 python3-venv git
```

**Windows (PowerShell):**
```powershell
winget install Gyan.FFmpeg
winget install ImageMagick.ImageMagick
winget install Python.Python.3.12
winget install Git.Git
```

### 2. Install Ollama and pull the models
Download Ollama from <https://ollama.com>, then:
```bash
ollama serve            # leave running in its own terminal
ollama pull qwen2.5:3b-instruct     # chat / tool-picking model (CPU-friendly)
ollama pull nomic-embed-text        # (optional) embeddings for future semantic recall
```
> Want stronger reasoning and have patience? `ollama pull qwen2.5:7b-instruct`
> and set `LLM_MODEL=qwen2.5:7b-instruct`. It will be noticeably slower on CPU.

### 3. Install Stable Diffusion WebUI Forge (the GPU app)
```bash
git clone https://github.com/lllyasviel/stable-diffusion-webui-forge
cd stable-diffusion-webui-forge
```
Put an **SD 1.5** checkpoint in `models/Stable-diffusion/` (SD 1.5 — *not* SDXL;
SDXL won't fit in 4 GB). Download the ControlNet model
`control_v11p_sd15_openpose` into `models/ControlNet/`.

Launch it with the API enabled and low-VRAM flags:
```bash
# Linux
./webui.sh --api --lowvram --xformers --no-half-vae
# Windows: edit webui-user.bat ->  set COMMANDLINE_ARGS=--api --lowvram --xformers --no-half-vae
```
Confirm <http://127.0.0.1:7860> loads before continuing.

### 4. Install the agent
```bash
cd fashion_agent
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
# Keep the GPU free for SD by installing the CPU build of torch (for masks):
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 5. (Optional) Private web search with SearXNG
```bash
docker run -d --name searxng -p 8888:8080 \
  -e "SEARXNG_SETTINGS__server__limiter=false" \
  searxng/searxng
```
Enable its JSON API: in the SearXNG `settings.yml`, under `search:`, add `json`
to `formats:`. Without SearXNG, the agent still runs — it just routes searches to
your **offline documents** instead.

---

## Running it

Start each service in its own terminal:
```bash
# Terminal 1
ollama serve
# Terminal 2  (inside the Forge folder)
./webui.sh --api --lowvram --xformers --no-half-vae
# Terminal 3  (inside fashion_agent, venv active)
python agent.py
```

Then just talk to it:
```
You: put a red Banarasi saree with a gold border on input_photos/photo1.jpg
You: enhance all images in generated_outfits/ into processed_images/
You: make a video with crossfades from processed_images/
You: add final_videos/music.mp3 to final_videos/show.mp4
You: remember that I prefer red and gold combinations
You: search for trending saree colors in 2026
```

### The outfit pipeline, by hand (if you prefer explicit control)
```bash
# 1) build a clothing-only mask (face & background are excluded automatically)
python generate_mask.py input_photos/photo1.jpg
# 2) the agent's create_outfit does masking + inpaint in one step, or call SD directly
```

---

## Offline mode

- Drop `.txt`, `.md`, or `.pdf` files into `offline_docs/`.
- Force offline anytime: `FORCE_OFFLINE=1 python agent.py`.
- When there is no connection, `search_web` automatically falls back to a local
  TF-IDF search over those documents. Image, mask, video, and memory tools work
  fully offline already.

---

## Configuration

Everything is environment-overridable (see `config.py`). Common knobs:

| Variable | Default | Meaning |
|----------|---------|---------|
| `LLM_MODEL` | `qwen2.5:3b-instruct` | Ollama chat model |
| `SD_API` | `http://127.0.0.1:7860` | Forge/A1111 API base URL |
| `SD_WIDTH` / `SD_HEIGHT` | `512` / `768` | generation size (keep small on 4 GB) |
| `USE_DEPTH_CONTROLNET` | `0` | add a second (depth) ControlNet — only if VRAM allows |
| `SEARXNG_URL` | `http://localhost:8888` | your SearXNG instance |
| `FORCE_OFFLINE` | `0` | set `1` to disable all networking |

---

## Why the outfit swap preserves your identity

The agent never asks a model to "redraw you in a saree". Instead:
1. **Human-parsing** (`generate_mask.py`) labels each pixel and masks **only the
   garment** classes. Your **face, hair, skin, and background are excluded** from
   the mask.
2. **Inpainting** regenerates **only the masked pixels**, so everything outside
   the clothing is copied through untouched.
3. **OpenPose ControlNet** locks your pose so the new garment drapes onto your
   exact stance. (Enable the optional depth ControlNet to further constrain body
   shape if you have VRAM headroom.)

> Reality check: this keeps your *silhouette and pose*, but diffusion does not
> literally measure you, so proportions are approximated, not metrologically
> exact. That is the honest limit of what runs locally on 4 GB today.

> Please only use real faces with consent (your own photos are ideal).

---

## What was fixed vs. the original scaffold

| Original problem | Fix here |
|------------------|----------|
| Told you to launch **Fooocus** but called the **A1111 ControlNet** API (404s) | `sd_tools.py` targets **Forge/A1111**; resolves ControlNet model names by prefix |
| `add_crossfade_transitions` referenced an undefined `[vout]` and never chained `xfade` (crashed every run) | `video_tools.py` builds a correct `xfade` chain with cumulative offsets — **verified** to produce exact-duration output |
| Qwen `<think>` tags broke `json.loads`, silently running no tool | `llm_utils.extract_json` strips reasoning tags + brace-scans; handles prose-wrapped JSON |
| SAM prompted with **one center point** → unreliable masks that repaint face/background | Human-parsing (`segformer_b2_clothes`) masks **only clothing**, preserving face/bg by construction |
| SAM checkpoint never downloaded | Mask model auto-downloads (cached into `models/`) |
| Assumed 8B LLM + SD + SAM coexist in 4 GB | LLM on **CPU**, SD on **GPU**; tools sequenced; CPU `torch` recommended |
| Brittle DuckDuckGo HTML scrape (titles/snippets only) | **SearXNG JSON API** + real page fetch (RAG) |
| No offline mode (a stated requirement) | Local-document TF-IDF search + `FORCE_OFFLINE` |
| `mem0` added an extra LLM call per turn | Dependency-free local **JSON memory** |
| `shell=True` with f-strings (breaks on spaces) | All subprocess calls use **argument lists** |
| LLM args passed straight into functions (TypeError on bad args) | `dispatch()` validates args against each function signature |

---

## Limitations (read this)

- **No local AI video generation** on 4 GB. Use the FFmpeg slideshow tools, or
  burst to a free cloud GPU (Colab/Kaggle) for that one feature — which would
  break the "private/offline" guarantee, so it's intentionally left out here.
- **SD 1.5 only.** SDXL/Flux are out of reach at 4 GB.
- **Speed.** Everything works; some steps take minutes. That is the cost of free
  + private + local on 2016-era hardware.
- **"Uncensored / no guardrails"** depends entirely on which model checkpoints
  you choose to install; this project does not bundle or endorse any. Use
  responsibly and only with images of consenting adults.
