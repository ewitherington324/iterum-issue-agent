---
name: iterum-repair-vs-replace
description: Produces a provisional repair-or-replace recommendation with a calibrated confidence score, a structured rationale, and the counter-argument against its own conclusion. Use inside the Iterum Issue Resolution Agent's decision loop once triage has finished and the appliance is confirmed out of warranty. The output routes the job either to autonomous scheduling (repair) or to engineer confirmation and PM approval (replace) — it is a routing decision, never a diagnosis.
---

# Repair vs. replace assessment

## Purpose

An engineer attending a fault needs to know what to bring. Booking a repair visit for an appliance that turns out to need replacing costs a second visit, several more days of resident disruption, and the property manager's confidence. Booking a replacement for something a £40 part would have fixed wastes several hundred pounds of the property manager's money.

This skill makes that call before the engineer travels, from triage evidence and appliance history, and states how confident it is so the system can decide whether to act autonomously or ask a human.

It is doing something subtler than it looks. It is not diagnosing the fault — it is deciding which of two *preparations* is more likely to be right. An engineer arriving with a replacement unit who finds a repairable fault has lost very little. An engineer arriving with a toolbag who finds a dead compressor has lost the day.

## When to use this skill

Use it when all of the following hold:

- Triage has exited with `status: needs_engineer` and populated `evidence_for_assessment`.
- `check_warranty()` returned out of warranty.
- No escalation trigger is active.

Do not use it when triage resolved the issue, when the appliance is in warranty, when the resident has raised a dispute or a liability question, or when triage produced no usable evidence *and* the appliance record has no age or history. In that last case there is nothing to reason from; route to an engineer with an explicit "insufficient evidence to assess" flag rather than producing a recommendation that only looks informed.

## Required inputs

| Input | Source | If missing |
|---|---|---|
| Triage evidence — confirmed symptoms, ruled out, error codes, duration | `iterum-triage-steps` output | Assess on history alone, cap confidence at 0.5 |
| Appliance record — type, brand, model, install date | `get_appliance()` | See "age unknown" below |
| Prior issues on this appliance | `get_appliance()` | Treat as no history, note it |
| Comparable job outcomes | `search_similar_issues()` | Proceed; note the absence in the rationale |
| Indicative repair cost — parts and labour | Inventory / ops cost reference | Use cost bands, widen the band, lower confidence |
| Indicative replacement cost including installation | Ops procurement reference | As above |

## The vocabulary

Return one of Iterum's own four codes, not the words "repair" and "replace". The codes carry a distinction the words lose — B and C are both *repairable*, and they route differently anyway.

| Code | Meaning | Routes as |
|---|---|---|
| **A** | Beyond economic repair | Replacement |
| **B** | Repairable and worth repairing | Repair |
| **C** | Repairable, but low remaining future value | Replacement |
| **D** | In warranty — the manufacturer handles it | OEM handoff |

C is the one that gets under-used. An appliance past 7 years with a repairable fault and a mediocre cost ratio is often C rather than B: technically fixable, not worth fixing. Reaching for B because the repair is *possible* is the most common way this assessment goes wrong.

D should rarely reach you — warranty is checked during triage and in-warranty jobs exit before this point. If you find yourself reaching for D, something upstream missed it; return D and say so plainly rather than assessing an appliance that was never yours to assess.

## Assessment framework

Weigh all six factors. Where they agree, confidence is high; where they conflict, say so rather than picking a side quietly — the conflict is information the engineer needs.

**1. Appliance age.** **An appliance older than 7 years has limited remaining future value.** That is Iterum's own figure from its decision-analysis brief, it applies flat across appliance types, and it is the decision boundary — the same one the rules-based fallback uses, so that the A/B compares two implementations of one policy rather than two different policies.

The table below is *context, not a second boundary*. Use it to judge how far past or short of end-of-life an appliance is, and to explain that in the rationale. Do not use it to move the 7-year line: a 9-year-old oven is past the boundary even though ovens typically outlast that, and the useful thing to say is that it is past the line but young for its type.

| Appliance | Expected service life in rental use | Notes |
|---|---|---|
| Oven | 12–15 years | Parts availability, rather than economics, is usually what forces replacement |
| Hob — gas and ceramic | 12–15 years | |
| Hob — induction | 10–12 years | Electronics, not elements, are the limiting factor |
| Fridge-freezer | 10–12 years | Sealed-system failure is the dominant replacement trigger |
| Extractor hood | 10–12 years | Performance declines well before failure if filters are not maintained |
| Dishwasher | 8–10 years | |
| Tumble dryer | 8–10 years | Heat pump models are newer in the portfolio — treat the figure as unvalidated |
| Wine cooler — compressor | 8–10 years | |
| Washing machine | 7–8 years | |
| Washer-dryer | 6–8 years | Shorter than either standalone appliance — the same components do roughly twice the work |
| Microwave | 6–8 years | Shortest-lived appliance in a typical kitchen |
| Wine cooler — thermoelectric | 5–7 years | Worse repair economics than compressor models |

Note that two appliance types split by technology. A wine cooler at seven years is near end of life if thermoelectric and mid-life if compressor, and the same fault routes differently as a result. Establish the technology before applying this table.

**2. Repair economics.** **A repair costing more than about 70% of replacement is beyond economic repair.** Also Iterum's own figure, and also the boundary the fallback uses.

"About" is doing real work in that sentence. It is a reference point you may depart from with a stated reason — a 65% repair on a 9-year-old appliance with two prior repairs is a replacement on the whole picture, and a 74% repair on a two-year-old integrated unit may well not be. State the departure rather than silently rounding toward the line.

**3. Fault class.** Some faults are strongly diagnostic on their own.

*Repair-leaning across most appliance types:* pumps, filters, door seals and catches, heating elements, thermostats and sensors, inlet valves, hoses, fans, belts, carbon brushes, spray arms, hinges.

*Replace-leaning:* motor failure, compressor or sealed-system failure, drum bearing failure on a sealed drum, tank or chassis corrosion, control board failure on an appliance past two-thirds of expected life, and any fault where the part is discontinued.

*Depends heavily on age:* control boards, door interlocks, anything where the part is cheap but the labour is not.

A small number of faults are **determinative** — the fault class settles the recommendation on its own and the other five factors do not apply. See the section below before weighing anything else.

**4. Repair history.** Two or more repairs on the same appliance within twelve months leans replace regardless of the current fault's cost — the pattern matters more than the instance.

**5. Comparable outcomes.** What actually happened on similar jobs is the strongest evidence available, and it strengthens over time. Weight real Iterum outcomes above the heuristics in factors 1–3 when they conflict, and say in the rationale that you did.

**6. Parts availability and lead time.** A discontinued or long-lead part shifts the balance toward replacement even where the repair would otherwise be economic, because a resident without a working fridge for three weeks is a different problem from one without it for three days.

## Determinative faults

Most assessments are a weighing exercise. A few are not. Where a determinative fault is confirmed, the recommendation is fixed by the fault alone — do not run the six factors, do not let a young appliance or cheap-looking repair pull the answer the other way, and do not average the determinative fault against anything else present.

| Fault | Code | Why it is determinative |
|---|---|---|
| **Cracked, chipped or shattered hob glass** — ceramic or induction. Taxonomy slug `hob_surface_damage` | **A** — beyond economic repair | The glass is a large proportion of unit cost, it is rarely available as a separate part, and a cracked hob is unsafe to use because cracks admit moisture to live components beneath. Age is irrelevant: a six-month-old cracked hob is code A on the same reasoning as a ten-year-old one. Neither the 7-year line nor the 70% ratio applies |

**Confidence on a determinative fault is about the evidence, not the conclusion.** This distinction does real work here. Nobody disputes that a cracked hob needs replacing — the uncertainty is entirely about whether it is actually cracked, reported as it is by a resident over WhatsApp who may be describing a scratch, a heat mark, a surface scuff, or a crack in a pan.

So:

- **Crack confirmed by photo:** confidence 0.95. Do not go higher; leave headroom, because a photo can still mislead.
- **Resident-reported with no photo:** ask for one before assessing. This is the cheapest evidence in the whole system and it converts a weak assessment into a near-certain one in a single message.
- **Photo requested and not supplied, or unclear:** assess at 0.6 or below with the ambiguity named in `evidence_gaps`, and let the engineer confirm on site.

**Routing is unchanged.** A determinative replace recommendation still goes to engineer confirmation, and then to PM approval if it clears the cost threshold. It does not book a replacement directly, however confident it is. That is deliberate: until there is enough override data to show the model calls these correctly at scale, high confidence earns a better-prepared engineer, not less human oversight. Revisit once the override log can demonstrate it.

**Candidates for this list, not yet approved.** Do not treat these as determinative until an engineer has signed them off — they are noted here so the list can be extended deliberately rather than by drift.

- Microwave door, hinge, seal or interlock damage — a containment issue rather than a cosmetic one
- Sealed-system refrigerant leak on a fridge-freezer or wine cooler
- Cabinet or liner damage where insulation is compromised

## Confidence

Confidence describes the strength of the evidence, not the severity of the fault. A clearly dead 11-year-old appliance and a clearly repairable 2-year-old one can both score 0.9.

| Band | Meaning |
|---|---|
| 0.8–1.0 | Fault class is diagnostic, age and economics agree, and either comparable outcomes support it or the fault class is unambiguous |
| 0.5–0.79 | Factors mostly agree but the fault is not pinned down, or cost data is indicative rather than known |
| Below 0.5 | Factors conflict, triage produced little, or the appliance record is incomplete |

The loop exits rather than asking another question at `KNOBS.confidence_threshold` — currently 0.75, and live-editable from the demo UI because what underlies that number is still undecided. Read it from config rather than assuming it; if it moves, the skill should follow without being rewritten.

Resist the pull to inflate confidence. An over-confident repair recommendation books a visit that fails; an honestly low one produces a better-prepared engineer. The confidence figure is also the number that will be scored against engineer findings once override data accumulates, so a habit of inflation destroys the dataset the PRD is trying to build.

## Routing rules

| Code | Confidence | Route |
|---|---|---|
| **B** | ≥ `KNOBS.confidence_threshold` | Autonomous — inventory check, slot proposal, booking |
| **B** | below it | Autonomous, but the engineer brief must lead with the uncertainty and the replace-side argument |
| **A** or **C** | any | Engineer confirmation, then PM approval if replacement cost clears `KNOBS.pm_cost_threshold_gbp`. Never autonomous |
| **D** | any | Ops handoff, OEM process. No booking, no quote |

Two things to hold onto. First, a low-confidence B still books, because the PRD's position is that an engineer attending a job that turns out to need a replacement is today's baseline and an acceptable worst case — but the brief has to carry the doubt so the engineer can bring options.

Second, **high confidence never unlocks the replacement gate.** Confidence is not authority. A 0.95 code A goes to the engineer exactly like a 0.6 one, because the gate exists to protect against the model being confidently wrong, which is the failure mode confidence scores cannot detect in themselves. In the prototype this is enforced structurally rather than by instruction — `book_visit` is deliberately absent from `AUTONOMOUS_TOOLS`, so the approval callback fires whatever this skill returns. Do not write output that assumes it can be bypassed.

## Language constraints

Everything the resident sees must read as provisional routing. This is partly liability and partly accuracy — the assessment is made without anyone having looked at the appliance.

**To the resident, never:** name a failed component; state or estimate a cost; say the appliance needs replacing, is beyond repair, or is dead; promise what the engineer will do; give a date before scheduling has produced one.

**Instead:** describe the next step and who decides. "Based on what we've checked, this one needs an engineer to look at it. One of our engineers will confirm what's needed when they visit." If a replacement is likely: "It may need replacing rather than repairing — our engineer will confirm that before anything is arranged."

To the engineer and to ops, be direct and technical. The hedging is for the resident, not for the record.

**Check `human_in_thread` before `resident_message` is sent.** If ops has joined the WhatsApp thread, the assessment still runs, still logs, and still routes — but nothing goes to the resident. The engineer brief and the ops record are unaffected; only the resident-facing message is suppressed. See `iterum-escalation`.

## Expected output

This maps onto the `RepairVsReplace` model in `agent/reasoning.py`. The first four fields are that model as it stands; the rest are the additions this skill argues for.

```json
{
  "code": "A | B | C | D",
  "confidence": 0.0,
  "rationale": "Two or three sentences an engineer can scan in ten seconds",
  "key_factors": [
    "8 years old — past the 7-year line",
    "Repair £140 of £310 replacement — 45%, inside the 70% boundary",
    "Drain pump failure — repairable fault class",
    "One prior repair 14 months ago",
    "3 of 4 comparable jobs repaired successfully"
  ],
  "contra_indicators": [
    "What argues against this code, stated as strongly as you can put it"
  ],
  "evidence_gaps": ["No model number on record"],
  "limits_applied": [
    {"limit": 0.6, "reason": "Which confidence ceiling applied, and what missing evidence triggered it"}
  ],
  "determinative": false
}
```

`contra_indicators` is not decoration. Forcing an argument against your own conclusion improves calibration, and when an engineer overrides the code, the override log is far more useful if it shows whether the model had already seen the reason. It is the single highest-value addition to the existing model, because it is what turns the decision log from a record of outcomes into a record of reasoning.

`determinative` flags that the code came from the fixed-outcome list rather than the six factors, so the two are distinguishable later when the override data is analysed. Without it, a determinative call and a finely-balanced one look identical in the log and the accuracy figure means less than it should.

Note what is *not* here. Cost bands, parts and the engineer brief are already assembled by the calling code from the inventory and appliance records — they are not this call's job, and generating them here would mean the model inventing numbers the system already knows.

## Edge cases

**Install date missing.** Common in practice, since appliances are often inherited with a building. Estimate from model and serial where possible and say you estimated. If you cannot, treat age as unknown, cap confidence at 0.6, and name it in `evidence_gaps` — do not silently assume a mid-life appliance.

**No comparable jobs.** Expected early on. Proceed on the heuristics and say the comparables were absent. Do not manufacture false precision from a single loosely similar job.

**Integrated or built-in appliance.** Replacement cost is materially higher — the unit, the installation, sometimes carcass or door-furniture modification — and lead times are longer. This shifts the economics toward repair. Always check whether the appliance is integrated before applying the 70% ratio.

**Discontinued model or unavailable part.** Strong replace signal regardless of fault class. Flag the lead time explicitly, because it drives the earliest viable slot downstream.

**Multiple concurrent faults.** Assess them together, not one at a time. Three independent faults on one appliance is a replace signal even where each is individually cheap, and assessing them separately hides that.

**Resident or PM has already asked for a replacement.** Note it, do not weight it. A resident's preference is not evidence about the appliance, and a PM's is not either — the PM is the one who will pay for it and is entitled to an independent assessment.

**Cost data unavailable.** Widen the bands, drop confidence below 0.7, and say so. A recommendation without economics is weaker than one with them, and should look weaker.

**Appliance was replaced recently under a different issue.** Something is wrong with the record or the installation. Flag to ops rather than assessing.

**Fault class contradicts the age signal** — a replace-leaning fault on a two-year-old appliance, or a trivial fault on a twelve-year-old one. Do not average them. State the conflict, recommend the safer preparation, and put the conflict in `contra_indicators`. Determinative faults are the exception: there, the fault wins outright and age does not enter the reasoning.

**A determinative fault appears alongside other faults.** The determinative one decides the recommendation. Record the others in the engineer brief anyway — a hob being replaced is the right moment to deal with anything else in the same kitchen, and the engineer can only act on what they are told.

## Nuances

Write the rationale for the engineer who is going to disagree with you. That framing produces better reasoning than writing for a system that will accept it.

The same fault means different things at different ages. A failed heating element on a two-year-old machine is a repair without argument; on a nine-year-old machine it is a prompt to ask what else is close to failing.

Do not let triage's fluency inflate your confidence. A detailed triage transcript that ruled nothing out is still thin evidence — length is not signal.

Absence of a symptom is only evidence if someone checked for it. Read `ruled_out` carefully and distinguish it from "not mentioned".

Every recommendation, confidence score, rationale and subsequent engineer override is logged against the issue. That log is the only route to ever knowing whether this skill is any good, and eventually to earning the autonomy the replacement path does not currently have.

## Example

**Input:** Beko washer-dryer, installed 8 years ago, `washer_dryer_not_draining`. Repair £140, replacement £310 — a 45% ratio. Triage: water remains after cycle, door interlocked, filter cleared by resident with no improvement, no pump sound during the drain phase, fault developing over two weeks. One prior repair — door seal, 14 months ago. Four comparable drain-pump jobs: three repaired, one replaced.

**Output:**

- `code: "B"`, `confidence: 0.68`
- `rationale`: "Silent pump with a cleared filter points to drain pump failure — a repairable fault at 45% of replacement, well inside the 70% boundary, and three of four comparable jobs were repaired successfully. The appliance is past the 7-year line, which argues for C, but the cost ratio and the comparables both point the other way."
- `key_factors`: ["8 years — past the 7-year low-future-value line", "£140 of £310 — 45%, inside the 70% boundary", "Drain pump failure, repairable fault class", "One prior repair 14 months ago", "3 of 4 comparables repaired"]
- `contra_indicators`: ["Past the 7-year line, which on its own points to C", "Second repair in 14 months — a third inside the year would be poor value", "Washer-dryers reach end of life sooner than either standalone appliance", "Bearing wear at this age may present shortly after this repair"]
- `determinative: false`

This is the B-versus-C call the vocabulary section warns about, and it lands on B for stated reasons rather than because the repair is possible. Confidence at 0.68 sits below `confidence_threshold`, so it still books — but the engineer brief leads with the age and the prior repair, which is what lets the engineer look at the bearings while the machine is already open. That is the difference between one visit and two.

Had the ratio been 72% rather than 45%, the same fault at the same age would be A on the economics alone, with no weighing needed.
