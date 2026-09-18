# Wine cooler — fault patterns

> **Status: draft, requires engineer validation.** General appliance knowledge, not Iterum service data. Engineer review required before resident use.

> **No taxonomy coverage.** Iterum's issue history has no category for this appliance type, so `fault_slug` will never match a section in this file. It is kept as prose for a portfolio type that is in scope but not yet represented in the data — the reasoning call falls back to matching on the fault description instead of the slug, and the rules-based path has nothing to look up. Nothing else covers this type. Until a category exists, a wine cooler issue reaches triage with an unmatched slug.

Covers freestanding and integrated wine coolers and wine cabinets, single and dual zone.

Two very different technologies sit behind the same cabinet, and they fail differently. **Establish which one before proposing steps.**

- **Thermoelectric (Peltier).** Silent or near-silent, no compressor, cools by a fixed differential below ambient temperature — typically in the region of 10–15°C below the room. Common in smaller units.
- **Compressor.** Works like a fridge, audible cycling, can reach a set temperature largely independent of ambient.

If the resident does not know which they have, ask whether it hums and cycles on and off like a fridge, or runs silently with a faint fan.

---

## The most common non-fault

A large proportion of reported wine cooler faults are placement and ambient-temperature issues, not failures. Rule these out before anything else — they account for more reports on this appliance type than on any other.

| Situation | Why it presents as a fault |
|---|---|
| Thermoelectric unit in a warm room | It can only reach a fixed differential below ambient. In a 28°C kitchen in summer, a unit set to 8°C will never get there. This is the unit working correctly |
| Built-in unit with blocked ventilation | Integrated coolers vent through a front plinth or grille. If it is obstructed, or the unit was installed in a cabinet without the required clearance, it will underperform permanently |
| Unit recently moved | Compressor models need to stand upright for several hours before being powered on |
| Frequent door opening, or a part-full cabinet | Both increase recovery time significantly |
| Ambient below the unit's minimum rating | Garages and unheated utility rooms in winter — some units will not run correctly below a minimum ambient |

Ask where the unit is, what the room temperature is like, and whether anything changed recently. These questions cost one message and resolve a meaningful share of reports.

---

## Symptom: not reaching set temperature

| Likely cause | Resident-safe check |
|---|---|
| Ambient or placement (see above) | Ask about the room and the vents |
| Temperature set point changed | Confirm the display setting; ask whether anyone adjusted it |
| Door seal failure | Close the door on a sheet of paper and pull — firm resistance means the seal holds |
| Door not closing fully, or shelves obstructing | Check the door closes flush and nothing protrudes |
| Dual-zone settings confused | On dual-zone units, confirm which zone is being judged — the upper and lower zones have different ranges |
| Vents blocked internally by bottles | Ask whether bottles are packed against the rear wall |
| Fan failure (thermoelectric) | Ask whether any fan noise is audible | 
| Compressor or sealed system fault | Ask whether the compressor is audible and cycling | — Engineer |

**Engineer-only signals:** compressor running continuously without cooling; no compressor sound at all on a compressor model; frost or ice on internal pipework; any oily residue (refrigerant leak).

---

## Symptom: not cooling at all

Check the socket switch and plug first; integrated units are frequently on a switched spur inside an adjacent cupboard. Ask whether the display is lit — a dead display with a live socket is a control or power supply fault, and a lit display with no cooling points at the cooling system itself. Either way, engineer.

---

## Symptom: condensation or humidity inside

| Likely cause | Resident-safe check |
|---|---|
| Door seal failure | Paper test as above |
| High ambient humidity | Ask about the room — kitchens and utility rooms after cooking or laundry |
| Frequent door opening | Ask about usage |
| Drain channel blocked | — Engineer |

Some condensation on the inner glass is normal in humid conditions and is not a fault. Establish whether it is pooling or merely misting before routing.

---

## Symptom: noisy or vibrating

| Sound | Likely cause | Route |
|---|---|---|
| Bottles rattling | Shelves not level, or unit not level | Resident check — ask whether the unit rocks |
| Fan hum (thermoelectric) | Normal operation | Not a fault |
| Compressor cycling | Normal operation | Not a fault |
| Buzzing or rattling from the rear | Loose component or fan obstruction | Engineer |
| Grinding | Fan or compressor | Engineer |

Wine coolers are often installed in living spaces rather than kitchens, so residents notice noise that would go unremarked elsewhere. Establish whether the noise is new or simply newly noticed.

---

## Error codes

Record verbatim and pass through. Do not interpret unlisted codes.

---

## Replace-leaning faults

- Compressor failure
- Sealed system fault or refrigerant leak
- Thermoelectric module failure — on smaller units this frequently exceeds the value of the cabinet
- Door glass damage or seal failure where the door is not separately available

## Typical service life

8–10 years for compressor models; 5–7 for thermoelectric, which have a shorter working life and worse repair economics. Note this split for the assessment — the same fault at the same age routes differently depending on the technology.
