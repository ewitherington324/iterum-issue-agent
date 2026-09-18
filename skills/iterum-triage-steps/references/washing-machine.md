# Washing machine — fault patterns

> **Status: draft, requires engineer validation.** The patterns and engineer-only signals below are a reasonable starting set, not Iterum service data. Before this goes anywhere near a resident, have an Iterum engineer review each row — particularly the "engineer-only signals" column, which is where an error is expensive. Once Iterum has enough closed jobs, rebuild these tables from actual outcomes rather than general knowledge.

> **No taxonomy coverage.** Iterum's issue history has no category for this appliance type, so `fault_slug` will never match a section in this file. It is kept as prose for a portfolio type that is in scope but not yet represented in the data — the reasoning call falls back to matching on the fault description instead of the slug, and the rules-based path has nothing to look up. Wash-side faults on a combined unit are keyed under `washer_dryer_*`; see `washer-dryer.md`, which carries those slugs.

This file is read on demand by `iterum-triage-steps`. It also serves as the rules-based fallback lookup when the reasoning call is unavailable.

## How to use this file

Match the resident's confirmed symptom to a section below. Within each section, causes are listed roughly in descending likelihood for a domestic machine in rental use. Propose resident-safe checks in the order given, subject to the three-step budget. If an engineer-only signal is present, stop triaging and route — the remaining steps will not change the outcome.

---

## Symptom: will not drain / water left in drum

Commonly presents with the door locked shut, since most machines interlock while water is present.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Blocked pump filter | Open the front access flap by hand or coin-turn, empty into a bowl, clear debris | Most common cause by a wide margin in rental properties. Always check first |
| Kinked or trapped drain hose | Look behind the machine *without moving it* — is the hose visibly bent or crushed | Only if the back is visible; never ask them to pull the machine out |
| Blocked sink trap / standpipe | Does the kitchen sink drain normally | A household drainage problem, not an appliance fault — route to ops, not an engineer |
| Drain pump failure | Listen during the drain phase — is there any hum or whirring at all | Silence with a clear filter is a strong pump-failure signal |
| Blocked pump impeller | — | Not resident-safe. Engineer |

**Engineer-only signals:** no pump sound at all with a clear filter; water leaking from underneath during drain; burning smell during the drain phase (escalate rather than route).

---

## Symptom: will not spin

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Unbalanced load | Redistribute the washing by hand and re-run a spin | Very common with single heavy items — one towel, a duvet |
| Residual water (see above) | Most machines will not spin until drained | If water is present, treat as a drain fault first |
| Wrong programme or spin speed set | Confirm the selected programme and spin setting | Frequent after a new resident moves in |
| Worn carbon brushes | — | Engineer. Cheap part, common on older direct-drive machines |
| Drum bearing failure | Ask what it sounds like during spin | Loud rumbling or grinding — see replace-leaning note below |
| Motor failure | — | Engineer |

**Engineer-only signals:** loud metallic grinding or rumbling on spin; drum moves excessively by hand; burning smell.

---

## Symptom: leaking water

Establish *where from* before anything else — it changes the cause entirely.

| Where from | Likely cause | Resident-safe check |
|---|---|---|
| Door | Perished or dirty door seal | Wipe the seal, look for tears or trapped debris |
| Detergent drawer | Overdosing, or blocked drawer | Check dosing; drawer can be pulled out and rinsed if it releases by hand |
| Underneath | Hose, pump or tank | None — engineer |
| Behind | Inlet or drain hose connection | Look only; do not tighten anything |

**Engineer-only signals:** anything from underneath; any water reaching a socket, extension lead or consumer unit — that is an escalation, not a routing decision.

---

## Symptom: will not start / no power

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Socket switched off, plug loose, or RCD tripped | Check the socket switch and that the plug is fully in; ask whether other kitchen sockets work | Do not ask them to reset a consumer unit breaker |
| Door not fully latched | Push the door firmly closed and re-select | Very common; machines give no useful feedback about this |
| Child lock engaged | Ask whether any padlock or key symbol shows on the display | Often triggered accidentally |
| Delay timer set | Check for a delay-start indicator | Frequently mistaken for a fault |
| Door interlock failure | — | Engineer |
| PCB / control board failure | — | Engineer. Cost varies hugely by age — see repair-vs-replace |

**Engineer-only signals:** other sockets on the same circuit dead (an electrical fault, route to ops as a property issue, not an appliance one); any burning smell or scorch marks around the plug — escalate.

---

## Symptom: not heating / clothes come out cold

Hard to confirm remotely, since residents often judge by feel through the door.

| Likely cause | Resident-safe check |
|---|---|
| Cold-wash programme selected | Confirm the programme and temperature setting |
| Heating element failure | — Engineer |
| Thermostat / NTC sensor failure | — Engineer |

**Note:** confirm the programme first. A meaningful share of "not heating" reports are eco or cold programmes selected by a resident who has not used that machine before.

---

## Symptom: excessive noise

| Sound | Likely cause | Route |
|---|---|---|
| Rattling, metallic, intermittent | Foreign object in drum or filter | Resident check — filter |
| Rumbling, constant, worse on spin | Drum bearings | Engineer — replace-leaning on most domestic machines |
| Grinding | Bearings or motor | Engineer |
| Banging, load-dependent | Unbalanced load, or transit bolts left in after a recent install | Resident check — redistribute; ask whether the machine was recently installed |

---

## Error codes

Record any displayed code verbatim and pass it through, whether or not it appears here. Codes are brand-specific and the same string means different things across manufacturers — do not interpret a code that is not listed for that brand.

Brand-specific code tables to be added once Iterum's engineers have confirmed the mappings for the brands actually installed across the portfolio. Until then, treat every code as evidence to carry forward rather than something to act on.

---

## Replace-leaning faults on this appliance type

Flagged here so triage can stop early. These do not mean "recommend replacement" — that is `iterum-repair-vs-replace`'s call — but they mean further resident troubleshooting will not help.

- Drum bearing failure on a sealed drum (labour typically exceeds the value of a mid-range domestic machine)
- Motor failure
- Tank or chassis corrosion
- Control board failure on a machine past roughly two-thirds of expected service life

## Typical service life

7–8 years in rental use. Shorter than owner-occupied, because of higher cycle counts and less consistent maintenance. Validate against Iterum's own replacement data when it exists.
