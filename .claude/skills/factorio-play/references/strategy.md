# Strategy: build order, ratios, milestone ladder (Factorio 2.0, this setup)

The source is `docs/research/factorio-strategy.md`, condensed and adapted to our start:
scenario `open_world`, inventory `{"iron-plate": 8, "wood": 1, "burner-mining-drill": 1,
"stone-furnace": 1}`, research NOT pre-completed, turn-based clock.

## Map facts (open_world, seed 44340; distances from spawn (0,0))
iron (-15,-50) about 53 tiles, patch about 6.7M · copper (-28,-61) about 68 · stone (60,-54) about 81 ·
coal (40,-82) about 92 · water (-14,34) about 37 · trees (-9,47) about 48. Iron and copper are close
together NW of spawn, and coal and stone are NE. Water and trees are south. Worms were removed by
`make_peaceful()`.

## Numbers to remember
| Thing | Rate |
|---|---|
| Burner drill | 0.25 ore/s = 15/min; burns about 2.25 coal/min (20 coal ≈ 9 min) |
| Stone furnace | 18.75 plates/min; about 1.35 coal/min (20 coal ≈ 15 min) |
| Electric drill | 30 ore/min, 90 kW |
| AM1 | speed 0.5 → gears 60/min, red science 6/min (5 s recipe ÷ 0.5) |
| Boiler | 1.8 MW, up to 27 coal/min at full load; 1 boiler : 2 steam engines |
| Steam engine | 900 kW ≈ 12 AM1 or 15 labs or 10 electric drills |
| Lab | Automation research = 10 red × 10 s |

- Burner drill : furnace is about 1:1, so drop the drill straight into the furnace.
- Electric drill : furnace = 1 : 1.6.
- Red science: 1 gear AM feeds 10 red AMs. Per red/s you need 2 iron/s and 1 copper/s.
- Circuits: 3 cable AM : 2 circuit AM.

Recipes: furnace 5 stone · gear 2 iron · burner drill 3 gear + 3 iron + furnace · burner
inserter 1 iron + 1 gear · belt ×2 = 1 gear + 1 iron · pipe 1 iron · offshore pump 2 pipe + 1 gear ·
boiler furnace + 4 pipe · steam engine 8 gear + 10 pipe + 5 iron · cable ×2 = 1 copper ·
circuit 1 iron + 3 cable · inserter circuit + gear + iron · small pole ×2 = 1 wood + 2 cable ·
lab 10 circuit + 10 gear + 4 belt · AM1 3 circuit + 5 gear + 9 iron · red pack 1 copper + 1 gear ·
electric drill 3 circuit + 5 gear + 10 iron.

## Research gates (verified)
| Unlock | How |
|---|---|
| pipe, offshore pump, boiler, steam engine | **steam-power trigger**: 50 iron plates produced (smelted) |
| cable, circuit, inserter, small pole, lab | **electronics trigger**: 10 copper plates produced |
| assembling-machine-1 | **Automation** research: 10 red packs in a powered lab |
| electric mining drill, logistics, ... | normal lab research with red packs |

## Milestone ladder
Run each check after the build; it must pass on a fresh call. `produced()` is the
force-wide all-time production statistic, which is robust against hand-collection.

| M | Goal | Done when (code check) |
|---|---|---|
| M0 | Bootstrap: scout and seed kit | resource positions are stored in variables (`iron_pos, copper_pos, coal_pos, stone_pos, water_pos, wood_pos`); inventory has ≥ 30 coal and ≥ 20 stone |
| M1 | **Automated iron**: burner drill → furnace on iron | `check_growth(Prototype.IronPlate, 60) > 0` and the iron drill and furnace are `working` |
| M2 | **Automated copper** (+ electronics unlocked) | `check_growth(Prototype.CopperPlate, 60) > 0`; `research_state()['enabled']['small-electric-pole']` |
| M3 | **Coal automation** + stone supply | the coal drill pair (or drill → chest) is working; the coal it holds grows over `advance(60)`; `refuel_all` keeps everything at ≥ 5 fuel |
| M3b | Scale smelting: ≥ 3 iron pairs, ≥ 2 copper pairs | `check_growth(IronPlate,60)` ≥ 30/min-equivalent; all furnaces `working` |
| M4 | **Steam power** (steam-power unlocked at 50 iron plates) | engine `energy > 0` with a consumer attached; boiler `working` with fuel ≥ 10 |
| M5 | **Lab + Automation researched** | `'automation' in research_state()['researched']` |
| M6 | **Automated gears** (AM1 fed by inserter from an iron source; not a hand-filled chest) | gear count in the output chest grows over `advance(60)` with no manual inserts |
| M7 | **Automated red science** | red pack count grows with no manual inserts; ≥ 5/min |
| M8 | Electric mining drills on iron/copper/coal; boiler fed automatically | the drills are `working`; boiler fuel is non-zero after `advance(300)` |
| M9 | **Automated electronic circuits** (3 cable : 2 circuit) | circuit count grows with no manual input |

## Opening from the vanilla-like kit (tested route to M1: about 12 programs, 45 iron/min with 3 pairs, about 130 hand-mined coal)
1. **Scout**: `nearest()` for every resource. Store the positions as variables.
2. **Fuel and stone**: `gather(Resource.Coal, 40)` and `gather(Resource.Stone, 25)`. Wood
   (2 MJ) is valid fuel as well.
3. **First drill on iron**: `place_drill_furnace(Resource.IronOre)` uses the kit's drill and furnace.
   Iron plates now accumulate, and they also feed the steam-power trigger.
4. **Second and third pairs**: each pair costs 9 plates + 10 stone (drill furnace + output furnace).
   Crafting the drill consumes a furnace, so craft 2 furnaces per pair.
   Collect plates (`collect()`), `craft_item(Prototype.StoneFurnace, n)`,
   `craft_item(Prototype.BurnerMiningDrill)`. Put the next pair on copper early to fire the
   electronics trigger (10 copper plates).
5. **Coal pair**: two burner drills facing each other on coal (recipe b). Extract coal from
   their fuel slots, or put a drill → wooden chest pair next to it.
6. Then steam power, lab, Automation, gears, red science. See recipes.md (d), (e) and (f).

Hand-mining is fine for bootstrap only. From M1 on, every program should add or fix an
**automated** chain.

## Layout rules
- Keep sections ≥ 10 tiles apart and assembly blocks ≥ 20 tiles apart. Pad `find_space` by 2.
- Use furnace-on-drop-position before belts. "Only use belts if you need them."
- Producer first, then destination, then connectors, then fuel.
- Keep a `sections` dict (name → positions) in the namespace and in JOURNAL.md.
- Treat a working section as frozen. Expand elsewhere.
