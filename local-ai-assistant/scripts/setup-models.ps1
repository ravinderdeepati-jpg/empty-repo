<#
.SYNOPSIS
    Pulls the LLM + embedding models tuned for a 4GB-VRAM / 16GB-RAM laptop.
    Run this ONCE (or whenever you want to add/update models).

.NOTES
    Requires: Ollama installed natively (https://ollama.com/download)
#>

$ErrorActionPreference = "Stop"

# --- Models -----------------------------------------------------------------
# Primary chat model: small, fast, fits comfortably on 4GB VRAM + RAM.
$ChatModel = "llama3.2:3b"

# Embedding model: needed for the "upload a file and ask about it" feature.
$EmbedModel = "nomic-embed-text"

# Optional larger model. Uncomment to also pull. A 7B Q4 model spills from the
# 4GB GPU into system RAM, so it runs noticeably slower but gives better answers.
# $AltModel = "qwen2.5:7b"
# ----------------------------------------------------------------------------

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Error "'ollama' command not found. Install Ollama first: https://ollama.com/download"
    exit 1
}

Write-Host "==> Pulling chat model: $ChatModel"
ollama pull $ChatModel

Write-Host "==> Pulling embedding model: $EmbedModel"
ollama pull $EmbedModel

if ($AltModel) {
    Write-Host "==> Pulling optional larger model: $AltModel"
    ollama pull $AltModel
}

Write-Host ""
Write-Host "Done. Installed models:"
ollama list
