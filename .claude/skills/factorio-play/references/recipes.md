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

---

# Patterns proven in run-01 (open_world, 3 shifts, red + green science)

Positions are run-01's (see `runs/run-01/JOURNAL.md` "Known positions"); shift positions to
your map. Directions in Lua output are 16-way: north 0, east 4, south 8, west 12. Code blocks
are the shift's own programs. Where a local `lay()/seg()` or `ug_out()` was used, it is shown
as the helper that now wraps the same code (`belt_line`, `ug_output`).

## (g) Self-refuelling coal belt  [M3, replaces hand refuelling]
Layout (shift 01, code not preserved; read back live with Lua):
- A row of burner drills on coal, 2 tiles apart, at (cx, -95), all facing **DOWN**. Each drops
  at (cx+0.5, -93.7) onto a 1-tile belt at (cx+0.5, -93.5) pointing DOWN.
- That joins a belt running **WEST** along y = -92.5 (the trunk to the smelters).
- A **burner inserter** at (cx-0.5, -93.5) facing DOWN picks coal from the trunk at
  (cx-0.5, -92.5) and drops into the drill above it, so each drill refuels from its own output.
  Burner inserters also refuel themselves from the coal they carry.
- 7 drills saturated the belt; it fed ~20 furnaces, 2 boilers and the burner inserters for
  2 shifts. Smelters take fuel with an inserter from a trunk that passes next to them.
Check: `belt_items(...)` on the trunk shows several items per belt, and `scan()` on the drills
shows `working` with fuel > 0 after a long `advance`.

## (h) Boiler at the base, water piped in; redundant fuel; second boiler  [M4/M8]
Layout (shift 02): offshore pump (-12.5,34.5) → **172-pipe water line** north along x=0.5 →
boiler (2.5,-60) at the smelting block, so the coal trunk (extended 6 tiles) can feed it and
no long pole line is needed. Keep every other entity one tile away from the water pipe; a
second engine touching it flooded the steam side (api.md "Fluids").
Redundant feed (shift 03): an electric inserter next to the original burner inserter, both
taking from the coal belt:
```python
craft_item(Prototype.Inserter, 6)
move_to(Position(x=2.5, y=-64.5))
pole = place_new(Prototype.SmallElectricPole, Position(x=3.5, y=-61.5))
ins = place_new(Prototype.Inserter, Position(x=1.5, y=-61.5), Direction.DOWN)   # belt y=-62.5 -> boiler
print("ins", ins.position, ins.direction, ins.pickup_position, ins.drop_position, ins.status)
```
Second boiler chained on the first boiler's water port, its own engine, fuel via a 1-slot chest:
```python
craft_item(Prototype.Boiler, 1); craft_item(Prototype.SteamEngine, 1); craft_item(Prototype.Pipe, 4)
move_to(Position(x=6.5, y=-64.5))
b2 = place_new(Prototype.Boiler, Position(x=6.5, y=-61), Direction.UP)
print("boiler2", b2.position, b2.direction, b2.connection_points, b2.steam_output_point)
move_to(Position(x=8.5, y=-65.5))
e3 = place_new(Prototype.SteamEngine, Position(x=10.5, y=-62.5), Direction.RIGHT)
move_to(Position(x=6.5, y=-64.5))
for p in [(6.5,-62.5),(7.5,-62.5),(4.5,-60.5)]:          # 2 steam pipes to e3, 1 water pipe boiler1->boiler2
    place_entity(Prototype.Pipe, position=Position(x=p[0], y=p[1]))
fi = place_new(Prototype.Inserter, Position(x=4.5, y=-63.5), Direction.RIGHT)   # coal belt -> chest
place_entity(Prototype.IronChest, position=Position(x=5.5, y=-63.5))
bi = place_new(Prototype.BurnerInserter, Position(x=5.5, y=-62.5), Direction.DOWN)  # chest -> boiler2
bi = insert_item(Prototype.Coal, bi, 5)
place_entity(Prototype.SmallElectricPole, position=Position(x=7.5, y=-64.5))
print(limit_chest(5.5, -63.5, 1))
advance(20)
power_report()
```
Observed: 3 engines = 2.7 MW, both boilers steady at 5 fuel.

## (i) Electric drill → furnace rows feeding a plate belt  [M8, 6 furnaces ≈ 112 iron/min]
North row: drills face DOWN into furnaces; an inserter moves plates onto the plate belt and a
long inserter brings coal from the coal belt one tile further out.
```python
move_to(Position(x=-3.5, y=-71.5))
for x in [-6.5, -3.5, -0.5]:
    d = place_new(Prototype.ElectricMiningDrill, Position(x=x, y=-75.5), Direction.DOWN)
    f = place_new(Prototype.StoneFurnace, d.drop_position)
    print("drill", d.position, d.drop_position, "furn", f.position)
move_to(Position(x=-3, y=-68.5))
for fx in [-6, -3, 0]:                                    # furnace centres
    o = place_new(Prototype.Inserter, Position(x=fx-0.5, y=-71.5), Direction.DOWN)          # plates -> belt y=-70.5
    l = place_new(Prototype.LongHandedInserter, Position(x=fx+0.5, y=-71.5), Direction.UP)  # coal y=-69.5 -> furnace
place_entity(Prototype.SmallElectricPole, position=Position(x=-4.5, y=-72.5))
place_entity(Prototype.SmallElectricPole, position=Position(x=1.5, y=-72.5))
```
South row (mirror image) with drills facing UP: place each furnace explicitly at
`(x+0.5, -67)`, **not** at `drop_position` (that overlapped the drill). The inserters swap
roles: a regular one takes coal from y=-69.5, a long one drops plates onto y=-70.5.

## (j) Science block: one row of AM1s on two belts  [M7/M9/M10]
An iron belt (y=-70.5) and a copper belt (y=-69.5) run east under a row of AM1s at y=-73.5,
4 tiles apart. Feed inserters at y=-71.5 reach the near belt with a regular inserter (iron)
or the far one with a long inserter (copper). Inserters at y=-73.5 between AMs pass
intermediates sideways, and the green assembler sits behind the row.
```python
ams = {}
for name, x, rec in [("C",12.5,Prototype.CopperCable),("E",16.5,Prototype.ElectronicCircuit),("I",20.5,Prototype.Inserter),
                     ("G",24.5,Prototype.IronGearWheel),("B",28.5,Prototype.TransportBelt),("R2",32.5,Prototype.AutomationSciencePack),
                     ("G2",36.5,Prototype.IronGearWheel)]:
    move_to(Position(x=x, y=-68.5))
    a = place_new(Prototype.AssemblingMachine1, Position(x=x, y=-73.5))
    a = set_entity_recipe(a, rec)
    ams[name] = a.position
for x, proto in [(12.5,Prototype.LongHandedInserter),(16.5,Prototype.Inserter),(20.5,Prototype.Inserter),(24.5,Prototype.Inserter),
                 (28.5,Prototype.Inserter),(32.5,Prototype.LongHandedInserter),(36.5,Prototype.Inserter)]:
    move_to(Position(x=x, y=-68.5))
    i = place_new(proto, Position(x=x, y=-71.5), Direction.UP)        # belt -> AM
for x, d in [(14.5,Direction.RIGHT),(18.5,Direction.RIGHT),(22.5,Direction.LEFT),(26.5,Direction.RIGHT),(34.5,Direction.LEFT)]:
    move_to(Position(x=x, y=-68.5))
    i = place_new(Prototype.Inserter, Position(x=x, y=-73.5), d)      # AM -> neighbour AM: C->E, E->I, G->I, G->B, G2->R2
    place_entity(Prototype.SmallElectricPole, position=Position(x=x, y=-72.5))
```
Green assembler S behind the row; I and B reach it through 1-slot relay chests; S feeds a lab:
```python
move_to(Position(x=24.5, y=-76))
s = place_new(Prototype.AssemblingMachine1, Position(x=24.5, y=-77.5))
s = set_entity_recipe(s, Prototype.LogisticsSciencePack)
for pos, d in [((21.5,-75.5),Direction.UP),((22.5,-76.5),Direction.RIGHT),((27.5,-75.5),Direction.UP),((26.5,-76.5),Direction.LEFT),((24.5,-79.5),Direction.UP)]:
    i = place_new(Prototype.Inserter, Position(x=pos[0], y=pos[1]), d)
for pos in [(21.5,-76.5),(27.5,-76.5)]:
    place_entity(Prototype.IronChest, position=Position(x=pos[0], y=pos[1]))
    print(limit_chest(pos[0], pos[1], 1))       # unbounded, they swallowed 53 belts / 38 inserters
place_entity(Prototype.SmallElectricPole, position=Position(x=23.5, y=-75.5))
move_to(Position(x=26.5, y=-79))
l1 = place_new(Prototype.Lab, Position(x=24.5, y=-81.5))
```
More labs sit in a row at y=-81.5, 4 tiles apart, chained by inserters at (x±2, -81.5), with a
pole at (x±2, -83.5). Result: green 4.8/min (AM1 cap 5), red 12/min from 2 red AMs, 4 labs
researching automatically. Check with `rate([Prototype.AutomationSciencePack, Prototype.LogisticsSciencePack], 120)`
and `lab_report()`.

## (k) Belt under another belt
```python
belt_line(-7.5, -70.5, 8.5, -70.5, Direction.RIGHT)
move_to(Position(x=10.5, y=-68))
place_entity(Prototype.UndergroundBelt, direction=Direction.RIGHT, position=Position(x=9.5, y=-70.5))
place_entity(Prototype.UndergroundBelt, direction=Direction.RIGHT, position=Position(x=11.5, y=-70.5))
print(ug_output(11.5, -70.5, 'east'))      # -> "output d4 nb=9.5,-70.5"
belt_line(12.5, -70.5, 37.5, -70.5, Direction.RIGHT)
```
