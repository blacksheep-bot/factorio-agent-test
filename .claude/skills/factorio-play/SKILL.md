---
name: factorio-play
description: Play Factorio through the Factorio Learning Environment (FLE) REPL in this repo by writing small Python programs (python3 setup/fle_exec.py). Use for any task that builds, inspects, repairs or advances a Factorio factory, plays a shift of a run in runs/<name>/, or checks/renders/saves the game state.
---

# Playing Factorio via FLE

You control one character in a headless Factorio 2.0.73 world. You do it by sending Python
snippets to a persistent REPL:

```bash
python3 setup/fle_exec.py -c 'status_report()'      # short inline
python3 setup/fle_exec.py /tmp/<scratch>/step.py     # anything longer than ~3 lines: write a file first
```

Variables and functions persist between calls. The game is **turn-based**: it is paused
between your calls and only advances while a program runs (`sleep(≤15)`, `advance(seconds)`).
Thinking costs no game time, so nothing runs out of fuel while you plan. But nothing is
produced either unless you wait.

References (read them when needed, not all up front):
- `references/api.md`: tested tool signatures and traps. **Read it before your first program.**
- `references/strategy.md`: ratios, research gates, milestone ladder with code checks.
- `references/recipes.md`: known-good snippets: drill→furnace, coal pair, refuel, steam power,
  gear assembler, lab.
- `agent/helpers.py`: preloaded helpers (`status_report`, `refuel_all`, `find_space`, `gather`,
  `collect`, `place_new`, `place_drill_furnace`, `advance`, `check_growth`, `produced`, `journal_snapshot`, ...).

## The loop (one iteration = one program)

1. **Orient.** At the start of a shift, and whenever you are unsure, run `status_report()`.
   It prints the inventory, every entity with status/fuel/contents, the problems list, the
   research state, trigger counters, and unlocked/locked recipes. Read the PROBLEMS line first.
2. **Pick the next milestone** from strategy.md (or the one the orchestrator gave you). Write
   down its code check.
3. **Write one small program** (≤ ~30 lines, one purpose):
   - Re-read the state you depend on at the top (`get_entity`, `inspect_inventory`).
   - `assert` preconditions with informative messages (`assert inv[...] >= 9, f"need 9 plates, have {...}"`).
   - Use `move_to` before every harvest, place, insert or extract.
   - Place with `nearest_buildable`, `find_space`, or `drop_position`/`pickup_position`, never with
     hand-computed coordinates near other things.
   - Place with `place_new(proto, pos, dir)`, which returns the entity actually created. Re-fetch
     with `get_entity(proto, pos)` after any wait.
   - `print` positions, counts and statuses: only what you need to decide the next step.
4. **Read the output.** On an error, execution stopped at that statement and **everything
   before it already happened**. Do not re-run the earlier lines. Inspect what exists, then
   continue from the failure point.
5. **Verify with inspection, not belief.** `advance(30-60)`, then re-fetch and check `status`
   and output counts (`check_growth(Prototype.IronPlate, 60)` or chest/furnace contents).
   An entity existing is not proof that the chain works.
6. **Journal.** After each milestone or important discovery, append 1–3 lines to
   `runs/<run>/JOURNAL.md` (see the shift protocol below). Store key positions in a
   namespace dict too, for example `sections['iron_smelting'] = {...}`.

## Golden rules
1. **Small programs and fail fast.** A 100-line script that dies at line 74 leaves a
   half-built mess.
2. **Never trust a returned object after waiting or after a placement next to a same-type
   entity.** Re-fetch it.
3. **Fuel is the clock.** Give 20 coal to every burner thing. Run `refuel_all()` at the start
   of every shift and before every long `advance`. Automate coal by M3.
4. **Automate, don't shuttle.** Hand-mining is only for the bootstrap. Every program after M1
   should add, extend or fix an automated chain. Hand-filled chests do not count for
   milestones.
5. **Leave working sections alone.** Build new sections ≥ 10 tiles away (≥ 20 for assembly).
   Never pick up or rotate a working entity to "tidy" things.
6. **Two strikes and you change approach.** If the same fix failed twice: inspect the
   surroundings, try another spot or patch, or build differently. Never conclude that "the
   environment is broken", and never reset the world.
7. **Check research gates before crafting.** `status_report()` lists locked recipes.
   steam-power = 50 iron plates produced; electronics = 10 copper plates produced;
   Automation = 10 red packs in a powered lab.
8. **No unbounded loops.** Use `for _ in range(N)` and `advance()`. A hung snippet blocks the
   REPL.

## Failure modes → mitigations
| Symptom | Fix |
|---|---|
| `Could not place X at ...` | `find_space(w, h, near)` / `nearest_buildable` with padding. Check reach (`move_to` first). Water tiles block boilers and engines. |
| Drill/furnace `no_fuel` | `refuel_all()`. Then automate coal. |
| Drill `waiting_for_space_in_destination` | Nothing takes the output. Put a furnace or chest on `drill.drop_position`, or pull from it. |
| Furnace `no_ingredients` with a drill next to it | The drill is not dropping into it. Compare `drill.drop_position` with the furnace footprint, and check the drill's fuel. |
| Assembler `item_ingredient_shortage` / `no_power` | Check the input inserter's direction (`pickup_position`/`drop_position`), the chest contents, and pole coverage (5×5 per small pole). |
| Inserter `no_power` | The pole's supply area misses it. `place_entity_next_to(SmallElectricPole, ins.position, RIGHT)`. |
| Inserter moving the wrong way | `place_entity_next_to(Inserter, X.position, side)` takes FROM X. `rotate_entity` it to feed INTO X. |
| `Could not place stone-furnace ...` right after crafting a drill | Crafting a burner drill ate your furnace. Craft another one. |
| `recipe ... is not unlocked` | Research gate. See rule 7. Do not loop on crafting it. |
| `NameError` for a helper | Helpers are gone (REPL restarted or `reset()` called): `python3 setup/fle_exec.py agent/helpers.py`. |
| Every call fails / connection refused | `python3 setup/fle_exec.py --status`. Then `--reinit`, or restart the REPL (CLAUDE.md). **Never** with `--fresh` mid-run. |
| Warning "output blocked by item on the ground" while status is WORKING | False positive. Trust status and counts. |

## Shift protocol (when run by the orchestrator)
You get: the run directory `runs/<run>/`, a milestone goal, and a budget of N executions.
1. Read `runs/<run>/JOURNAL.md`, especially the latest handoff. Run `status_report()` and
   `refuel_all()`. Re-create the namespace variables you need from the handoff positions
   (`get_entity(...)`). Variables from earlier shifts may be gone.
2. Play the loop toward the milestone. Count your executions and stop at the budget even if
   the milestone is unfinished. Leave the factory in a fuelled, non-broken state.
3. Before ending: `refuel_all()`, run the milestone's code check, `journal_snapshot()`, then
   render and save:
   ```bash
   python3 setup/fle_exec.py --render runs/<run>/renders/shift-NN.png --x <base cx> --y <base cy> --radius 30
   python3 setup/fle_exec.py --save <run>-shift-NN     # -> .fle/saves/<run>-shift-NN.zip
   ```
   Render each separate area (smelting, power, ...) if they are more than about 50 tiles
   apart. Look at the PNG (Read it) to sanity-check the layout.
4. Append a handoff to `runs/<run>/JOURNAL.md` in exactly this shape:
   ```markdown
   ## Shift NN — <milestone goal> — <DONE | PARTIAL | BLOCKED>
   - Executions used: N / budget. Game tick: T.
   - Milestones reached: M1 (check: check_growth iron = +14/60s) ...
   - Built (name → positions): iron_smelting: drills (1,-63),(3,-63) → furnaces (2,-61),(4,-61); ...
   - Works: ... Broken/at risk: ... (fuel levels, blocked outputs)
   - Inventory highlights: coal=…, iron-plate=…, notable items
   - Research: researched=[...], current=..., triggers iron …/50 copper …/10
   - Lessons / traps hit this shift: ...
   - NEXT: the single most useful next step, with positions.
   - Render: renders/shift-NN.png · Save: .fle/saves/<run>-shift-NN.zip
   ```
   Also add one line to the run's timeline table at the top of JOURNAL.md, and the render to
   `runs/<run>/README.md` if it exists.

## When to render or save
- Render after finishing a section and at the end of every shift. Do not render after every
  step: it moves the character and costs time.
- Save at the end of every shift and before anything risky (big rebuilds). Saves are cheap
  (about 1 s) and loadable in real Factorio 2.0.73+.
