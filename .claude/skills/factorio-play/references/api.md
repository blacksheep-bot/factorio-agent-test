# FLE API cheat-sheet (verified on this stack)

FLE 0.4.3 client, Factorio 2.0.73 headless, `setup/fle_repl.py` in turn-based mode
(`--pause-between`). Every claim below was checked against the live server unless marked
*(doc only)*. The full upstream manual is `docs/research/fle-system-prompt.md` (3.5k lines);
grep it for a tool name if you need more than this page.

## Running code

```bash
python3 setup/fle_exec.py -c 'print(inspect_inventory())'   # inline snippet
python3 setup/fle_exec.py /path/snippet.py                   # file (best for >5 lines; no quoting pain)
python3 setup/fle_exec.py agent/helpers.py                   # (re)load the helpers
python3 setup/fle_exec.py --render runs/<run>/renders/x.png --x X --y Y --radius 20
python3 setup/fle_exec.py --save <name>                      # -> .fle/saves/<name>.zip
python3 setup/fle_exec.py --status                            # REPL alive? tick, player position
```

- Output: one line per `print`, formatted `"<line>: (<repr of args>,)"`. A bare expression prints
  nothing. Output is capped at 512 lines. The exit code is 1 if the output contains an error.
- Statements run **one top-level statement at a time**. On an error, execution stops at that
  statement. **Everything before it already happened** (entities placed, items spent) and the
  variables assigned before it persist. Do not re-run the earlier lines.
- Variables and `def`s persist across calls. **Names starting with `_` are NOT persisted.**
  Tool names (`move_to`, ...) cannot be redefined. Never call `reset()`: it wipes your
  variables and the helpers.
- `import json, math, time` works inside snippets.
- `instance` is the live `FactorioInstance`. Raw Lua: `lua("rcon.print(game.tick)")` (helper).
- **Turn-based clock:** the game is paused between executions and runs only while a
  program runs. `sleep(n)` (max 15 per call) and `advance(seconds)` are how the factory
  produces. At game speed 10, `advance(60)` takes about 6 s of wall time.
- Timeouts: the default is 120 s per call (`--timeout N`). A timed-out snippet keeps running in
  a thread, so never write unbounded loops.

## Core tools (signature → behaviour → gotchas)

| Tool | Notes |
|---|---|
| `inspect_inventory(entity=None) -> Inventory` | `inv[Prototype.IronPlate]` → int (0 if absent). `inv.get(Prototype.Coal, 0)`. `inspect_inventory(furnace)` works on any container. |
| `nearest(Resource.X \| Prototype.X) -> Position` | Resources: `IronOre, CopperOre, Coal, Stone, Water, Wood, CrudeOil`. Searches about 500 tiles and raises if nothing is found. `Resource.X` is a tuple, so `Resource.Coal[0] == 'coal'`. |
| `get_resource_patch(Resource.X, pos) -> ResourcePatch` | `.size` (total amount), `.bounding_box.left_top/right_bottom`. |
| `move_to(pos) -> Position` | Near-instant (`fast=True`). **Required before** harvest, place, insert or extract (reach is about 10 tiles). |
| `harvest_resource(pos, quantity=1, radius=10) -> int` | Takes about 2.5 s wall per call regardless of quantity. Trees: `nearest(Resource.Wood)`; one call for 5 gave 8 wood. Returns the amount actually mined. |
| `craft_item(Prototype.X, quantity=1) -> int` | Crafts intermediates recursively from what you hold (plates→gears→drill). Instant. A locked recipe raises `"...recipe for pipe is not unlocked yet (requires steam-power technology)"`. |
| `get_prototype_recipe(Prototype.X) -> Recipe` | `.ingredients` are correct. **`.enabled` is unreliable** (it said False for burner-mining-drill, which was craftable). Use `research_state()['enabled']` instead. |
| `place_entity(proto, direction=Direction.UP, position=pos) -> Entity` | Snaps to the grid (for example, a drill at left_top (0.5,-63.5) lands at (1,-63)). **The returned object can be stale or even a different neighbouring entity of the same type.** Re-fetching with `get_entity(proto, returned.position)` can then fetch the *neighbour* too, so use the helper **`place_new(proto, pos, direction)`**, which diffs entities before and after and returns the one actually created. |
| `place_entity_next_to(proto, ref_pos, direction=RIGHT, spacing=0)` | Places adjacent to the reference entity on the given side. **For inserters: the result TAKES FROM the reference and drops away from it.** To feed INTO the reference, `rotate_entity(ins, <opposite direction>)`. |
| `rotate_entity(entity, Direction.X) -> Entity` | Inserter `.direction` = the side it drops toward. Check `pickup_position`/`drop_position` after rotating. |
| `can_place_entity(proto, direction=UP, position=pos) -> bool` | Works. |
| `nearest_buildable(proto, BuildingBox(width=w, height=h), center) -> BoundingBox` | Free w×h area. For drills it must be on ore. `.left_top`, `.center` (**a property, not a method**). Raises if there is no space. |
| `insert_item(Prototype.Item, target_entity, quantity=5) -> Entity` | Returns the **updated** entity, so reassign it. Must be in reach. |
| `extract_item(Prototype.Item, entity_or_pos, quantity=5) -> int` | Works on furnace results, chests, assembler output and drill fuel slots. |
| `pickup_entity(entity \| group) -> bool` | Returns items to the inventory. A whole `BeltGroup` works. |
| `get_entity(proto, pos) -> Entity` | Fresh state. Use it after every wait. |
| `get_entities(set_of_protos=set(), position=None, radius=1000) -> list` | Belts, pipes and poles come back as **groups** (`BeltGroup.belts`, `PipeGroup.pipes`, `ElectricityGroup.poles`). |
| `connect_entities(src, dst, Prototype.Pipe \| TransportBelt \| SmallElectricPole)` | Routes around obstacles. Accepts entities or Positions. Returns a group. **Poles: it stops as soon as the target is powered.** It will not add a pole for a second consumer that is already "on the network" by the group's logic but outside the 5×5 supply area. Place one with `place_entity_next_to(SmallElectricPole, consumer.position, RIGHT)`. |
| `get_connection_amount(a, b, proto) -> int` | Works for poles (3 for 10 tiles). **Broken for TransportBelt** (`TypeError: 'BeltGroup' object is not subscriptable`). |
| `set_entity_recipe(assembler, Prototype.IronGearWheel) -> Entity` | Works on AM1 without Automation research for already-enabled recipes (gears). |
| `set_research(Technology.Automation) -> [Ingredient]` | Returns the packs needed. The lab must hold packs and have power. |
| `get_research_progress(Technology.X) -> [Ingredient]` | `[]` means done. |
| `sleep(seconds)` | Capped at 15 game-seconds per call. Use `advance(n)` for longer waits. |
| `score() -> (score, automated)` | Also returned per exec as `score=`. |

## Entity fields that matter
- Every entity: `.name .position .direction .status (EntityStatus) .warnings (list[str]) .energy`.
- Burners (drill, furnace, burner inserter, boiler): `.fuel` (Inventory).
- Furnace: `.furnace_source`, `.furnace_result`. Assembler: `.recipe`, `.assembling_machine_input/_output`.
- Chest: `.inventory`. Lab: `.lab_input`. Drill: `.drop_position`, `.resources`.
- Inserter: `.pickup_position`, `.drop_position`. Fluid entities: `.connection_points`; boiler `.steam_output_point`.
- **`getattr(entity, 'anything')` returns something for ANY name** (dynamic fallback). Test
  fields with `has_field(e, 'fuel')` (helper) or `'fuel' in e.__dict__`, never `hasattr`.
- `status.value` strings: `working, no_fuel, no_power, no_ingredients, waiting_for_space_in_destination,
  full_output, item_ingredient_shortage, not_plugged_in_electric_network, waiting_for_source_items, ...`

## Misleading signals
- A burner drill dropping into a furnace shows the warning `"output blocked by item on the ground..."`
  while `status == WORKING`. **Trust `status` and the output counts, not `warnings`.**
- A steam engine with no consumer shows `NOT_PLUGGED_IN_ELECTRIC_NETWORK`. That is normal.
- An idle output inserter shows `WAITING_FOR_SOURCE_ITEMS`. That is normal.
- `player_location` only updates on `move_to`, and inside helper functions it is frozen at
  load time. Use `player_pos()`.
- `get_research_progress()` with no argument raises if no research is active.

## Research and recipes (Factorio 2.0, research NOT pre-completed; verified)
At start, enabled recipes are: burner-mining-drill, stone-furnace, iron-gear-wheel,
burner-inserter, transport-belt, wooden-chest, iron-chest, automation-science-pack (FLE
pre-researches the `automation-science-pack` tech; firearm-magazine is also on).
2.0 **research triggers** fire from real production (furnace output counts):
- `steam-power`: produce 50 iron plates. Unlocks pipe, pipe-to-ground, offshore-pump,
  boiler, steam-engine.
- `electronics`: produce 10 copper plates. Unlocks copper-cable, electronic-circuit, lab,
  inserter, small-electric-pole.
- `automation`: 10 red packs in a powered lab (10 s each). Unlocks assembling-machine-1
  and long-handed inserter.
- After that come normal lab research (logistics, electric mining drill via
  automation-science, and so on).
`status_report()` prints the trigger counters and enabled/locked recipes.

## Helpers (agent/helpers.py, auto-loaded)
`status_report(show_ok=True, radius=None)`, `refuel_all(min_fuel=5, amount=20, fuel=None)`,
`find_space(w, h, near, proto=None, pad=2) -> inner left_top Position`, `gather(Resource.X, qty)`,
`collect(item=None, min_count=1)`, `place_drill_furnace(ore=Resource.IronOre, near=None, fuel=10)`,
`place_new(proto, pos, direction=None)`, `advance(seconds)`, `wait_for(pred, timeout=60, step=5)`, `produced(Prototype.X)` (all-time
production stat), `check_growth(Prototype.X, seconds=30)`, `ensure_crafted(proto, n)`,
`research_state()`, `journal_snapshot()`, `player_pos()`, `lua(code)`, `inv_dict(inv)`,
`has_field(e, attr)`, `make_peaceful()`, `helpers_help()`.

## Crafting traps
- `craft_item(Prototype.BurnerMiningDrill)` **consumes a stone furnace from your inventory**
  if you have one (it is an ingredient). Craft one furnace per drill-furnace pair on top.
- `craft_item` recurses (stone→furnace, plates→gears) but never smelts: ore is not plates.

## REPL / server traps
- Rarely, a helper's print line is missing from the output (seen once). If the output
  looks incomplete, check the state directly instead of re-running actions.
- **REPL restart (no `--fresh`)**: FLE's connect resets research, inventory and the
  character. `fle_repl.py` snapshots these over RCON first and restores them. Your Python
  variables are lost, so re-derive entities with `get_entities()`. `--fresh` WIPES every
  built entity: never use it mid-run.
- Renders are centred on the character: `--x/--y` moves you there first. Lab and
  character sprites are missing (a lab shows only as an alert icon).
- Save with `fle_exec.py --save` only. A raw `game.server_save` crashes the server (Lua
  functions in `storage`).
- If every call errors after a server restart: `python3 setup/fle_exec.py --reinit`.
