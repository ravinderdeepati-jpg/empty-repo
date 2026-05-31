#!/usr/bin/env bash
#
# Stops the Vane container. Your settings/history are preserved in the
# 'vane-data' Docker volume, so they'll still be there next time you start.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "${SCRIPT_DIR}")"

echo "==> Stopping Vane..."
docker compose -f "${COMPOSE_DIR}/docker-compose.yml" down

echo "Stopped. Data is preserved in the 'vane-data' volume."
