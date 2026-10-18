"""Customize UI: the theme studio's server.

Started by weft/lib.sh (service_start) with data/config.json as its argument.
Burrow mounts it at /__gate/customize-ui/ (burrow/extension.mjs) and sends the
gate key with every request; the bare port only answers /health and a "locked"
page. State lives in ADDON_DATA only: theme.json, logo.<ext>, key.

Routes (all relative to where the page is served, so they work under the mount):
  GET  /                      the studio (needs the key)
  GET  /health                {"app": "customize-ui", "ok": true, "version": …}
  GET  /api/state             theme, screens, logo, host facts
  PUT  /api/theme             save the whole theme (JSON)
  POST /api/logo              {"data_url": "data:image/svg+xml;base64,…"} (≤ 512 KB)
  DELETE /api/logo
  GET  /logo                  the uploaded logo
  POST /api/origin            {"origin": "https://…"}: the dashboard's public address,
                              kept in the Connected apps entry so "Open" works remotely
  GET  /api/preview/<screen>?mode=dark|light   a screen with the theme applied
  GET  /api/export.json | /api/export.css      the theme pack
"""
import base64
import copy
import json
import os
import re
import sys
import time
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "weft"))
import mesh  # noqa: E402  (weft/mesh.py, vendored)
import screens  # noqa: E402  (app/screens.py: previews and presets)

cfg = mesh.load_config(sys.argv[1])
DATA = os.path.dirname(os.path.abspath(sys.argv[1]))
THEME_FILE = os.path.join(DATA, "theme.json")
LOGO_META = os.path.join(DATA, "logo.json")
KEY_FILE = os.path.join(DATA, "key")
INTEG_FILE = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config"),
                          "aegis", "integrations", cfg["id"] + ".json")
UI = open(os.path.join(HERE, "ui", "index.html"), encoding="utf-8").read()
MAX_LOGO = 512 * 1024
LOGO_TYPES = {"image/svg+xml": "svg", "image/png": "png", "image/webp": "webp", "image/jpeg": "jpg"}


def read_key():
    try:
        return open(KEY_FILE).read().strip()
    except OSError:
        return ""


def load_theme():
    try:
        t = json.load(open(THEME_FILE))
        if isinstance(t, dict) and t.get("spec") == 1:
            return screens.clean_theme(t)
    except (OSError, ValueError):
        pass
    return screens.default_theme(cfg.get("preset") or "glacier", cfg.get("home_tile") in ("1", 1, True))


def logo_meta():
    try:
        m = json.load(open(LOGO_META))
        if os.path.isfile(os.path.join(DATA, m["file"])):
            return m
    except (OSError, ValueError, KeyError):
        pass
    return None


def integration_set_public(origin):
    """Keep the dashboard's real address in our Connected apps entry (only our own file)."""
    try:
        entry = json.load(open(INTEG_FILE))
    except (OSError, ValueError):
        return False
    entry["public_url"] = origin.rstrip("/") + "/__gate/" + cfg["id"] + "/"
    entry["updated"] = int(time.time())
    mesh.write_json(INTEG_FILE, entry)
    return True


class Studio(mesh.Handler):
    def authed(self):
        key = read_key()
        if not key:
            return False
        q = parse_qs(urlparse(self.path).query)
        return self.headers.get("x-customize-ui-key", "") == key or q.get("key", [""])[0] == key

    def body_json(self):
        n = int(self.headers.get("content-length") or 0)
        if n > 2 * 1024 * 1024:
            raise ValueError("too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def html(self, code, text, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        data = text.encode()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        path, q = u.path, parse_qs(u.query)
        if path == "/health":
            return self.send(200, {"app": cfg["id"], "ok": True, "version": cfg.get("version", "")})
        if path == "/logo":
            m = logo_meta()
            if not m:
                return self.send(404, {"error": "no logo"})
            data = open(os.path.join(DATA, m["file"]), "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", m["type"])
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return self.wfile.write(data)
        if not self.authed():
            if path.startswith("/api/"):
                return self.send(401, {"error": "open the studio through your dashboard: Settings → Connected apps → Customize UI"})
            return self.html(200, screens.locked_page(cfg))
        if path == "/" or path == "/index.html":
            return self.html(200, UI)
        if path == "/api/state":
            m = logo_meta()
            return self.send(200, {
                "theme": load_theme(), "screens": screens.SCREENS, "presets": list(screens.PRESETS),
                "logo": {"type": m["type"], "size": m["size"]} if m else None,
                "host": {"kind": cfg.get("host", ""), "url": cfg.get("host_url", ""), "id": cfg["id"], "version": cfg.get("version", "")},
                "locked": screens.LOCKED,
            })
        if path.startswith("/api/preview/"):
            name = path[len("/api/preview/"):]
            if name not in screens.SCREENS:
                return self.send(404, {"error": "no such screen"})
            t = load_theme()
            draft = q.get("draft", [""])[0]
            if draft:
                try:
                    t = screens.clean_theme(json.loads(base64.urlsafe_b64decode(draft + "=" * (-len(draft) % 4))))
                except Exception:
                    pass
            mode = "light" if q.get("mode", ["dark"])[0] == "light" else "dark"
            has_logo = bool(logo_meta())
            return self.html(200, screens.render(name, t, mode, has_logo, cfg), {"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:"})
        if path == "/api/export.json":
            data = json.dumps(load_theme(), indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="customize-ui-theme.json"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        if path == "/api/export.css":
            data = screens.theme_pack_css(load_theme()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/css; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="customize-ui-theme.css"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        return self.send(404, {"error": "not found"})

    def do_PUT(self):
        if not self.authed():
            return self.send(401, {"error": "locked"})
        if urlparse(self.path).path == "/api/theme":
            try:
                t = screens.clean_theme(self.body_json())
            except (ValueError, TypeError) as e:
                return self.send(400, {"error": "that isn't a theme: %s" % e})
            t["updated"] = int(time.time())
            mesh.write_json(THEME_FILE, t)
            return self.send(200, {"ok": True, "theme": t})
        return self.send(404, {"error": "not found"})

    def do_DELETE(self):
        if not self.authed():
            return self.send(401, {"error": "locked"})
        if urlparse(self.path).path == "/api/logo":
            m = logo_meta()
            if m:
                try:
                    os.remove(os.path.join(DATA, m["file"]))
                except OSError:
                    pass
            try:
                os.remove(LOGO_META)
            except OSError:
                pass
            return self.send(200, {"ok": True})
        return self.send(404, {"error": "not found"})

    def do_POST(self):
        if not self.authed():
            return self.send(401, {"error": "locked"})
        path = urlparse(self.path).path
        if path == "/api/logo":
            try:
                body = self.body_json()
                m = re.match(r"^data:(image/(?:svg\+xml|png|webp|jpeg));base64,([A-Za-z0-9+/=\s]+)$", str(body.get("data_url", "")))
                if not m:
                    return self.send(400, {"error": "use an .svg, .png, .webp or .jpg"})
                ctype, raw = m.group(1), base64.b64decode(m.group(2))
            except (ValueError, TypeError):
                return self.send(400, {"error": "bad upload"})
            if len(raw) > MAX_LOGO:
                return self.send(400, {"error": "the logo must be 512 KB or less"})
            if ctype == "image/svg+xml" and not re.search(rb"<svg[\s>]", raw[:2048], re.I):
                return self.send(400, {"error": "that SVG doesn't look like one"})
            for ext in LOGO_TYPES.values():  # one logo at a time
                try:
                    os.remove(os.path.join(DATA, "logo." + ext))
                except OSError:
                    pass
            fn = "logo." + LOGO_TYPES[ctype]
            with open(os.path.join(DATA, fn), "wb") as fh:
                fh.write(raw)
            mesh.write_json(LOGO_META, {"file": fn, "type": ctype, "size": len(raw), "updated": int(time.time())})
            return self.send(200, {"ok": True, "logo": {"type": ctype, "size": len(raw)}})
        if path.startswith("/api/preview/"):
            # a draft, unsaved: the studio sends the theme it is editing
            name = path[len("/api/preview/"):]
            if name not in screens.SCREENS:
                return self.send(404, {"error": "no such screen"})
            try:
                t = screens.clean_theme(self.body_json())
            except (ValueError, TypeError):
                t = load_theme()
            mode = "light" if parse_qs(urlparse(self.path).query).get("mode", ["dark"])[0] == "light" else "dark"
            return self.html(200, screens.render(name, t, mode, bool(logo_meta()), cfg))
        if path == "/api/origin":
            try:
                origin = str(self.body_json().get("origin", ""))
            except (ValueError, TypeError):
                origin = ""
            p = urlparse(origin)
            if p.scheme not in ("http", "https") or not p.netloc or p.path not in ("", "/"):
                return self.send(400, {"error": "not an origin"})
            return self.send(200, {"ok": integration_set_public(origin)})
        return self.send(404, {"error": "not found"})


def announce():
    t = load_theme()
    mesh.announce(cfg, "Customize UI", ["themes"], items=[{"name": "theme", "title": t.get("name", ""), "running": True, "url": ""}])


mesh.heartbeat(announce)
mesh.serve(cfg, Studio)
