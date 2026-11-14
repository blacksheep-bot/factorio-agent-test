#!/usr/bin/env python3
"""
Persistent FLE REPL server: holds ONE long-lived FactorioInstance so that variables /
functions defined by one code snippet are visible to the next (FLE's namespace only
persists inside the Python process that owns the FactorioInstance).

Run (from repo root, with the venv):
    .venv/bin/python -W ignore setup/fle_repl.py [--port 8765] [--fresh] [--inventory JSON]

  --fresh       wipe all player-built entities on connect (FLE default behaviour) and
                start from --inventory with research reset.
                Without it the map is kept (clear_entities=False). FLE's connect would
                ALSO reset research + inventory + character position, so (unless
                --no-restore) the REPL snapshots researched techs, current research
                progress, the character inventory and position over raw RCON before
                connecting and restores them afterwards.
  --helpers F   python file eval'd into the agent namespace after every connect
                (default agent/helpers.py if it exists; --no-helpers to skip).
                Reload by hand any time: fle_exec.py agent/helpers.py
  --pause-between  turn-based play: the game is paused except while a program runs, so
                agent think-time does not burn fuel; use sleep() to let the factory work.
  --host        address to listen on (default 127.0.0.1; the Docker image uses 0.0.0.0)
  --server-host / --rcon-port   Factorio RCON endpoint (default localhost:27000)

Every flag has an env-var default (used by docker-compose.yml): FLE_LISTEN_HOST,
FLE_REPL_PORT, FLE_SERVER_HOST, FLE_RCON_PORT, FLE_INVENTORY, FLE_FRESH=1, FLE_ALL_TECH=1, FLE_PAUSE_BETWEEN=1, FLE_NO_RESTORE=1, FLE_HELPERS, FLE_NO_HELPERS=1,
FLE_SAVES_DIR (where the server's saves dir is visible to this process; default
./.fle/saves), FLE_HOST_ROOT + FLE_WORKSPACE (in Docker: host repo path -> its mount
point, so absolute host paths sent by fle_exec.py are rewritten to container paths),
FLE_FALLBACK_DIR + FLE_DATA_HOST_HINT (where paths outside the repo go, and its host name).

HTTP API (JSON in/out; requests are serialised with a lock):
    POST /exec    {"code": str, "timeout": 120}  -> {"output", "score", "duration", "tick"}
    POST /render  {"radius":20,"path":"out.png","x":..,"y":..}  player-centred; x/y => move_to first
    POST /save    {"name": "mysave", "copy_to": "/abs/path.zip"(optional)}
    POST /helpers {}  (re)load the helpers file into the namespace
    POST /reinit  {"fresh": false}  re-create the FactorioInstance (e.g. after a server restart)
    GET  /status
Use setup/fle_exec.py as the CLI client.
"""
import argparse
import json
import os
import shutil
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # FLE looks for .fle/sprites by walking up from cwd
os.environ.setdefault("FLE_SPRITES_DIR", str(ROOT / ".fle" / "sprites"))

from fle.env.instance import FactorioInstance  # noqa: E402
from fle.env.entities import Position  # noqa: E402

# Dir where the *server's* /factorio/saves is visible to us: bind-mounted by start_server.sh
# (host) or shared by docker-compose.yml (container: /data/saves).
SAVES_HOST_DIR = Path(os.environ.get("FLE_SAVES_DIR") or ROOT / ".fle" / "saves")
# Docker: the client sends absolute HOST paths (fle_exec.py makes paths absolute). Map them
# onto the container mount of the repo; anything else that doesn't exist here falls back to
# FLE_FALLBACK_DIR (a mounted dir) so the file still ends up on the host.
HOST_ROOT = os.environ.get("FLE_HOST_ROOT", "").rstrip("/")
WORKSPACE = os.environ.get("FLE_WORKSPACE", "").rstrip("/")
FALLBACK_DIR = os.environ.get("FLE_FALLBACK_DIR", "").rstrip("/")
DATA_HOST_HINT = os.environ.get("FLE_DATA_HOST_HINT", "").rstrip("/")  # host dir mounted at FALLBACK_DIR


def map_path(p, kind="renders"):
    p = str(Path(p).expanduser())
    if HOST_ROOT and WORKSPACE and (p == HOST_ROOT or p.startswith(HOST_ROOT + "/")):
        p = WORKSPACE + p[len(HOST_ROOT):]
    elif FALLBACK_DIR and not Path(p).resolve().parent.is_dir():
        p = str(Path(FALLBACK_DIR) / kind / Path(p).name)
    path = Path(p).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def host_path(p):
    """Inverse of map_path for display (container path -> host path)."""
    p = str(p)
    if HOST_ROOT and WORKSPACE and (p == WORKSPACE or p.startswith(WORKSPACE + "/")):
        return HOST_ROOT + p[len(WORKSPACE):]
    if FALLBACK_DIR and DATA_HOST_HINT and p.startswith(FALLBACK_DIR + "/"):
        return DATA_HOST_HINT + p[len(FALLBACK_DIR):]
    return p

# Lua: FLE keeps its tool functions in `storage` (storage.actions.*, storage.utils.*),
# which Factorio cannot serialise -> any save (incl. autosave) crashes the server with
# "Cannot serialise lua functions". We pause, stash the functions in a non-persistent
# global, save, then restore and unpause.
LUA_STRIP = (
    "/sc __fle_stash = {} local seen = {} local n = 0 "
    "local function walk(t, d) if seen[t] or d > 12 then return end seen[t] = true "
    "for k, v in pairs(t) do local tv = type(v) "
    "if tv == 'function' then __fle_stash[#__fle_stash+1] = {t, k, v} t[k] = nil n = n + 1 "
    "elseif tv == 'table' then walk(v, d + 1) end end end "
    "walk(storage, 0) rcon.print(n)"
)
LUA_RESTORE = (
    "/sc local n = 0 for _, e in ipairs(__fle_stash or {}) do e[1][e[2]] = e[3] n = n + 1 end "
    "__fle_stash = nil rcon.print(n)"
)


# Lua: snapshot of what FLE's connect/_reset would destroy (research, inventory, position).
LUA_SNAPSHOT = (
    "/sc local f = game.forces.player local r = {} for n, t in pairs(f.technologies) do "
    "if t.researched then r[#r+1] = n end end "
    "local out = {researched = r} "
    "if f.current_research then out.current = f.current_research.name out.progress = f.research_progress end "
    "local c = storage.agent_characters and storage.agent_characters[1] "
    "if c and c.valid then local inv = {} for _, it in pairs(c.get_main_inventory().get_contents()) do "
    "inv[it.name] = (inv[it.name] or 0) + it.count end out.inventory = inv "
    "out.position = {x = c.position.x, y = c.position.y} end "
    "rcon.print(helpers.table_to_json(out))"
)


class Repl:
    def __init__(self, args):
        self.args = args
        self.lock = threading.Lock()
        self.inst = None
        self.connect(fresh=args.fresh, retries=args.connect_retries)

    def snapshot(self):
        """Read research/inventory/position over a throwaway RCON connection (no FLE Lua needed),
        because FactorioInstance() resets all three on connect even with clear_entities=False."""
        try:
            rc, _ = FactorioInstance.connect_to_server(self.args.server_host, self.args.rcon_port)
            snap = json.loads(rc.send_command(LUA_SNAPSHOT))
            try:
                rc.close()
            except Exception:
                pass
            return snap
        except Exception as e:
            print(f"snapshot failed (continuing without restore): {e!r}", flush=True)
            return None

    def restore(self, snap):
        r = self.inst.rcon_client
        names = [n for n in snap.get("researched", []) if n.replace("-", "").replace("_", "").isalnum()]
        if names:
            r.send_command("/sc local f = game.forces.player for _, n in pairs({"
                           + ",".join(f"'{n}'" for n in names)
                           + "}) do if f.technologies[n] then f.technologies[n].researched = true end end")
        cur = snap.get("current")
        if cur:
            r.send_command(f"/sc local f = game.forces.player f.add_research('{cur}') "
                           f"f.research_progress = {float(snap.get('progress') or 0)}")
        pos = snap.get("position")
        if pos:
            r.send_command(f"/sc local c = storage.agent_characters[1] if c and c.valid then "
                           f"c.teleport({{x={pos['x']}, y={pos['y']}}}) end")
            self.inst.namespace.player_location = Position(x=pos["x"], y=pos["y"])  # only move_to updates it
        return {"researched": len(names), "current": cur, "position": pos,
                "inventory_items": len(snap.get("inventory") or {})}

    def load_helpers(self):
        path = getattr(self.args, "helpers", None)
        if getattr(self.args, "no_helpers", False) or not path or not Path(path).exists():
            return {"helpers": None}
        _, _, out = self.inst.eval(Path(path).read_text(), timeout=60)
        ok = "Error occurred" not in out and "Exception:" not in out
        print(f"helpers {path}: {'ok' if ok else out}", flush=True)
        return {"helpers": str(path), "ok": ok, "output": out[-2000:]}

    def connect(self, fresh, retries=1):
        inv = json.loads(self.args.inventory) if self.args.inventory else {}
        for attempt in range(retries):
            try:
                snap = None if (fresh or self.args.no_restore) else self.snapshot()
                if snap and snap.get("inventory") is not None:
                    inv = snap["inventory"]  # FLE sets the inventory to exactly this on connect
                self.inst = FactorioInstance(
                    address=self.args.server_host,
                    tcp_port=self.args.rcon_port,
                    fast=not self.args.slow,
                    inventory=inv,
                    all_technologies_researched=self.args.all_tech,
                    clear_entities=fresh,
                    cache_scripts=False,  # True would skip reloading Lua if checksums survive in a loaded save -> silent failures
                )
                restored = self.restore(snap) if snap else None
                if restored:
                    print(f"restored after connect: {restored}", flush=True)
                h = self.load_helpers()
                if getattr(self.args, "pause_between", False):
                    self.inst.rcon_client.send_command("/sc game.tick_paused = true")
                return {"connected": True, "fresh": fresh, "restored": restored,
                        "helpers": h.get("helpers"), "helpers_ok": h.get("ok")}
            except Exception as e:
                if attempt == retries - 1:
                    raise
                print(f"connect to {self.args.server_host}:{self.args.rcon_port} failed ({e!r}); retrying",
                      flush=True)
                time.sleep(3)

    @property
    def ns(self):
        return self.inst.namespace

    def tick(self):
        try:
            return int(self.inst.rcon_client.send_command("/sc rcon.print(game.tick)"))
        except Exception:
            return None

    def exec(self, code, timeout=120):
        self.inst.ensure_connected()
        turn_based = getattr(self.args, "pause_between", False)
        if turn_based:  # game time only passes while a program runs (incl. its sleep() calls)
            self.inst.rcon_client.send_command("/sc game.tick_paused = false")
        try:
            score, duration, output = self.inst.eval(code, timeout=timeout)
        finally:
            if turn_based:
                self.inst.rcon_client.send_command("/sc game.tick_paused = true")
        return {"output": output, "score": score, "duration": round(duration, 3), "tick": self.tick()}

    def render(self, x=None, y=None, radius=20, path="render.png"):
        """FLE's renderer is always centred on the PLAYER (the Lua side scans around the
        character; the `position` kwarg of _render only affects the entity query). So if
        x/y are given we move_to() there first (this really moves the character)."""
        if x is not None and y is not None:
            self.exec(f"move_to(Position(x={x}, y={y}))", timeout=60)  # exec(): unpauses in turn-based mode
        img = self.ns._render(radius=radius, max_render_radius=radius)
        path = map_path(path, "renders")
        img.save(str(path))
        vp = img.viewport
        return {"path": host_path(path), "size": list(img.image.size),
                "world_bbox": [vp.world_min_x, vp.world_min_y, vp.world_max_x, vp.world_max_y]}

    def save(self, name="fle_save", copy_to=None):
        r = self.inst.rcon_client
        was_paused = r.send_command("/sc rcon.print(game.tick_paused)") == "true"
        r.send_command("/sc game.tick_paused = true")
        n = r.send_command(LUA_STRIP)
        try:
            r.send_command(f'/sc game.server_save("{name}")')
            target = SAVES_HOST_DIR / f"{name}.zip"
            t0 = time.time()
            while time.time() - t0 < 30:  # saving is async; wait for the file to settle
                time.sleep(1)
                if target.exists() and time.time() - target.stat().st_mtime > 1:
                    break
        finally:
            restored = r.send_command(LUA_RESTORE)
            if not was_paused:
                r.send_command("/sc game.tick_paused = false")
        out = {"stripped": n, "restored": restored, "save": host_path(target), "exists": target.exists()}
        if copy_to and target.exists():
            dst = map_path(copy_to, "saves")
            shutil.copy2(target, dst)
            out["copied_to"] = host_path(dst)
        return out


def make_handler(repl):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, obj):
            body = json.dumps(obj, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/status":
                with repl.lock:
                    try:
                        loc = repl.ns.player_location
                        self._send(200, {"ok": True, "tick": repl.tick(), "player_location": [loc.x, loc.y],
                                         "connected": repl.inst.is_rcon_connected()})
                    except Exception as e:
                        self._send(500, {"ok": False, "error": repr(e)})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            routes = {
                "/exec": lambda: repl.exec(req["code"], req.get("timeout", 120)),
                "/render": lambda: repl.render(req.get("x"), req.get("y"), req.get("radius", 20),
                                               req.get("path", "render.png")),
                "/save": lambda: repl.save(req.get("name", "fle_save"), req.get("copy_to")),
                "/reinit": lambda: {"result": repl.connect(fresh=req.get("fresh", False))},
                "/helpers": lambda: repl.load_helpers(),
            }
            if self.path not in routes:
                return self._send(404, {"error": "not found"})
            with repl.lock:
                try:
                    self._send(200, routes[self.path]())
                except Exception as e:
                    self._send(500, {"error": repr(e), "traceback": traceback.format_exc()})

    return H


def main():
    env = os.environ.get
    flag = lambda k: env(k, "").strip().lower() in ("1", "true", "yes", "on")  # noqa: E731
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(env("FLE_REPL_PORT", 8765)))
    ap.add_argument("--host", default=env("FLE_LISTEN_HOST", "127.0.0.1"), help="address to listen on")
    ap.add_argument("--server-host", default=env("FLE_SERVER_HOST", "localhost"), help="Factorio RCON host")
    ap.add_argument("--rcon-port", type=int, default=int(env("FLE_RCON_PORT", 27000)))
    ap.add_argument("--fresh", action="store_true", default=flag("FLE_FRESH"), help="clear all entities on connect")
    ap.add_argument("--slow", action="store_true", help="fast=False (real-time walking/crafting)")
    ap.add_argument("--all-tech", action="store_true", default=flag("FLE_ALL_TECH"),
                    help="research all technologies on connect")
    ap.add_argument("--inventory", default=env("FLE_INVENTORY") or None, help='JSON dict, e.g. \'{"iron-plate": 50}\'')
    ap.add_argument("--connect-retries", type=int, default=int(env("FLE_CONNECT_RETRIES", 1)),
                    help="retry the initial RCON connect N times (3 s apart)")
    ap.add_argument("--no-restore", action="store_true", default=flag("FLE_NO_RESTORE"),
                    help="without --fresh: do NOT restore research/inventory/position after connect")
    ap.add_argument("--helpers", default=env("FLE_HELPERS") or str(ROOT / "agent" / "helpers.py"),
                    help="python file eval'd into the agent namespace after connect (default agent/helpers.py)")
    ap.add_argument("--no-helpers", action="store_true", default=flag("FLE_NO_HELPERS"),
                    help="do not auto-load the helpers file")
    ap.add_argument("--pause-between", action="store_true", default=flag("FLE_PAUSE_BETWEEN"),
                    help="turn-based: pause the game between /exec calls, so game time only advances "
                         "while a program runs (sleep() is how you let the factory work)")
    args = ap.parse_args()
    repl = Repl(args)
    srv = ThreadingHTTPServer((args.host, args.port), make_handler(repl))
    print(f"FLE REPL listening on http://{args.host}:{args.port} "
          f"(server {args.server_host}:{args.rcon_port}, fresh={args.fresh})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
