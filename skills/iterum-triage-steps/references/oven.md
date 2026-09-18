# Oven — fault patterns

> **Status: draft, requires engineer validation.** The section keys are real Iterum taxonomy slugs, extracted from Iterum's issue history. The fault content under them is not — it is general appliance knowledge, not Iterum service data, and needs engineer sign-off row by row, especially the engineer-only signals.

Covers built-in and freestanding electric ovens, single and double. Gas ovens follow `hob.md` — no resident troubleshooting beyond describing what they observe.

## How to use this file

The caller passes a `fault_slug`. Match it to a section heading exactly; if nothing matches, fall back to `oven_other`. Causes run in descending likelihood; propose checks in order, within the three-step budget. An engineer-only signal means route now.

---

## `oven_not_heating` — Not Heating

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Clock set to auto or delayed start | Ask what the display shows | Commonest false fault; most ovens need the clock manual |
| Function selector on an unheated setting | Confirm function and temperature | Grill, light, defrost misread as faults |
| Child or control lock engaged | Ask whether a key or padlock symbol shows | |
| Power off at the wall, or breaker tripped | Ask whether the cooker switch is on, and whether other appliances work | Never reset a breaker |
| Element or thermostat failure | — | Engineer |

**Engineer-only signals:** other kitchen circuits dead (property fault — ops); any burning smell (`oven_smoke_or_smell`); one cavity heating, another not.

---

## `oven_uneven_cooking` — Uneven Cooking

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Door seal perished or dislodged | Look for gaps, tears or loose sections | Cheap part |
| Door not closing fully | Close it; check it sits flush | |
| Shelf position or overloading | Ask how the oven was loaded | |
| Fan motor failure (fan ovens) | Ask whether the fan is audible when on | |
| Partial element failure or thermostat drift | — | Engineer |

**Note:** "it takes ages" is a perception, not a reading. Ask what changed and when — gradual decline points to thermostat or element, sudden to discrete failure.

**Engineer-only signals:** grill or second cavity dead while the main oven heats. Record which functions work — it says which element to bring.

---

## `oven_door_issue` — Door Issue

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Pyrolytic lock not released | Ask whether the oven has fully cooled | Releases only below a set temperature; the one resident-fixable door fault |
| Perished or gapped seal | Look for gaps, tears or loose sections | Engineer; cheap part |
| Hinge failure — door drops or will not stay shut | Close it; look at how it sits | Engineer |
| Cracked or shattered glass | Look; photograph | Engineer. Stop using immediately |

**Engineer-only signals:** cracked or shattered glass; hinge failure; a door locked shut on a cold oven.

---

## `oven_not_powering` — Not Turning On

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Cooker switch at the wall off | Ask whether it is on | Commonest after works or a clean |
| Plug out or socket off (freestanding) | Confirm plug in, socket on | Looking and switching only |
| Wider power loss or tripped breaker | Ask whether other appliances work | If not, property fault — ops. Never reset a breaker |
| Display blank after a power cut | Ask what it shows | Some models need the clock set first |
| Internal supply or board failure | — | Engineer |

**Engineer-only signals:** whole circuit dead (ops); display dead with power confirmed; buzzing or scorching at the socket (escalate).

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `oven_controls_faulty` — Controls Not Working

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Child or control lock engaged | Ask whether a key or padlock symbol shows | |
| Clock in auto or delay mode | Ask what the display shows | Many ovens ignore controls until manual |
| Wet or greasy touch panel | Wipe dry with a cloth; retry | |
| Single knob or button dead | Confirm which controls respond | Engineer — selector switch |
| Panel responds, oven does not follow | — | Engineer — control board |

**Engineer-only signals:** controls dead with the display lit; board fault on an older appliance (see replace-leaning); any smell or noise with it.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `oven_error_code` — Display/Error Code

Record the code **verbatim** and pass it through, listed or not. Codes are brand-specific — the same string means different things by manufacturer. Never interpret an unlisted code.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Transient fault after a power interruption | Read out or photograph the code exactly; switch off at the wall a minute; say whether it returns | A cleared code can still recur; record either way |
| Component fault reported by the board | Ask what else it does — no heat, door locked, fan running | Engineer needs code plus behaviour |
| Unlisted or unfamiliar code | — | Pass through unchanged. Do not guess |

Brand-specific mappings to be added once engineers confirm the portfolio's brands.

**Engineer-only signals:** any code persisting after a power-off; any code with smoke, smell or a locked door; any code on gas.

---

## `oven_smoke_or_smell` — Smells or Smoke

**Not a triage fault.** Smoke, burning or an electrical smell is a safety escalation. No troubleshooting steps, no checks — hand to escalation.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Any smoke, burning or electrical smell | None — do not troubleshoot | Escalate immediately |

Give one instruction and nothing else: **stop using the appliance, do not touch it, and switch it off at the wall socket only if that is safe and dry to reach.**

**Engineer-only signals:** all of them. This category routes immediately, whatever steps remain.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `oven_noise` — Noise

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Loose shelf, tray or bakeware | Once cold, empty the cavity; listen again | Commonest false fault |
| Cooling fan running on after switch-off | Ask how long it runs | Normal on many models, up to 30 minutes |
| Clicking while heating | Ask whether it tracks temperature cycling | Thermostat; normal unless new or constant |
| Fan bearing wear — whine or grinding | Ask whether it only happens with the fan on | Engineer |
| Buzzing or humming from controls or socket | — | Stop using. Escalate |

**Engineer-only signals:** grinding, scraping or a rising whine; any noise with a burning smell (escalate); buzzing at the socket.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `oven_other` — Other

Nothing above matches. Confirm the symptom carefully in the resident's own words — what happens, when it started, what changed. Propose only checks safe on any oven, then route early rather than improvise.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Clock in auto or delayed-start mode | Ask what the display shows | Rules out the commonest false fault |
| Wrong function or temperature | Confirm function and temperature | |
| No power at the wall | Ask whether the cooker switch or socket is on | Looking and switching only |
| Oven light not working | Note it; propose nothing | A lamp change means reaching into the cavity past a live fitting — never asked of residents. Minor: pick up next visit |

**Engineer-only signals:** a symptom the resident cannot describe consistently; anything involving smoke, smell, water or door glass; anything unclear after those checks.

---

## Replace-leaning faults

Flagged so triage can stop early. The recommendation itself belongs to `iterum-repair-vs-replace`.

- Cavity or liner corrosion
- Control board failure on an appliance past roughly two-thirds of expected service life
- Multiple concurrent failures (for example element and fan together)
- Any fault where the part is discontinued — common on ovens, which outlive their parts supply

## Typical service life

12–15 years. The longest-lived appliance in a typical kitchen, which means an oven fault is more often a repair decision than a replacement one — and also that parts availability, rather than economics, is frequently what forces a replacement.
