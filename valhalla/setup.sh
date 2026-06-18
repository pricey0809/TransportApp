#!/usr/bin/env bash
# valhalla/setup.sh
#
# First-time Valhalla setup for TransportApp.
# Downloads the Australia OSM extract and builds routing tiles.
#
# Run from the project root:
#   bash valhalla/setup.sh
#
# Requirements:
#   - Docker Desktop running
#   - curl (installed by default on macOS/Linux; Git Bash on Windows includes it)
#   - ~5 GB free disk space (PBF ~780 MB + tiles ~3–4 GB)
#   - ~4 GB RAM available to Docker
#   - 30–60 minutes the first time

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PBF_URL="https://download.geofabrik.de/australia-oceania/australia-latest.osm.pbf"
PBF_PATH="$SCRIPT_DIR/custom_files/australia-latest.osm.pbf"

cd "$PROJECT_ROOT"

echo "=================================================="
echo "  TransportApp — Valhalla routing engine setup"
echo "=================================================="
echo ""

# ── Pre-flight checks ─────────────────────────────────────────────────────────

if ! docker info > /dev/null 2>&1; then
  echo "ERROR: Docker is not running. Start Docker Desktop and try again."
  exit 1
fi

if ! docker compose version > /dev/null 2>&1; then
  echo "ERROR: docker compose (v2) not found. Update Docker Desktop."
  exit 1
fi

mkdir -p "$SCRIPT_DIR/custom_files/tiles"

# ── Download OSM PBF ──────────────────────────────────────────────────────────

if [ -f "$PBF_PATH" ]; then
  echo "✓ PBF already present: $PBF_PATH"
  echo "  Delete it and re-run to force a fresh download."
else
  echo "Downloading Australia OSM extract from Geofabrik (~780 MB)..."
  echo "URL: $PBF_URL"
  echo ""
  curl -L --progress-bar "$PBF_URL" -o "$PBF_PATH"
  echo ""
  echo "✓ Download complete."
fi

echo ""

# ── Build tiles ───────────────────────────────────────────────────────────────

echo "Building Valhalla tiles (30–60 min — do not interrupt)..."
echo ""

docker compose --profile build run --rm valhalla-build

echo ""
echo "=================================================="
echo "  Setup complete."
echo ""
echo "  Start Valhalla:"
echo "    docker compose up -d valhalla"
echo ""
echo "  Check it's healthy:"
echo "    curl http://localhost:8002/status"
echo ""
echo "  Then start the Flask app as usual:"
echo "    python app.py"
echo "=================================================="
