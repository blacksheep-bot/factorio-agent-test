# Factorio Strategy Guide for an FLE Code-Writing Agent

Practical notes for an LLM agent that plays Factorio by writing Python against the
Factorio Learning Environment (FLE) tool API. The guide covers the build order, ratios,
milestones with checkable success criteria, failure modes and FLE-specific tips.

Primary sources:
- Paper: "Factorio Learning Environment", arXiv 2503.09617 (NeurIPS 2025 D&B), https://arxiv.org/abs/2503.09617
- Repo: https://github.com/JackHopkins/factorio-learning-environment (read at the Sept 2026 HEAD)
  - In-game manual: `fle/eval/open/MANUAL.md`
  - Pattern guide and stats: `fle/env/tools/agent.md`
  - Per-tool docs: `fle/env/tools/agent/<tool>/agent.md`
- Release notes: v0.2.0 https://jackhopkins.github.io/factorio-learning-environment/versions/0.2.0.html
  and v0.3.0 https://jackhopkins.github.io/factorio-learning-environment/versions/0.3.0.html
- Factorio wiki (game numbers): https://wiki.factorio.com/

---

## 0. Know which game you are in

| | Lab-play (throughput tasks) | Open-play |
|---|---|---|
| Start inventory | Large: 500 coal, 50 burner drills, 50 electric drills, 500 belts, 500 medium poles, 10 AM2, 2 boiler/pump/engine, ... (`fle/eval/tasks/throughput_task.py`) | **Empty** (`default_task.py`: `starting_inventory={}`) |
| Research | All technologies researched (`all_technology_reserached=True`) | **None** researched; you must research |
| Goal | Reach a target throughput (16 items or 250 fluid per 60 s) measured in a 60 s holdout after each step | Maximise production score (PS); 5,000 steps |
| Budget | 64 steps in v0.3, early stop on success (128 in the original paper) | 5,000 steps |

- The server is **Factorio 2.0.73** (`fle/cluster/run_envs.py`: `factoriotools/factorio:2.0.73`).
  Use 2.0 recipes and tech, not 1.1.
- In 2.0 the earliest techs are unlocked by **research triggers**, not science packs:
  - Electronics: craft 10 copper plates. https://wiki.factorio.com/Electronics_(research)
  - Steam power: trigger is about 50 iron plates; the wiki infobox is ambiguous. https://wiki.factorio.com/Steam_power_(research)
  - Automation science pack: craft one Lab. https://wiki.factorio.com/Automation_science_pack_(research)
  - Automation (assembling machine 1): the first real lab research, costing 10 red packs at 10 s each. https://wiki.factorio.com/Automation_(research)
- Do not assume a recipe is unlocked. If `craft_item` fails with a recipe error, check
  `get_research_progress` and the trigger list above.
- Production score:
  - Items are priced from raw-resource prices (iron ore 3.1, copper ore 3.6, coal 3, stone 2.4)
    plus value added per recipe step (`fle/env/tools/agent/score/server.lua`).
  - The **automated** score excludes manually harvested and hand-crafted value. Only machine
    output counts. Hand-crafting 300 chests scores nothing.
  - Complex intermediates are worth more than plates. Science packs and circuits beat plates.
  - The open-play prompt says: "Focus on building sustainable, scalable automation rather than
    manual crafting" (`fle/eval/tasks/task_definitions/unbounded/open_play_production.jinja2.md`).

---

## 1. Key numbers (Factorio 2.0)

Rates (wiki and `fle/env/tools/agent.md` "Useful statistics"):

| Entity | Rate / use | Fuel or power draw |
|---|---|---|
| Burner mining drill (2x2) | 0.25 ore/s = 15/min | 150 kW, about 2.25 coal/min (coal is 4 MJ) |
| Electric mining drill (3x3) | 0.5 ore/s = 30/min | 90 kW |
| Stone furnace (2x2) | iron/copper plate in 3.2 s, so 18.75 plates/min | 90 kW, about 1.35 coal/min |
| Assembling machine 1 (3x3) | crafting speed 0.5 | 75 kW |
| Assembling machine 2 | crafting speed 0.75 | 150 kW |
| Lab (3x3) | consumes packs at the tech's time per unit | 60 kW |
| Boiler (3x2) | 1.8 MW; 6 water/s to 60 steam/s | at full load about 0.45 coal/s = **27 coal/min** |
| Steam engine (3x5) | 900 kW; 30 steam/s | - |
| Offshore pump | 1,200 water/s | none |

Sources: https://wiki.factorio.com/Burner_mining_drill and https://wiki.factorio.com/Power_production

Ratios to memorise:
- **Burner drill to stone furnace is about 1:1.** A drill gives 15 ore/min and a furnace takes
  18.75/min. Exact balance is 5 drills : 4 furnaces.
  - Simplest automation: place the furnace on the drill's `drop_position`. No belt or inserter is needed.
- **Electric drill to stone furnace is 1 : 1.6**, or 5 drills : 8 furnaces.
- **Steam power in 2.0 is 1 offshore pump : 200 boilers : 400 engines.** The 1.1 ratio was 1:20:40.
  A single pump is never the bottleneck early on. **1 boiler : 2 steam engines.**
- **One steam engine (900 kW)** powers about 12 AM1, 10 electric drills or 15 labs.
  One boiler with two engines gives 1.8 MW.
- **Boiler coal:**
  - A boiler at full load burns about 27 coal/min. That is about 2 self-fuelled burner drills on
    coal (12.75 net each) or 1 electric drill on coal.
  - Early loads are small, so a boiler with 50 or more coal plus an inserter-fed coal belt or chest is fine.
- **Red science (automation pack):**
  - Recipe: 1 copper plate + 1 gear, 5 s. One AM1 makes 6/min.
  - Gear: 2 iron, 0.5 s. One AM1 makes 60/min.
  - **Ratio is 10 red assemblers : 1 gear assembler.**
  - Per 1 red/s you need 2 iron/s (6.4 furnaces) and 1 copper/s (3.2 furnaces).
  - A minimal 6/min line needs 1 iron furnace, 1 copper furnace, 1 burner drill each, 1 gear AM1 and 1 red AM1.
- **Electronic circuit:**
  - Recipe: 1 iron + 3 copper cable, 0.5 s. Copper cable: 1 copper gives 2 cables, 0.5 s.
  - **Ratio is 3 cable assemblers : 2 circuit assemblers.** Each circuit needs 1 iron + 1.5 copper.
- **Fuel endurance:**
  - 20 coal runs a burner drill for about 9 min and a stone furnace for about 15 min.
  - FLE's guide says to "always put 20+ fuel into all entities that require fuel".
- **Power poles:**
  - Small pole: 7.5-tile wire reach, 5x5 supply area. Recipe is 1 wood + 2 copper cable, giving 2 poles.
    It needs **wood**, so harvest trees with `harvest_resource(nearest(Resource.Wood), …)`.
  - Medium poles need steel.

Key 2.0 recipes for bootstrapping (verify with `get_prototype_recipe` before batch crafting):

| Item | Ingredients |
|---|---|
| Stone furnace | 5 stone |
| Burner mining drill | 3 gear + 3 iron plate + 1 stone furnace |
| Burner inserter | 1 iron plate + 1 gear |
| Transport belt (x2) | 1 gear + 1 iron plate |
| Pipe | 1 iron plate |
| Offshore pump | 2 pipe + 1 gear |
| Boiler | 1 stone furnace + 4 pipe |
| Steam engine | 8 gear + 10 pipe + 5 iron plate |
| Electronic circuit | 1 iron plate + 3 copper cable |
| Inserter | 1 circuit + 1 gear + 1 iron plate |
| Lab | 10 circuit + 10 gear + 4 belt |
| Assembling machine 1 | 3 circuit + 5 gear + 9 iron plate |
| Electric mining drill | 3 circuit + 5 gear + 10 iron plate |
| Wooden chest | 2 wood |
| Iron chest | 8 iron plate |

---

## 2. Opening build order (open-play, empty inventory)

Phases are ordered. Every phase ends with a verification print or assert.
Gather ores by hand only to bootstrap; automate as early as possible.

1. **Scout.**
   - `nearest(Resource.X)` for Coal, IronOre, CopperOre, Stone, Water and Wood.
   - `get_resource_patch` for coal and iron to learn sizes and bounding boxes.
   - Print all positions and store them as variables. The namespace persists between steps.
2. **Hand-harvest the seed kit.** Use `move_to` before every `harvest_resource`.
   - About 50 stone (enough for 10 furnaces), 50+ coal, 50+ iron ore and about 20 copper ore.
   - Optionally collect 10-20 wood from trees for chests and poles.
3. **Hand-smelt.**
   - Craft 2-4 stone furnaces and place them.
   - Insert coal (5-10) and ore. Poll until plates appear (see the timeout loop in section 5), then `extract_item`.
   - Smelting 50+ iron plates and 10+ copper plates should also fire the steam-power and electronics triggers.
4. **First automation: drill straight into furnace.**
   - Craft burner drills, which need gears, plates and a stone furnace.
   - On iron: place the drill, then `place_entity_next_to(StoneFurnace, drill.drop_position, …)`.
     Better still, place the furnace at `drill.drop_position`. Fuel both with 20+ coal.
   - Do the same on copper.
   - Start with 2-4 iron pairs and 1-2 copper pairs.
   - Check: furnace output `inspect_inventory(furnace)[IronPlate]` rises after `sleep(30)`.
5. **Coal automation.**
   - Burner drills on coal outputting into a wooden or iron chest, which is a buffer you collect from.
   - Or the self-fuelling pattern: drill to belt to burner inserter back into the drill
     (`MANUAL.md` §8, `agent.md` "Self-Fueling Coal Mining System").
   - Two burner drills facing each other refuel each other but stall after about 3 minutes
     without an extraction chest (https://wiki.factorio.com/Burner_mining_drill).
   - Coal is the clock of the whole early game. Losing fuel kills everything silently.
6. **Electricity.** Requires the steam-power tech.
   - Craft an offshore pump, a boiler and 1-2 steam engines.
   - Place the pump at water. The boiler and engine must not be on water.
   - Use `nearest_buildable(Prototype.Boiler, BuildingBox(w+4, h+4), pump.position)` to find
     legal land at least 4 tiles away, leaving room for pipes.
   - Connect the pump to the boiler, then the boiler to the engine, with `connect_entities(..., Prototype.Pipe)`.
   - Fuel the boiler with 20-50 coal. Later automate coal into it with a burner inserter from a coal belt or chest.
   - Check after `sleep(5)`: `get_entity(SteamEngine, pos).energy > 0`, and check the warnings and status fields.
7. **Circuits, lab and research.**
   - Hand-craft copper cable, then electronic circuits, then a Lab. Crafting the lab fires the
     automation-science-pack trigger.
   - Craft red science by hand (10 packs) for the **Automation** tech.
   - Place the lab and connect it to the engine with `connect_entities(engine, lab, Prototype.SmallElectricPole)`.
   - Insert packs, then `set_research(Technology.Automation)`.
   - Check that `get_research_progress` counts decrease.
8. **Assemblers.** After Automation research:
   - Craft AM1s. Gears are the first automated intermediate.
   - Feed the assembler from furnace output: output inserter, then belt (or chest), then input inserter.
   - Power it with small poles. `set_entity_recipe(assembler, Prototype.IronGearWheel)`.
9. **Automated red science.**
   - Iron line to gear AM1. Gears plus copper plate to red AM1, then inserter to lab (or chest).
   - Then research Logistics and Electric mining drill.
   - In the paper, the biggest open-play jump came after research and electric drills.
10. **Scale.**
    - Swap burner drills for electric drills: 1 electric drill feeds 1.6 furnaces.
    - Add furnaces, then add a circuit line (3 cable : 2 circuit).
    - Add steam engines as power demand grows; check `entity.status` for low power.

Layout rules (`fle/env/tools/agent.md` "TIPS WHEN CREATING STRUCTURES"):
- Keep at least 10 tiles between factory sections, and at least 20 for assembly blocks.
  This leaves room for belts and poles.
- "Keep it simple! Only use transport belts if you need them." Use furnaces or chests on the
  drill `drop_position` before building belts.
- Inserters are needed to move items into or out of furnaces, assemblers, chests, boilers and labs.
  The exception is a drill dropping directly into an entity.
- Place the producer first, then the destination, then connectors, then fuel (`MANUAL.md` §4).

---

## 3. Milestones for a 1-3 hour session, ordered by difficulty

Each milestone has a check you can run in code. Keep the scoreboard as variables and re-run the checks.

| # | Milestone | Success check (run after `sleep(30-60)`) |
|---|---|---|
| M1 | Resources scouted, seed kit gathered | Inventory has at least 50 stone, 50 coal and 50 iron ore; resource positions are stored in variables |
| M2 | First hand-smelt | At least 20 iron plates in inventory |
| M3 | **Automated iron plates** (burner drill into furnace) | `inspect_inventory(furnace)[IronPlate]` grows between two reads 30 s apart; drill status is not NO_FUEL or WAITING_FOR_SPACE |
| M4 | **Automated copper plates** | Same check on the copper furnace |
| M5 | **Automated coal** (self-fuelled or into a chest) | Chest coal count grows; drill fuel stays above 0 for 5 min |
| M6 | Scale smelting to at least 4 iron and 2 copper pairs | Combined plate rate of about 60/min or more (diff of inventories over 60 s) |
| M7 | **Electricity** (pump, boiler, engine) | `steam_engine.energy > 0`; boiler has fuel; no warnings |
| M8 | Lab placed and powered; Automation researched | `lab.energy > 0`; `get_research_progress(Automation)` reaches done; AM1 craftable |
| M9 | **Automated gears** (AM1 fed by an inserter from an iron source) | Output chest or downstream gear count grows; assembler status WORKING |
| M10 | **Automated red science** | Red pack count in the lab or chest grows without manual inserts; above 5/min sustained |
| M11 | Automated research loop | Research progresses with no manual pack inserts for 5+ min |
| M12 | Electric mining drills on iron, copper and coal; automated boiler fuel | Drills powered and WORKING; boiler fuel stays non-zero over 5 min |
| M13 | **Automated electronic circuits** (3 cable : 2 circuit AM) | Circuit count grows without manual input |
| M14 | Stretch goals: Logistics research, belts feeding several assemblers, inserter or green-science chain | Throughput of 16 or more per 60 s for the target item (the lab-play quota) |

Calibration:
- Original paper, Claude 3.5 Sonnet:
  - Lab-play: about 22% success rate, 7/24 tasks.
  - Open-play: median PS about 293k with 28 milestones. It built a lab, researched, and moved to
    electric drills around step 3k.
- Weaker models:
  - Never built production lines of more than 3 entities.
  - Failed on electronic circuits in open play.
- v0.3 (Sept 2025):
  - Frontier models (Claude Opus 4.1, GPT-5, Gemini 2.5 Pro, Grok 4) solved some of the harder
    half of lab tasks.
  - No model is reported to master open play.
- M10 (automated red science) is a strong result. M13 is excellent.

---

## 4. Failure modes seen in FLE, and how to avoid them

From the paper (§5, appendix), the v0.2 and v0.3 release notes, and the manual:

1. **Poor spatial reasoning.** The paper's most-cited failure.
   - Symptoms: entities placed on top of or too close to each other, no room for connections,
     misplaced or misrotated inserters, boilers placed on water.
   - Mitigations:
     - Use `nearest_buildable` with a `BuildingBox` padded by at least 2-4 tiles.
     - Use `place_entity_next_to(..., spacing=…)` instead of hand-computed coordinates.
     - Use `drop_position` and `pickup_position` for chaining.
     - Use `can_place_entity` before placing.
     - Print the returned `.position` and assert it with `is_close`.
2. **Not verifying topology.**
   - Agents checked that single entities existed but not that the chain actually flowed.
   - Mitigations:
     - After building, `sleep(10-30)` and then re-fetch every entity with `get_entity`.
       Returned objects are snapshots.
     - Check `status` and `warnings` on each one.
     - Assert that the *final* output count increases.
3. **Repeating the same failing fix.** Degenerate loops:
   - GPT-4o repeated one incorrect call for 78 steps.
   - Grok 4 had debug loops in v0.3.
   - A model asked for a reset 234 times after `nearest(Stone)` "failed".
   - Mitigations:
     - If a fix fails twice, change hypothesis.
     - Inspect the surroundings, try a larger radius, try a different patch, or rebuild elsewhere.
     - Never conclude that "the environment is broken".
4. **Breaking working structures.**
   - Lab-play scores often fell over time because agents broke working setups while fixing others.
   - Mitigations:
     - Treat working sections as frozen. Build new sections at least 10-20 tiles away.
     - Keep a registry dict of section name to entity positions and status.
5. **Half-completed builds after a mid-script crash.** v0.2 notes.
   - Mitigations:
     - Write small programs, about 10-40 lines with one purpose each.
     - Fix the error at the reported line.
     - **Do not re-run earlier successful lines.** They change state, for example by placing
       duplicates or spending inventory.
     - Inspect what exists before continuing.
6. **High error rates are normal.** 56% of steps in successful lab-play runs had errors; open-play
   error rates were 30-76%; v0.3 frontier models were at 23-41%.
   - Most v0.3 errors were *pragmatic*: a wrong belief about game state, not syntax.
   - Mitigation: re-observe state (inventory, entities) at the start of each program instead of
     trusting memory.
7. **Fuel starvation.** Burner drills, furnaces, burner inserters and boilers go idle silently.
   - Mitigations:
     - Insert 20+ coal everywhere.
     - Automate coal early.
     - Periodically check every burner entity for low fuel or a NO_FUEL status.
8. **Output blocked (`WAITING_FOR_SPACE_IN_DESTINATION`).** Nothing is collecting the drill or furnace output.
   - Mitigation: add an output inserter and chest, or a furnace at `drop_position`.
9. **Missing prerequisites.**
   - Common causes:
     - Crafting from ore instead of plates.
     - Placing an item that is not in inventory.
     - Acting without `move_to` first.
     - Research not unlocked.
     - No wood for poles.
   - Mitigations:
     - `get_prototype_recipe` first, then check inventory, then craft recursively.
     - Always `move_to` before harvest, place or insert.
10. **Short-sighted or local-optimum play.**
    - Gemini-2 hand-crafted 300+ wooden chests.
    - v0.3 agents shuttled items by hand into chest buffers instead of building logistics.
    - Hand-shuttling does not count toward the automated score, and lab-play's 60 s holdout defeats buffers.
    - Mitigation: each step should either add or extend an *automated* chain or fix one.
11. **Over-ambitious programs.**
    - A 100-line script that fails at line 74 wastes the sample.
    - Gemini wrote the longest programs and had the most code errors.
    - The FLE system prompt says: "Fail fast at gates; small action quanta."

---

## 5. FLE coding patterns that help

From the paper's Appendix H.4 system prompt and the repo's `unbounded_system.jinja2.md`:

- **Observe, branch, act.**
  - Start each program by reading state: `inspect_inventory()`, `get_entities()`, `get_entity(...)`.
  - Branch on what you read. Do not run a fixed linear script.
- **Assert preconditions early** with informative messages (`assert inv[Prototype.IronPlate] >= 9, f"need 9 plates, have {…}"`).
  - Claude's high assertion success rate correlated with its lead.
- **Print selectively.** Print positions, counts and statuses, not whole objects. Output is the only observation.
- **Use the persistent namespace.**
  - Store positions and entities in variables.
  - Define small helpers once: `ensure_crafted(proto, n)`, `refuel_all()`, `wait_for(pred, timeout)`, `section_ok(name)`.
  - Only Gemini 2.5 Pro did this regularly in v0.3, which shows the habit is rare.
- **Bounded waits.** Never use open-ended sleeps.
  ```python
  for _ in range(30):
      if inspect_inventory(furnace)[Prototype.IronPlate] >= 10: break
      sleep(1)
  else:
      raise Exception("timeout: check fuel/inputs")
  ```
- **Re-fetch after waiting.** `entity = get_entity(Prototype.X, entity.position)`, then check
  `.energy`, `.status` and `.warnings`.
- **Use `try/except` with a fallback** for uncertain placement, such as `nearest_buildable` raising
  when there is no space.
- **Use `connect_entities`.**
  - It routes belts, pipes and poles around obstacles.
  - Pass entities or positions; for belts use `drill.drop_position` to `inserter.pickup_position`.
  - Use `{Prototype.TransportBelt, Prototype.UndergroundBelt}` sets when crossing.
- **Fluids.** For chemical plants and refineries, call `set_entity_recipe` **before** connecting pipes.
- **Track ticks.**
  - The open-play feedback reports production-score delta, ticks elapsed and a "ticks cost" per step.
  - Long `sleep`s burn game time, which counts for production but also for fuel use.
- **Reflection or backtracking** gave about +6% on lab-play in v0.2.
  - On error, rewrite the failing program from the pre-error state rather than patching forward
    on a half-built factory.
- Vision or rendered maps did not significantly help as of v0.2. Rely on coordinates and prints.

---

## 6. One-screen checklist per step

1. What is my current milestone, and what is its success check?
2. Re-read state: inventory, the relevant entities, statuses and fuel.
3. Write the smallest program that moves one milestone forward. Assert preconditions at the top.
4. Place things with `nearest_buildable`, `place_entity_next_to` and `drop_position`. Use generous spacing.
5. Fuel everything with 20+ coal. Power assemblers and labs, then verify `energy > 0`.
6. Wait with a bounded loop, then verify the final output count increased.
7. If a step failed twice in the same way, change approach. Do not repeat or reset.
8. Never touch a working section. Expand somewhere else.
