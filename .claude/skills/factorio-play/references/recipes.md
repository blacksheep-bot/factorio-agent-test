# Known-good recipes (each one executed successfully against the live server)

**Test conditions:** server `open_world` scenario (seed 44340), Factorio 2.0.73, FLE 0.4.3, REPL
`setup/fle_repl.py --fresh --pause-between --inventory '<INV>'`, research NOT pre-completed
(only FLE's automatic `automation-science-pack`), helpers auto-loaded. The recipes ran in order
a→f as separate `fle_exec.py <file>` calls on 2026-11-14, so later recipes reuse variables
(`engine`, `am`) from earlier ones. Test inventory:
```json
{"coal":200,"iron-plate":200,"copper-plate":100,"stone-furnace":10,"burner-mining-drill":6,
 "wooden-chest":10,"transport-belt":100,"burner-inserter":10,"inserter":10,"small-electric-pole":30,
 "offshore-pump":1,"boiler":1,"steam-engine":2,"pipe":30,"assembling-machine-1":3,"lab":1,
 "automation-science-pack":20,"wood":20,"stone":50}
```
Placing an entity does **not** need its recipe unlocked. Crafting it does, and in a real run you
craft everything, so mind the research gates in strategy.md. Recipe (a) was also re-run in
the real vanilla-like start during the smoke test, using `place_drill_furnace()`, which
wraps it.

Adapt the positions; never paste blindly. Each recipe re-fetches entities after placing them,
because `place_entity` can return a stale or neighbouring entity.

## (a) Burner drill on iron feeding a stone furnace directly  [M1]

> In practice use `place_drill_furnace(Resource.IronOre, near=...)` (helpers). It does the same
> thing but uses `place_new()`, because `get_entity(proto, d.position)` below returned the
> *neighbouring* drill when the new drill was placed right next to an existing one
> (smoke test). The snippet is fine for the first drill on a patch.

```python
# (a) burner drill on iron -> stone furnace on its drop_position
iron = nearest(Resource.IronOre)
bb = nearest_buildable(Prototype.BurnerMiningDrill, BuildingBox(width=2, height=4), iron)
move_to(bb.left_top)
d = place_entity(Prototype.BurnerMiningDrill, direction=Direction.DOWN, position=bb.left_top)
iron_drill = get_entity(Prototype.BurnerMiningDrill, d.position)          # re-fetch: return value can be stale
place_entity(Prototype.StoneFurnace, position=iron_drill.drop_position)
iron_furnace = get_entity(Prototype.StoneFurnace, iron_drill.drop_position)
iron_drill = insert_item(Prototype.Coal, iron_drill, 10)
iron_furnace = insert_item(Prototype.Coal, iron_furnace, 10)
print("drill", iron_drill.position, "drop", iron_drill.drop_position, "furnace", iron_furnace.position)
sleep(15)
iron_furnace = get_entity(Prototype.StoneFurnace, iron_furnace.position)
iron_drill = get_entity(Prototype.BurnerMiningDrill, iron_drill.position)
print(iron_drill.status, iron_furnace.status, iron_furnace.furnace_result)
assert iron_furnace.furnace_result[Prototype.IronPlate] > 0, "no plates yet"
```
Observed:
```
drill (-19,-54) drop (-18.5,-52.5) furnace (-18,-52)
(WORKING, WORKING, Inventory(iron-plate=2))
```

## (b) Self-feeding coal drill pair  [M3]

```python
# (b) two burner drills on coal feeding each other's fuel slot
coal = nearest(Resource.Coal)
bb = nearest_buildable(Prototype.BurnerMiningDrill, BuildingBox(width=4, height=2), coal)
move_to(bb.left_top)
place_entity(Prototype.BurnerMiningDrill, direction=Direction.RIGHT, position=bb.left_top)
c1 = get_entity(Prototype.BurnerMiningDrill, Position(x=bb.left_top.x + 0.5, y=bb.left_top.y + 0.5))
place_entity(Prototype.BurnerMiningDrill, direction=Direction.LEFT, position=Position(x=c1.position.x + 2, y=c1.position.y))
c2 = get_entity(Prototype.BurnerMiningDrill, Position(x=c1.position.x + 2, y=c1.position.y))
assert c1.position != c2.position, "got the same drill twice"
c1 = insert_item(Prototype.Coal, c1, 5)
c2 = insert_item(Prototype.Coal, c2, 5)
print("c1", c1.position, "drop", c1.drop_position, "| c2", c2.position, "drop", c2.drop_position)
advance(60)
for d in get_entities({Prototype.BurnerMiningDrill}, position=c1.position, radius=4):
    print(d.position, d.status, d.fuel)
```
Observed:
```
c1 (38,-86) drop (39.5,-86.5) | c2 (40,-86) drop (38.5,-85.5)
after advance(60): both WORKING, coal=16 each (started with 5)
```

## (c) Refuel everything

```python
# (c) refuel: helper + the manual pattern it wraps
refuel_all(min_fuel=10, amount=20)          # tops up every burner entity below 10 fuel
for e in get_entities({Prototype.BurnerMiningDrill, Prototype.StoneFurnace, Prototype.BurnerInserter, Prototype.Boiler}):
    if e.fuel.get(Prototype.Coal, 0) < 10:
        move_to(e.position)
        insert_item(Prototype.Coal, e, 20)
        print("manual refuel", e.name, e.position)
```
Observed:
```
refuel_all: +20 coal -> burner-mining-drill@(-19,-54) (had 6)
refuel_all: +20 coal -> stone-furnace@(-18,-52) (had 8)
```

## (d) Offshore pump → boiler → steam engine  [M4]

```python
# (d) offshore pump -> boiler -> steam engine, then poles to a consumer
water = nearest(Resource.Water)
move_to(water)
pump = place_entity(Prototype.OffshorePump, position=water)
bb = nearest_buildable(Prototype.Boiler, BuildingBox(width=Prototype.Boiler.WIDTH + 4, height=Prototype.Boiler.HEIGHT + 4), pump.position)
move_to(bb.center)
boiler = place_entity(Prototype.Boiler, position=bb.center, direction=Direction.LEFT)
boiler = insert_item(Prototype.Coal, boiler, 20)
bb2 = nearest_buildable(Prototype.SteamEngine, BuildingBox(width=Prototype.SteamEngine.WIDTH + 4, height=Prototype.SteamEngine.HEIGHT + 4), boiler.position)
move_to(bb2.center)
engine = place_entity(Prototype.SteamEngine, position=bb2.center, direction=Direction.LEFT)
print("pump", pump.position, "boiler", boiler.position, "engine", engine.position)
connect_entities(pump, boiler, Prototype.Pipe)
connect_entities(boiler, engine, Prototype.Pipe)
sleep(5)
engine = get_entity(Prototype.SteamEngine, engine.position)
boiler = get_entity(Prototype.Boiler, boiler.position)
print("engine", engine.status, "boiler", boiler.status, boiler.fuel)
# an engine with nothing attached reports NOT_PLUGGED_IN_ELECTRIC_NETWORK - that is expected
```
Observed:
```
pump (-13.5,33.5) boiler (-7,33.5) engine (-1.5,37.5)
engine NOT_PLUGGED_IN_ELECTRIC_NETWORK (no consumer yet), boiler WORKING coal=15
```

## (e) Assembler making gears, fed by inserters from a chest, powered by poles  [M6 building block]

```python
# (e) assembler making gears: chest -> inserter -> AM1 -> inserter -> chest, powered from `engine`
spot = find_space(3, 7, Position(x=engine.position.x + 12, y=engine.position.y), pad=2)
move_to(spot)
am = place_entity(Prototype.AssemblingMachine1, position=Position(x=spot.x + 1.5, y=spot.y + 3.5))
am = set_entity_recipe(am, Prototype.IronGearWheel)
# place_entity_next_to(Inserter, X.position, SIDE) makes an inserter that TAKES FROM X and drops away
ins_in = place_entity_next_to(Prototype.Inserter, am.position, direction=Direction.UP, spacing=0)
ins_in = rotate_entity(ins_in, Direction.DOWN)                    # now drops INTO the assembler
chest_in = place_entity(Prototype.WoodenChest, position=ins_in.pickup_position)
ins_out = place_entity_next_to(Prototype.Inserter, am.position, direction=Direction.DOWN, spacing=0)
chest_out = place_entity(Prototype.WoodenChest, position=ins_out.drop_position)
chest_in = insert_item(Prototype.IronPlate, chest_in, 50)
connect_entities(engine, am, Prototype.SmallElectricPole)
# connect_entities stops once the TARGET is powered; a 5x5 pole area may miss the far inserter:
place_entity_next_to(Prototype.SmallElectricPole, ins_out.position, direction=Direction.RIGHT, spacing=0)
sleep(15)
am = get_entity(Prototype.AssemblingMachine1, am.position)
chest_out = get_entity(Prototype.WoodenChest, chest_out.position)
print("am", am.position, am.status, "out chest", chest_out.inventory)
assert chest_out.inventory[Prototype.IronGearWheel] > 0
```
Observed:
```
am (14.5,43.5) WORKING, out chest Inventory(iron-gear-wheel=6) after sleep(15)
```

## (f) Lab with red science → Automation research  [M5]

```python
# (f) lab with red science, powered from the same network
spot = find_space(3, 3, Position(x=am.position.x, y=am.position.y - 10), pad=1)
move_to(spot)
lab = place_entity(Prototype.Lab, position=Position(x=spot.x + 1.5, y=spot.y + 1.5))
connect_entities(am, lab, Prototype.SmallElectricPole)
lab = insert_item(Prototype.AutomationSciencePack, lab, 10)
print(set_research(Technology.Automation))                 # -> remaining packs
sleep(15)
lab = get_entity(Prototype.Lab, lab.position)
print("lab", lab.position, lab.status, lab.lab_input, get_research_progress(Technology.Automation))
advance(100)
print("remaining", get_research_progress(Technology.Automation), research_state()["researched"])
```
Observed:
```
set_research -> 10 packs; lab WORKING, remaining 9 after 15 s; after advance(100): remaining [] and 'automation' researched
```

## Variants and notes (drill→chest and furnace→burner-inserter→chest also verified: 7 ore / 25 plates after advance(30))
- **Drill → chest** (coal or ore buffer): `place_entity(Prototype.WoodenChest, position=drill.drop_position)`.
  Do NOT use `place_entity_next_to` for this, because it misses the drop position and the ore lands on the ground.
- **Furnace output → chest**: `ins = place_entity_next_to(Prototype.BurnerInserter, furnace.position, Direction.DOWN)`
  takes from the furnace and drops below it. Then `place_entity(Prototype.WoodenChest, position=ins.drop_position)`
  and give the burner inserter fuel.
- **Belts:** `connect_entities(pos_a, pos_b, Prototype.TransportBelt)` returns a `BeltGroup`
  (`.belts`, `.inputs`, `.outputs`). `pickup_entity(group)` takes the whole line back.
- **Coal pair caveat:** the two drills only fill each other's fuel slots (max 50) and then
  stall with `waiting_for_space_in_destination`. Harvest coal with
  `extract_item(Prototype.Coal, c1, 30)`. For a real coal supply, add drill → chest pairs.
