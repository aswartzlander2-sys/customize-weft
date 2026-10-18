#!/usr/bin/env bash
# uninstall: stop and remove the service (a linked copy is left to its host),
# take this addon off the mesh and out of Settings → Connected apps. The host
# deletes the data folder (theme, logo, key) itself when ADDON_KEEP_DATA=0.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
. "$(dirname "$0")/common.sh"
case "$(conf linked 2>/dev/null)" in
  True|true) echo "it was linked: the Weft host that runs it keeps running it" ;;
  *) service_remove; mesh_withdraw; integration_remove; echo "stopped and removed ${ADDON_NAME:-$ADDON_ID} (and its Connected apps entry)" ;;
esac
