# factorio-agent-test

A Claude Code agent that plays Factorio 2.0.73 through the Factorio Learning Environment (FLE).
A headless server runs FLE's Lua tools over RCON. `setup/fle_repl.py` keeps one long-lived
`FactorioInstance` behind HTTP :8765, and agents send it Python snippets with
`python3 setup/fle_exec.py`. The plan is in `docs/PLAN.md`; the research notes are in `docs/research/`.

- Skill: `.claude/skills/factorio-play/SKILL.md` (play loop, rules), with `references/api.md`,
  `strategy.md` and `recipes.md`.
- Subagent: `.claude/agents/factorio-player.md` (plays one shift).
- Helpers: `agent/helpers.py`, auto-loaded into the REPL namespace. Reload with
  `python3 setup/fle_exec.py agent/helpers.py`.
- Runs: `runs/<name>/` (`JOURNAL.md`, `renders/`, `README.md`). Saves go to `.fle/saves/`.
  Copy the template from `runs/_template/`.

## Recommended start config (tested)
- **Scenario `open_world`** (seed 44340). Every resource is within 100 tiles of spawn: iron
  53, copper 68, stone 81, coal 92, water 37, trees 48. `default_lab_scenario` also has
  everything, but it is a tiny, artificial lab map.
- **Inventory** `{"iron-plate": 8, "wood": 1, "burner-mining-drill": 1, "stone-furnace": 1}`
  (the vanilla freeplay kit, minus the pistol and ammo).
- **Research not pre-completed** (the REPL default; `--all-tech` would research everything).
  FLE pre-researches only `automation-science-pack`. Craftable at start: burner drill, stone
  furnace, gear, burner inserter, belt, wooden/iron chest, red science pack. Pipe, offshore
  pump, boiler and steam engine unlock after **50 iron plates are smelted**; copper cable,
  circuit, inserter, small pole and lab after **10 copper plates**; assembling machine 1
  after **Automation** (10 red packs in a lab). All of this was verified live.
- **Turn-based clock: `--pause-between`.** The game is paused except while a program runs,
  so LLM think time does not burn fuel. With the default continuous mode at speed 10, a
  burner drill ran dry between two agent turns.
- Enemies: FLE removes biters on connect, and `make_peaceful()` (run when the helpers load)
  also removes worms and sets peaceful mode.

## Bring up the stack
**Host scripts** (this is what the kit was built and tested with):
```bash
bash setup/install.sh                      # once: venv, FLE 0.4.3, sprites, docker image
setup/start_server.sh open_world           # headless server, container fle_factorio_0, RCON :27000
nohup .venv/bin/python -W ignore setup/fle_repl.py --fresh --pause-between \
  --inventory '{"iron-plate": 8, "wood": 1, "burner-mining-drill": 1, "stone-furnace": 1}' \
  > .fle/repl.log 2>&1 &                   # NEW RUN ONLY (--fresh wipes built entities)
python3 setup/fle_exec.py --status
```
**Docker compose** (`docker-compose.yml`, `docker/`, `Makefile`; see README "Quick start"):
`FLE_FRESH=1 docker compose up -d --build` for a new run. The compose defaults are already
open_world, the inventory above, and `FLE_PAUSE_BETWEEN=1`. For later restarts use
`FLE_FRESH=0`. If `helpers_help()` raises NameError in the container, run
`python3 setup/fle_exec.py agent/helpers.py`: the helpers are sent over HTTP, so this always
works.

**Restarting the REPL mid-run** (it died or hung):
`pkill -f setup/fle_repl.py; nohup .venv/bin/python -W ignore setup/fle_repl.py --pause-between > .fle/repl.log 2>&1 &`
Never pass `--fresh` here. Without it, the REPL keeps entities and snapshots and restores
research, inventory and position (FLE's connect would otherwise reset them). Python
variables are lost; the helpers are reloaded. After a server restart use
`python3 setup/fle_exec.py --reinit`.
Resume from a save: `FLE_SAVE=<name> setup/start_server.sh`, then restart the REPL as above.

## Starting a run
1. Bring the stack up with the recommended config (the `--fresh` REPL start).
2. `mkdir -p runs/<name>/renders && cp runs/_template/JOURNAL.md runs/<name>/`, then fill in
   the header.
3. Run the orchestrator protocol below.

## Orchestrator protocol
You (the main session) do not play. You run shifts:
1. Launch **one** `factorio-player` subagent at a time, never in parallel: there is one
   character and one REPL. Its prompt names: the run dir, the shift number NN, the milestone
   goal (strategy.md ladder M1→M9), and a budget (60–120 executions).
2. When it returns, read the newest handoff in `runs/<name>/JOURNAL.md`. Check that the
   render and save exist and look at the PNG. If the shift left no save, save it yourself:
   `python3 setup/fle_exec.py --save <name>-shift-NN`.
3. Optionally verify the claimed milestone yourself:
   `python3 setup/fle_exec.py -c 'status_report(show_ok=False)'`.
4. Choose the next goal. If the milestone is DONE, take the next rung. If it is PARTIAL,
   repeat it with the handoff's NEXT step. If it is BLOCKED twice on the same thing, change
   the goal or give a concrete hint from the lessons.
5. Keep `runs/<name>/README.md` as a gallery: one render per shift, with a one-line caption.
6. At the end, make a final save `<name>-final`, record the timeline in JOURNAL.md, and copy
   the final save into `runs/<name>/` if the user wants it in the repo.

## Conventions
- Never commit `.fle/`, `.venv/` or `.vendor/` (they are gitignored).
- Treat `setup/fle_repl.py` CLI flags and HTTP endpoints as a stable interface (the Docker
  image uses them).
