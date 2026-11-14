# Plan: a Claude agent that plays Factorio through FLE

## Goal
1. **Boilerplate**: `docker compose up` starts a headless Factorio 2.0.73 server and an FLE client
   container that runs a persistent Python REPL. A Claude Code agent then drives it using the
   skill and agent files in this repo.
2. **A played game**: one real session played by the agent, starting from a vanilla-like
   freeplay inventory. It produces renders (PNGs) of what was built, a timeline, and a
   Factorio save file you can open in the real game.

## Architecture
```
Claude Code (orchestrator)
   └─ factorio-player subagent(s)  ── follow .claude/skills/factorio-play/SKILL.md
          │  bash: python3 setup/fle_exec.py -c '<python snippet>'
          ▼
   fle_repl.py (HTTP :8765, one long-lived FactorioInstance; namespace persists)
          │  RCON :27000
          ▼
   factoriotools/factorio:2.0.73 headless server (FLE Lua tools injected over RCON)
```

The agent writes small Python programs against FLE's tool API (`nearest`, `move_to`,
`harvest_resource`, `craft_item`, `place_entity`, `connect_entities`, `insert_item`, ...).
It prints state, checks the result, and moves on to the next step. This matches FLE's own
"code-as-policy" REPL design, but the policy is a Claude Code subagent instead of FLE's
built-in LLM loop.

## Agent kit (what we ship)
- `CLAUDE.md`: entry point that explains how to bring the stack up and play.
- `.claude/skills/factorio-play/SKILL.md`: the play loop, golden rules and failure modes,
  with references:
  - `references/api.md`: a condensed, tested API cheat-sheet (signatures, gotchas).
  - `references/strategy.md`: build order, ratios and milestones with checks you can run
    in code (taken from docs/research/factorio-strategy.md).
  - `references/recipes.md`: known-good code snippets (drill→furnace pair, power plant,
    assembler line, lab), each verified against the live server.
- `.claude/agents/factorio-player.md`: subagent definition (tools: Bash/Read/Write; points at
  the skill).
- `agent/helpers.py`: helper functions loaded into the REPL namespace (factory status
  report, refuel all, find build spot, etc.).
- `runs/<run-name>/`: per-run journal (`JOURNAL.md`), `renders/`, `saves/`, `state.json`.

## Play protocol (context-bounded sessions)
A single subagent can't play for hours, because its context window fills up. So the game is
played in **shifts**:
- Each shift is a fresh `factorio-player` subagent with one milestone goal and a step budget
  (about 60–120 code executions).
- At the end of a shift it writes a handoff in the run's `JOURNAL.md` (what exists and where,
  what works, what's broken, the next step), renders the base and saves the game.
- The orchestrator reads the handoff and launches the next shift.
- Milestones (strategy doc M1→M9): automated iron → copper → coal/stone → steam power →
  lab and research → automated gears → automated red science → electric mining →
  circuits.

## Visualising
- `fle_exec.py --render` produces a PNG centred on a point, after every shift.
- `fle_exec.py --save` produces a `.zip` you can load in real Factorio (single player → Load
  game), or restart the server from it with `FLE_SAVE=name`.
- `runs/<run>/README.md` collects a gallery of renders per shift.
