#!/usr/bin/env bash
# valhalla/rebuild_tiles.sh
#
# Monthly tile refresh — downloads the latest Australia OSM extract from
# Geofabrik and rebuilds Valhalla tiles with zero-downtime switchover.
#
# Run from the project root:
#   bash valhalla/rebuild_tiles.sh
#
# Strategy:
#   1. Download fresh PBF alongside the existing one (temp file)
#   2. Build new tiles into a staging directory
#   3. Stop Valhalla, swap tile directories, restart Valhalla
#   This keeps the service down for ~10–30 seconds rather than 30–60 minutes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PBF_URL="https://download.geofabrik.de/australia-oceania/australia-latest.osm.pbf"
CUSTOM_FILES="$SCRIPT_DIR/custom_files"
PBF_NEW="$CUSTOM_FILES/australia-latest-new.osm.pbf"
TILES_LIVE="$CUSTOM_FILES/tiles"
TILES_NEW="$CUSTOM_FILES/tiles-new"
TILES_OLD="$CUSTOM_FILES/tiles-old"

cd "$PROJECT_ROOT"

echo "=================================================="
echo "  TransportApp — Valhalla monthly tile rebuild"
echo "  $(date '+%Y-%m-%d %H:%M')"
echo "=================================================="
echo ""

if ! docker info > /dev/null 2>&1; then
  echo "ERROR: Docker is not running."
  exit 1
fi

# ── Download fresh PBF ────────────────────────────────────────────────────────

echo "Downloading fresh Australia OSM extract (~780 MB)..."
curl -L --progress-bar "$PBF_URL" -o "$PBF_NEW"
echo "✓ Download complete."
echo ""

# ── Build new tiles into staging directory ────────────────────────────────────

mkdir -p "$TILES_NEW"

echo "Building new tiles into tiles-new/ (30–60 min)..."
docker run --rm \
  -v "$CUSTOM_FILES:/custom_files" \
  ghcr.io/valhalla/valhalla:run-latest \
  /bin/bash -c "
    set -e
    # Temporarily point tile_dir at tiles-new
    sed 's|/custom_files/tiles\"|/custom_files/tiles-new\"|g; s|/custom_files/tiles/admins|/custom_files/tiles-new/admins|g' \
      /custom_files/valhalla.json > /tmp/valhalla-new.json

    echo '[1/2] Building routing tiles...'
    valhalla_build_tiles -c /tmp/valhalla-new.json /custom_files/australia-latest-new.osm.pbf

    echo '[2/2] Building admin regions...'
    valhalla_build_admins -c /tmp/valhalla-new.json /custom_files/australia-latest-new.osm.pbf

    echo 'Build complete.'
  "

echo "✓ New tiles built."
echo ""

# ── Swap tile directories (brief downtime) ────────────────────────────────────

echo "Swapping tile directories (~10 sec downtime)..."

docker compose stop valhalla

# Rotate: live → old, new → live
[ -d "$TILES_OLD" ] && rm -rf "$TILES_OLD"
mv "$TILES_LIVE" "$TILES_OLD"
mv "$TILES_NEW" "$TILES_LIVE"

# Update PBF: new → live, remove old
mv "$PBF_NEW" "$CUSTOM_FILES/australia-latest.osm.pbf"

docker compose up -d valhalla

echo "✓ Valhalla restarted with new tiles."
echo ""

# ── Cleanup ───────────────────────────────────────────────────────────────────

echo "Removing old tiles (~$(du -sh "$TILES_OLD" 2>/dev/null | cut -f1 || echo '?') freed)..."
rm -rf "$TILES_OLD"
echo "✓ Cleanup done."

echo ""
echo "=================================================="
echo "  Rebuild complete. $(date '+%Y-%m-%d %H:%M')"
echo "  Verify: curl http://localhost:8002/status"
echo "=================================================="
