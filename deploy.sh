#!/usr/bin/env bash
# deploy.sh — Pull latest code and restart the Flask app container.
# Run from /opt/truckcodex on the VPS:
#   bash deploy.sh

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "[1/3] Pulling latest code from GitHub..."
git pull origin main

echo "[2/3] Rebuilding and restarting app container..."
docker compose up -d --build app

echo "[3/3] Done."
echo "  App status: $(docker compose ps app --format 'table {{.Status}}')"
