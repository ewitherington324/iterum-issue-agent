# Hob — fault patterns

> **Status: draft, requires engineer validation.** Section keys below are real Iterum taxonomy slugs, taken from Iterum's issue history. The fault content under them is still general appliance knowledge, not Iterum service data, and needs engineer sign-off — the gas section especially, which must be reviewed by a registered engineer before this reaches a resident.

---

## Gas hobs — read this first

Three technologies — gas, induction, ceramic-electric — with different fault sets and very different safety boundaries. **Establish which the hob is before proposing anything. If it cannot be established, treat it as gas and propose nothing.**

Work on gas appliances is restricted by law to engineers on a national registration scheme (Gas Safe in the UK, with equivalents elsewhere). This is a legal boundary, not a judgement call, and **it applies across every slug below**. Wherever a section names a gas cause, the only permitted resident actions are:

- Describing what they observe — which burners light, what the flame looks like, what they hear.
- Checking that burner caps and crowns sit flat and correctly seated, clean and dry. These lift off and on by hand and are designed to be removed for cleaning.
- Nothing else. Not the ignition, not the jets, not the supply, not the connection.

| Gas signal | Meaning | Route |
|---|---|---|
| **Yellow or orange flame, or sooting on pans** | **Incomplete combustion** | **Stop using. Engineer urgently** — carbon monoxide risk. A blue flame is correct |
| **Smell of gas** | — | **Escalation, not triage.** Follow `iterum-escalation` category 1 immediately |

---

## How to use this file

The caller passes a `fault_slug`. Match it exactly against a section heading below; no match means use `_other`. Within a section the likely cause depends on the technology, so tables are split by technology where it matters. Route immediately on any engineer-only signal.

---

## `hob_not_heating` — Not Heating

| Likely cause | Technology | Resident-safe check | Notes |
|---|---|---|---|
| Pan not ferrous, or too small for the zone | Induction | Fridge magnet on the pan base; no firm stick, no heat | The commonest induction "fault" |
| Control or child lock | Induction/ceramic | Key or padlock symbol showing? | |
| Isolator off, breaker tripped | Induction/ceramic | Wall cooker switch on? Other kitchen appliances working? | Never a consumer-unit reset |
| Caps or crowns dislodged, wet, dirty | Gas | Lift off, dry, reseat flat by hand | The only permitted gas action |
| Element, thermostat, inverter board, blocked gas ports | All | — | Engineer |

**Engineer-only signals:** nothing heats with a ferrous pan and the lock off; other kitchen circuits dead (property fault — route to ops); burning smell (escalate); a gas hob still failing after caps are reseated.

---

## `hob_not_powering` — Not Turning On

| Likely cause | Technology | Resident-safe check | Notes |
|---|---|---|---|
| Cooker isolator off, or breaker tripped | Induction/ceramic | Wall switch on? Other kitchen appliances working? | Never ask them to reset the consumer unit |
| Socket switched off | Socket-fed only | Switch off and back on at the wall socket | |
| Lock on, or blank after a power cut | Induction/ceramic | Key or padlock symbol? What shows on the display? | |
| No spark on ignition | Gas | Confirm caps seated, burner dry | Otherwise engineer — ignition module or wet electrodes |
| Supply or main board failure | All | — | Engineer |

**Engineer-only signals:** dead with power confirmed at the isolator; whole kitchen circuit dead; any burning smell.

---

## `hob_single_zone_fault` — One Zone Not Working

| Likely cause | Technology | Resident-safe check | Notes |
|---|---|---|---|
| Power sharing between paired zones | Induction | Was the neighbouring zone in use? | Normal design behaviour |
| Pan unsuitable for that zone | Induction | Magnet test it; does another pan work there? | |
| Wrong control mapped to the zone | All | Which control do they turn for it? | |
| Cap misseated on that burner | Gas | Lift off, dry, reseat flat | Nothing further |
| Element, switch, coil or inverter failure | Induction/ceramic | Confirm control position, lock off | Engineer. Stop using that zone |

**Engineer-only signals:** a zone failing with a ferrous pan, no power sharing and the lock off; a zone that will not switch off. Record which zone — it tells the engineer which part to bring.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `hob_controls_faulty` — Controls Unresponsive

| Likely cause | Technology | Resident-safe check | Notes |
|---|---|---|---|
| Control or child lock | Induction/ceramic | Key or padlock symbol showing? | By far the most common cause |
| Wet, greasy or covered panel | Induction/ceramic | Wipe dry; clear anything resting on it | |
| Controller hung after a power cut | Socket-fed only | Switch off at the socket, wait, switch back on | |
| Gloves, plasters, long nails | Induction/ceramic | How are they touching the panel? | |
| Knob or touch board failure | All | Describe only | Engineer |

**Engineer-only signals:** panel dry, clear and unlocked but still unresponsive; zones selecting themselves; any control that will not switch a zone off.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `hob_error_code` — Display/Error Code

Record the code verbatim and pass it through whether or not it is listed. **Never interpret an unlisted code.** Induction code sets are extensive and brand-specific — the same characters mean different things across manufacturers.

| Likely cause | Technology | Resident-safe check | Notes |
|---|---|---|---|
| Residual heat or lock symbol read as a code | Induction/ceramic | Does it clear as the surface cools? Key or padlock symbol? | Not a fault |
| Pan-detection code | Induction | Magnet test the pan | |
| Overheat cut-out | Induction | Anything stored below the hob, blocking ventilation? | |
| Any other code | All | Record verbatim; photograph the display | Engineer |

**Engineer-only signals:** any code recurring once the hob has cooled and ventilation is clear; any code with a burning smell. Brand tables to follow once engineers confirm portfolio mappings.

---

## `hob_surface_damage` — Cracked Surface

**A cracked, chipped or shattered ceramic or induction hob: stop using it immediately. No troubleshooting. Route to an engineer.** Cracks admit moisture to live components beneath, so the risk is electrical as well as injury. It is a determinative replacement at any age — `iterum-repair-vs-replace` treats it as a fixed outcome, not a weighing exercise.

**Get a photo during triage if there is any way to do so.** A resident may be describing a scratch, a heat mark or a surface scuff rather than a crack, and those are cosmetic. The photo is the cheapest evidence in the system, and it is what moves the downstream assessment from uncertain to near-certain.

| Likely cause | Technology | Resident-safe check | Notes |
|---|---|---|---|
| Impact, thermal shock from cold liquid on a hot surface, or a chipped edge | Induction/ceramic | Photograph only. Do not use the hob | Determinative replacement |
| Scratch, scuff or heat mark, not a crack | Induction/ceramic | Photograph; does a fingernail catch in it? | Cosmetic if the surface is intact |
| Cracked cap, damaged pan support | Gas | Photograph and describe | Engineer — part, not hob, replacement |

**Engineer-only signals:** all of them. There is no resident-safe repair or workaround for a damaged hob surface.

---

## `hob_noise` — Noise

Induction hobs are audibly active in normal use. Establish whether the noise is new, and whether it tracks the setting or the pan.

| Likely cause | Technology | Resident-safe check | Notes |
|---|---|---|---|
| Cooling fan, including after switch-off | Induction | Does it stop a few minutes after use? | Normal |
| Buzz or hum rising with the setting; clicking at low power | Induction | Does it change with a different pan? | Normal |
| Rattling pan support or burner cap | Gas | Reseat by hand | Nothing further |
| Fan bearing, or buzzing from controls | All | — | Engineer. Stop using |

**Engineer-only signals:** grinding or screeching; noise with a burning smell; noise continuing with the hob off. Hissing on a gas hob with any odour is a gas escalation, not triage.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `hob_other` — Other

Use when no slug above fits. Confirm the technology and the symptom first — reports here are usually imprecise rather than unusual. Propose only universally safe checks: looking, listening, smelling, photographing, wiping, and switching off at the socket where socket-fed.

| Likely cause | Technology | Resident-safe check | Notes |
|---|---|---|---|
| Symptom not pinned down | All | Which zones, which controls, when it started, what changed | |
| Misattributed — oven, grill or extractor | All | Establish which appliance is affected | Route to the correct reference |
| Residue or staining | Induction/ceramic | Wipe with a cloth | Not a fault |
| Anything else | All | — | Engineer. Route early rather than improvising |

**Engineer-only signals:** anything unexplained once technology and symptom are established.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## Replace-leaning faults

- **Cracked, chipped or shattered ceramic or induction glass — treated as determinative.** This is a replacement at any age, and `iterum-repair-vs-replace` handles it as a fixed outcome rather than a weighing exercise. Get a photo during triage if there is any way to do so: it is the cheapest evidence in the system and it is what moves the assessment from uncertain to near-certain
- Induction generator or inverter board failure
- Multiple zone failures
- Any gas hob fault where parts are discontinued

## Typical service life

12–15 years for gas and ceramic; 10–12 for induction, where the electronics rather than the elements tend to be the limiting factor.
