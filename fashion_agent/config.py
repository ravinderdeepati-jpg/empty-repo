"""
Central configuration for the local fashion AI agent.

Everything is tuned for a Lenovo/ThinkPad P51 with an NVIDIA Quadro M1200 (4 GB
VRAM) and 16 GB system RAM. The single most important rule on this hardware:

    The LLM runs on the CPU. The GPU is reserved for Stable Diffusion.

A 4 GB card cannot hold an 8B chat model AND a Stable Diffusion pipeline at the
same time, so we deliberately keep them on separate compute devices.

All values can be overridden with environment variables so you never have to
edit code to retune for a different machine.
"""

import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
# Resolve everything relative to this file so the agent works no matter what
# directory you launch it from.
BASE_DIR = Path(__file__).resolve().parent

INPUT_PHOTOS_DIR = BASE_DIR / "input_photos"
MASKS_DIR = BASE_DIR / "masks"
GENERATED_OUTFITS_DIR = BASE_DIR / "generated_outfits"
PROCESSED_IMAGES_DIR = BASE_DIR / "processed_images"
FINAL_VIDEOS_DIR = BASE_DIR / "final_videos"
DOCS_DIR = BASE_DIR / "offline_docs"            # drop PDFs / .txt / .md here for offline RAG
MODELS_DIR = BASE_DIR / "models"                # local model checkpoints (SAM-style helpers, etc.)
MEMORY_DIR = BASE_DIR / "memory"                # private JSON memory + RAG index live here

# Directories the agent is allowed to read/write. Used to sandbox file access.
ALLOWED_DIRS = [
    INPUT_PHOTOS_DIR,
    MASKS_DIR,
    GENERATED_OUTFITS_DIR,
    PROCESSED_IMAGES_DIR,
    FINAL_VIDEOS_DIR,
    DOCS_DIR,
    MODELS_DIR,
    MEMORY_DIR,
]


def ensure_dirs() -> None:
    """Create every working directory if it does not exist yet."""
    for d in [
        INPUT_PHOTOS_DIR,
        MASKS_DIR,
        GENERATED_OUTFITS_DIR,
        PROCESSED_IMAGES_DIR,
        FINAL_VIDEOS_DIR,
        DOCS_DIR,
        MODELS_DIR,
        MEMORY_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# LLM (Ollama) settings
# --------------------------------------------------------------------------- #
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Default chat model. qwen2.5:3b is the sweet spot for a 4 GB / CPU setup:
# it is small enough to stay responsive on CPU and is reliable at emitting JSON.
# If you have patience (or run the LLM on a second machine), bump to a 7-8B model.
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:3b-instruct")

# Embedding model for offline document RAG.
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")

# Some Qwen3 / reasoning builds emit <think>...</think> blocks. We strip them,
# but we also try to ask the model not to think when the backend supports it.
LLM_DISABLE_THINKING = os.environ.get("LLM_DISABLE_THINKING", "1") == "1"

# Seconds to wait for an LLM response before giving up (CPU inference is slow).
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "180"))


# --------------------------------------------------------------------------- #
# Stable Diffusion (Forge / AUTOMATIC1111 compatible) settings
# --------------------------------------------------------------------------- #
# IMPORTANT: this must be the Forge or AUTOMATIC1111 WebUI launched with --api.
# Fooocus does NOT speak this API. See README for launch flags.
SD_API = os.environ.get("SD_API", "http://127.0.0.1:7860")

# Generation defaults tuned for SD 1.5 on 4 GB VRAM.
SD_STEPS = int(os.environ.get("SD_STEPS", "25"))
SD_CFG_SCALE = float(os.environ.get("SD_CFG_SCALE", "7.0"))
SD_WIDTH = int(os.environ.get("SD_WIDTH", "512"))
SD_HEIGHT = int(os.environ.get("SD_HEIGHT", "768"))
SD_DENOISING_STRENGTH = float(os.environ.get("SD_DENOISING_STRENGTH", "0.85"))
SD_SAMPLER = os.environ.get("SD_SAMPLER", "DPM++ 2M Karras")

# ControlNet model names as they appear in your Forge install. The hash suffix
# varies between downloads, so we match by prefix at call time.
CN_OPENPOSE_MODEL = os.environ.get("CN_OPENPOSE_MODEL", "control_v11p_sd15_openpose")
CN_DEPTH_MODEL = os.environ.get("CN_DEPTH_MODEL", "control_v11f1p_sd15_depth")

# On 4 GB VRAM, running TWO ControlNets on top of SD 1.5 inpainting frequently
# OOMs. Default to OpenPose only. Set USE_DEPTH_CONTROLNET=1 if you have headroom.
USE_DEPTH_CONTROLNET = os.environ.get("USE_DEPTH_CONTROLNET", "0") == "1"


# --------------------------------------------------------------------------- #
# Search settings
# --------------------------------------------------------------------------- #
# Self-hosted SearXNG instance (recommended). Run it in Docker (see README).
# We hit its JSON API, which is far more robust than scraping a search engine.
SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://localhost:8888")

# How many result pages to actually fetch and read for RAG-style summaries.
SEARCH_FETCH_PAGES = int(os.environ.get("SEARCH_FETCH_PAGES", "3"))

# Per-request network timeout for search/fetch.
NET_TIMEOUT = int(os.environ.get("NET_TIMEOUT", "15"))


# --------------------------------------------------------------------------- #
# Offline / online mode
# --------------------------------------------------------------------------- #
# FORCE_OFFLINE=1 hard-disables every network call. Otherwise the agent probes
# connectivity at startup and per-search, and falls back to local document RAG
# when the internet is unreachable.
FORCE_OFFLINE = os.environ.get("FORCE_OFFLINE", "0") == "1"


# --------------------------------------------------------------------------- #
# External binaries
# --------------------------------------------------------------------------- #
# ImageMagick v7 uses the unified `magick` binary; v6 uses `convert`.
# image_tools.py auto-detects, but you can force one here.
IMAGEMAGICK_BIN = os.environ.get("IMAGEMAGICK_BIN", "")  # "" = auto-detect
FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")
FFPROBE_BIN = os.environ.get("FFPROBE_BIN", "ffprobe")
