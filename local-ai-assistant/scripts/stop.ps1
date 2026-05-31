<#
.SYNOPSIS
    Stops the Vane container. Your settings/history are preserved in the
    'vane-data' Docker volume, so they'll still be there next time you start.
#>

$ErrorActionPreference = "Stop"

$ComposeDir = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $ComposeDir "docker-compose.yml"

Write-Host "==> Stopping Vane..."
docker compose -f $ComposeFile down

Write-Host "Stopped. Data is preserved in the 'vane-data' volume."
