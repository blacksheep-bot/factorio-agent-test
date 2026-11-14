# Run: smoke-test (agent-kit validation, 2026-11-14)

- Started: 2026-11-14 · Orchestrator: Claude Code · Player: factorio-player subagent (skill: factorio-play)
- Start config: scenario `open_world` (seed 44340), inventory
  `{"iron-plate": 8, "wood": 1, "burner-mining-drill": 1, "stone-furnace": 1}`, research not
  pre-completed, REPL `--pause-between` (turn-based), game speed 10 while programs run.
- Saves: `.fle/saves/smoke-test-shift-NN.zip` · Renders: `renders/shift-NN.png`

## Timeline
| Shift | Goal | Result | Executions | Game tick | Milestones reached | Render |
|---|---|---|---|---|---|---|
| 01 | M1 automated iron | DONE | 15 | 243694 | M0, M1 (45 iron/min) | renders/shift-01.png |

## Known positions (keep this current)
| Section | Positions | Notes |
|---|---|---|
| resources | iron (-15.5,-50.5), copper (-28.5,-61.5), coal (40.5,-82.5), stone (60.5,-54.5), water (-14,34), trees (-10.5,50) | from `nearest()` |
| iron_smelting | drills (-19,-54),(-17,-54),(-15,-55) → furnaces (-18,-52),(-16,-52),(-14,-53) | burner drill drops straight into furnace |

## Lessons (carry these forward)
- Crafting a burner drill CONSUMES a stone furnace from inventory. Keep 1 furnace spare per pair.
- place_entity can return the neighbouring same-type entity. Use `place_new()` / `place_drill_furnace()`.
- Coal is the bottleneck. Three pairs plus refuels used about 130 hand-mined coal. Automate coal next (M3).

---
<!-- Handoffs are appended below, newest last, in the format from SKILL.md:

## Shift NN — <milestone goal> — <DONE | PARTIAL | BLOCKED>
- Executions used: N / budget. Game tick: T.
- Milestones reached: ...
- Built (name → positions): ...
- Works: ... Broken/at risk: ...
- Inventory highlights: ...
- Research: researched=[...], current=..., triggers iron …/50 copper …/10
- Lessons / traps hit this shift: ...
- NEXT: ...
- Render: renders/shift-NN.png · Save: .fle/saves/<run>-shift-NN.zip
-->

## Shift 01 — M1 automated iron — DONE
- Executions used: 15 / 25 (2 of them were diagnostics). Game tick: 243694.
- Milestones reached: M0 (40 coal, 25 stone, positions stored); M1 (check_growth iron = +45 / 60 s, 3 drills and 3 furnaces working).
- Built: iron_smelting: drills (-19,-54),(-17,-54),(-15,-55) → furnaces (-18,-52),(-16,-52),(-14,-53).
- Works: all 3 pairs; about 40 plates are waiting in each furnace. At risk: fuel is about 15-25 per entity (about 7 game-min for drills), and there is 0 coal in inventory.
- Inventory highlights: iron-plate=23, stone=9, wood=1, coal=0.
- Research: researched=[steam-power] (fired by smelting); electronics trigger 0/10 copper.
- Lessons / traps hit this shift: the drill-crafting-consumes-furnace trap; place_entity returning a neighbour (fixed in helpers by place_new).
- NEXT: M2. Collect plates, craft drill and furnace pairs, and place 1-2 on copper near (-28.5,-61.5) to fire electronics. Then build a coal pair at (40.5,-82.5).
- Render: renders/shift-01.png · Save: .fle/saves/smoke-test-shift-01.zip
