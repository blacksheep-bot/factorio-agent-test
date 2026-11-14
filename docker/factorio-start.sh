#!/bin/bash
# Entrypoint of the `factorio` compose service. Same flags as setup/start_server.sh.
#   FLE_SCENARIO = open_world (default) | default_lab_scenario
#   FLE_SAVE     = name of /factorio/saves/<name>.zip to load instead of the scenario
#   FLE_SEED     = map-gen seed (default 44340, as FLE)
set -euo pipefail
SAVES=/factorio/saves
# Saves dir is a host bind mount; the server runs as uid 845 and must be able to write it
# (gotcha G4: if it is missing, game.server_save() kills the server).
mkdir -p "$SAVES"
if [ "$(id -u)" = 0 ]; then
  chmod a+rwX "$SAVES"
  RUN="runuser -u factorio -g factorio --"
else
  RUN=""
fi
if [ -n "${FLE_SAVE:-}" ]; then
  f="$SAVES/${FLE_SAVE%.zip}.zip"
  [ -f "$f" ] || { echo "FLE_SAVE=$FLE_SAVE but $f does not exist; saves: $(ls $SAVES)" >&2; exit 1; }
  LAUNCH=(--start-server "$f")
else
  LAUNCH=(--start-server-load-scenario "${FLE_SCENARIO:-open_world}")
fi
echo "fle-factorio: ${LAUNCH[*]}"
exec $RUN /opt/factorio/bin/x64/factorio "${LAUNCH[@]}" \
  --port 34197 --rcon-port 27015 --rcon-password "${FLE_RCON_PASSWORD:-factorio}" \
  --server-settings /opt/factorio/config/server-settings.json \
  --map-gen-settings /opt/factorio/config/map-gen-settings.json \
  --map-settings /opt/factorio/config/map-settings.json \
  --server-adminlist /opt/factorio/config/server-adminlist.json \
  --mod-directory /opt/factorio/mods --map-gen-seed "${FLE_SEED:-44340}"
