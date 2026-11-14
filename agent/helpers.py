# Agent helpers, eval'd into the FLE REPL namespace by setup/fle_repl.py on every connect.
# Reload by hand (e.g. after editing, or after calling reset()):
#     python3 setup/fle_exec.py agent/helpers.py
#
# Rules for this file (it runs through FLE's namespace eval, not a normal import):
#   * only top-level `def`s, plain constants and imports; names starting with "_" are NOT persisted
#   * tool names (move_to, insert_item, ...) cannot be redefined
#   * every helper prints compact, line-oriented output; nothing here sleeps unboundedly

HELPERS_VERSION = "1.1"

# Entities that burn fuel (have a `.fuel` inventory).
BURNER_NAMES = ["burner-mining-drill", "stone-furnace", "steel-furnace", "burner-inserter", "boiler"]
FUEL_ITEMS = ["coal", "wood", "solid-fuel"]
# Statuses that mean "this machine is not producing" (string values of EntityStatus).
BAD_STATUSES = ["no_fuel", "no_power", "low_power", "no_ingredients", "no_input_fluid",
                "no_minable_resources", "waiting_for_space_in_destination", "full_output",
                "not_enough_space_in_output", "item_ingredient_shortage", "no_recipe",
                "missing_required_fluid", "not_connected", "not_plugged_in_electric_network",
                "no_research_in_progress", "missing_science_packs"]
# (waiting_for_source_items is normal for an idle inserter and is not flagged)
# "Soft" statuses: often transient (a furnace fed by one burner drill idles ~20% of the time,
# since it smelts faster than the drill mines). Reported under IDLE, not PROBLEMS.
SOFT_STATUSES = ["no_ingredients", "item_ingredient_shortage", "waiting_for_source_items"]
# Early-game recipes worth tracking (Factorio 2.0, research NOT pre-completed).
KEY_RECIPES = ["burner-mining-drill", "stone-furnace", "iron-gear-wheel", "burner-inserter",
               "transport-belt", "wooden-chest", "iron-chest", "pipe", "offshore-pump", "boiler",
               "steam-engine", "copper-cable", "electronic-circuit", "inserter",
               "small-electric-pole", "lab", "automation-science-pack", "assembling-machine-1",
               "electric-mining-drill", "underground-belt", "splitter", "steel-plate"]


def lua(code):
    """Run raw Lua (a /sc command body) on the server and return what it rcon.print()s."""
    return instance.rcon_client.send_command("/sc " + code)


def item_name(x):
    """Prototype.IronPlate -> 'iron-plate'; strings pass through."""
    if isinstance(x, str):
        return x
    v = getattr(x, "value", x)
    return v[0] if isinstance(v, tuple) else str(v)


def inv_dict(inv):
    """Inventory -> plain {name: count} with zero entries dropped."""
    out = {}
    try:
        for k, v in inv.items():
            if v:
                out[item_name(k)] = v
    except Exception:
        pass
    return out


def status_str(e):
    s = getattr(e, "status", None)
    return str(getattr(s, "value", s))


def fuel_count(e):
    if not has_field(e, "fuel"):
        return None
    f = e.__dict__["fuel"]
    if f is None:
        return None
    return sum(inv_dict(f).values())


def player_pos():
    """True character position (player_location can be stale, esp. inside helper functions)."""
    import json
    d = json.loads(lua("local c=storage.agent_characters[1] rcon.print(helpers.table_to_json({x=c.position.x,y=c.position.y}))"))
    return Position(x=d["x"], y=d["y"])


def pos_str(p):
    return f"({p.x:g},{p.y:g})"


def has_field(e, attr):
    """FLE entity objects answer getattr() for ANY name (dynamic fallback), so check __dict__."""
    return attr in getattr(e, "__dict__", {})


def entity_contents(e):
    """Short string of the interesting inventories of an entity."""
    parts = []
    for attr, label in [("furnace_source", "in"), ("furnace_result", "out"),
                        ("assembling_machine_input", "in"), ("assembling_machine_output", "out"),
                        ("lab_input", "packs"), ("inventory", "inv")]:
        if not has_field(e, attr):
            continue
        v = e.__dict__[attr]
        if attr == "inventory" and parts:
            continue
        d = inv_dict(v) if hasattr(v, "items") else {}
        if d:
            parts.append(label + "=" + ",".join(f"{k}:{n}" for k, n in d.items()))
    if has_field(e, "recipe") and e.recipe:
        parts.append("recipe=" + str(getattr(e.recipe, "name", e.recipe)))
    return " ".join(parts)


def flatten_entities(ents=None):
    """get_entities() groups belts/pipes/poles; return (singles, groups)."""
    if ents is None:
        ents = get_entities()
    singles, groups = [], []
    for e in ents:
        if has_field(e, "belts") or has_field(e, "pipes") or has_field(e, "poles"):
            groups.append(e)
        else:
            singles.append(e)
    return singles, groups


def research_state():
    """Dict: current research, progress, researched techs (minus the trivial), key recipe flags."""
    raw = lua(
        "local f=game.forces.player local r={} for n,t in pairs(f.technologies) do "
        "if t.researched then r[#r+1]=n end end local cur=f.current_research "
        "local e={} for _,n in pairs({" + ",".join(f"'{n}'" for n in KEY_RECIPES) + "}) do "
        "local rc=f.recipes[n] e[n]=rc and rc.enabled or false end "
        "local ps=f.get_item_production_statistics(game.surfaces[1]) "
        "rcon.print(helpers.table_to_json({researched=r, current=cur and cur.name or '', "
        "progress=f.research_progress, enabled=e, made_iron=ps.get_input_count('iron-plate'), "
        "made_copper=ps.get_input_count('copper-plate')}))")
    import json
    return json.loads(raw)


def status_report(show_ok=True, radius=None):
    """One-call orientation: tick, position, inventory, every entity (status/fuel/contents),
    problems, research + unlocked recipes. Call at the start of every shift and after builds."""
    tick = lua("rcon.print(game.tick)")
    print(f"== STATUS tick={tick} (game time {int(tick) / 3600:.1f} min) player={pos_str(player_pos())}")
    inv = inv_dict(inspect_inventory())
    print("INVENTORY: " + (", ".join(f"{k}={v}" for k, v in sorted(inv.items())) or "(empty)"))
    ents = get_entities(position=player_pos(), radius=radius) if radius else get_entities()
    singles, groups = flatten_entities(ents)
    problems = []
    idle = []
    by_name = {}
    for e in singles:
        by_name.setdefault(e.name, []).append(e)
    for name in sorted(by_name):
        lst = by_name[name]
        print(f"-- {name} x{len(lst)}")
        for e in lst:
            st = status_str(e)
            fc = fuel_count(e)
            fuel = "" if fc is None else f" fuel={fc}"
            line = f"   {pos_str(e.position)} {st}{fuel} {entity_contents(e)}".rstrip()
            soft = st in SOFT_STATUSES
            bad = (st in BAD_STATUSES and not soft) or (fc is not None and fc < 5)
            if bad:
                problems.append(f"{name}@{pos_str(e.position)}: {st}{fuel}")
            elif soft:
                idle.append(f"{name}@{pos_str(e.position)}")
            if show_ok or bad:
                print(line)
    for g in groups:
        kind = "belts" if has_field(g, "belts") else ("pipes" if has_field(g, "pipes") else "poles")
        members = getattr(g, kind)
        print(f"-- {g.name} group: {len(members)} {kind} at {pos_str(g.position)} {status_str(g)}")
    if not singles and not groups:
        print("-- no entities placed")
    rs = research_state()
    on = [k for k, v in rs["enabled"].items() if v]
    off = [k for k, v in rs["enabled"].items() if not v]
    triv = {"automation-science-pack"}
    done = [t for t in rs["researched"] if t not in triv]
    print(f"RESEARCH: current={rs['current'] or '-'} progress={rs['progress']:.2f} "
          f"researched={done or '[automation-science-pack only]'}")
    print(f"TRIGGERS: iron plates made={rs['made_iron']}/50 (steam-power), "
          f"copper plates made={rs['made_copper']}/10 (electronics)")
    print("RECIPES on: " + ", ".join(on))
    print("RECIPES locked: " + ", ".join(off))
    print("IDLE (often transient; re-check after advance): " + (", ".join(idle) if idle else "none"))
    print("PROBLEMS: " + ("; ".join(problems) if problems else "none"))
    return problems


def refuel_all(min_fuel=5, amount=20, fuel=None, positions=None):
    """Top up every burner entity whose fuel < min_fuel with `amount` of `fuel`
    (default: coal, else wood). Walks to each. Returns number refuelled.
    `positions=[(x, y), ...]` limits it to those entities: once coal is belt-fed, list only the
    hand-fed ones, or the coal goes into self-fed drills and burner inserters first."""
    inv = inv_dict(inspect_inventory())
    if fuel is None:
        fuel = Prototype.Coal if inv.get("coal", 0) > 0 else Prototype.Wood
    fname = item_name(fuel)
    n = 0
    for e in flatten_entities()[0]:
        if e.name not in BURNER_NAMES:
            continue
        if positions is not None and not any(abs(e.position.x - px) < 0.6 and abs(e.position.y - py) < 0.6
                                             for px, py in positions):
            continue
        fc = fuel_count(e) or 0
        if fc >= min_fuel:
            continue
        have = inv_dict(inspect_inventory()).get(fname, 0)
        if have <= 0:
            print(f"refuel_all: out of {fname}; {e.name}@{pos_str(e.position)} still has {fc}")
            break
        q = min(amount, have)
        move_to(e.position)
        insert_item(fuel, e, q)
        n += 1
        print(f"refuel_all: +{q} {fname} -> {e.name}@{pos_str(e.position)} (had {fc})")
    print(f"refuel_all: refuelled {n} entities; {fname} left={inv_dict(inspect_inventory()).get(fname, 0)}")
    return n


def find_space(w, h, near, proto=None, pad=2):
    """Free, buildable w x h area (+pad tiles each side) nearest `near`. Returns the left_top
    Position of the INNER w x h box (where to start placing). proto defaults to a wooden chest
    (any 1x1 entity); pass the drill prototype when the area must be on ore."""
    proto = proto or Prototype.WoodenChest
    bb = nearest_buildable(proto, BuildingBox(width=w + 2 * pad, height=h + 2 * pad), near)
    p = Position(x=bb.left_top.x + pad, y=bb.left_top.y + pad)
    print(f"find_space({w}x{h}, pad={pad}) near {pos_str(near)} -> inner left_top {pos_str(p)}")
    return p


def gather(resource, qty):
    """Hand-mine `qty` of a resource (Resource.Coal/IronOre/CopperOre/Stone/Wood) at the nearest
    patch. Loops because harvest_resource can return less than asked. Returns amount mined."""
    got = 0
    for _ in range(10):
        if got >= qty:
            break
        p = nearest(resource)
        move_to(p)
        got += harvest_resource(p, quantity=qty - got, radius=10)
    print(f"gather {resource[0] if isinstance(resource, tuple) else resource}: {got}/{qty}")
    return got


def collect(item=None, min_count=1):
    """Extract `item` (default: iron+copper plates) from every furnace/chest/assembler output
    that holds >= min_count of it. Walks to each. Returns total collected."""
    items = [item] if item else [Prototype.IronPlate, Prototype.CopperPlate]
    total = 0
    for e in flatten_entities()[0]:
        for it in items:
            nm = item_name(it)
            have = 0
            for attr in ["furnace_result", "inventory", "assembling_machine_output"]:
                if has_field(e, attr) and hasattr(e.__dict__[attr], "items"):
                    have += inv_dict(e.__dict__[attr]).get(nm, 0)
                    if attr == "furnace_result":
                        break
            if have >= min_count:
                move_to(e.position)
                got = extract_item(it, e.position, quantity=have)
                total += got
                print(f"collect: {got} {nm} from {e.name}@{pos_str(e.position)}")
    print(f"collect: total {total}")
    return total


def wait_for(pred, timeout=60, step=5):
    """Call sleep(step) until pred() is truthy or `timeout` game-seconds pass. Returns bool."""
    waited = 0
    while waited < timeout:
        if pred():
            return True
        sleep(step)
        waited += step
    return bool(pred())


def game_tick():
    """Current game tick (60 ticks = 1 game second)."""
    return int(lua("rcon.print(game.tick)"))


def advance(seconds=60):
    """Let `seconds` GAME seconds pass, measured by tick delta. (FLE's sleep(n) is wall-clock based
    and only yields ~0.75*n game seconds at speed 10, so a plain sleep loop under-runs.)
    Returns the game seconds that actually passed."""
    t0 = game_tick()
    target = int(seconds * 60)
    for _ in range(int(seconds) // 4 + 10):
        left = target - (game_tick() - t0)
        if left <= 30:
            break
        sleep(max(1, min(15, int(left / 60))))
    return (game_tick() - t0) / 60.0


def produced(item=Prototype.IronPlate):
    """Total ever produced on the map (force production statistics) - the robust M-check."""
    return int(lua(f"rcon.print(game.forces.player.get_item_production_statistics(game.surfaces[1])"
                   f".get_input_count('{item_name(item)}'))"))


def check_growth(item=Prototype.IronPlate, seconds=30):
    """Production-stat delta of `item` over `seconds` of game time (tick-measured). Prints a rate/min.
    The stat can lag a little: use >= 60 s windows, or rate()/am_finished() for assemblers."""
    a = produced(item)
    t0 = game_tick()
    advance(seconds)
    b = produced(item)
    dt = max(1, game_tick() - t0) / 3600.0
    print(f"check_growth {item_name(item)}: {a} -> {b} in {dt * 60:.0f}s = {(b - a) / dt:.1f}/min")
    return b - a


def am_finished():
    """{(x, y): (recipe, products_finished)} for every assembling machine, via Lua (exact, no stat lag)."""
    import json
    raw = lua("local o={} for _,a in pairs(game.surfaces[1].find_entities_filtered{type='assembling-machine'}) do "
              "local r=a.get_recipe() o[#o+1]={x=a.position.x,y=a.position.y,r=r and r.name or '',n=a.products_finished} end "
              "rcon.print(helpers.table_to_json(o))")
    return {(d["x"], d["y"]): (d["r"], d["n"]) for d in (json.loads(raw) or [])}


def rate(items=None, seconds=60):
    """Measure real production rates per game-minute over `seconds` (tick delta, not the nominal
    advance time). `items`: list of Prototypes for the force production stat (default: iron/copper
    plate, gear, circuit, red+green packs). Also prints per-recipe assembler output from
    products_finished (exact). Returns {item: per_min}."""
    items = items or [Prototype.IronPlate, Prototype.CopperPlate, Prototype.IronGearWheel,
                      Prototype.ElectronicCircuit, Prototype.AutomationSciencePack, Prototype.LogisticsSciencePack]
    a = {item_name(i): produced(i) for i in items}
    f0 = am_finished()
    t0 = game_tick()
    advance(seconds)
    dt = max(1, game_tick() - t0) / 3600.0
    b = {k: produced(k) for k in a}
    f1 = am_finished()
    out = {k: round((b[k] - a[k]) / dt, 1) for k in a}
    print(f"rate over {dt * 60:.0f} game-s (stat): " + ", ".join(f"{k}={v}/min" for k, v in out.items()))
    per = {}
    for pos, (r, n) in f1.items():
        if pos in f0 and r:
            per[r] = per.get(r, 0) + n - f0[pos][1]
    if per:
        print("assembler crafts (products_finished; x2 for cable/belt): "
              + ", ".join(f"{r}={n / dt:.1f}/min" for r, n in sorted(per.items())))
    return out


def ensure_crafted(proto, n=1):
    """Craft until the inventory holds >= n of proto (craft_item recurses into intermediates)."""
    have = inv_dict(inspect_inventory()).get(item_name(proto), 0)
    if have < n:
        craft_item(proto, n - have)
    have = inv_dict(inspect_inventory()).get(item_name(proto), 0)
    print(f"ensure_crafted {item_name(proto)}: have {have}")
    return have


def place_new(proto, position, direction=None):
    """place_entity + return the entity that was ACTUALLY created. place_entity's return value
    can describe a neighbouring entity of the same type (seen with adjacent drills), so we diff
    get_entities() before/after. Must already be in reach (move_to first)."""
    before = set((e.position.x, e.position.y) for e in get_entities({proto}, position=position, radius=12))
    if direction is None:
        place_entity(proto, position=position)
    else:
        place_entity(proto, direction=direction, position=position)
    after = get_entities({proto}, position=position, radius=12)
    fresh = [e for e in after if (e.position.x, e.position.y) not in before]
    if not fresh:
        raise Exception(f"place_new: no new {item_name(proto)} found near {pos_str(position)}")
    return get_entity(proto, fresh[0].position)


def place_drill_furnace(ore=None, near=None, fuel=10):
    """M1/M2 building block: burner drill on ore dropping straight into a stone furnace
    (no inserter/belt needed). Needs 1 burner-mining-drill, 1 stone-furnace and 2*fuel coal
    (falls back to wood) in inventory. Returns fresh (drill, furnace)."""
    ore = ore or Resource.IronOre
    inv = inv_dict(inspect_inventory())
    assert inv.get("burner-mining-drill", 0) >= 1 and inv.get("stone-furnace", 0) >= 1, \
        f"place_drill_furnace needs 1 burner-mining-drill + 1 stone-furnace (crafting a drill CONSUMES a furnace); have {inv}"
    near = near or nearest(ore)
    bb = nearest_buildable(Prototype.BurnerMiningDrill, BuildingBox(width=2, height=4), near)
    move_to(bb.left_top)
    drill = place_new(Prototype.BurnerMiningDrill, bb.left_top, Direction.DOWN)
    furn = place_new(Prototype.StoneFurnace, drill.drop_position)
    f = Prototype.Coal if inv_dict(inspect_inventory()).get("coal", 0) >= 2 * fuel else Prototype.Wood
    drill = insert_item(f, drill, fuel)
    furn = insert_item(f, furn, fuel)
    print(f"drill@{pos_str(drill.position)} drop={pos_str(drill.drop_position)} -> furnace@{pos_str(furn.position)}; "
          f"{item_name(f)} x{fuel} each")
    return drill, furn


# ---- Lua-side inspection (fast: get_entities() takes ~15 s wall on a 200+ entity base, and the
# game runs while it does, ~2 game-min at speed 10; these take well under a second) ----

STATUS_LUA = "local st={} for k,v in pairs(defines.entity_status) do st[v]=k end "


def area_lua(x0, y0, x1, y1):
    return "{{%s,%s},{%s,%s}}" % (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def scan(x0, y0, x1, y1, types=None):
    """One line per machine in the area: name@x,y:status [+ AM output count, lab packs, fuel].
    Default types: inserter, assembler, lab, drill, furnace, boiler, generator. Read-only, fast.
    Works for labs (FLE's get_entity/get_entities on labs fails)."""
    types = types or ["inserter", "assembling-machine", "lab", "mining-drill", "furnace", "boiler", "generator"]
    tl = "{" + ",".join(f"'{t}'" for t in types) + "}"
    out = lua(STATUS_LUA + "local o={} for _,e in pairs(game.surfaces[1].find_entities_filtered{area=" + area_lua(x0, y0, x1, y1)
              + ",type=" + tl + "}) do local x='' "
              "if e.type=='assembling-machine' then x=' out='..e.get_output_inventory().get_item_count() end "
              "if e.type=='lab' then for _,it in pairs(e.get_inventory(defines.inventory.lab_input).get_contents()) do x=x..' '..it.name..'='..it.count end end "
              "local f=e.get_fuel_inventory() if f then x=x..' fuel='..f.get_item_count() end "
              "o[#o+1]=e.name..'@'..e.position.x..','..e.position.y..':'..(st[e.status] or tostring(e.status))..x end "
              "rcon.print(table.concat(o,' | '))")
    print(out or "(nothing)")
    return out


def lab_report():
    """Labs (status + packs) and research state, via Lua."""
    print(lua(STATUS_LUA + "local f=game.forces.player local o={} for _,e in pairs(game.surfaces[1].find_entities_filtered{type='lab'}) do "
              "local x='' for _,it in pairs(e.get_inventory(defines.inventory.lab_input).get_contents()) do x=x..' '..it.name..'='..it.count end "
              "o[#o+1]='lab@'..e.position.x..','..e.position.y..':'..(st[e.status] or '?')..x end "
              "local q={} for _,t in pairs(f.research_queue) do q[#q+1]=t.name end "
              "rcon.print(table.concat(o,' | ')..' || current='..tostring(f.current_research and f.current_research.name)"
              "..' progress='..string.format('%.2f',f.research_progress)..' queue='..table.concat(q,','))"))


def power_report():
    """Electric network production/consumption (kW, 1-min average) vs steam-engine capacity, plus boilers."""
    print(lua("local s=game.surfaces[1] local p=s.find_entities_filtered{type='electric-pole',limit=1}[1] "
              "if not p then rcon.print('no poles') return end local st=p.electric_network_statistics "
              "local function tot(cat,tbl) local t=0 for n,_ in pairs(tbl) do t=t+st.get_flow_count{name=n,category=cat,"
              "precision_index=defines.flow_precision_index.one_minute}*60/1000 end return t end "
              "local cap=900*#s.find_entities_filtered{name='steam-engine'} local b={} "
              "for _,x in pairs(s.find_entities_filtered{type='boiler'}) do b[#b+1]=x.position.x..','..x.position.y..' fuel='..x.get_fuel_inventory().get_item_count() end "
              "rcon.print(string.format('produced=%.0fkW consumed=%.0fkW capacity=%dkW (one network sampled) | boilers: ',"
              "tot('output',st.output_counts),tot('input',st.input_counts),cap)..table.concat(b,'; '))"))


def belt_items(x0, y0, x1, y1):
    """(belts, items on them) in an area: is a supply belt backed up (~7-8 items/belt) or starved?"""
    r = lua("local t=0 local n=0 for _,e in pairs(game.surfaces[1].find_entities_filtered{type='transport-belt',area="
            + area_lua(x0, y0, x1, y1) + "}) do n=n+1 t=t+e.get_transport_line(1).get_item_count()+e.get_transport_line(2).get_item_count() end "
            "rcon.print(n..' '..t)")
    n, t = (int(v) for v in r.split())
    print(f"belt_items: {n} belts, {t} items ({t / max(n, 1):.1f}/belt)")
    return n, t


def ascii_map(x0, x1, y0, y1):
    """Text map, one char per tile: D drill F furnace A assembler > inserter = belt ~ pipe + pole
    o chest # other building, t tree r rock, lowercase letter = ore (i/c/s/...), . empty.
    Read-only. Keep it <= ~60x50 tiles per call."""
    code = ("local s=game.surfaces[1] local o={} for y=%d,%d do local row={} for x=%d,%d do "
            "local a={{x+0.1,y+0.1},{x+0.9,y+0.9}} local c='.' "
            "local r=s.find_entities_filtered{area=a,type='resource',limit=1} if #r>0 then c=string.sub(r[1].name,1,1) end "
            "local e=s.find_entities_filtered{area=a,type={'resource'},invert=true,limit=1} if #e>0 then local t=e[1].type "
            "if t=='tree' then c='t' elseif t=='simple-entity' then c='r' elseif t=='transport-belt' or t=='underground-belt' then c='=' "
            "elseif t=='electric-pole' then c='+' elseif t=='pipe' then c='~' elseif t=='inserter' then c='>' elseif t=='container' then c='o' "
            "elseif t=='furnace' then c='F' elseif t=='mining-drill' then c='D' elseif t=='assembling-machine' then c='A' else c='#' end end "
            "row[#row+1]=c end o[#o+1]=string.format('%%4d ',y)..table.concat(row,'') end rcon.print(table.concat(o,'\\n'))") % (y0, y1, x0, x1)
    print(f"ascii_map x {x0}..{x1}")
    for line in lua(code).split("\n"):
        print(line)


def limit_chest(x, y, slots=1):
    """Limit a chest (the inventory bar) to `slots` slots, so a relay chest between machines buffers a
    little instead of swallowing every intermediate. Returns the new bar."""
    return lua("local c=game.surfaces[1].find_entities_filtered{type='container',position={%s,%s},limit=1}[1] "
               "if not c then rcon.print('no chest') return end local i=c.get_inventory(defines.inventory.chest) "
               "i.set_bar(%d) rcon.print(i.get_bar())" % (x, y, slots + 1))


def ug_output(x, y, direction="east"):
    """FLE's place_entity(UndergroundBelt) always makes an INPUT. Place both ends with FLE, then call
    this on the EXIT end: it destroys it and re-creates it as an output facing `direction`
    ('north'/'east'/'south'/'west' = the belt's travel direction). Prints type, direction, neighbour."""
    return lua("local s=game.surfaces[1] local e=s.find_entity('underground-belt',{%s,%s}) if e then e.destroy() end "
               "local n=s.create_entity{name='underground-belt',position={%s,%s},direction=defines.direction.%s,force='player',type='output'} "
               "local a=n.neighbours rcon.print(n.belt_to_ground_type..' d'..n.direction..' nb='..tostring(a and (a.position.x..','..a.position.y)))"
               % (x, y, x, y, direction))


def belt_line(x0, y0, x1, y1, direction):
    """Lay a straight belt from (x0,y0) to (x1,y1) inclusive (same x or same y), every tile facing
    `direction`, walking along as needed. Exact routing, unlike connect_entities. Returns tiles placed."""
    pts = []
    if x0 == x1:
        st = 1 if y1 >= y0 else -1
        pts = [(x0, y0 + st * i) for i in range(int(abs(y1 - y0)) + 1)]
    else:
        assert y0 == y1, "belt_line: segment must be horizontal or vertical"
        st = 1 if x1 >= x0 else -1
        pts = [(x0 + st * i, y0) for i in range(int(abs(x1 - x0)) + 1)]
    n = 0
    for (x, y) in pts:
        pp = player_pos()
        if abs(pp.x - x) > 6 or abs(pp.y - y) > 6:
            move_to(Position(x=x + 1, y=y + 1))
        place_entity(Prototype.TransportBelt, direction=direction, position=Position(x=x, y=y))
        n += 1
    print(f"belt_line ({x0:g},{y0:g})->({x1:g},{y1:g}): {n} belts")
    return n


def make_peaceful():
    """Idempotent: peaceful mode on, expansion off, remove worms/spawners (open_world has
    worms ~170 tiles from spawn). Runs automatically when this file is loaded."""
    return lua("local s=game.surfaces[1] s.peaceful_mode=true game.map_settings.enemy_expansion.enabled=false "
               "local n=0 for _,e in pairs(s.find_entities_filtered{force='enemy'}) do e.destroy() n=n+1 end "
               "rcon.print(n)")


def journal_snapshot():
    """Compact machine-readable summary for JOURNAL.md handoffs: entity counts + research + inventory."""
    singles, groups = flatten_entities()
    counts = {}
    for e in singles:
        counts[e.name] = counts.get(e.name, 0) + 1
    for g in groups:
        counts[g.name + "-group"] = counts.get(g.name + "-group", 0) + 1
    rs = research_state()
    snap = {"tick": int(lua("rcon.print(game.tick)")), "entities": counts,
            "inventory": inv_dict(inspect_inventory()),
            "researched": [t for t in rs["researched"] if t != "automation-science-pack"],
            "current_research": rs["current"], "iron_made": rs["made_iron"], "copper_made": rs["made_copper"]}
    print(snap)
    return snap


def helpers_help():
    print("helpers: status_report(show_ok=True, radius=None) refuel_all(min_fuel=5, amount=20, fuel=None, positions=None) "
          "find_space(w,h,near,proto=None,pad=2) gather(resource,qty) collect(item=None,min_count=1) "
          "wait_for(pred,timeout=60,step=5) advance(seconds=60) game_tick() produced(item) check_growth(item,seconds=30) "
          "rate(items=None,seconds=60) am_finished() scan(x0,y0,x1,y1,types=None) lab_report() power_report() "
          "belt_items(x0,y0,x1,y1) ascii_map(x0,x1,y0,y1) limit_chest(x,y,slots=1) ug_output(x,y,direction) "
          "belt_line(x0,y0,x1,y1,direction) "
          "ensure_crafted(proto,n) place_new(proto,pos,direction=None) place_drill_furnace(ore=None,near=None,fuel=10) research_state() "
          "journal_snapshot() player_pos() make_peaceful() lua(code) inv_dict(inv) has_field(e,attr)")


make_peaceful()
print(f"agent helpers v{HELPERS_VERSION} loaded; helpers_help() lists them")
