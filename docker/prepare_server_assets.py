"""Copy FLE's server assets (scenarios, config, mod-list) out of the pip package into DEST,
with autosave effectively disabled (gotcha G3: any save while FLE's Lua is loaded crashes
the server; only fle_repl.py's /save is safe). Mirrors setup/start_server.sh."""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

dest = Path(sys.argv[1])
pkg = Path(importlib.util.find_spec("fle").submodule_search_locations[0]) / "cluster"
shutil.copytree(pkg / "scenarios", dest / "scenarios")
shutil.copytree(pkg / "config", dest / "config")
(dest / "mods").mkdir(parents=True)
shutil.copy2(pkg / "mods" / "mod-list.json", dest / "mods" / "mod-list.json")
p = dest / "config" / "server-settings.json"
s = json.loads(p.read_text())
s.update(autosave_interval=525600, autosave_slots=0, auto_pause=False)  # minutes; ~1 year
p.write_text(json.dumps(s, indent=2))
print("assets:", sorted(x.name for x in dest.rglob("*") if x.parent == dest / "scenarios"))
