#!/usr/bin/env bash
# install (and update): run the studio as a service, or link the copy another
# Weft host already runs. Talks back with ::phase, ::progress, ::open and ::warn.
#
# Beyond Hello Weft's skeleton it also:
#   - keeps a random key in $ADDON_DATA/key: Burrow's mount (burrow/extension.mjs)
#     sends it with every request, so only the dashboard's signed-in users reach
#     the studio (the bare port answers /health and a "locked" page);
#   - drops ~/.config/aegis/integrations/customize-ui.json, which is what puts
#     "Customize UI · Open" under Settings → Connected apps (see README).
set -euo pipefail
. "$(dirname "$0")/lib.sh"
. "$(dirname "$0")/common.sh"
port="$(setting PORT)"
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }

linked() { [ "$(conf linked)" = True ] || [ "$(conf linked)" = true ]; }

if [ "${ADDON_ADOPT:-0}" = 1 ] && [ "${ADDON_UPDATE:-0}" != 1 ] && [ ! -f "$UNIT_FILE" ] && [ ! -f "$PIDF" ]; then
  # Another host runs it: point at that one, start nothing (see SPEC.md, "Linking").
  echo "::phase Linking the ${ADDON_NAME:-$ADDON_ID} already running"
  conf_write "$port"
  python3 -c 'import json,sys; p=sys.argv[1]; c=json.load(open(p)); c["linked"]=True; json.dump(c,open(p,"w"),indent=2)' "$CONF"
  healthy || { echo "It stopped answering on port $port while linking."; exit 1; }
  echo "linked: $(url) is run by another Weft host; this one shows it and leaves it alone"
  echo "::open $(url)"
  exit 0
fi
if [ -f "$CONF" ] && linked; then
  echo "::phase Updating the link"
  conf_write "$(conf port)"
  echo "still linked to $(url)"
  echo "::open $(url)"
  exit 0
fi

if [ "${ADDON_UPDATE:-0}" = 1 ]; then echo "::phase Updating ${ADDON_NAME:-$ADDON_ID}"; else echo "::phase Installing ${ADDON_NAME:-$ADDON_ID}"; fi
echo "::progress 15 Checking port $port"
if port_taken "$port"; then
  echo "Port $port is used by something else. Pick another one in the addon's settings."
  exit 1
fi
echo "::progress 35 Writing the settings"
conf_write "$port"
echo "settings in $CONF"
echo "::progress 50 Keeping the gate key"
key_ensure
echo "::progress 65 Starting it"
service_install
service_start
if ! wait_up; then
  echo "It did not start. The last lines of its log:"
  tail -n 20 "$LOG" 2>/dev/null || journalctl --user -u "$UNIT" -n 20 --no-pager 2>/dev/null || true
  exit 1
fi
echo "::progress 85 Telling the dashboard"
integration_write
echo "listed under Settings → Connected apps ($INTEG_FILE)"
echo "running as $(service_how), on $(url)"
echo "::progress 100 Ready"
if [ "${ADDON_HOST:-}" = burrow ] && [ -n "${ADDON_HOST_URL:-}" ]; then
  echo "open it from the dashboard: Settings → Connected apps → Customize UI → Open (or ${ADDON_HOST_URL%/}/__gate/customize-ui/)"
  echo "::open ${ADDON_HOST_URL%/}/__gate/customize-ui/"
elif [ "${ADDON_HOST:-}" = burrow ]; then
  echo "open it from the dashboard: Settings → Connected apps → Customize UI → Open"
  echo "::open $(url)"
else
  echo "::warn Made for Aegis × Burrow: the studio needs Burrow's mount to reach your dashboard's screens."
  echo "::open $(url)"
fi
