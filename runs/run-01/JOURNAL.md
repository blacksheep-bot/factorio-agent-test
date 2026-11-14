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
| 03 | Boiler SPOF, red ≥10/min, M10 green, auto research, tidy | DONE | 63 / 110 | 491637 | M10 (green 4.8/min, all inputs automated), red 12/min (red1 6.2 + red2 5.8), red+green research in 4 labs (automation-2 done, logistics-2 running), 2nd boiler+engine (2.7 MW) | renders/shift-03.png |

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
| circuits (M9) | copper chest (-19.5,-72.5) → ins → AM cable (-18.5,-75.5) → ins → AM circuit (-18.5,-79.5) → ins → chest (-18.5,-82.5). Iron: furnace (-12,-78) → ins (-11.5,-79.5) → chest (-11.5,-80.5) → long ins (-13.5,-80.5) over trunk → chest (-15.5,-80.5) → ins (-16.5,-80.5) → AM | ~17 circuits/min since shift 03 (removed the dead-end ins (-12.5,-76.5) that split furnace (-12,-78) output into chest (-12.5,-75.5)) |
| middle furnace fixes | long-handed ins (-16.5,-63.5) → chest (-16.5,-61.5) (iron); (-32.5,-63.5) → copper belt start | |
| boiler feed (shift 03) | electric inserter (1.5,-61.5) + original burner inserter (2.5,-61.5) both feed boiler1 from coal belt y=-62.5; pole (3.5,-61.5) | redundant feed |
| boiler2 + engine3 (shift 03) | water pipe (4.5,-60.5) chains boiler1 → boiler2 (6.5,-61) facing UP; steam pipes (6.5,-62.5),(7.5,-62.5) → engine3 (10.5,-62.5) horizontal. Fuel: elec ins (4.5,-63.5) from coal belt → iron chest (5.5,-63.5, bar=1 slot) → burner ins (5.5,-62.5) → boiler2. Pole (7.5,-64.5) | 3 engines = 2.7 MW |
| coal belt extension (shift 03) | trunk end (2.5,-62.5) now continues north x=3.5 (-62.5..-68.5), then west along y=-69.5 to (-7.5,-69.5) (end) | feeds new iron furnaces + boiler2; backed up (surplus) |
| new iron smelting (shift 03) | north row: elec drills (-6.5/-3.5/-0.5,-75.5) DOWN → furnaces (-6,-73),(-3,-73),(0,-73); out ins (x-0.5,-71.5) → iron belt; fuel long ins (x+0.5,-71.5) from coal y=-69.5. South row: elec drills (-6.5/-3.5/-0.5,-64.5) UP → furnaces (-6,-67),(-3,-67),(0,-67); fuel ins (x-0.5,-68.5) from coal; out long ins (x+0.5,-68.5) → iron belt. Poles (-4.5,-72.5),(1.5,-72.5),(-4.5,-66.5),(1.5,-66.5) | 6 furnaces ≈ 112 iron/min onto the science iron belt |
| science iron belt | y=-70.5 east from (-7.5,-70.5) to (37.5,-70.5); underground (9.5)→(11.5) under the copper column | |
| science copper belt | elec ins (-27.5,-73.5) takes from copper chest (-27.5,-72.5) → belt north x=-27.5 to -84.5, east y=-84.5 (underground (-15.5)→(-13.5) under the coal trunk), south x=10.5 to -70.5, east y=-69.5 to (33.5,-69.5) | chest is fed by electric copper furnace (-25,-72) + old furnace (-30,-72) |
| science block row1 (y=-73.5) | AM1s: C cable (12.5), E circuit (16.5), I inserter (20.5), G gear (24.5), B belt (28.5), R2 red (32.5), G2 gear (36.5). Belt feed ins at y=-71.5 (long for C and R2 = copper; regular = iron). Links at y=-73.5: 14.5→, 18.5→, 22.5← (G→I), 26.5→ (G→B), 34.5← (G2→R2). Poles at (14.5/18.5/22.5/26.5/34.5,-72.5) | |
| green (M10) | S logistic AM (24.5,-77.5). I → ins (21.5,-75.5) → chest (21.5,-76.5, bar 1 slot) → ins (22.5,-76.5) → S. B → ins (27.5,-75.5) → chest (27.5,-76.5, bar 1 slot) → ins (26.5,-76.5) → S. S → ins (24.5,-79.5) → lab L1 | ~4.8/min (AM1 cap 5) |
| labs (shift 03) | L-1 (16.5,-81.5), L0 (20.5,-81.5), L1 (24.5,-81.5), L2 (28.5,-81.5). Links: (26.5,-81.5) L1→L2, (26.5,-82.5) L2→L1, (22.5,-81.5) L1→L0, (18.5,-81.5) L0→L-1. Red2: ins (31.5,-75.5) → belt x=31.5 (-76.5..-80.5) → ins (30.5,-80.5) → L2 | research red+green automatically |

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

## Shift 03 — boiler SPOF, red ≥10/min, M10 green science, automatic red+green research, tidy-up — DONE
- Executions used: 63 / 110 (60 code + 2 renders + 1 save; plus 1 pre-boiler2 safety save). Game tick: 491637 (~136 game-min).
- Milestones reached: goal 1 (boiler1 now has an electric inserter (1.5,-61.5) in addition to the burner one; boiler fuel stays 5, power 45–52% of 2.7 MW); goal 2 red 12/min total (products_finished over 7496 ticks: red1 +13 = 6.2/min, red2 +12 = 5.8/min); M10 green 4.8/min (S products_finished +10 over 125 s; AM1 cap is 5/min), every ingredient is inserter-fed from belts that are fed by drills→furnaces (iron) and furnace→chest→inserter (copper); goal 4: 4 labs take red+green automatically, automation-2 researched, logistics-2 at 31%, queue = logistics-2, electric-energy-distribution-1, advanced-material-processing; goal 5: circuit block iron doubled (~7 → 17 circuits/min) and a 2nd boiler + 3rd engine added (capacity 1.8 → 2.7 MW).
- Built (name → positions): see Known positions rows "boiler feed" through "labs (shift 03)". Science block spans x 11..38, y -84..-69; new iron smelting x -8..2, y -77..-63.
- Works: coal belt is backed up to its very end (4 items/tile on the x=3.5 and y=-69.5 segments) after adding 6 furnaces + boiler2. All 13 new science-block AMs/labs and 6 furnaces were checked WORKING or output-full. Broken/at risk: the hand-fuelled drills (old iron (-25,-61),(-19,-54),(-17,-54),(-14,-55), old copper (-34,-74),(-31,-74), coal-chest drills, stone (61,-58)) were refilled with 40 coal at tick ~477k, which lasts about 18 game-min. They are optional (no new chain depends on them). The old red-only lab (-6.5,-42.5) is idle because every queued tech needs green; red1 packs pile up in chest (-6.5,-45.5) (harmless).
- Inventory highlights: coal=572, iron-plate=1195, copper-plate=1127, transport-belt=12, lab=2 (spare), small-electric-pole=4, wood=6, stone=179.
- Research: researched=[automation, automation-2, electric-mining-drill, electronics, fast-inserter, logistic-science-pack, logistics, steam-power, steel-processing], current=logistics-2 (31%), triggers iron 22289/50 copper 10166/10.
- Lessons / traps hit this shift: (1) `advance(N)` runs only about 0.75·N game seconds (advance(120) = 5410 ticks). Measure rates from tick deltas plus `assembler.products_finished` via lua, not from produced() over advance(N). (2) FLE `place_entity(UndergroundBelt)` always makes an INPUT. Rotating it in lua flips the direction too, and setting `.direction` resets it. Working fix: place it with FLE, then in lua `destroy()` and `create_entity{name='underground-belt', type='output', direction=defines.direction.east, force='player'}` (that is what FLE's connect_entities does). No `game.players[1]` exists in FLE. (3) Unbounded relay chests between AMs swallow intermediates (53 belts, 38 inserters) and starve the line. Limit them with lua `inv.set_bar(2)` (one slot). (4) `place_new(Prototype.Lab, …)` or `place_entity(Lab)` can raise "[-2]" AFTER the lab was actually placed. Check with lua `can_place_entity`/find_entity before retrying. (5) An electric drill facing UP drops at y-2 of its centre; place the furnace explicitly at (x+0.5, y-2.5), not at `drop_position` (it overlaps the drill). (6) A dead-tree trunk and a big rock blocked labs; `harvest_resource` at the exact position after `move_to` next to it works.
- NEXT: raise green to 10/min with a second logistic AM. The I and B relay chests (21.5,-76.5)/(27.5,-76.5) can't reach a 2nd S, so build a second I+B+S trio east of x=40 (or north at y≈-90) off the same iron/copper belts (extend the iron belt past 37.5). Iron supply (112/min) and circuits (E idles at full_output) have headroom. A third red AM is also needed to keep red at 1:1. Later: electric-energy-distribution-1 → medium poles; steel furnaces after advanced-material-processing.
- Render: renders/shift-03.png (+ shift-03-science.png) · Save: .fle/saves/run-01-shift-03.zip
