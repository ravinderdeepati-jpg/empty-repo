#!/usr/bin/env bash
#
# Starts the Vane search assistant (bundled SearXNG included).
# Ollama should already be running natively in the background.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "${SCRIPT_DIR}")"

# --- Pre-flight checks ------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker not found. Install Docker Desktop / Docker Engine first."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is installed but not running. Start Docker and retry."
  exit 1
fi

# Warn (don't fail) if Ollama doesn't answer on the default port.
if command -v curl >/dev/null 2>&1; then
  if ! curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "WARNING: Ollama doesn't seem to be responding on http://localhost:11434"
    echo "         Make sure Ollama is installed and running, then run ./scripts/setup-models.sh"
    echo ""
  fi
fi

echo "==> Starting Vane..."
docker compose -f "${COMPOSE_DIR}/docker-compose.yml" up -d

echo ""
echo "Vane is starting. Open: http://localhost:3000"
echo ""
echo "First-run setup screen -> choose Ollama and set the API URL to:"
echo "  Windows / macOS : http://host.docker.internal:11434"
echo "  Linux           : http://host.docker.internal:11434  (works via host-gateway)"
echo "Then pick chat model 'llama3.2:3b' and embedding model 'nomic-embed-text'."
