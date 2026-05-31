<#
.SYNOPSIS
    Starts the Vane search assistant (bundled SearXNG included).
    Ollama should already be running natively in the background.
#>

$ErrorActionPreference = "Stop"

$ComposeDir = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $ComposeDir "docker-compose.yml"

# --- Pre-flight checks ------------------------------------------------------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install Docker Desktop first."
    exit 1
}

try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is installed but not running. Start Docker Desktop and retry."
    exit 1
}

# Warn (don't fail) if Ollama doesn't answer on the default port.
try {
    Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null
} catch {
    Write-Warning "Ollama doesn't seem to be responding on http://localhost:11434"
    Write-Warning "Make sure Ollama is installed and running, then run .\scripts\setup-models.ps1"
    Write-Host ""
}

Write-Host "==> Starting Vane..."
docker compose -f $ComposeFile up -d

Write-Host ""
Write-Host "Vane is starting. Open: http://localhost:3000"
Write-Host ""
Write-Host "First-run setup screen -> choose Ollama and set the API URL to:"
Write-Host "  http://host.docker.internal:11434"
Write-Host "Then pick chat model 'llama3.2:3b' and embedding model 'nomic-embed-text'."
