# Microwave — fault patterns

> **Status: draft, requires engineer validation.** General appliance knowledge, not Iterum service data. Engineer review required before resident use. The safety boundary below is the part that most needs signing off.

> **No taxonomy coverage.** Iterum's issue history has no category for this appliance type, so `fault_slug` will never match a section in this file. It is kept as prose for a portfolio type that is in scope but not yet represented in the data — the reasoning call falls back to matching on the fault description instead of the slug, and the rules-based path has nothing to look up. Nothing else covers this type. Until a category exists, a microwave issue reaches triage with an unmatched slug.

Covers countertop, built-in and combination (microwave/grill/convection) units.

---

## The safety boundary on this appliance

Read this before proposing anything.

A microwave contains a high-voltage capacitor that can retain a dangerous charge long after the appliance is unplugged. It is the one appliance in the portfolio where opening the casing can kill someone who has done everything else right. There is no version of "just have a quick look inside" that is acceptable here.

**Resident-safe actions are limited to:** operating the controls; opening, closing and inspecting the door; wiping the interior and the door seal; and lifting out the turntable, roller ring and glass plate, which are designed to be removed for cleaning.

**Never ask a resident to:** remove any panel or cover, including the internal waveguide cover; touch anything behind the casing; interfere with the door catches or interlocks; or operate the unit with the door damaged.

**Escalate immediately, do not troubleshoot,** if the resident reports arcing or sparking inside the cavity, smoke, a burning smell, or any damage to the door, door glass, hinges or seal. Arcing is a fire risk, and door damage means the unit may not be containing microwave energy — both are `iterum-escalation` category 1, and in both cases the instruction is to stop using it and unplug it if that is safe to reach.

---

## Symptom: runs but does not heat the food

The turntable turns, the light is on, the fan runs, the timer counts down — and the food comes out cold.

This is almost always magnetron, high-voltage diode or capacitor failure, and there is no resident-safe check for any of them. Confirm the symptom precisely (does the light come on, does the plate turn, does the timer run) and route.

Worth flagging to the assessment: on most domestic microwaves the cost of diagnosing and replacing a magnetron approaches or exceeds the cost of the unit, so this symptom is usually a replacement decision rather than a repair one.

---

## Symptom: will not start at all

| Likely cause | Resident-safe check |
|---|---|
| Door not fully closed | Open and close the door firmly, then reselect. The interlock is deliberately unforgiving |
| Child lock engaged | Look for a lock symbol on the display |
| Clock not set | Some models will not run until the clock is set, particularly after a power cut |
| Start not pressed after entering a time | Confirm the sequence they used — combination models often need an explicit start |
| Socket off or plug loose | Check the switch. Built-in units are often on a switched spur inside an adjacent cupboard |
| Door interlock switch failure | — Engineer |
| Fuse or control board failure | — Engineer |

Door-related non-faults are common enough to be worth the first step nearly every time.

---

## Symptom: turntable not rotating

| Likely cause | Resident-safe check |
|---|---|
| Glass plate or roller ring not seated on the coupler | Lift both out and refit — the plate has a moulded centre that must engage the drive coupling |
| Debris under the roller ring | Remove and wipe the cavity floor |
| Turntable motor failure | — Engineer |

One of the few genuinely resident-fixable microwave faults, and worth checking before routing.

---

## Symptom: noisy

| Sound | Likely cause | Route |
|---|---|---|
| Scraping or grinding | Roller ring or plate misseated | Resident check as above |
| Loud humming that is new | Magnetron or transformer | Engineer |
| Rattling | Loose item on top, or plate | Resident check |
| **Buzzing with visible arcing** | — | **Escalation, not triage** |

---

## Symptom: display or controls faulty

Touch panels fail with grease ingress and age. Ask them to wipe the panel dry as a single step, then route. A blank display with the unit otherwise dead is a power or fuse question — check the socket first.

---

## Error codes

Record verbatim and pass through. Do not interpret unlisted codes. Brand-specific tables to be added after engineer validation.

---

## Replace-leaning faults

On this appliance type, almost everything beyond the controls, the door catch and the turntable assembly is replace-leaning on cost grounds.

- Magnetron failure
- High-voltage transformer, diode or capacitor failure
- Any door, hinge, seal or interlock damage — a containment issue, not a cosmetic one
- Casing damage
- Waveguide cover burnt through with cavity damage behind it

## Typical service life

6–8 years. The shortest-lived appliance in a typical kitchen, and the one where repair economics most often favour replacement. Expect a high replacement rate relative to other appliance types, and do not read that as the assessment being miscalibrated.
