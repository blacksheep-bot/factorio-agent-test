#!/usr/bin/env python3
"""
CLI client for setup/fle_repl.py (stdlib only; any python3 works).

  fle_exec.py -c 'print(inspect_inventory())'      # run a snippet
  fle_exec.py snippet.py                            # run a file
  echo 'print(1)' | fle_exec.py                     # run stdin
  fle_exec.py --render out.png [--x 0 --y 0] [--radius 20]
  fle_exec.py --save mysave [--copy-to /abs/out.zip]
  fle_exec.py --status | --reinit [--fresh]

Prints the FLE program output (one line per print: "<lineno>: (<repr of args>,)").
Exit code 1 if the output contains an FLE error.
"""
import argparse
import json
import sys
import urllib.request


def call(base, path, payload=None, timeout=600):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("-c", "--code")
    ap.add_argument("--url", default="http://127.0.0.1:8765")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--render")
    ap.add_argument("--x", type=float)
    ap.add_argument("--y", type=float)
    ap.add_argument("--radius", type=int, default=20)
    ap.add_argument("--save")
    ap.add_argument("--copy-to")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--reinit", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--json", action="store_true", help="print raw JSON response")
    a = ap.parse_args()

    # The REPL server resolves relative paths against the repo root, so make them absolute here.
    import os
    abspath = lambda p: os.path.abspath(p) if p else p  # noqa: E731

    if a.status:
        res = call(a.url, "/status")
    elif a.reinit:
        res = call(a.url, "/reinit", {"fresh": a.fresh})
    elif a.render:
        res = call(a.url, "/render", {"x": a.x, "y": a.y, "radius": a.radius, "path": abspath(a.render)})
    elif a.save:
        res = call(a.url, "/save", {"name": a.save, "copy_to": abspath(a.copy_to)})
    else:
        code = a.code if a.code is not None else (open(a.file).read() if a.file else sys.stdin.read())
        res = call(a.url, "/exec", {"code": code, "timeout": a.timeout}, timeout=a.timeout + 30)
        if not a.json and "output" in res:
            print(res["output"])
            print(f"[score={res['score']} duration={res['duration']}s tick={res['tick']}]", file=sys.stderr)
            out = res["output"]
            return 1 if ("Error occurred" in out or "Exception:" in out or "Error: Evaluation timed out" in out) else 0
    print(json.dumps(res, indent=2, default=str))
    return 1 if "error" in res else 0


if __name__ == "__main__":
    sys.exit(main())
