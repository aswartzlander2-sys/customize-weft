// Customize UI's Burrow extension (SPEC.md §10). Burrow runs this inside
// itself while the addon is installed. It does two things:
//
//   mount()   puts the studio under the dashboard's login at /__gate/customize-ui,
//             sending the gate key (ADDON_DATA/key) with every request, so only
//             signed-in users of the dashboard reach it (Bulwark does the same).
//             Same origin as the dashboard: that is what lets the studio's page
//             call /__gate/api/prefs to apply a theme.
//   handle()  answers /__gate/api/x/customize-ui/… by passing it to the studio's
//             /api/… with the key, for anything on the Burrow page that asks.
//
// It never touches another addon's files, tunnels or entries.
import { readFileSync } from "node:fs";
import { join } from "node:path";

const ID = "customize-ui";
let ctx = null, cfg = null, key = "", lastTry = 0;

function load() {
  if (!ctx) return false;
  if (cfg && key) return true;
  if (Date.now() - lastTry < 2000) return false;          // mount() runs on every request: stay cheap
  lastTry = Date.now();
  try {
    cfg = JSON.parse(readFileSync(join(ctx.dataDir, "config.json"), "utf8"));
    key = readFileSync(join(ctx.dataDir, "key"), "utf8").trim();
    return !!(cfg.port && key);
  } catch { cfg = null; key = ""; return false; }
}

function appUrl() {
  const b = cfg.bind || "127.0.0.1";
  const h = ["0.0.0.0", "::", ""].includes(b) ? "127.0.0.1" : b.includes(":") ? `[${b}]` : b;
  return `http://${h}:${cfg.port}`;
}

export async function start(c) {
  ctx = c;
  if (load()) c.log(`studio at ${appUrl()}, mounted at /__gate/${ID}`);
  else c.log("not set up yet: the install script writes config.json and the key");
}

export function stop() { ctx = null; cfg = null; key = ""; }

export function mount() {
  if (!load()) return null;
  return {
    prefix: `/__gate/${ID}`, upstream: appUrl(), name: "Customize UI",
    headers: { "x-customize-ui-key": key },
    // the home tile this creates is hidden by the studio itself unless the
    // HOME_TILE setting (or the studio's switch) says otherwise
    tile: { text: "Themes for the sign-in, tunnel password and home screens." },
  };
}

export async function handle({ method, path, json }) {
  if (!load()) return { status: 503, json: { error: "Customize UI isn't set up yet." } };
  if (!/^\/[a-z0-9./_-]*$/i.test(path)) return { status: 400, json: { error: "bad path" } };
  const body = method === "GET" || method === "DELETE" ? undefined : JSON.stringify(json ? await json().catch(() => ({})) : {});
  try {
    const r = await fetch(`${appUrl()}/api${path}`, {
      method, body, headers: { "Content-Type": "application/json", "x-customize-ui-key": key }, signal: AbortSignal.timeout(15000),
    });
    return { status: r.status, json: await r.json().catch(() => ({})) };
  } catch (e) { return { status: 503, json: { error: `Customize UI isn't answering (${e.cause?.code || e.message}).` } }; }
}
