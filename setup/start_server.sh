#!/usr/bin/env bash
# Start ONE headless Factorio 2.0.73 server the way FLE's `fle cluster start` does
# (same image, scenario, flags, ports), plus:
#   * a bind-mounted saves dir (./.fle/saves) so save files land on the host
#   * a copied server-settings.json with autosave effectively disabled
#     (GOTCHA: any save while FLE's Lua tools are loaded crashes the server, see docs)
#
# Usage: setup/start_server.sh [scenario]   (default_lab_scenario | open_world)
#        FLE_SAVE=fle_demo setup/start_server.sh   # load .fle/saves/fle_demo.zip instead
# Env:   FLE_CONTAINER (default fle_factorio_0), FLE_RCON_PORT (27000), FLE_GAME_PORT (34197)
# Ports: RCON tcp/27000 (password "factorio"), game udp/34197.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCENARIO="${1:-default_lab_scenario}"
NAME="${FLE_CONTAINER:-fle_factorio_0}"
IMAGE="factoriotools/factorio:2.0.73"
RCON_PORT="${FLE_RCON_PORT:-27000}"
GAME_PORT="${FLE_GAME_PORT:-34197}"
if [ -n "${FLE_SAVE:-}" ]; then
  [ -f "$ROOT/.fle/saves/${FLE_SAVE%.zip}.zip" ] || { echo "no such save: .fle/saves/${FLE_SAVE%.zip}.zip"; exit 1; }
  LAUNCH="--start-server /factorio/saves/${FLE_SAVE%.zip}.zip"
else
  LAUNCH="--start-server-load-scenario $SCENARIO"
fi
PKG="$("$ROOT/.venv/bin/python" -c 'import importlib.util;print(importlib.util.find_spec("fle").submodule_search_locations[0])')"

docker info >/dev/null 2>&1 || { echo "docker daemon not running: (dockerd > /tmp/dockerd.log 2>&1 &)"; exit 1; }

STATE="$ROOT/.fle/server"
mkdir -p "$STATE/config" "$STATE/mods" "$ROOT/.fle/saves" "$ROOT/.fle/data/_screenshots"
cp "$PKG"/cluster/config/* "$STATE/config/"
cp "$PKG"/cluster/mods/mod-list.json "$STATE/mods/"
# Disable autosave (interval in minutes; Factorio has no "off", so make it ~1 year).
"$ROOT/.venv/bin/python" - "$STATE/config/server-settings.json" <<'EOF'
import json, sys
p = sys.argv[1]; s = json.load(open(p))
s["autosave_interval"] = 525600; s["autosave_slots"] = 0; s["auto_pause"] = False
json.dump(s, open(p, "w"), indent=2)
EOF
chmod -R a+rwX "$STATE" "$ROOT/.fle/saves" "$ROOT/.fle/data/_screenshots"

docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" \
  --restart unless-stopped \
  --user factorio --entrypoint "" \
  --cpus 1 --memory 1024m \
  -p "$RCON_PORT":27015/tcp -p "$GAME_PORT":34197/udp \
  -v "$PKG/cluster/scenarios:/opt/factorio/scenarios:ro" \
  -v "$STATE/config:/opt/factorio/config" \
  -v "$STATE/mods:/opt/factorio/mods" \
  -v "$ROOT/.fle/saves:/factorio/saves" \
  -v "$ROOT/.fle/data/_screenshots:/opt/factorio/script-output" \
  "$IMAGE" /bin/sh -c "rm -rf /opt/factorio/data/elevated-rails /opt/factorio/data/quality /opt/factorio/data/space-age && \
    exec /opt/factorio/bin/x64/factorio $LAUNCH \
    --port 34197 --rcon-port 27015 --rcon-password factorio \
    --server-settings /opt/factorio/config/server-settings.json \
    --map-gen-settings /opt/factorio/config/map-gen-settings.json \
    --map-settings /opt/factorio/config/map-settings.json \
    --server-adminlist /opt/factorio/config/server-adminlist.json \
    --mod-directory /opt/factorio/mods --map-gen-seed 44340" >/dev/null

# Wait for RCON
for i in $(seq 1 60); do
  if docker logs "$NAME" 2>&1 | grep -q "Starting RCON interface"; then
    echo "Factorio server '$NAME' up: RCON localhost:$RCON_PORT (pw factorio), game udp $GAME_PORT, $LAUNCH"
    exit 0
  fi
  sleep 1
done
echo "server did not come up; see: docker logs $NAME" >&2; exit 1
