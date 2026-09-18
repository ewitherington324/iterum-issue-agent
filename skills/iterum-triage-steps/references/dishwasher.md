# Dishwasher — fault patterns

> **Status: draft, requires engineer validation.** Section keys are now real Iterum taxonomy slugs from Iterum's issue history. The fault content beneath them is still general appliance knowledge, not Iterum service data, and needs engineer sign-off before resident use.

Covers freestanding, integrated and slimline dishwashers. High self-fix rate — filters and spray arms account for a large share of reported faults and are designed to be resident-serviceable.

## How to use this file

The caller passes a `fault_slug`. Match the section heading exactly. No match means use `_other`.

---

## `dishwasher_not_draining` — Not Draining

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Blocked filter | The filter assembly sits in the base of the tub and lifts out by hand, usually a quarter turn. Rinse and refit | Most common cause. Check first |
| Blocked spray arm | The arms unclip by hand on most models — check the small holes for debris | Usually presents alongside poor cleaning |
| Sink waste or trap blocked | Does the kitchen sink drain normally? | A drainage problem, not an appliance fault — route to ops, not an engineer |
| New waste disposal unit with the blanking plug still fitted | Ask whether anything was fitted under the sink recently | Rare, but a complete non-fault |
| Kinked drain hose | Look behind *without moving the appliance* | Only if visible |
| Drain pump failure | Ask whether pump noise is audible when draining | Silence with a clear filter is a strong pump signal |

**Engineer-only signals:** water underneath the appliance; no pump sound with a clear filter; repeated anti-flood activation.

---

## `dishwasher_not_cleaning` — Not Cleaning Properly

Very often usage, not a fault. Work through these before routing.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Blocked filter | Lift out by hand, rinse, refit — see `dishwasher_not_draining` | Check first here too |
| Blocked or obstructed spray arms | Check the small holes; spin the arms by hand to confirm nothing blocks rotation | Unclip by hand |
| Overloading or shielding | Ask how items are stacked | Flat items shield what is behind them |
| Rinse aid or salt empty | Check the panel indicators | Resident refill, not a fault |
| Wrong or old detergent | Ask what is used and whether it changed | A change often dates the report |
| Low water temperature | Ask which programme is used | Eco programmes clean at lower temperatures and take longer |
| Heating element failure | — | Engineer |

**Note:** limescale in hard-water areas is gradual decline, not sudden fault. "Gradually got worse" with salt indicators ignored is maintenance.

**Wet dishes:** check the rinse aid first — on condensing machines, which most domestic dishwashers are, an empty reservoir is the commonest cause and a resident refill. Plastics staying wet is normal.

**Engineer-only signals:** cold water throughout the cycle with filter and arms clear; no wash action audible.

---

## `dishwasher_not_powering` — Not Turning On

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Socket off or plug loose | Check the switch; ask whether other kitchen sockets work | Integrated units often have a switched spur in an adjacent cupboard. Never a breaker reset |
| Door not latched | Push firmly closed and reselect | Looks dead, only inhibited |
| Child lock engaged | Look for a key or padlock symbol | Common after wiping the panel |
| Delay start set | Check for a delay indicator | Not a fault |
| Interlock or control board failure | — | Engineer |

**Engineer-only signals:** dead with power confirmed at the socket; any burning smell; anything behind or beneath the appliance.

---

## `dishwasher_leaking` — Leaking

Establish where the water comes from before anything else.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Door seal dirty, perished or torn | Wipe the seal and its seating with a cloth, then look along it | Wiping is resident-safe and often resolves it. Replacement is engineer |
| Detergent overdosing causing foam | Ask what is dosed and how much | Foam escapes at the door. Reduce and rerun |
| Hose, pump or tank | Water underneath — catch it with a bowl or towel | Engineer |
| Overfilling or levelling | Water at the base at the front | Engineer — levelling needs it moved |

If water is running freely: switch off at the wall socket and close the isolation valve under the sink if accessible.

**Any water reaching a socket or consumer unit is an escalation, not a routing decision.**

**Engineer-only signals:** water underneath; repeated anti-flood activation; anything needing the appliance moved or a panel removed.

---

## `dishwasher_door_issue` — Door Issue

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Not latching, or contents fouling the door | Push firmly closed; ask whether anything protrudes from the top rack | Most common. If it will not start at all, see `dishwasher_not_powering` |
| Seal dirty or sticky | Wipe with a cloth | Resident-safe |
| Seal perished or deformed | Look along the seal | Engineer |
| Door heavy, dropping or springing open | — | Hinge or spring. Engineer. Never adjust |
| Integrated door panel loose | — | Engineer. Never a resident task |

**Engineer-only signals:** hinge, spring or interlock work; seal replacement; any panel removal or refitting.

---

## `dishwasher_error_code` — Error Code

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Displayed code or flashing fault light | Record verbatim; photograph the display | Pass through unchanged |

Never interpret an unlisted code, and never ask a resident to cycle power to clear one. Brand-specific tables follow engineer validation.

**Engineer-only signals:** all code interpretation and clearing.

---

## `dishwasher_smell` — Bad Smell

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Dirty filter | Lift out by hand, rinse, refit | Most common cause |
| Food trapped in the filter housing or spray arms | Unclip the arms by hand; check the holes | Resident-safe |
| Standing water or soiled drain hose | Ask whether water sits in the base between cycles | Standing water routes as `dishwasher_not_draining` |
| Only cold or eco cycles run | Ask which programme is normally used | Low temperatures leave grease behind |
| Door kept closed between cycles | Ask whether it is left ajar to dry | Damp tub, then mould at the seal |

Resident-safe sequence: clean the filter, wipe the seal, run a hot cycle empty. Route if it persists after all three.

**Engineer-only signals:** any burning, chemical or electrical smell; smell persisting after a clear filter, a wiped seal and a hot empty cycle.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `dishwasher_noise` — Noise

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Items rattling together or against the spray arm | Ask how the racks are loaded; spin the arms by hand for clearance | Most common. Not a fault |
| Cutlery basket overloaded | Ask whether it is packed | Rattles against the door or arm |
| Foreign object in the filter housing | Lift the filter out and look — glass, a stone, a bone | Hands only |
| Machine not level | Ask whether it rocks during a cycle | Levelling needs it moved — engineer |
| Wash motor or pump | Ask them to describe the sound | Grinding or a loud hum is the wash motor |

**Engineer-only signals:** grinding; loud humming from the base; any noise needing the appliance moved or opened to locate.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `dishwasher_stopping_midcycle` — Stopping Mid-Cycle

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Door not latching fully | Push firmly closed and restart | See `dishwasher_door_issue` |
| Anti-flood device triggered | Ask whether the hose has a bulky box at the tap end and whether an indicator shows | Water detected. Do not reset repeatedly |
| Water or power interrupted | Check the valve under the sink and the socket switch | Often knocked or closed during other work |
| Programme longer than the resident expects | Ask which programme and its duration | Eco cycles run for hours and pause at temperature. Not a fault |
| Thermal cut-out | Ask whether it stops at the same point each time | Engineer |

Repeated mid-cycle stops route to an engineer regardless of which check clears.

**Engineer-only signals:** repeated anti-flood activation; stopping at the same point each cycle; any code shown at the stop — record it verbatim.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `dishwasher_other` — Other

Confirm the symptom in the resident's own words, verbatim. These checks are safe for any dishwasher fault, and cover not filling, which has no slug of its own.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Water supply isolated | Ask whether the valve under the sink is open | Commonest not-filling cause. Often closed during other work and forgotten |
| Anti-flood device triggered | Ask about a bulky box at the tap end and any indicator | Water detected somewhere. Route |
| Kinked inlet hose | Look only, do not move the appliance | Only if visible |
| Blocked filter | Lift out by hand, rinse, refit | Worth doing on almost any report |
| Inlet valve or filter screen | — | Engineer |

Route early rather than improvising.

**Engineer-only signals:** anything the checks above do not answer; anything requiring the appliance to be moved, opened or unpanelled.

---

## Replace-leaning faults

- Tank leak or corrosion
- Wash motor failure
- Control board failure on an appliance past roughly two-thirds of expected service life

## Typical service life

8–10 years.
