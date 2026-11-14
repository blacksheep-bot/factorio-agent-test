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
- Runs: `runs/<name>/` (`JOURNAL.md`, `renders/`, `saves/`, `README.md`). Saves are written
  to `.fle/saves/` (gitignored) and copied into `runs/<name>/saves/` with `--copy-to`.
  Copy the template from `runs/_template/`. Example: `runs/run-01/`.

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
2. `mkdir -p runs/<name>/renders runs/<name>/saves && cp runs/_template/JOURNAL.md runs/<name>/`,
   then fill in the header.
3. Run the orchestrator protocol below.

## Orchestrator protocol
You (the main session) do not play. You run shifts, one at a time, never in parallel: there
is one character and one REPL.
1. **Launch a shift.** If the `factorio-player` agent type is available, use it. Custom agent
   types in `.claude/agents/` are only loaded when a Claude Code session starts, so in the
   session that created or edited them launch a **general-purpose** subagent instead and tell
   it: "Your role is defined in `.claude/agents/factorio-player.md`; read it first and follow
   it." Either way the prompt names the run dir, the shift number NN, the milestone goal
   (strategy.md ladder M0→M11, plus the previous handoff's NEXT and any at-risk items), and a
   budget. Run-01 used a budget of 110; shifts used 50–70 executions and each cleared 3–5
   milestones, so give 3–5 milestones per shift.
2. **Read the handoff** when it returns (newest block in `runs/<name>/JOURNAL.md`). Check
   that the render exists and look at the PNG. Check that the save is in
   `runs/<name>/saves/<name>-shift-NN.zip` (committed with the run). If not, save it yourself:
   `python3 setup/fle_exec.py --save <name>-shift-NN --copy-to runs/<name>/saves/<name>-shift-NN.zip`.
3. **Verify independently** with a production delta. Do not trust the claimed rates:
   `python3 setup/fle_exec.py -c 'rate([Prototype.IronPlate, Prototype.AutomationSciencePack, Prototype.LogisticsSciencePack], 60); lab_report(); power_report()'`
   (one execution; it lets 60 game-s pass, which is harmless).
4. **Choose the next goal.** If the milestone is DONE, take the next rungs. If it is PARTIAL,
   repeat it with the handoff's NEXT step. If it is BLOCKED twice on the same thing, change
   the goal or give a concrete hint from the lessons. Pass on the "Broken/at risk" items.
5. Keep `runs/<name>/README.md` as a gallery: one render per shift, with a one-line caption.
6. At the end, record the timeline in JOURNAL.md and fold new traps and patterns from the
   handoffs' "Lessons" back into the skill (api.md, SKILL.md, recipes.md) and helpers.

## Conventions
- Never commit `.fle/`, `.venv/` or `.vendor/` (they are gitignored).
- Treat `setup/fle_repl.py` CLI flags and HTTP endpoints as a stable interface (the Docker
  image uses them).
