# Extractor hood — fault patterns

> **Status: draft, requires engineer validation.** Section keys are now real Iterum taxonomy slugs from Iterum's issue history. The fault content beneath them is still general appliance knowledge, not Iterum service data, and needs engineer sign-off before resident use.

Covers chimney, integrated, canopy and downdraft extractors, ducted and recirculating. Iterum's taxonomy calls this type "Hood"; the slugs below are `hood_*`.

This appliance has the highest self-fix rate in the portfolio. Grease and carbon filters are consumables, and a large share of reported "extractor broken" issues are a saturated filter or a switched-off isolator. Triage thoroughly here before dispatching anyone.

**Establish whether the hood is ducted (vents outside) or recirculating (filters and returns air to the room) before proposing steps** — the causes of weak extraction differ entirely.

## How to use this file

The caller passes a `fault_slug`. Match the section heading exactly. No match means use `_other`.

---

## `hood_fan_not_working` — Fan Not Working

Covers a fan that does not run, and a fan that runs while extraction is weak. Establish which first.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Fan on its lowest setting | Confirm the speed setting | Reported as weak extraction. Not a fault |
| Grease filter saturated | Release and wash the filters — see `hood_filter_issue` | Commonest cause of weak extraction. Both types |
| Carbon filter expired | Ask when it was last changed — see `hood_filter_issue` | Recirculating only. Highest-value question here |
| Isolator or fused spur off | Look for a separate wall switch — see `hood_not_powering` | Fan silent, lights dead with it |
| External vent flap stuck closed | Ask whether they can see the outside vent, and whether it opens when the hood runs | Ducted. Looking only |
| Ducting blocked, crushed or disconnected | — | Ducted. Engineer or ops. Looking only |
| Fan motor failure | Ask whether the motor makes any sound | Engineer |

**Engineer-only signals:** no motor sound with power confirmed; burning smell; anything inside the ducting; anything needing a panel, a tool, or the hood reached from a worktop.

---

## `hood_lights_not_working` — Lights Not Working

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Isolator or fused spur off | Check the wall switch — see `hood_not_powering` | Lights and fan dead together |
| Replaceable lamp failed | Confirm the fan still runs | Ops — a consumable replacement, not an engineer callout |
| Integrated LED module failed | Ask whether the whole strip is out | Engineer. On many units the module is not separately replaceable, making this a cost question rather than a repair |
| Driver or transformer failure | — | Engineer |

**Do not ask a resident to change a hood lamp.** It means reaching into a live fitting above a cooking surface. Establish lamp versus module by asking, never by asking them to look inside the fitting.

**Engineer-only signals:** lamp, fitting, module and driver alike.

---

## `hood_noise` — Noise

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Filter not seated correctly after cleaning | Release and refit the filters by hand | Rattling or buzzing. The usual cause after a clean |
| Loose ducting behind the unit | Ask them to describe the sound | Vibration or drumming. Engineer |
| Fan motor bearing | — | Grinding or whining. Engineer |
| Motor beginning to fail | Ask whether the noise rose suddenly | Engineer |

**Engineer-only signals:** grinding, whining or a sudden rise in noise; any noise behind the canopy or in the ducting.

---

## `hood_not_powering` — Not Turning On

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Isolator or fused spur switched off | Ask them to look for a separate switch — commonly on the wall above a worktop, or inside an adjacent cupboard — and check it is on | **Ask this first.** Residents rarely know it exists, and it is frequently switched off after a kitchen clean or at a new tenancy |
| Breaker tripped | Ask whether other kitchen circuits work | Never ask them to reset a breaker. Route it |
| Control panel or touch-sensor fault | — | Engineer |
| Motor failure | — | Engineer. See replace-leaning below |

A hood that **runs on its own, or will not switch off**, points the same way — usually grease ingress on the touch controls. Ask them to wipe the control surface dry as a single step, then route. If it cannot be switched off, tell them to isolate it at the wall switch.

**Engineer-only signals:** anything beyond the isolator and a wipe of the controls; a breaker that trips again; burning smell.

---

## `hood_filter_issue` — Filter Issue

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Grease filter saturated | The metal mesh filters below the hood release by hand, usually with a small catch or spring clip. They wash in hot soapy water or a dishwasher | Resident-safe. Refit dry and seated — see `hood_noise` |
| Carbon filter expired | Ask when it was last changed | Recirculating only. A **consumable, not a repairable part** — typically replaced every three to six months depending on use |
| Filter clip or catch broken | Ask whether the filter holds in place | Ops or engineer, depending on the part |

**The carbon filter question is the highest-value one on this appliance.** A hood with a filter that has never been changed extracts almost nothing while appearing to work perfectly, and the resident has no way of knowing. Ask it early. If the answer is "never" or "I didn't know", route it to ops as a consumable replacement rather than to an engineer as a fault.

**Engineer-only signals:** anything needing the hood opened, a tool, or reaching from a worktop.

---

## `hood_smell` — Smell

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Grease filter saturated | Release and wash the filters — see `hood_filter_issue` | Commonest cause. Stale cooking smell |
| Carbon filter expired | Ask when it was last changed — see `hood_filter_issue` | Recirculating only. The carbon removes the odour; expired, it does nothing |
| Run too briefly for the cooking | Ask when they switch it on and off | Run it from before cooking until well after, not only during. Not a fault |
| Hood undersized for the cooking | Ask what they cook and on which speed | Specification, not failure. Note for the property manager |
| Grease in the ducting | — | Ducted. Ops or engineer clean. Looking only |
| Burning or electrical smell | Switch off at the isolator or wall switch | **A different problem — escalate, do not triage** |

**Engineer-only signals:** any burning or electrical smell; smell persisting after clean filters and an in-date carbon filter; anything inside the ducting.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `hood_other` — Other

Confirm the symptom in the resident's own words, verbatim. Error codes are uncommon here; record any verbatim, photograph it, pass it through uninterpreted. Only these checks are safe for any hood fault.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Ducted or recirculating not established | Ask whether it vents outside or back into the room | Determines everything downstream |
| Isolator or fused spur off | Look for a separate wall switch | Ask first on anything dead — see `hood_not_powering` |
| Grease or carbon filter | Wash the grease filters; ask when the carbon filter was last changed | See `hood_filter_issue` |

A hood running on its own or refusing to switch off is covered under `hood_not_powering`. Route early rather than improvising.

**Engineer-only signals:** anything the checks above do not answer.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## Replace-leaning faults

- Motor failure — often a significant proportion of unit cost on integrated and canopy hoods
- Control panel failure where the panel is bonded to the unit
- Integrated LED failure where the module is not separately replaceable
- Corrosion or damage to the canopy

## Typical service life

10–12 years, though performance declines long before failure if filters are not maintained. Worth noting for the property manager: a filter replacement schedule prevents a meaningful share of these issues from ever being reported.
