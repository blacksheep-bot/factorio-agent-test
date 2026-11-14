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
| 02 | Fix at-risk, M4 steam, M5 Automation, M6 gears, M7 red | DONE | 68 / 110 | 354114 | M4, M5, M6, M7 (~5-6/min), M8 (7 electric drills, boiler belt-fed), M9 (circuits ~7/min) | renders/shift-02.png |

## Known positions (keep this current)
| Section | Positions | Notes |
|---|---|---|
| resources | iron (-15.5,-50.5), copper (-28.5,-61.5), coal (40.5,-82.5), stone (60.5,-54.5), water (-14,34), trees (-9.25,47) | from `nearest()`. Copper patch overlaps iron around x -30..-22: pure copper is x -38..-26, y -82..-66 |
| coal_unit (belt source) | 7 burner drills (38..50 step 2, -95) facing DOWN onto belt; burner inserters at (cx-0.5,-93.5) refuel each drill from the belt | self-fuelling; belt saturated at the source |
| coal trunk belt | (50.5,-92.5) west to (-13.5,-92.5), down x=-14.5 to -70.5, west on y=-69.5 to -38.5, down x=-39.5, east on y=-62.5 to (-3.5,-62.5) (end) | ~600 coal on belts at end of shift 01 |
| iron_belt (vertical pairs) | drills (-20,-67),(-18,-67),(-16,-67) DOWN → furnaces (-19,-65),(-17,-65),(-15,-65) | fuel inserters from y=-69.5 (drills) and y=-62.5 (furnaces); end output chests (-21.5,-65.5),(-12.5,-65.5); middle furnace (-17,-65) has no output (hand-collect) |
| copper_belt (vertical pairs) | drills (-36,-67),(-34,-67),(-32,-67) → furnaces (-35,-65),(-33,-65),(-31,-65) | output chests (-37.5,-65.5),(-28.5,-65.5); middle (-33,-65) hand-collect |
| iron_belt2 (side-by-side pairs) | drills (-21,-60),(-17,-60),(-13,-60),(-9,-60) RIGHT → furnaces (-19,-60),(-15,-60),(-11,-60),(-7,-60) | fuel from belt y=-62.5; ELECTRIC output inserters (shift 02) → chests (-18.5,-57.5),(-14.5,-57.5),(-10.5,-57.5),(-6.5,-57.5) |
| old hand-fed iron | drills (-19,-54),(-17,-54),(-14,-55),(-25,-61) → furnaces (-18,-52),(-16,-52),(-13,-53),(-24,-59) | HAND-FUELLED (refilled to 50 at end of shift 02). Output chests (-18.5,-49.5),(-15.5,-49.5),(-12.5,-50.5),(-23.5,-56.5) |
| old copper | drills (-34,-74),(-31,-74) (HAND-FUELLED) → furnaces (-33,-72),(-30,-72) (belt-fuelled via inserters at (-32.5,-70.5),(-30.5,-70.5)) | output chests (-35.5,-72.5),(-27.5,-72.5) |
| coal chests (hand-fed drills) | pair (41,-84)↔(43,-84); drills (44,-86),(46,-86),(40,-89),(37,-89) → iron chests (44.5,-84.5),(46.5,-84.5),(40.5,-87.5),(37.5,-87.5) | buffer for hand refuelling; drills hand-fuelled |
| stone | drill (61,-58) → iron chest (61.5,-56.5) | hand-fuelled |
| power plant (shift 02) | offshore pump (-12.5,34.5) → 172-pipe water line north along x=0.5 → boiler (2.5,-60) DOWN; steam → engine1 (2.5,-54.5) vertical, engine2 (7.5,-57.5) horizontal via pipes (3.5,-57.5),(4.5,-57.5) | boiler fed by burner inserter (2.5,-61.5) from coal trunk extended east to (2.5,-62.5). Nothing may touch the water pipe at y=-46.5 / x=0.5 |
| poles | network from (5.5,-52.5)/(-0.5,-55.5) west along y=-57.5, -61.5, -64.5 over the smelting block; north column x=-11.5 (-76.5,-72.5,-68.5); line (10.5,-56.5)…(50.5,-88.5) to coal field | one network, 2 engines = 1.8 MW |
| gears (M6) | furnace (-7,-60) → elec inserter (-6.5,-58.5) → chest (-6.5,-57.5) → ins (-6.5,-56.5) → AM1 gears (-6.5,-54.5) → ins → chest (-6.5,-51.5). Boost: chest (-10.5,-57.5) → ins (-10.5,-56.5) → belt (-10.5..-9.5,-55.5) → ins (-8.5,-55.5) → AM | gear chest also feeds red AM |
| red science (M7) | gear chest (-6.5,-51.5) → ins (-6.5,-50.5) → AM1 red (-6.5,-48.5); copper belt from long inserter (-32.5,-63.5) (middle copper furnace) staircase to (-9.5,-48.5) → ins (-8.5,-48.5); out ins → chest (-6.5,-45.5) → ins (-6.5,-44.5) → lab (-6.5,-42.5) | research runs automatically (queue via lua add_research) |
| electric iron (M8) | 3 modules: elec drill (-9.5,-77.5/-73.5/-69.5) LEFT → furnace (-12,-78/-74/-70); fuel burner ins (-13.5,y-0.5) from trunk x=-14.5; out ins (-12.5,y+1.5) → chests (-12.5,-75.5/-71.5/-67.5) | |
| electric copper (M8) | drills (-25.5,-74.5),(-22.5,-74.5) DOWN → furnaces (-25,-72),(-22,-72); fuel ins (-25.5,-70.5),(-22.5,-70.5) from belt y=-69.5; outputs → old chest (-27.5,-72.5) and chest (-19.5,-72.5) | |
| electric coal (M8) | drills (48.5,-89.5),(48.5,-86.5) RIGHT → chests (50.5,-89.5),(50.5,-86.5) | coal buffer for hand refuelling |
| circuits (M9) | copper chest (-19.5,-72.5) → ins → AM cable (-18.5,-75.5) → ins → AM circuit (-18.5,-79.5) → ins → chest (-18.5,-82.5). Iron: furnace (-12,-78) → ins (-11.5,-79.5) → chest (-11.5,-80.5) → long ins (-13.5,-80.5) over trunk → chest (-15.5,-80.5) → ins (-16.5,-80.5) → AM | ~7 circuits/min, iron-limited |
| middle furnace fixes | long-handed ins (-16.5,-63.5) → chest (-16.5,-61.5) (iron); (-32.5,-63.5) → copper belt start | |

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

## Shift 02 — fix at-risk, M4 steam, M5 Automation, M6 gears, M7 red science — DONE
- Executions used: 68 / 110 (63 code + 4 renders + 1 save). Game tick: 354114 (~98 game-min).
- Milestones reached: M4 (2 engines WORKING, boiler WORKING, belt-fed); M5 (automation researched, then electric-mining-drill, logistics, steel-processing; logistic-science-pack 73% running off automated red); M6 (gear chest 391→436 over 120 s, 54 gears made/2 min, no manual inserts); M7 (red 10/2 min = 5/min, AM1 cap is 6/min); M8 (7 electric drills: 3 iron, 2 copper, 2 coal; boiler fuel 5 after long advances, fed from belt); M9 bonus (circuits 15/2 min into chest (-18.5,-82.5)).
- Built (name → positions): see the Known positions table, rows from "power plant" down. The boiler is AT THE BASE (2.5,-60), not at the water: a 172-pipe line runs from pump (-12.5,34.5) and the coal trunk was extended east 6 tiles to feed it.
- Works: everything belt-fed or electric, and research keeps running automatically. Broken/at risk: boiler feeder is a burner inserter (2.5,-61.5); it dropped to fuel 1 once and was topped to 21 (watch it, or swap for an electric inserter). Middle copper furnace (-33,-65) shows full_output when the copper belt backs up (harmless). The old hand-fed lines (4 iron drills, 2 copper drills, stone drill (61,-58), burner output inserters (-23.5,-57.5),(-18.5,-50.5),(-15.5,-50.5),(-12.5,-51.5),(-34.5,-72.5),(-28.5,-72.5)) were refilled to 50/20 coal at the end, enough for about 20 game-min.
- Inventory highlights: coal=1087 (buffer for hand-fed lines), iron-plate=604, copper-plate=1347, stone=184, transport-belt=17, pipe=16, small-electric-pole=3, wood=0.
- Research: researched=[automation, electric-mining-drill, electronics, logistics, steam-power, steel-processing], current=logistic-science-pack (queued via lua; fast-inserter queued after), triggers iron 12656/50 copper 6732/10.
- Lessons / traps hit this shift: (1) A water pipe touching a steam engine's far connection floods engine and steam pipe with water, and the lab gets NO_POWER. Fix: remove the touching engine, then clear the fluids with lua `fluidbox[1]=nil` (flush() did not help). (2) The FLE `get_entity(Prototype.Lab, …)` raises `'list' object has no attribute 'items'`, so read the lab via lua. (3) `x0,y0,x1,y1 = 5.5,-52.5,50.5,-88.5` in the REPL left x0=702, x1=801 and placed 9 poles at x≈700-800. Use separate assignments and print values before placing. (4) A generic refuel loop pours coal into belt-fed entities first; list the hand-fed entities explicitly. (5) connect_entities for poles asked for 20 poles over 58 tiles; placing them by hand every ~6.4 tiles used 9. (6) `set_research` lacks an enum for electric-mining-drill, so use `lua("game.forces.player.add_research('…')")`.
- NEXT: raise red science (2nd red AM near (-3.5,-48.5) with its own gear feed) and the circuit iron supply, then build green science (logistic-science-pack research is finishing): inserter + belt from the gear chest. Consider an electric inserter on the boiler (2.5,-61.5) and more electric coal drills dropping onto the trunk at (52.5,-92.5) once consumption rises.
- Render: renders/shift-02.png (+ shift-02-power.png, shift-02-coal.png, shift-02-pump.png) · Save: .fle/saves/run-01-shift-02.zip
