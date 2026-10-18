# weft/common.sh: Customize UI's own helpers, next to the vendored lib.sh
# (which is never edited). Sourced after lib.sh.
#
#   KEY_FILE          $ADDON_DATA/key: the secret Burrow's mount sends along
#   key_ensure        make it once, 0600, keep it across updates
#   INTEG_FILE        ~/.config/aegis/integrations/customize-ui.json
#   integration_write the file that lists the studio under Settings → Connected apps
#   integration_remove

KEY_FILE="$DATA/key"
INTEG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/aegis/integrations"
INTEG_FILE="$INTEG_DIR/$ADDON_ID.json"

key_ensure() {
  mkdir -p "$DATA"
  if [ ! -s "$KEY_FILE" ]; then
    (umask 077; python3 -c 'import secrets; print(secrets.token_urlsafe(32))' > "$KEY_FILE")
  fi
  chmod 600 "$KEY_FILE"
}

# The dashboard reads this folder on every request. Only this addon's own file
# is written: <id>.json, named after the id, as aegis/integrations.mjs wants.
integration_write() {
  mkdir -p "$INTEG_DIR"
  KEY_UNUSED=1 python3 - "$INTEG_FILE" "$CONF" "$DIR/logo.svg" <<'PY'
import json, os, sys, time
path, conf, logo = sys.argv[1:4]
cfg = json.load(open(conf))
bind = cfg.get("bind") or "127.0.0.1"
host = "127.0.0.1" if bind in ("0.0.0.0", "::", "") else ("[%s]" % bind if ":" in bind else bind)
url = "http://%s:%s/" % (host, cfg.get("port"))
host_url = (cfg.get("host_url") or "").rstrip("/")
# keep the public address the studio learned from the browser (see app/server.py)
try:
    old = json.load(open(path))
except Exception:
    old = {}
public = old.get("public_url") or (host_url + "/__gate/customize-ui/" if host_url else "")
try:
    svg = open(logo).read()
except Exception:
    svg = ""
entry = {
    "spec": 1, "id": cfg["id"], "kind": "customize-ui", "name": "Customize UI",
    "version": cfg.get("version", ""), "url": url, "port": cfg.get("port"),
    "public_url": public, "logo": svg if svg.lstrip().startswith("<svg") and len(svg) <= 65536 else "",
    "updated": int(time.time()),
}
tmp = path + ".tmp"
with open(tmp, "w") as fh:
    json.dump(entry, fh, indent=2)
os.chmod(tmp, 0o644)
os.replace(tmp, path)
PY
}

integration_remove() { rm -f "$INTEG_FILE" "$INTEG_FILE.tmp"; }
