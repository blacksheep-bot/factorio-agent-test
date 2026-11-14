#!/usr/bin/env python3
"""
Persistent FLE REPL server: holds ONE long-lived FactorioInstance so that variables /
functions defined by one code snippet are visible to the next (FLE's namespace only
persists inside the Python process that owns the FactorioInstance).

Run (from repo root, with the venv):
    .venv/bin/python -W ignore setup/fle_repl.py [--port 8765] [--fresh] [--inventory JSON]

  --fresh       wipe all player-built entities on connect (FLE default behaviour).
                Without it the map is kept (clear_entities=False), but NOTE that FLE
                still resets the character inventory to --inventory on connect.

HTTP API (JSON in/out, 127.0.0.1 only; requests are serialised with a lock):
    POST /exec    {"code": str, "timeout": 120}  -> {"output", "score", "duration", "tick"}
    POST /render  {"radius":20,"path":"out.png","x":..,"y":..}  player-centred; x/y => move_to first
    POST /save    {"name": "mysave", "copy_to": "/abs/path.zip"(optional)}
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

SAVES_HOST_DIR = ROOT / ".fle" / "saves"  # bind-mounted to /factorio/saves by start_server.sh

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


class Repl:
    def __init__(self, args):
        self.args = args
        self.lock = threading.Lock()
        self.inst = None
        self.connect(fresh=args.fresh)

    def connect(self, fresh):
        inv = json.loads(self.args.inventory) if self.args.inventory else {}
        self.inst = FactorioInstance(
            address=self.args.host,
            tcp_port=self.args.rcon_port,
            fast=not self.args.slow,
            inventory=inv,
            all_technologies_researched=self.args.all_tech,
            clear_entities=fresh,
            cache_scripts=False,  # True would skip reloading Lua if checksums survive in a loaded save -> silent failures
        )
        return "connected"

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
        score, duration, output = self.inst.eval(code, timeout=timeout)
        return {"output": output, "score": score, "duration": round(duration, 3), "tick": self.tick()}

    def render(self, x=None, y=None, radius=20, path="render.png"):
        """FLE's renderer is always centred on the PLAYER (the Lua side scans around the
        character; the `position` kwarg of _render only affects the entity query). So if
        x/y are given we move_to() there first (this really moves the character)."""
        if x is not None and y is not None:
            self.inst.eval(f"move_to(Position(x={x}, y={y}))", timeout=60)
        img = self.ns._render(radius=radius, max_render_radius=radius)
        path = str(Path(path).expanduser().resolve())
        img.save(path)
        vp = img.viewport
        return {"path": path, "size": list(img.image.size),
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
        out = {"stripped": n, "restored": restored, "save": str(target), "exists": target.exists()}
        if copy_to and target.exists():
            shutil.copy2(target, copy_to)
            out["copied_to"] = copy_to
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="localhost", help="Factorio RCON host")
    ap.add_argument("--rcon-port", type=int, default=27000)
    ap.add_argument("--fresh", action="store_true", help="clear all entities on connect")
    ap.add_argument("--slow", action="store_true", help="fast=False (real-time walking/crafting)")
    ap.add_argument("--all-tech", action="store_true", help="research all technologies on connect")
    ap.add_argument("--inventory", default=None, help='JSON dict, e.g. \'{"iron-plate": 50}\'')
    args = ap.parse_args()
    repl = Repl(args)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(repl))
    print(f"FLE REPL listening on http://127.0.0.1:{args.port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
