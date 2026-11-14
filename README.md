# factorio-agent-test

A Claude Code agent that plays Factorio 2.0.73 through the
[Factorio Learning Environment](https://github.com/JackHopkins/factorio-learning-environment) (FLE).
A headless server runs FLE's Lua tools over RCON. A persistent Python REPL
(`setup/fle_repl.py`, HTTP on 127.0.0.1:8765) holds one `FactorioInstance`, and agents send it
code with `python3 setup/fle_exec.py`. See `docs/PLAN.md` and `docs/research/`.

## Quick start (Docker)
You only need Docker (with Compose v2) and any `python3` for the stdlib-only client.
```bash
docker compose up -d --build --wait     # first build ~5-10 min (downloads ~370 MB of sprites)
python3 setup/fle_exec.py -c 'print(inspect_inventory()); print(nearest(Resource.IronOre))'
python3 setup/fle_exec.py --render runs/demo/base.png --radius 20   # PNG lands in the repo
python3 setup/fle_exec.py --save mysave                             # -> .fle/saves/mysave.zip
FLE_SAVE=mysave docker compose up -d --force-recreate --wait        # restart from that save
docker compose down                                                  # saves stay in .fle/saves
```
Or use the `Makefile`: `make up`, `make down`, `make logs`, `make status`,
`make render OUT=runs/x/a.png [X= Y= R=20]`, `make save NAME=x`, `make load SAVE=x`,
`make reset [SCENARIO=default_lab_scenario]` (fresh map, wipes the live world).

Services: `factorio` (factoriotools/factorio:2.0.73 with FLE's scenarios and config baked in,
autosave off, RCON on 127.0.0.1:27000, game UDP 34197) and `fle` (the REPL on
127.0.0.1:8765). Settings are environment variables, set in your shell or in `.env`:

| var | default | meaning |
|---|---|---|
| `FLE_SCENARIO` | `open_world` | or `default_lab_scenario` (ignored when `FLE_SAVE` is set) |
| `FLE_SAVE` | (none) | load `.fle/saves/<name>.zip` instead of the scenario |
| `FLE_INVENTORY` | freeplay kit JSON | starting inventory (applied only on a fresh start) |
| `FLE_FRESH` | `0` | `1` = wipe player-built entities when the REPL connects |
| `FLE_PAUSE_BETWEEN` | `1` | turn-based clock: the game is paused except while a program runs |
| `FLE_ALL_TECH` | `0` | `1` = research everything on connect |
| `FLE_DATA_DIR` | `./.fle` | host dir for `saves/` (and `renders/` for paths outside the repo) |
| `FLE_REPL_PORT`, `FLE_RCON_HOST_PORT`, `FLE_GAME_PORT` | 8765, 27000, 34197 | host ports |

Notes:
- Saves must go through `fle_exec.py --save` (or `make save`). A plain Factorio save or an
  autosave crashes the server, because FLE keeps Lua functions in `storage`; the REPL works
  around this. Open a `.zip` in the real game via Single player → Load game, or join the
  server on UDP 34197.
- Render/copy paths inside the repo are written through the `/workspace` mount. Other paths
  fall back to `$FLE_DATA_DIR/renders/`. Files written by the containers are owned by root
  (saves by uid 845).
- If you are behind a TLS-intercepting proxy, set `FLE_EXTRA_CA=/path/to/ca.pem` for the
  build. It is passed as a build secret and is not stored in the image.
- Non-Docker alternative: `bash setup/install.sh`, then `setup/start_server.sh` and
  `setup/fle_repl.py` (see `CLAUDE.md` and `docs/research/fle-setup-and-api.md`).

## Playing with Claude Code
The kit: the skill `.claude/skills/factorio-play/` (play loop, API traps, strategy, proven
code), the subagent `.claude/agents/factorio-player.md` (plays one shift), helpers in
`agent/helpers.py`, and the orchestrator protocol in `CLAUDE.md`.

**Start a run.** Bring the stack up fresh (`FLE_FRESH=1 docker compose up -d --build --wait`),
open Claude Code in the repo, and give it a prompt like:
> Start a new Factorio run called run-02 following CLAUDE.md. Be the orchestrator: play
> 3 shifts with a budget of 110 executions each, one subagent at a time, aiming for
> automated red and green science. Verify each shift yourself and keep the run README gallery.

The main session plays no shifts itself. It launches one player subagent per shift (a
general-purpose one told to read `factorio-player.md` if the agent type was created in this
session), reads its handoff, checks production, and picks the next goal.

**Outputs** go to `runs/<name>/`: `JOURNAL.md` (timeline, known positions, lessons and one
handoff per shift), `renders/shift-NN.png`, `saves/<name>-shift-NN.zip`, and a `README.md`
gallery. See [`runs/run-01/`](runs/run-01/) for a 3-shift example that reached automated red
and green science, research and steam power.

**View them.**
- Renders: open the PNGs.
- Saves in real Factorio 2.0 (2.0.73 or newer): copy the `.zip` into your Factorio saves
  directory (`~/.factorio/saves/` on Linux, `%APPDATA%\Factorio\saves\` on Windows,
  `~/Library/Application Support/factorio/saves/` on macOS), then Single player → Load game.
- Or resume one on the server: copy it to `.fle/saves/`, then
  `FLE_SAVE=run-01-shift-03 docker compose up -d --force-recreate --wait` (name without `.zip`).
