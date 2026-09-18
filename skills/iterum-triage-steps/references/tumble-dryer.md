# Tumble dryer — fault patterns

> **Status: draft, requires engineer validation.** General appliance knowledge, not Iterum service data. Engineer review required before resident use.

> **No taxonomy coverage.** Iterum's issue history has no category for this appliance type, so `fault_slug` will never match a section in this file. It is kept as prose for a portfolio type that is in scope but not yet represented in the data — the reasoning call falls back to matching on the fault description instead of the slug, and the rules-based path has nothing to look up. Drying faults on a combined unit are keyed under `washer_dryer_not_drying`; see `washer-dryer.md`.

Three technologies — vented, condenser and heat pump — with overlapping but distinct fault sets. **Establish which type before proposing steps**, since the filters differ and the wrong instruction wastes a step.

**Fire risk note.** Lint accumulation is the primary fire risk on this appliance type. Any report of a burning smell, scorching or smoke is an escalation under `iterum-escalation` category 1, not a troubleshooting step — and it takes precedence even mid-conversation.

---

## Symptom: not drying, or taking far longer than usual

Nearly always a filter or airflow problem. Work through in this order.

| Likely cause | Resident-safe check | Applies to |
|---|---|---|
| Lint filter blocked | The filter in or around the door opening lifts out by hand — clear it and refit | All types |
| Condenser filter blocked | A second filter behind a flap at the base of the machine, usually released by hand. On heat pump models this is the evaporator filter | Condenser, heat pump |
| Water container full | Many models stop or refuse to run when the container is full — it lifts out and empties at a sink | Condenser, heat pump |
| Vent hose kinked, crushed or blocked | Look at the hose *without moving the machine* — is it visibly bent or trapped | Vented |
| External vent flap stuck or obstructed | Ask whether they can see the outside vent and whether it opens | Vented |
| Overloading | Ask how full the drum was — drying capacity is lower than wash capacity | All types |
| Load too wet going in | Ask what spin speed the washing machine used | All types. A low spin leaves far more water to remove |
| Heat pump evaporator fins clogged | — | Engineer. Heat pump only |
| Heating element or thermostat failure | — | Engineer |

**Note:** residents very commonly clean the door lint filter and do not know a second filter exists. Ask specifically about the lower flap rather than asking whether they have "cleaned the filter".

---

## Symptom: not heating at all

| Likely cause | Resident-safe check |
|---|---|
| Programme selected is air-dry or cool | Confirm the programme |
| Thermal cut-out tripped by restricted airflow | Clear all filters as above and retry — but if it trips repeatedly, route |
| Element or thermostat failure | — Engineer |

Repeated thermal cut-out is an engineer job and should not be reset around. It is a protection device doing its job, and the underlying airflow restriction is what needs finding.

---

## Symptom: will not start

| Likely cause | Resident-safe check |
|---|---|
| Door not fully latched | Push firmly closed and reselect |
| Water container full | Empty and refit |
| Child lock engaged | Look for a key or padlock symbol |
| Delay start set | Check for a delay indicator |
| Socket off or plug loose | Check the switch |
| Door catch or interlock failure | — Engineer |

---

## Symptom: noisy

| Sound | Likely cause | Route |
|---|---|---|
| Rattling, intermittent | Foreign object in the drum or filter housing | Resident check — empty drum, check filter |
| Squealing or rhythmic rubbing | Belt or drum support rollers | Engineer |
| Rumbling or grinding | Drum bearings | Engineer |
| Loud humming without drum rotation | Belt broken, or motor | Engineer |

---

## Symptom: clothes come out creased, damp in patches, or over-dried

Usually load-related — sensor drying reads moisture at the drum and is confounded by overloading, mixed fabric weights, or fabric conditioner residue on the sensor bars. Ask about load composition before routing. On condenser and heat pump models, a partially blocked condenser also produces uneven results before it produces no results.

---

## Error codes

Record verbatim and pass through. Do not interpret unlisted codes. Brand-specific tables to be added after engineer validation.

---

## Replace-leaning faults

- Heat pump compressor failure — typically exceeds the value of the machine
- Drum bearing failure on a sealed drum
- Motor failure
- Cabinet or drum damage

## Typical service life

8–10 years for vented and condenser; heat pump models are newer in the portfolio and the service life figure should be treated as unvalidated until Iterum has its own data.
