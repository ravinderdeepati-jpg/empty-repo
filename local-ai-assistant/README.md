# Private Hybrid AI Search Assistant

A **private, offline-first** AI assistant that answers from a local LLM, and
goes **online only when you ask it to search** — then returns answers with
**cited sources**. Nothing leaves your machine except the actual web searches
you trigger (and those go out through your own bundled SearXNG meta-search, not
a tracking company).

Tuned for a **Lenovo P51 / Quadro M1200 (4GB VRAM) / 16GB RAM**.

---

## What you get

| Goal | How this delivers it |
| --- | --- |
| Private | LLM runs locally via Ollama; answers are synthesized on your machine |
| Offline chat | The LLM works with no internet for chat, reasoning, and Q&A over your files |
| Online search on demand | Toggle web search; SearXNG queries Google/Bing/Brave/DuckDuckGo and the LLM summarizes with citations |
| Free | All components are free and open-source |
| Your own data | Upload PDFs/text/images and ask questions about them (local embeddings) |

> **The honest tradeoff:** "works offline" and "search the whole internet" are
> opposites. This setup is **hybrid**: full offline chat, plus web search that
> only happens when you have internet and turn it on. That is the realistic way
> to satisfy both.

---

## Architecture (two pieces)

```
  +------------------------------+        +-------------------------------+
  |  Ollama (NATIVE on laptop)   |        |  Vane container (Docker)      |
  |  - runs the LLM on your GPU  | <----- |  - chat UI at :3000           |
  |  - http://localhost:11434    |        |  - bundled SearXNG meta-search|
  +------------------------------+        +-------------------------------+
```

- **Ollama runs natively** (not in Docker) so it can use your Quadro M1200 GPU.
- **Vane runs in Docker** and already bundles SearXNG, so there's nothing else
  to install for web search.

---

## Prerequisites

1. **Ollama** — native install: <https://ollama.com/download>
   (Windows installer, or Linux one-liner. It auto-detects NVIDIA CUDA.)
2. **Docker** — Docker Desktop (Windows/macOS) or Docker Engine (Linux):
   <https://docs.docker.com/get-docker/>

---

## Setup (first time)

### Windows (PowerShell)

```powershell
# 1. Pull the models (run once)
.\scripts\setup-models.ps1

# 2. Start the assistant
.\scripts\start.ps1
```

### Linux / macOS (bash)

```bash
# 1. Pull the models (run once)
./scripts/setup-models.sh

# 2. Start the assistant
./scripts/start.sh
```

> Linux note: so the Vane container can reach native Ollama, expose Ollama on
> all interfaces. Add `Environment="OLLAMA_HOST=0.0.0.0:11434"` under
> `/etc/systemd/system/ollama.service`, then
> `sudo systemctl daemon-reload && sudo systemctl restart ollama`.

### Finish in the browser

1. Open <http://localhost:3000>.
2. On the first-run setup screen, choose **Ollama** as the provider.
3. Set the **Ollama API URL** to:
   - Windows / macOS / Linux: `http://host.docker.internal:11434`
4. Select:
   - **Chat model:** `llama3.2:3b`
   - **Embedding model:** `nomic-embed-text`
5. Save. Ask a question. Toggle web search on when you want live results.

---

## Choosing a model for 4GB VRAM + 16GB RAM

| Model | Pull name | Notes |
| --- | --- | --- |
| Llama 3.2 3B | `llama3.2:3b` | **Default.** Fast, mostly fits in VRAM. Best starting point. |
| Qwen 2.5 3B | `qwen2.5:3b` | Strong small alternative, good at reasoning. |
| Phi-3 mini | `phi3:mini` | ~3.8B, snappy, good general quality. |
| Qwen 2.5 7B | `qwen2.5:7b` | Better answers, but spills into RAM → slower. Use if you can wait. |

Rule of thumb on your hardware: **3B models feel interactive; 7B models work
but are noticeably slower** because only part of the model fits in the 4GB GPU
and the rest runs on CPU/RAM. Stick with `llama3.2:3b` unless you specifically
need more depth.

To switch models later, edit `scripts/setup-models.*`, re-run it, then pick the
new model in the Vane settings screen.

---

## Daily use

```bash
# start
./scripts/start.sh        # or  .\scripts\start.ps1

# stop (settings/history are preserved)
./scripts/stop.sh         # or  .\scripts\stop.ps1
```

- **Offline mode:** just don't toggle web search. The LLM answers from its own
  knowledge and from any files you've uploaded.
- **Online mode:** toggle web search for live, cited results.

---

## Troubleshooting

**"No chat model providers configured" / Ollama connection error**
- Confirm Ollama is running: open <http://localhost:11434> in a browser — you
  should see "Ollama is running".
- In Vane settings, the URL must be `http://host.docker.internal:11434`
  (not `127.0.0.1` — that points inside the container, not your host).
- Linux: make sure you set `OLLAMA_HOST=0.0.0.0:11434` (see Linux note above).

**Generation is very slow**
- Use a 3B model, not 7B.
- Close other GPU/RAM-heavy apps (browsers with many tabs, etc.).
- First response after startup is always slowest (model loads into memory).

**Out of memory**
- Switch to a smaller model (`llama3.2:3b` or `qwen2.5:3b`).
- Reduce the context length in Ollama if you customized it.

---

## What this setup is NOT

This is the **search/chat** half of the larger idea. Local **image editing**
(e.g. virtual try-on) is a separate tool (Stable Diffusion 1.5 + ControlNet +
inpainting via SD Forge) and local **video generation** is not realistic on a
4GB GPU. See the conversation notes for the full breakdown.

---

## Sources / further reading

- Vane (formerly Perplexica): <https://github.com/ItzCrazyKns/Vane>
- SearXNG: <https://github.com/searxng/searxng>
- Ollama: <https://ollama.com>

_Setup notes were rephrased and summarized from the official Vane README for
compliance with licensing restrictions._
