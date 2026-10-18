#!/usr/bin/env bash
# status: one JSON line, quickly: {"state", "url", "port", "version", "detail"}.
set -u
. "$(dirname "$0")/lib.sh"
[ -f "$CONF" ] || { echo '{"state":"error","detail":"no settings: install it again"}'; exit 0; }
how="its own service"; case "$(conf linked)" in True|true) how="run by another Weft host" ;; esac
# the theme's name goes into the JSON line: letters, digits and a few marks only
theme="$(python3 -c 'import json,re,sys; print(re.sub(r"[^A-Za-z0-9 ._-]", "", str(json.load(open(sys.argv[1])).get("name","")))[:40])' "$DATA/theme.json" 2>/dev/null || true)"
[ -n "$theme" ] && how="theme $theme, $how"
if healthy; then status_line running "Settings → Connected apps → Open; on port $(conf port), $how"; else status_line stopped "not answering on port $(conf port) ($how)"; fi
