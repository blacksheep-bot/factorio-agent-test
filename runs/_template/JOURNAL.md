# Run: <run-name>

- Started: <date> · Orchestrator: Claude Code · Player: factorio-player subagent (skill: factorio-play)
- Start config: scenario `open_world` (seed 44340), inventory
  `{"iron-plate": 8, "wood": 1, "burner-mining-drill": 1, "stone-furnace": 1}`, research not
  pre-completed, REPL `--pause-between` (turn-based), game speed 10 while programs run.
- Saves: `saves/<run>-shift-NN.zip` (copied from `.fle/saves/`) · Renders: `renders/shift-NN.png`

## Timeline
| Shift | Goal | Result | Executions | Game tick | Milestones reached | Render |
|---|---|---|---|---|---|---|
| 01 | M1 automated iron | | | | | renders/shift-01.png |

## Known positions (keep this current)
| Section | Positions | Notes |
|---|---|---|
| resources | iron …, copper …, coal …, stone …, water …, trees … | from `nearest()` |

## Lessons (carry these forward)
- …

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
- Render: renders/shift-NN.png · Save: saves/<run>-shift-NN.zip
-->
