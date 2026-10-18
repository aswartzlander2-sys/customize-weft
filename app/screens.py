"""Customize UI: the screens, the presets, the theme's shape, and the previews.

The sign-in (login.html) and tunnel-password (unlock.html) previews use the
real markup and stylesheet of Aegis × Burrow, vendored in app/screens/ under
its MIT licence (LICENSE-aegis-burrow), so what you see is what the gate
shows. The home, tunnels, settings and first-run previews are compact mocks
that use the same CSS variables and class names (--bg, --card, .hello, .card,
.opts…), so CSS written here carries over.

Locked regions: the <form> of the sign-in and password screens is never
touched by a theme. The fields and their ids are what login.js seals the
password with (ML-KEM-768 + X25519 → AES-256-GCM), so they stay as they are.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weft"))
import mesh  # noqa: E402  (weft/mesh.py, vendored)

HERE = os.path.dirname(os.path.abspath(__file__))
VENDORED = os.path.join(HERE, "screens")

SCREENS = {
    "login":    {"title": "Sign-in",          "what": "The gate's login page (/__gate/login).", "locked": True},
    "unlock":   {"title": "Tunnel password",  "what": "The password page a tunnel with a password of its own shows.", "locked": True},
    "home":     {"title": "Home",             "what": "The page after sign-in: greeting, tagline, tiles.", "locked": False},
    "tunnels":  {"title": "Burrow · Tunnels", "what": "The tunnel manager (/__gate/tunnels).", "locked": False},
    "settings": {"title": "Settings",         "what": "Settings (/__gate/settings).", "locked": False},
    "welcome":  {"title": "First run",        "what": "The welcome and setup pages.", "locked": False},
}
LOCKED = {
    "login":  ["form#f", "input#username", "input#password", "button#peek", "button#go", "p#msg", "script /__gate/login.js"],
    "unlock": ["form#f", "input#password", "button#peek", "button#go", "p#msg", "script /__gate/login.js"],
}
VAR_KEYS = ["bg", "card", "card2", "field", "line", "text", "muted", "faint", "accent", "ok", "err"]
SCREEN_KEYS = {"login": ["title", "subtitle"], "unlock": ["name"], "home": ["greeting", "tagline", "columns", "background"],
               "tunnels": [], "settings": [], "welcome": []}
LIMITS = {"title": 40, "subtitle": 40, "name": 60, "greeting": 60, "tagline": 80}
HOME_TILE_IDS = ["addon:customize-ui", "app:customize-ui"]

# Cold palettes. Each has a dark and a light face; the studio follows the system.
PRESETS = {
    "glacier": {
        "label": "Glacier", "about": "Deep navy room, ice-blue accents.",
        "dark":  {"bg": "#070b12", "card": "#0e141d", "card2": "#0a0f17", "field": "#070b11", "line": "rgba(159,196,235,.10)", "text": "#e6eef8", "muted": "#8ea2bb", "faint": "#56667c", "accent": "#7fc1f0", "ok": "#5fd7c0", "err": "#ff6b7a"},
        "light": {"bg": "#eef3f9", "card": "#ffffff", "card2": "#f6f9fd", "field": "#f3f6fa", "line": "rgba(20,50,90,.10)", "text": "#0f1b2d", "muted": "#51637b", "faint": "#8a98ab", "accent": "#2f7fc6", "ok": "#15917d", "err": "#d13b4b"},
    },
    "steel": {
        "label": "Steel", "about": "Blue-grey, matte, quiet.",
        "dark":  {"bg": "#0b0e12", "card": "#14191f", "card2": "#10141a", "field": "#0c0f13", "line": "rgba(190,205,220,.10)", "text": "#e4e8ed", "muted": "#97a3b0", "faint": "#5f6a76", "accent": "#9cb4cc", "ok": "#6cc9b0", "err": "#ff7272"},
        "light": {"bg": "#eceff2", "card": "#ffffff", "card2": "#f5f7f9", "field": "#f1f3f6", "line": "rgba(30,40,55,.10)", "text": "#161b21", "muted": "#5a6572", "faint": "#8d97a2", "accent": "#4a6a8a", "ok": "#1b8f78", "err": "#c93c47"},
    },
    "deep-sea": {
        "label": "Deep sea", "about": "Teal depths, aqua highlights.",
        "dark":  {"bg": "#05100f", "card": "#0b1a19", "card2": "#081413", "field": "#06100f", "line": "rgba(140,220,210,.10)", "text": "#e3f3f1", "muted": "#86aaa6", "faint": "#4f6f6b", "accent": "#5fd3c6", "ok": "#6fe3b5", "err": "#ff7a6b"},
        "light": {"bg": "#edf5f4", "card": "#ffffff", "card2": "#f4faf9", "field": "#f0f6f5", "line": "rgba(10,70,65,.10)", "text": "#0e2321", "muted": "#4a6a66", "faint": "#86a19d", "accent": "#148f84", "ok": "#1a9a6c", "err": "#d04a3e"},
    },
    "arctic": {
        "label": "Arctic", "about": "Near-white, frost-blue lines.",
        "dark":  {"bg": "#0c1016", "card": "#151b23", "card2": "#11161d", "field": "#0d1117", "line": "rgba(200,225,255,.12)", "text": "#eef4fb", "muted": "#9db0c6", "faint": "#657994", "accent": "#b9dcff", "ok": "#8be0cc", "err": "#ff8a8a"},
        "light": {"bg": "#f6f9fc", "card": "#ffffff", "card2": "#f9fbfd", "field": "#f3f7fb", "line": "rgba(40,80,130,.12)", "text": "#121c28", "muted": "#5a6d84", "faint": "#93a3b6", "accent": "#3b8ad6", "ok": "#1a9b85", "err": "#d8414f"},
    },
}

FONT = "'Helvetica Medium', 'Helvetica Neue', Helvetica, Arial, sans-serif"


def default_theme(preset="glacier", home_tile=False):
    p = PRESETS.get(preset) or PRESETS["glacier"]
    return clean_theme({
        "spec": 1, "name": p["label"], "preset": preset, "home_tile": bool(home_tile),
        "global": {"vars": {"dark": dict(p["dark"]), "light": dict(p["light"])}, "radius": 14, "follow_system": True, "css": ""},
        "screens": {
            "login": {"title": "", "subtitle": "", "css": ""},
            "unlock": {"name": "", "css": ""},
            "home": {"greeting": "", "tagline": "", "columns": 2, "background": "grid", "css": ""},
            "tunnels": {"css": ""}, "settings": {"css": ""}, "welcome": {"css": ""},
        },
    })


def _color(v):
    v = str(v or "").strip()
    return v if re.match(r"^(#[0-9a-fA-F]{3,8}|rgba?\([\d.,\s%]+\)|hsla?\([\d.,\s%]+\)|[a-zA-Z]{3,20})$", v) else ""


def _text(v, n):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(v or "")).strip()[:n]


def _css(v):
    s = str(v or "")
    if len(s) > 64 * 1024:
        raise ValueError("a CSS block must be 64 KB or less")
    # a style block can't be broken out of, and no outside resources are pulled in
    return s.replace("</style", "<\\/style").replace("@import", "/* @import */")


def clean_theme(t):
    if not isinstance(t, dict):
        raise ValueError("not an object")
    g = t.get("global") if isinstance(t.get("global"), dict) else {}
    vars_in = g.get("vars") if isinstance(g.get("vars"), dict) else {}
    preset = t.get("preset") if t.get("preset") in PRESETS else "glacier"
    out_vars = {}
    for mode in ("dark", "light"):
        src = vars_in.get(mode) if isinstance(vars_in.get(mode), dict) else {}
        out_vars[mode] = {k: _color(src.get(k)) or PRESETS[preset][mode][k] for k in VAR_KEYS}
    out = {
        "spec": 1, "name": _text(t.get("name"), 40) or "Untitled", "preset": preset, "home_tile": bool(t.get("home_tile")),
        "updated": int(t.get("updated") or 0),
        "global": {"vars": out_vars, "radius": max(0, min(32, int(g.get("radius") or 14))),
                   "follow_system": g.get("follow_system") is not False, "css": _css(g.get("css"))},
        "screens": {},
    }
    scr = t.get("screens") if isinstance(t.get("screens"), dict) else {}
    for name, keys in SCREEN_KEYS.items():
        s = scr.get(name) if isinstance(scr.get(name), dict) else {}
        o = {"css": _css(s.get("css"))}
        for k in keys:
            if k == "columns":
                o[k] = 3 if str(s.get(k)) == "3" else 2
            elif k == "background":
                o[k] = s.get(k) if s.get(k) in ("grid", "glow", "plain") else "grid"
            else:
                o[k] = _text(s.get(k), LIMITS[k])
        out["screens"][name] = o
    return out


# ------------------------------------------------------------------ rendering

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def vars_css(theme, mode):
    v = theme["global"]["vars"][mode]
    r = theme["global"]["radius"]
    return (":root{color-scheme:%s;--bg:%s;--card:%s;--card-2:%s;--raise:%s;--field:%s;--line:%s;--line-2:%s;--line-hi:%s;"
            "--text:%s;--muted:%s;--faint:%s;--ok:%s;--err:%s;--warn:#f2c14e;--blue:%s;--acc:%s;--accent:%s;--radius:%dpx;"
            "--sans:%s;--mono:ui-monospace,'SF Mono','JetBrains Mono',Menlo,Consolas,monospace}"
            "body,button,input,select,textarea{font-family:var(--sans);font-weight:500}"
            "main,.card,form,input,button#go{border-radius:var(--radius)}"
            "::selection{background:var(--accent);color:var(--bg)}"
            "a{color:var(--accent)}"
            # login.css's few fixed colours, brought onto the palette
            ".shield{background:var(--card-2);border-color:var(--line)}.shield svg{color:var(--accent)}"
            "footer{background:var(--card-2)}footer b{color:var(--muted)}"
            "button#go{background:var(--accent);color:var(--bg);border-color:transparent}"
            "input{background:var(--field);color:var(--text);border-color:var(--line)}input:focus{border-color:var(--accent)}"
            "body[data-state=idle] .dot{background:var(--ok)}"
            % (mode, v["bg"], v["card"], v["card2"], v["card2"], v["field"], v["line"], v["line"], v["accent"], v["text"], v["muted"],
               v["faint"], v["ok"], v["err"], v["accent"], v["accent"], v["accent"], r, FONT))


def screen_css(theme, name, mode):
    return "\n".join([
        "/* Customize UI · %s · %s */" % (name, mode), vars_css(theme, mode),
        "/* global */", theme["global"]["css"],
        "/* %s */" % name, theme["screens"].get(name, {}).get("css", ""),
    ])


def _vendored(name):
    return open(os.path.join(VENDORED, name), encoding="utf-8").read()


def _gate_page(html, theme, name, mode, has_logo, fills):
    """A real gate page (login/unlock) with the theme in place of the stylesheet. The form is untouched."""
    for k, v in fills.items():
        html = html.replace("{{%s}}" % k, esc(v))
    css = _vendored("login.css") + "\n" + screen_css(theme, name, mode)
    html = html.replace('<link rel="stylesheet" href="/__gate/login.css">', "<style>%s</style>" % css)
    html = html.replace('<script type="module" src="/__gate/login.js"></script>', "<!-- login.js: kept by the gate; not run in a preview -->")
    html = html.replace('href="/__gate/logos/aegis-burrow.svg"', 'href="data:,"')
    if has_logo:
        html = re.sub(r'<span class="shield" aria-hidden="true">.*?</span>',
                      '<span class="shield" aria-hidden="true"><img src="../../logo" alt="" style="width:100%;height:100%;object-fit:contain;border-radius:inherit"></span>',
                      html, count=1, flags=re.S)
    return html.replace("<body ", '<body data-preview="1" ')


MOCK_CSS = """
*{box-sizing:border-box}html,body{margin:0;min-height:100%}
body{position:relative;background:var(--bg);color:var(--text);font:14px/1.5 var(--sans);-webkit-font-smoothing:antialiased}
body.bg-grid::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:44px 44px;mask-image:radial-gradient(ellipse 80% 60% at 50% 0%,#000 0,transparent 75%);-webkit-mask-image:radial-gradient(ellipse 80% 60% at 50% 0%,#000 0,transparent 75%)}
body.bg-glow::after{content:"";position:fixed;left:50%;top:-260px;width:1100px;height:640px;transform:translateX(-50%);pointer-events:none;z-index:0;background:radial-gradient(closest-side,color-mix(in srgb,var(--accent) 18%,transparent),transparent)}
body.home{display:grid;place-items:center;min-height:100vh;padding:16px}
.home-in{position:relative;z-index:1;width:100%;max-width:700px}.home-in.wide{max-width:860px}
.hello{display:flex;align-items:center;gap:12px;margin:0 4px 22px}
.hello-logo{width:40px;height:40px;border-radius:11px;flex:none;object-fit:contain;background:var(--card)}
.hello>div:not([class])>b{display:block;font-size:17px;letter-spacing:-.01em}
.hello>div:not([class])>span{font:500 10px/1 var(--mono);letter-spacing:.2em;text-transform:uppercase;color:var(--faint)}
.gear{margin-left:auto;width:36px;height:36px;display:grid;place-items:center;border-radius:10px;border:1px solid var(--line);color:var(--muted)}.gear svg{width:18px;height:18px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:7px 12px;border-radius:9px;border:1px solid var(--line-2);background:var(--card);color:var(--text);font:inherit;text-decoration:none}
.btn.ghost{background:transparent}.btn.sm{padding:5px 10px;font-size:12.5px}.btn.pri{background:var(--accent);color:var(--bg);border-color:transparent}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:14px}.opts.cols3{grid-template-columns:1fr 1fr 1fr}
.card{position:relative;display:block;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;text-decoration:none;color:inherit}
.card.lit::before{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;background:radial-gradient(120% 100% at 0% 0%,color-mix(in srgb,var(--accent) 10%,transparent),transparent 60%)}
.card .ico{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:var(--card-2);border:1px solid var(--line);margin-bottom:12px;color:var(--accent)}.card .ico svg{width:18px;height:18px}
.card b{display:block;font-size:15px;letter-spacing:-.01em}.card p{margin:4px 0 0;color:var(--muted);font-size:13px}.card .foot{margin-top:12px;font:500 11px/1 var(--mono);color:var(--faint)}
main.page{position:relative;z-index:1;max-width:980px;margin:0 auto;padding:28px 18px 60px}
.head{display:flex;align-items:center;gap:14px;margin-bottom:18px}.head h1{margin:0;font-size:24px;letter-spacing:-.02em}.head p{margin:2px 0 0;color:var(--muted)}.spacer{flex:1}
.sec{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;margin-bottom:14px}.sec h3{margin:0 0 4px;font-size:15px}.sec>p{margin:0 0 12px;color:var(--muted);font-size:13px}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.row.end{justify-content:flex-end}
.input{font:inherit;color:var(--text);background:var(--field);border:1px solid var(--line-2);border-radius:9px;padding:8px 11px;min-width:200px}
.pill{display:inline-flex;align-items:center;gap:6px;padding:2px 9px;border-radius:99px;border:1px solid var(--line);font:500 11.5px var(--mono);color:var(--muted)}.pill.ok{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 40%,transparent)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 10px var(--ok);display:inline-block}
.trow{display:grid;grid-template-columns:1fr auto auto;gap:14px;align-items:center;padding:12px 0;border-top:1px solid var(--line)}.trow:first-of-type{border-top:0}.trow .mono{font-family:var(--mono);font-size:12.5px;color:var(--muted)}
.muted{color:var(--muted)}.faint{color:var(--faint)}.small{font-size:12.5px}.mono{font-family:var(--mono)}
.welcome{display:grid;place-items:center;min-height:100vh;padding:24px}.welcome main{position:relative;z-index:1;width:100%;max-width:560px;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:28px}
.welcome h1{margin:0 0 6px;font-size:26px;letter-spacing:-.02em}.welcome .steps{display:grid;gap:10px;margin:18px 0}.welcome .step{display:flex;gap:12px;align-items:flex-start;padding:12px;border:1px solid var(--line);border-radius:12px;background:var(--card-2)}
.welcome .n{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;background:var(--accent);color:var(--bg);font-size:12px;flex:none}
"""

GEAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/></svg>'
ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M4 12h16M12 4v16"/></svg>'
LOGO_MARK = ('<svg class="hello-logo" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="11" fill="var(--card)"/>'
             '<path d="M12 14h16M12 20h16M12 26h16" stroke="var(--accent)" stroke-width="2.4" stroke-linecap="round"/></svg>')


def _mock(theme, name, mode, has_logo, cfg):
    s = theme["screens"][name]
    h = theme["screens"]["home"]
    title = theme["screens"]["login"]["title"] or "Aegis"
    logo = '<img class="hello-logo" src="../../logo" alt="">' if has_logo else LOGO_MARK
    css = MOCK_CSS + "\n" + screen_css(theme, name, mode)
    if name == "home":
        tiles = [("Burrow", "Publish a port on its own address, with live traffic and clients.", "tunnel-PORT-example.net"),
                 ("Termix", "SSH terminals, files and hosts.", "this machine"),
                 ("Bulwark", "Attacks, bans and every request, live.", "behind your Aegis login"),
                 ("A link of yours", "Link tiles can carry an image or an emoji.", "example.net")]
        body = ('<body class="home bg-%s"><main class="home-in%s"><div class="hello">%s<div><b id="greet">%s</b><span id="tagline">%s</span></div>'
                '<a class="gear" href="#">%s</a><a class="btn ghost sm out" href="#">Sign out</a></div><div class="opts%s" id="opts">%s</div></main></body>'
                % (h["background"], " wide" if h["columns"] == 3 else "", logo, esc(h["greeting"] or "Unlocked"), esc(h["tagline"] or "Where to?"), GEAR,
                   " cols3" if h["columns"] == 3 else "",
                   "".join('<a class="card lit" href="#"><span class="ico">%s</span><b>%s</b><p>%s</p><div class="foot">%s</div></a>' % (ICO, a, b, c) for a, b, c in tiles)))
    elif name == "tunnels":
        rows = [("grafana.example.net", "3000", "signed in"), ("tunnel-8080-aegis.example.net", "8080", "public"), ("blog.example.net", "4321", "password")]
        body = ('<body class="bg-%s"><main class="page"><div class="head"><div><h1>Burrow</h1><p>%s · tunnels</p></div><div class="spacer"></div>'
                '<span class="pill ok"><i class="dot"></i> cloudflared connected</span><a class="btn pri" href="#">New tunnel</a></div>'
                '<div class="sec"><h3>Tunnels</h3><p>Every port you published, with its address and who may open it.</p>%s</div>'
                '<div class="sec"><h3>Selkies Forge</h3><p>Desktops, their links and tunnels.</p><span class="pill">nothing linked</span></div></main></body>'
                % (h["background"], esc(title), "".join('<div class="trow"><div><b>%s</b><div class="mono">127.0.0.1:%s → https://%s</div></div><span class="pill">%s</span><a class="btn sm" href="#">Open</a></div>' % (a, b, a, c) for a, b, c in rows)))
    elif name == "settings":
        body = ('<body class="bg-%s"><main class="page"><div class="head"><div><h1>Settings</h1><p>%s <span class="mono faint">v2.23</span></p></div><div class="spacer"></div><a class="btn" href="#">Search all settings <span class="mono faint">/</span></a></div>'
                '<div class="sec"><h3>Sign-in</h3><p>What the sign-in page says, and how long a sign-in lasts.</p><div class="row"><input class="input" value="%s"><input class="input" value="%s"><a class="btn" href="#">Save</a></div></div>'
                '<div class="sec"><h3>Connected apps</h3><p>Apps on this machine that plugged into the dashboard.</p><div class="trow"><div><b>Customize UI</b><div class="mono">http://127.0.0.1:%s/</div></div><span></span><a class="btn sm ghost" href="#">Open</a></div></div>'
                '<div class="sec"><h3>Login</h3><p>One login for the dashboard, Termix and every tunnel.</p><div class="row"><input class="input" placeholder="New password" type="password"><a class="btn" href="#">Change</a></div></div></main></body>'
                % (h["background"], esc(title), esc(title), esc(theme["screens"]["login"]["subtitle"] or "Secure channel"), esc(str(cfg.get("port", "")))))
    else:
        body = ('<body class="welcome bg-%s"><main><div class="hello">%s<div><b>%s</b><span>first run</span></div></div><h1>Welcome.</h1><p class="muted">Three steps and your gate is up.</p>'
                '<div class="steps"><div class="step"><span class="n">1</span><div><b>Your login</b><p class="muted small">A username and a password. The password is sealed in your browser before it leaves.</p></div></div>'
                '<div class="step"><span class="n">2</span><div><b>Burrow</b><p class="muted small">On by default. Publish any port at its own HTTPS address.</p></div></div>'
                '<div class="step"><span class="n">3</span><div><b>Your own address</b><p class="muted small">Optional. Connect Cloudflare and pick a subdomain.</p></div></div></div>'
                '<div class="row end"><a class="btn ghost" href="#">Later</a><a class="btn pri" href="#">Continue</a></div></main></body>' % (h["background"], logo, esc(title)))
    body = re.sub(r">\s*<", ">\n<", body)   # one tag per line: readable in the Structure tab
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title>\n'
            '<style>%s</style></head>\n%s\n</html>' % (esc(SCREENS[name]["title"]), css, body))


def render(name, theme, mode, has_logo, cfg):
    s = theme["screens"]
    if name == "login":
        return _gate_page(_vendored("login.html"), theme, name, mode, has_logo,
                          {"title": s["login"]["title"] or "Aegis", "subtitle": s["login"]["subtitle"] or "Secure channel"})
    if name == "unlock":
        return _gate_page(_vendored("unlock.html"), theme, name, mode, has_logo,
                          {"name": s["unlock"]["name"] or "grafana", "host": "grafana.example.net", "title": s["login"]["title"] or "Aegis"})
    return _mock(theme, name, mode, has_logo, cfg)


def theme_pack_css(theme):
    out = ["/* Customize UI theme pack: %s (preset %s)\n   One block per screen, dark and light. Drop it in front of the gate's\n   own stylesheets wherever a host or proxy lets you. */" % (theme["name"], theme["preset"])]
    for name in SCREENS:
        for mode in ("dark", "light"):
            wrap = "@media (prefers-color-scheme: %s) {\n%s\n}" % (mode, screen_css(theme, name, mode)) if theme["global"]["follow_system"] else screen_css(theme, name, mode)
            out.append("/* ===== %s ===== */\n%s" % (name, wrap))
            if not theme["global"]["follow_system"]:
                break
    out.append("/* texts: %s */" % json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "css"} for k, v in theme["screens"].items()}))
    return "\n\n".join(out) + "\n"


def locked_page(cfg):
    return mesh.page(cfg, "Customize UI", "The theme studio for your dashboard",
                     "<div class=card><p style='margin:0;font-size:17px'>Open it through your dashboard.</p>"
                     "<p class=sub>Settings → Connected apps → <b>Customize UI</b> → Open, or <span class=mono>/__gate/customize-ui/</span> on the dashboard. "
                     "This bare port only answers the dashboard's mount, which carries the key kept in the addon's data folder.</p></div>")

