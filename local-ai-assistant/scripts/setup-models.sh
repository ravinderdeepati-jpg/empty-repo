#!/usr/bin/env bash
#
# Pulls the LLM + embedding models tuned for a 4GB-VRAM / 16GB-RAM laptop.
# Run this ONCE (or whenever you want to add/update models).
#
# Requires: Ollama installed natively (https://ollama.com/download)
#
set -euo pipefail

# --- Models -----------------------------------------------------------------
# Primary chat model: small, fast, fits comfortably on 4GB VRAM + RAM.
CHAT_MODEL="llama3.2:3b"

# Embedding model: needed for the "upload a file and ask about it" feature.
EMBED_MODEL="nomic-embed-text"

# Optional larger model. Uncomment to also pull. A 7B Q4 model spills from the
# 4GB GPU into system RAM, so it runs noticeably slower but gives better answers.
# ALT_MODEL="qwen2.5:7b"
# ----------------------------------------------------------------------------

if ! command -v ollama >/dev/null 2>&1; then
  echo "ERROR: 'ollama' command not found."
  echo "Install Ollama first: https://ollama.com/download"
  exit 1
fi

echo "==> Pulling chat model: ${CHAT_MODEL}"
ollama pull "${CHAT_MODEL}"

echo "==> Pulling embedding model: ${EMBED_MODEL}"
ollama pull "${EMBED_MODEL}"

if [ -n "${ALT_MODEL:-}" ]; then
  echo "==> Pulling optional larger model: ${ALT_MODEL}"
  ollama pull "${ALT_MODEL}"
fi

echo ""
echo "Done. Installed models:"
ollama list
