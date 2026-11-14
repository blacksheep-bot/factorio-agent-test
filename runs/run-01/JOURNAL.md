# Run: run-01

- Started: 2026-11-14 · Orchestrator: Claude Code · Player: factorio-player subagent (skill: factorio-play)
- Start config: scenario `open_world` (seed 44340), inventory
  `{"iron-plate": 8, "wood": 1, "burner-mining-drill": 1, "stone-furnace": 1}`, research not
  pre-completed, REPL `--pause-between` (turn-based), game speed 10 while programs run.
- Saves: `.fle/saves/run-01-shift-NN.zip` · Renders: `renders/shift-NN.png`

## Timeline
| Shift | Goal | Result | Executions | Game tick | Milestones reached | Render |
|---|---|---|---|---|---|---|
| 01 | M0–M3 bootstrap, automated iron/copper/coal (+M3b) | DONE | 52 / 110 | 169206 | M0, M1, M2, M3, M3b (+steam-power & electronics triggers) | renders/shift-01.png |

## Known positions (keep this current)
| Section | Positions | Notes |
|---|---|---|
| resources | iron (-15.5,-50.5), copper (-28.5,-61.5), coal (40.5,-82.5), stone (60.5,-54.5), water (-14,34), trees (-9.25,47) | from `nearest()`. Copper patch overlaps iron around x -30..-22: pure copper is x -38..-26, y -82..-66 |
| coal_unit (belt source) | 7 burner drills (38..50 step 2, -95) facing DOWN onto belt; burner inserters at (cx-0.5,-93.5) refuel each drill from the belt | self-fuelling; belt saturated at the source |
| coal trunk belt | (50.5,-92.5) west to (-13.5,-92.5), down x=-14.5 to -70.5, west on y=-69.5 to -38.5, down x=-39.5, east on y=-62.5 to (-3.5,-62.5) (end) | ~600 coal on belts at end of shift 01 |
| iron_belt (vertical pairs) | drills (-20,-67),(-18,-67),(-16,-67) DOWN → furnaces (-19,-65),(-17,-65),(-15,-65) | fuel inserters from y=-69.5 (drills) and y=-62.5 (furnaces); end output chests (-21.5,-65.5),(-12.5,-65.5); middle furnace (-17,-65) has no output (hand-collect) |
| copper_belt (vertical pairs) | drills (-36,-67),(-34,-67),(-32,-67) → furnaces (-35,-65),(-33,-65),(-31,-65) | output chests (-37.5,-65.5),(-28.5,-65.5); middle (-33,-65) hand-collect |
| iron_belt2 (side-by-side pairs) | drills (-21,-60),(-17,-60),(-13,-60),(-9,-60) RIGHT → furnaces (-19,-60),(-15,-60),(-11,-60),(-7,-60) | fuel from belt y=-62.5; burner output inserters → chests (-18.5,-57.5),(-14.5,-57.5),(-10.5,-57.5),(-6.5,-57.5) |
| old hand-fed iron | drills (-19,-54),(-17,-54),(-14,-55),(-25,-61) → furnaces (-18,-52),(-16,-52),(-13,-53),(-24,-59) | HAND-FUELLED (≈50 coal/drill). Output chests (-18.5,-49.5),(-15.5,-49.5),(-12.5,-50.5),(-23.5,-56.5) |
| old copper | drills (-34,-74),(-31,-74) (HAND-FUELLED) → furnaces (-33,-72),(-30,-72) (belt-fuelled via inserters at (-32.5,-70.5),(-30.5,-70.5)) | output chests (-35.5,-72.5),(-27.5,-72.5) |
| coal chests (hand-fed drills) | pair (41,-84)↔(43,-84); drills (44,-86),(46,-86),(40,-89),(37,-89) → iron chests (44.5,-84.5),(46.5,-84.5),(40.5,-87.5),(37.5,-87.5) | buffer for hand refuelling; drills hand-fuelled |
| stone | drill (61,-58) → iron chest (61.5,-56.5) | hand-fuelled |
| idle | stone furnace (-9,-46) (bootstrap hand furnace) | can be picked up |

## Lessons (carry these forward)
- nearest(Resource.CopperOre) lands on mixed iron/copper ore; check `drill.resources` or scan with Lua before placing copper drills.
- Self-fuelling coal source: drill facing DOWN drops on a belt tile pointing DOWN into a westward belt; a burner inserter at (cx-0.5, drop row) picks from that belt and refuels the drill.
- `refuel_all()` also tops up self-fed coal drills and burner inserters, which wastes coal. Use targeted refuelling.
- Furnaces cap at 100 plates (`full_output`). Every furnace needs an output inserter → chest.
- Walking and hand-gathering use game time: one long gather program used minutes of fuel.

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
- Render: renders/shift-NN.png · Save: .fle/saves/run-01-shift-NN.zip
-->

## Shift 01 — M0–M3 bootstrap, automated iron/copper/coal (+M3b) — DONE
- Executions used: 52 / 110 (plus 3 renders, 1 save). Game tick: 169206 (~47 game-min).
- Milestones reached: M0 (positions stored, coal/stone gathered); M1 (iron +63/60s via produced(), drills/furnaces working); M2 (copper +98/60s measured in furnaces/chests; small-electric-pole enabled); M3 (coal chests 441→497 over 60s; 7 self-fuelled coal drills feed the belt); M3b (11 iron pairs, 5 copper pairs, 10 of them belt-fuelled).
- Built (name → positions): see the Known positions table. Coal belt loop from coal_unit (38..50,-95) to the smelting block at x -40..-3, y -70..-62. iron_belt 3 pairs, copper_belt 3 pairs, iron_belt2 4 pairs (all belt-fuelled). Old hand-fed lines have 4 iron pairs and 2 copper pairs. Coal drills → chests, plus a stone drill → chest.
- Works: the belt-fuelled lines (10 pairs) and the coal_unit run indefinitely, and the coal belt is saturated at the source. Broken/at risk: the hand-fuelled drills (old iron 4, old copper 2, coal-chest drills 4 + pair, stone drill) have ≈50 coal, about 20 game-min. Middle furnaces (-17,-65) and (-33,-65) have no output inserter and stop at 100 plates. The burner output inserters were given about 10–20 coal each and run dry eventually. Hand furnace (-9,-46) is idle.
- Inventory highlights: iron-plate≈1200, copper-plate≈1130, coal≈0–77, offshore-pump 1, boiler 1, steam-engine 2, pipe 20, small-electric-pole 6, lab 1, inserter 6, electronic-circuit 14, automation-science-pack 10, wood 0 (all used for poles).
- Research: researched=[steam-power, electronics], current=none, triggers iron 3698/50, copper 1897/10.
- Lessons / traps hit this shift: copper `nearest()` sits on mixed ore; refuel_all wastes coal on self-fed entities; furnaces cap at 100 output; a dead tree trunk blocked the belt path (harvest_resource needs move_to to the exact spot); production stat sometimes lags (copper read +2/min once, +98/min on the next check).
- NEXT: M4 steam power at water (-14,34) with the pre-crafted pump, boiler and 2 engines (recipe d). Then the lab (in inventory) plus 10 red packs → Automation. Fuel the boiler by belting coal or by refilling it. Swap burner output inserters for electric inserters once power reaches the smelting block (~100 tiles from water), or put the lab/assembly near water. Gather wood for more poles (trees at (-9,47)).
- Render: renders/shift-01.png (+ shift-01-smelting.png, shift-01-coal-stone.png) · Save: .fle/saves/run-01-shift-01.zip
