# Factorio Learning Environment (FLE): setup, API, visualization, persistence

Tested on 2026-11-14 in this container (Linux x86_64, 4 CPU, Python 3.12 venv via `uv`,
Docker daemon started by hand). Everything here was run, unless it is marked
**untested**.

- FLE: PyPI `factorio-learning-environment==0.4.3` (the latest on PyPI). The GitHub `main`
  branch is at 0.4.8, which has not been released to PyPI. A copy is cloned at `.vendor/fle`
  for reading. It differs from 0.4.3 in a few files (a2a import fix, run-envs.sh, reset,
  connect_entities).
- Factorio server: Docker image `factoriotools/factorio:2.0.73`. It runs headless, base game
  only: the launch command deletes the `space-age`, `quality` and `elevated-rails` data
  directories.
- Paths in this doc that start with `fle/...` are relative to
  `.venv/lib/python3.12/site-packages/fle/`.

---

## 1. Quick start (exact commands)

```bash
cd /home/user/factorio-agent-test
# 0. docker daemon (if dead):  (dockerd > /tmp/dockerd.log 2>&1 &)
bash setup/install.sh                 # venv + FLE 0.4.3 + a2a-sdk<1 + sprites (+fix) + docker image
setup/start_server.sh                 # headless Factorio, RCON localhost:27000 pw "factorio"
# persistent REPL (keeps ONE FactorioInstance alive -> variables persist between snippets)
nohup .venv/bin/python -W ignore setup/fle_repl.py --fresh \
  --inventory '{"coal":50,"iron-plate":50,"stone-furnace":5,"burner-mining-drill":3}' \
  > .fle/repl.log 2>&1 &
python3 setup/fle_exec.py -c 'print(inspect_inventory()); print(nearest(Resource.IronOre))'
python3 setup/fle_exec.py --render docs/research/test-render.png --radius 16 [--x 21 --y 72]
python3 setup/fle_exec.py --save mysave          # -> .fle/saves/mysave.zip (on the host)
```

**State when I finished:** container `fle_factorio_0` is running (RCON `localhost:27000`,
password `factorio`, game UDP `34197`). The REPL from the commands above is running on
`http://127.0.0.1:8765` (PID in `ps aux | grep fle_repl`), connected to a near-empty map.
To restart the REPL: `pkill -f setup/fle_repl.py` and run the nohup line again. Leave out
`--fresh` to keep the map. Python variables are lost on restart, but the game world is not.

### Setup scripts (`setup/`)

| file | purpose |
|---|---|
| `install.sh` | Idempotent. Sets up the `uv` venv (py3.12), FLE 0.4.3, `a2a-sdk<1`, `fle sprites`, `fix_sprites.py`, a `~/.fle/sprites` symlink, and `docker pull`. `WITH_MCP=1` also installs `fastmcp<2.14 dulwich` for FLE's MCP server. |
| `start_server.sh [scenario]` | Uses `docker run` to start one server the way `fle cluster start` does (same image, flags and ports). It also bind-mounts `.fle/saves` → `/factorio/saves` and turns autosave off. Env vars: `FLE_SAVE=name` loads `.fle/saves/name.zip`; `FLE_CONTAINER`, `FLE_RCON_PORT` and `FLE_GAME_PORT` let you run a second server. |
| `fle_repl.py` | Persistent HTTP REPL around one `FactorioInstance`. Endpoints: `/exec`, `/render`, `/save`, `/reinit`, `/status`. Binds 127.0.0.1:8765 only. |
| `fle_exec.py` | Stdlib-only CLI client for the REPL. Exits with code 1 if the FLE output contains an error. |
| `fix_sprites.py` | Makes entity sprites render without the `basisu` tool (see gotcha G7). |
| `dump_system_prompt.py` | Writes FLE's generated agent prompt to `docs/research/fle-system-prompt.md` (117 KB, already generated). |

The official route also works: `fle cluster start` (I ran it). It creates a compose project
`cluster`, container `cluster-factorio_0-1`, scenario `default_lab_scenario`, RCON host port
`27000` mapped to container port `27015`, game UDP `34197`, and `fle cluster stop`. I
replaced it with `start_server.sh` because the official route has no saves mount and the
saves directory does not exist inside the container (G4). It also writes a placeholder
`.env` into the current directory.

---

## 2. How FLE is wired

- **Server.** Vanilla headless Factorio 2.0.73 started with `--start-server-load-scenario
  default_lab_scenario` (or `open_world`). Scenarios come from `fle/cluster/scenarios/`; the
  lab scenario is a pre-made 1.1.110 `level.dat` that gets migrated. Config comes from
  `fle/cluster/config/`: `require_user_verification=false`, `autosave_slots=0`, and LAN-only
  visibility. **There is no Factorio mod.** All FLE logic is Lua that the client injects over
  RCON.
- **Connection.** `FactorioInstance(address, tcp_port=27000, ...)` uses `factorio-rcon-py`
  with the password `factorio`. It loads `fle/env/mods/*.lua` (utilities) and each
  `fle/env/tools/{agent,admin}/<tool>/server.lua` into `storage.actions.*` /
  `storage.utils.*`. It also builds one Python controller per `client.py` and attaches
  them to a `FactorioNamespace`.
- **Character.** FLE does not use a connected player. Every `FactorioInstance(...)`
  destroys all characters and creates a new one at (0,0) (`storage.agent_characters[1]`).
- **Constructor arguments that matter.**
  - `fast=True`: actions are instant. Walking is near-teleport, and mining and crafting are
    instant but still add time to `storage.elapsed_ticks`.
  - `inventory={...}`: the inventory is **set** to exactly this on every connect or reset.
  - `all_technologies_researched` (default True).
  - `clear_entities` (default **True**: wipes everything the player force built).
  - `cache_scripts`: skips re-sending Lua whose checksum is unchanged (see G9).
  - `peaceful=True`: removes enemies.
  - `reset_speed=10`: `game.speed=10` on connect.
- **Time.** The server simulates continuously at `game.speed` (10x after connect), even
  between agent programs, so factories keep running. `sleep(n)` (capped at 15) advances
  `storage.elapsed_ticks` by n*60 and blocks for roughly n/speed real seconds. Read
  `game.tick` with `inst.rcon_client.send_command("/sc rcon.print(game.tick)")`; the REPL
  returns it as `tick`. Other controls: `inst.set_speed(x)`, `inst.pause()`,
  `inst.unpause()`, `inst.get_elapsed_ticks()`.
- **Gym environment.** `fle/env/gym_env/` registers `gym.make("<task>")` for each task in
  `fle/eval/tasks/task_definitions/`. `env.step(Action(agent_idx=0, code=...))` calls
  `instance.eval`. It is not needed for our use, and creating one resets the world.

### Python version

`requires-python >=3.10` and classifiers go up to 3.13. I used 3.12 (`uv venv -p 3.12`)
and did not try 3.13.

---

## 3. Gotchas (all hit and fixed unless noted)

| # | Symptom | Cause / fix |
|---|---|---|
| G1 | `ImportError: cannot import name 'TextPart' from 'a2a.types'` when constructing `FactorioInstance` | 0.4.3 depends on an unpinned `a2a-sdk`, and 1.x removed `TextPart`. **Fix:** `uv pip install "a2a-sdk<1"` (0.3.26 works). |
| G2 | The world is wiped or the inventory is reset unexpectedly | Each `FactorioInstance(...)` (and `instance.reset()`) re-creates the character at (0,0), sets the inventory to `inventory=`, and with the default `clear_entities=True` deletes every player-force entity. Pass `clear_entities=False` to keep the map; the inventory is still overwritten. **Importing** `fle.env.protocols._mcp` also builds a gym env, which calls `FactorioInstance()` and wipes the world. This happened to me. |
| G3 | **The server crashes on any save:** `Error while running event level::on_save() Cannot serialise lua functions` → "Goodbye" → Docker restarts it and all progress is lost | FLE stores Lua functions in `storage` (82 functions in `storage.actions`, `storage.utils`, ...). **Fix (in `fle_repl.py /save`):** set `game.tick_paused=true`, move every function out of `storage` into a non-persisted global, call `game.server_save(name)`, wait for the file, put the functions back, then unpause. Pausing is required: a `nth_tick` handler calls `storage.actions.update_walking_queues` and crashes the server if it runs while the functions are missing. Autosave would trigger the same crash, but the shipped config has `autosave_slots: 0`. I tested `autosave_interval=1` with `slots=0` for 2.5 minutes and no autosave happened. `start_server.sh` also sets the interval to one year. |
| G4 | `game.server_save` → `filesystem error: cannot make canonical path [/opt/factorio/saves]` (this also killed the server) | In the image, `/opt/factorio/saves` is a symlink to `/factorio/saves`, which does not exist unless it is mounted. `start_server.sh` mounts the host directory `.fle/saves` there (with chmod a+rwX; the container runs as uid 845). |
| G5 | After a server crash or restart, every tool call fails | The Lua state is gone. Re-create the `FactorioInstance` with `POST /reinit` or `fle_exec.py --reinit`. |
| G6 | `Sprites not found ... Vision rendering will produce empty images` | Run `fle sprites` (downloads ~370 MB from the HF dataset `Noddybear/fle_images` into `.fle/spritemaps`, then generates `.fle/sprites`). Lookup order: walk up from cwd looking for `.fle/sprites`, then `~/.fle/sprites`, then `$FLE_SPRITES_DIR`. `install.sh` symlinks `~/.fle/sprites`. |
| G7 | Renders show ore, water and alert icons but **no entities** | Entity spritesheets are `.basis` files and need the `basisu` binary (`basisu -unpack`), which is not installed; building it from source was blocked here. The HF dataset already ships transcoded PNGs in `spritemaps/cache/`, but under the author's absolute-path key. `setup/fix_sprites.py` symlinks them to the key FLE expects and regenerates sprites (1802 → 2176). After that, drills, furnaces, belts and inserters render. The **character** sprite is still missing, so the player is not drawn. |
| G8 | `_render(position=...)` ignores `position` | The Lua side scans around the **character**, and the renderer centres on the character, so `position` only affects a secondary `get_entities` query. `move_to` the area first; `fle_exec.py --render --x --y` does this for you. `radius` limits the scan, and `max_render_radius` (default 32) sets the image extent, so pass both. The output is capped at 1024 px. |
| G9 | Loading a save made by FLE, then connecting: `get_entities()` returns `[]` silently | `storage.__lua_script_checksums` survives in the save, so with `cache_scripts=True` FLE skips re-sending the Lua, and calls into the missing `storage.utils.serialize_entity` fail silently. **Fix:** `cache_scripts=False` (the REPL uses this). |
| G10 | `player_location` is stale inside a snippet | `eval` snapshots namespace attributes at the start of each program. Inside a snippet, use the `Position` returned by `move_to`; `player_location` is correct from the next snippet on. |
| G11 | A snippet times out but keeps running (I measured 93% CPU) | `instance.eval` runs code in a `ThreadPoolExecutor(max_workers=2)` and only stops waiting at the timeout. The thread is never killed, so two runaway snippets block all future evals. Avoid unbounded loops (use `for _ in range(N): ... sleep(1)`). Recovery: restart `fle_repl.py`. |
| G12 | `place_entity(..., position=p)` lands at a slightly different spot (for example 16.5,71.5 → 17,72), and returned objects can be stale | Entities snap to the grid. Re-read state with `get_entity(Prototype.X, pos)` or `get_entities()`. Once, `d2.drop_position` and `insert_item(..., d2)` acted on the wrong drill after two quick placements. Rotation also changes `drop_position`. |
| G13 | A drill's output is "blocked by item on the ground" | `place_entity_next_to(WoodenChest, drill.position, RIGHT)` does not put the chest on the drill's drop position. Use `place_entity(Prototype.WoodenChest, position=drill.drop_position)`. |
| G14 | FLE's MCP server does not start | The 0.4.3 `[mcp]` extra forgets `fastmcp`, and `fastmcp>=2.14` rejects `FastMCP(dependencies=...)`. `fastmcp<2.14` (2.13.3) works. It also needs a container whose name contains `factorio_` (docker ps filter), and see G2: it wipes the world on import. |
| G15 | `fle` CLI drops a placeholder `.env` (fake API keys) into cwd | Harmless (`load_dotenv` does not override existing env). It is deleted and gitignored. |
| G16 | Gym import prints a scary "Gym has been unmaintained" banner and SyntaxWarnings | Cosmetic. Run Python with `-W ignore`. |
| G17 | A second server loading a save without the FLE config fails with `Failed to reach auth server ... SSL certificate problem` | Without `--server-settings` the default requires user verification, which reaches factorio.com and is blocked by the TLS proxy. Always pass FLE's `server-settings.json` (`start_server.sh` does). |

---

## 4. Running a program: output, errors, persistence

`score, duration, output = instance.eval(code: str, agent_idx=0, timeout=60)`
(`fle/env/instance.py`). It calls `FactorioNamespace.eval_with_timeout`
(`fle/env/namespace.py`):

- The code is parsed with `ast` and run **one top-level statement at a time** against a
  dict built from builtins, every tool, the type and entity classes, and `persistent_vars`.
  `import` works; I used `import time`.
- Each `print(...)` becomes a log line `"<line_no>: (<repr of args>,)"`, for example
  `3: (Position(x=15.5, y=70.5),)`. Output is capped at 512 lines. A bare expression does
  not print.
- **Python errors:** execution stops at the failing top-level statement. Output gets
  `"Error occurred:\n  Line 1: <src>\n\nNameError: ..."`, with "Did you mean" suggestions
  for NameErrors. The return value is still the normal score. Persistent variables roll back
  to the last successful statement.
- **Tool errors** (for example placing something not in the inventory, or crafting a locked
  recipe) appear as `('\nException: Could not place assembling-machine-1 at (5.0, 5.0),
  <inventory>',)` and also stop execution. Messages are descriptive, for example "recipe for
  electric-mining-drill is not unlocked yet (requires electric-mining-drill technology)".
- **Timeout:** output is `...partial...\n\nError: Evaluation timed out after Ns` and score
  is -1 (see G11).
- `score` is FLE's production score from `score()`. It is often 0 in the lab scenario.
- **Persistence:** assignments, `def` functions (stored as `SerializableFunction`) and
  classes go into `namespace.persistent_vars`. They live as long as the `FactorioInstance`
  Python object, so **one long-lived process is required**. I verified this: `x = 42` and
  `def dist(a, b)` defined in one `/exec` were usable in later calls. Tool and builtin names
  are protected; redefining `move_to` raises `NameError: Cannot redefine ...`.
  `instance.reset()` clears agent variables. `GameState.from_instance(inst)` /
  `inst.reset(game_state)` can snapshot and restore entities, inventory, research and the
  pickled namespace. The MCP server's "VCS" uses this; I did not test it directly.

---

## 5. Agent API reference (namespace available inside programs)

Signatures come from `inspect.signature` on the live controllers in 0.4.3. Per-tool manuals
are in `fle/env/tools/agent/<tool>/agent.md`, and all of them are concatenated into
**`docs/research/fle-system-prompt.md`**. That file is the exact system prompt FLE gives
its agents: Prototype/Resource/Technology/Direction enums, entity classes and every tool
manual. Point the Claude agent at it.

| tool | signature | description |
|---|---|---|
| `inspect_inventory` | `(entity=None, all_players=False) -> Inventory` | Your inventory, or an entity's (chest, furnace, ...). `inv[Prototype.IronPlate]` gives a count. |
| `nearest` | `(type: Prototype\|Resource) -> Position` | Nearest resource or entity within 500 tiles; raises if none. Resources: `Resource.IronOre/CopperOre/Coal/Stone/Water/CrudeOil/Wood/UraniumOre`. |
| `get_resource_patch` | `(resource, position, radius=30) -> ResourcePatch` | Patch name, size and `bounding_box`. |
| `move_to` | `(position, laying: Prototype=None, leading: Prototype=None) -> Position` | Path-find and walk (near-instant with `fast=True`); can lay belts or pipes behind you. |
| `harvest_resource` | `(position, quantity=1, radius=10) -> int` | Mine by hand (ore, coal, stone, trees for wood). Must be near. |
| `craft_item` | `(entity: Prototype, quantity=1) -> int` | Hand-craft, crafting intermediates recursively if raw materials are present. |
| `get_prototype_recipe` | `(prototype) -> Recipe` | Ingredients and products. |
| `place_entity` | `(entity, direction=Direction.UP, position=Position(0,0), exact=True) -> Entity` | Place from the inventory; must be within reach (about 10 tiles). |
| `place_entity_next_to` | `(entity, reference_position, direction=RIGHT, spacing=0) -> Entity` | Place adjacent to a position. |
| `can_place_entity` | `(entity, direction=UP, position) -> bool` | Placement check. |
| `nearest_buildable` | `(entity, building_box: BuildingBox, center_position) -> BoundingBox` | Find free space (on ore, for drills). Use `.center` / `.left_top`. |
| `rotate_entity` | `(entity, direction=UP) -> Entity` | Rotate. |
| `pickup_entity` | `(entity\|Prototype\|EntityGroup, position=None) -> bool` | Mine a placed entity back into the inventory. |
| `insert_item` | `(entity: Prototype, target: Entity\|EntityGroup, quantity=5) -> Entity` | Put items or fuel into an entity. Returns the **updated** entity; reassign it. |
| `extract_item` | `(entity: Prototype, source: Position\|Entity, quantity=5) -> int` | Take items out of an entity. |
| `connect_entities` | `(*args, **kwargs)`, i.e. `(source, target, Prototype.TransportBelt\|Pipe\|SmallElectricPole...)` | Route belts, pipes or poles between positions or entities. Returns a `BeltGroup`, `PipeGroup` or `ElectricityGroup`. |
| `get_connection_amount` | `(source, target, connection_type=Prototype.Pipe) -> int` | How many pieces a connection needs. |
| `get_entity` | `(entity: Prototype, position) -> Entity` | Fresh state of one entity. |
| `get_entities` | `(entities: set[Prototype]\|Prototype = set(), position=None, radius=1000) -> list[Entity\|EntityGroup]` | All player-force entities, with belts and pipes grouped. Each has `.status` and `.warnings`. |
| `set_entity_recipe` | `(entity, prototype: Prototype\|RecipeName) -> Entity` | Set an assembler or chemical plant recipe. |
| `set_research` | `(technology: Technology) -> list[Ingredient]` | Start research; returns the science packs needed. |
| `get_research_progress` | `(technology=None) -> list[Ingredient]` | Remaining packs. |
| `sleep` | `(seconds: int) -> bool` | Let game time pass (≤15 s game time per call). |
| `launch_rocket` | `(silo) -> RocketSilo` | |
| `score` | `() -> (score, automated_score)` | Production score. |
| `send_message` | `(message, recipient=None, metadata=None) -> bool` | Multi-agent messaging (A2A); not needed. |
| `print` | `(*args)` | Logged to the output (see section 4). |
| `reset` | `()`: this is `FactorioNamespace.reset`, not the admin tool | Clears all of the agent's persisted variables. Do not call it. (The world-wiping admin tool is `_reset` and is not reachable.) |

**Escape hatch (verified):** agent code can reach `instance`, the live `FactorioInstance`.
For example, `instance.rcon_client.send_command("/sc rcon.print(game.tick)")` works, as do
`instance.namespace._render(...)` and raw Lua. This is powerful and lets agent code wreck
the server, so use it deliberately.

Other names in scope:
- `Prototype.*` (every item and entity, for example `Prototype.BurnerMiningDrill` and
  `Prototype.IronGearWheel`; each has `.WIDTH` and `.HEIGHT`).
- `Resource.*`, `Technology.*`, `RecipeName.*`.
- `Direction.UP/DOWN/LEFT/RIGHT` and the aliases `UP`, `NORTH`, `EAST`, ...
- `Position(x=, y=)`, `BoundingBox`, `BuildingBox(width=, height=)`, `EntityStatus.*`.
- Entity classes (`BurnerMiningDrill`, `Furnace`, `TransportBelt`, ...).
- Math helpers: `sqrt`, `floor`, `ceil`, `pi`, ...
- `player_location` (see G10).

Admin tools are attached to the namespace with a leading underscore (`ns._render`). They
are not visible to agent code because names starting with `_` are excluded, so call them
from the host process:
`_render`, `_render_simple`, `_save_blueprint`, `_load_blueprint`, `_save_entity_state`,
`_load_entity_state`, `_save_research_state`, `_load_research_state`, `_set_inventory`,
`_get_production_stats`, `_get_factory_centroid`, `_regenerate_resources`,
`_clear_entities`, `_create_agent_characters`, `_request_path`, `_get_path`,
`_render_message`, `_extend_collision_boxes`, `_clear_collision_boxes`, `_reset`.

**Other docs FLE ships (useful as agent context):**
- `fle/env/tools/agent.md`: patterns, such as a self-fuelling coal drill.
- `fle/eval/open/MANUAL.md` (27 KB): a gameplay manual with right and wrong examples.
- `fle/eval/algorithms/beam/MANUAL_short.md` (52 KB).
- `fle/env/protocols/_mcp/tutorial.md`.
- `fle/eval/inspect/integration/prompts/unbounded_system.jinja2.md`: their current agent
  system prompt, with policy-writing tips.
- `fle/env/tools/admin/render/agent.md`.
- The generated `docs/research/fle-system-prompt.md`.

### Lab scenario map facts (`default_lab_scenario`; no enemies, always day)

- Spawn: (0,0).
- Iron: patch from (15.5,70.5) to (38.5,95.5).
- Coal: (15.5,-0.5).
- Stone: (-46.5,-0.5).
- Copper: (-46.5,70.5).
- Water: (-11,0).
- Crude oil: a grid around (2..23,-29).
- Resource tiles hold about 40k each.
- With `all_technologies_researched=False`, only starting recipes are available. The REPL
  default is False; pass `--all-tech` to research everything.

---

## 6. Seeing what was built

### A. FLE PNG renderer (works after G6 and G7)

```python
img = inst.namespace._render(radius=16, max_render_radius=16)   # centred on the character
img.save("out.png"); img.viewport  # world_min_x/.../scaling -> map pixel<->world
```

or `python3 setup/fle_exec.py --render out.png --radius 16 --x 21 --y 72`. That command
moves the character to (21,72) first and returns the world bounding box.

`docs/research/test-render.png` is the result. It shows the iron patch, 3 burner drills, an
11-tile belt, 2 burner inserters and 3 furnaces, with status alert icons. The character is
not drawn (no sprite).

Alternative: `ns._render_simple(position=..., style={...})` also produced a PNG. It is a
simpler schematic renderer.

### B. Real Factorio save file (`.zip`)

Use `fle_exec.py --save NAME [--copy-to /abs/path.zip]` or `Repl.save()` in
`setup/fle_repl.py`; it applies the G3 workaround. The file appears at
`/home/user/factorio-agent-test/.fle/saves/NAME.zip` because that directory is
bind-mounted. Without the mount, use `docker cp fle_factorio_0:/factorio/saves/NAME.zip .`
after creating the directory (G4).

I verified the round trip. `fle_demo.zip` (1.08 MB, map tick 131615) loaded in a fresh
container (`FLE_SAVE=fle_demo FLE_CONTAINER=fle_loadtest FLE_RCON_PORT=27001
setup/start_server.sh`), and RCON listed all 37 placed drills, belts, furnaces and
inserters. FLE reconnected to it with `cache_scripts=False, clear_entities=False` and
`get_entities()` returned 12 entities/groups.

The save is base-game 2.0.73. Copy it into a desktop Factorio ≥2.0.73
`saves/` folder and load it to look around (**untested with a GUI client**).

### C. Other options (not used)

- Headless Factorio cannot `game.take_screenshot` (it needs graphics). **Untested**, but
  this is a documented Factorio limitation. The `script-output` mount exists for FLE's
  desktop-client tooling (`fle/cluster`, pyautogui/opencv in the `[cluster]` extra).
- `fle/eval/analysis/run_to_mp4.py` builds timelapses from renders of stored trajectories
  (DB-backed). I did not run it.
- Joining with a real client over UDP 34197 is possible in principle (LAN visibility, no
  verification), but this container is not reachable from outside.

---

## 7. Persistent session for a Claude agent

Options found in FLE:

1. **FLE MCP server**: `python -m fle.env.protocols._mcp` (FastMCP, stdio). It has 9
   tools: `render`, `execute`, `reconnect`, `undo`, `commit`, `restore`, `view_history`,
   `list_tags`, `view_code`. It also exposes resources (`fle://entities`, recipes,
   `fle://api/docs/{method}`, ...) and prompts. `execute(code)` runs
   `instance.eval(code, timeout=60)` on one long-lived instance, so variables persist. It
   auto-commits a `GameState` snapshot after every call (dulwich-backed "VCS", for undo and
   restore), returns a PNG from `render`, and writes `/tmp/factorio_game_state.json`.
   Caveats: G14 (dependency pins), G2 (it wipes the world and sets a tiny inventory on
   import/connect), it auto-discovers containers by name `factorio_`, and the extra
   snapshot on every call costs time. I confirmed it imports and lists its tools with
   `fastmcp==2.13.3`. I did **not** wire it into Claude Code.
2. **Gym env** (`gym.make(task)` → `env.step(Action(code=...))`): task- and
   reward-oriented, and resets the world. Not a good fit.
3. **`setup/fle_repl.py` + `setup/fle_exec.py` (recommended, built and tested here).** A
   minimal HTTP REPL around one `FactorioInstance` (`fast=True`, `cache_scripts=False`).
   The Claude agent writes snippets and runs `python3 setup/fle_exec.py -c '...'` or
   `fle_exec.py file.py`. Variables and functions persist across calls, and there are
   render and save commands. It does not wipe the map unless started with `--fresh`.
   Requests are serialised with a lock. If a snippet hangs (G11) or the server restarts
   (G5), restart the REPL or call `--reinit`.
