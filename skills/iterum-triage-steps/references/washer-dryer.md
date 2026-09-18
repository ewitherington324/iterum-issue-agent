# Washer-dryer — fault patterns

> **Status: draft, requires engineer validation.** Section keys are now real Iterum taxonomy slugs from Iterum's issue history. The fault content beneath them is still general appliance knowledge, not Iterum service data, and needs engineer sign-off before resident use. This file carries wash-side and dry-side patterns together, because the taxonomy has a single laundry appliance type.

Combined units run harder than either standalone appliance and fail more often. One board and one motor serve both functions, so a single component failure can take out both halves at once — a stronger replace signal than the same fault on a standalone machine.

## How to use this file

The caller passes a `fault_slug`. Match the section heading exactly. No match means use `_other`.

**Establish which half the fault is in before proposing anything.** "The washer-dryer isn't working" is two triage paths, and the resident-safe checks diverge at once. Where both halves are affected, say so in the handover.

---

## `washer_dryer_not_powering` — Not Turning On

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Socket off or plug loose | Check the switch and that the plug is home; ask whether other kitchen sockets work | Never a breaker reset |
| Door not fully latched | Push firmly closed and re-select | Very common. Machines give no useful feedback |
| Child lock engaged | Ask whether a padlock or key symbol shows | Often triggered accidentally |
| Delay timer set | Check for a delay-start indicator | Frequently mistaken for a fault |
| Door interlock failure | — | Engineer |
| Control board failure | — | Engineer. Takes out both halves. Replace-leaning |

**Engineer-only signals:** other sockets on the circuit dead (property fault, route to ops); any burning smell or scorching at the plug — escalate.

---

## `washer_dryer_not_draining` — Not Draining

Usually presents with the door locked, since the interlock holds while water is present.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Blocked pump filter | Small flap at the bottom front, opens by hand or coin-turn. Towel and a shallow bowl down first — water will come out | The most common cause by a wide margin. Always check first |
| Kinked or trapped drain hose | Look behind *without moving the machine* | Only if the back is already visible |
| Blocked sink trap or standpipe | Does the kitchen sink drain normally | Household drainage. Route to ops |
| Drain pump failure | Listen during drain — any hum at all | Silence with a clear filter is a strong signal |
| Blocked impeller | — | Engineer |

A drain fault degrades drying before it stops the wash. Poor drying reported *with* anything about drainage: treat drainage as primary.

**Engineer-only signals:** no pump sound with a clear filter; water from underneath; burning smell during drain — escalate.

---

## `washer_dryer_noise_during_cycle` — Excessive Noise

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Foreign object in drum or filter | Empty the drum; open the filter flap and look | Rattling, metallic, intermittent. Coins and underwires |
| Unbalanced load, or transit bolts left in | Redistribute by hand and re-run; ask whether it was installed recently | Banging, load-dependent |
| Drum bearings | Ask what it sounds like on spin | Rumbling, worse on spin. Engineer. Replace-leaning |
| Belt or drum rollers | — | Squealing or rhythmic rubbing. Engineer |
| Bearings or motor | — | Grinding, or humming without rotation. Engineer |

**Engineer-only signals:** loud metallic grinding or rumbling on spin; drum moves excessively by hand; any burning smell.

---

## `washer_dryer_door_issue` — Door Issue

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Water still in the drum | Ask whether water is visible through the glass | The interlock holds the door while water is present, so a door that will not open is often a drainage fault first — work `washer_dryer_not_draining` |
| Cycle still running or cooling | Check the display and whether the programme ended | Many machines hold the door a minute or two after |
| Child lock engaged | Look for a padlock or key symbol | |
| Seal dirty, or trapped item | Wipe round the seal by hand | Resident-safe |
| Handle, catch, hinge or interlock failure | — | Engineer |

**Engineer-only signals:** door that will not open with the drum confirmed empty; broken handle or catch; hinge work. Never ask a resident to force a door.

---

## `washer_dryer_not_filling` — Not Filling With Water Properly

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Tap turned off or part open | Ask them to check the tap serving the machine is fully open | An accessible isolation valve is resident-safe to turn. Common after other plumbing work |
| Kinked or crushed inlet hose | Look behind *without moving the machine* | Look only. Do not tighten anything |
| Anti-flood device tripped | Ask whether the hose has a bulky head at the tap end, and whether an indicator has changed colour | Stays shut once tripped. Engineer — and find out why |
| Mains supply interruption | Does the kitchen cold tap run normally | Property issue |
| Blocked inlet filter or valve failure | — | Engineer |
| Pressure sensor fault | — | Engineer. Fills and drains repeatedly, or reports a fill error with water present |

**Engineer-only signals:** tripped anti-flood device; any fill fault with the tap confirmed open and the hose unkinked; water appearing while idle.

---

## `washer_dryer_leak` — Leaking Water

Establish *where from* before anything else — it changes the cause entirely.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Door — perished or dirty seal | Wipe the seal; look for tears or trapped debris | Resident-safe |
| Detergent drawer — overdosing or blockage | Check the dose; the drawer can be pulled out and rinsed if it releases by hand | Very common. Resident-safe |
| Filter flap — cap not seated after cleaning | Re-seat the coin-turn cap, towel down | Resident-safe |
| Underneath — hose, pump or tank | None. Switch off at the socket | Engineer |
| Behind — hose connections | Look only; do not tighten anything | Engineer |

**Engineer-only signals:** anything from underneath; any water reaching a socket, extension lead or consumer unit — escalation, not a routing decision.

---

## `washer_dryer_not_spinning` — Not Spinning

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Unbalanced load | Redistribute by hand and re-run a spin | Very common with one heavy item — a towel, a duvet |
| Residual water in the drum | Look for standing water | Most machines will not spin until drained. Treat as a drain fault first |
| Wrong programme or spin speed | Confirm the selection | Frequent after a new resident moves in |
| Worn carbon brushes | — | Engineer. Cheap part, common on older machines |
| Drum bearings | Ask what it sounds like on spin | Loud rumbling. Engineer. Replace-leaning |
| Motor failure | — | Engineer |

A low spin also matters downstream: a load that enters the drying phase soaking will not dry.

**Engineer-only signals:** loud metallic grinding or rumbling on spin; drum moves excessively by hand; any burning smell.

---

## `washer_dryer_not_drying` — Not Drying Properly

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Load too large for the drying cycle | Ask how much was in the drum | Most common cause. Drying capacity is roughly half wash capacity and almost no resident knows this. A full wash load will not dry |
| Cold water tap not fully open | Ask whether the tap is fully open | Most washer-dryers condense using the cold supply. A partly closed tap leaves the wash working and the dry not — exactly the reported symptom |
| Drying stage not selected | Confirm the programme and any drying time or dryness level | Combined cycles often need it selecting explicitly |
| Blocked pump filter | Open the flap — towel and bowl first | Restricted drainage degrades condensing |
| Low spin before drying | Ask what spin the wash used | A wet load cannot dry in a normal cycle |
| Mixed fabric weights | Ask what was in the load | Towels and shirts will not finish together |
| Element, thermostat or condenser fault | — | Engineer. Uneven results before no results |

**Ask about the cold tap early.** Five seconds, costs nothing, resolves a meaningful share of "won't dry" reports.

**Engineer-only signals:** repeated thermal cut-out or a cycle stopping short; machine running very hot; water in the drum during drying with the filter clear; any burning smell, scorching or smoke — escalate mid-conversation if necessary.

---

## `washer_dryer_error_code` — Display/Error Code

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Displayed code or fault light | Record verbatim; photograph the display | Pass through unchanged, listed or not |

Never interpret an unlisted code — the same string means different things across brands. Washer-dryers use separate code ranges for wash and dry faults on many brands, so the code often tells the engineer which half failed, which makes capturing it accurately more valuable here than on a single-function appliance. Never ask a resident to cycle power to clear one. Brand tables to follow after engineer validation.

**Engineer-only signals:** all code interpretation and clearing.

---

## `washer_dryer_smell` — Bad Smell

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Damp left in the drum | Ask whether washing is left in, and whether the door and drawer are kept closed | The usual cause. Leave the door ajar between washes |
| Low-temperature washes only | Ask what programmes are normally used | Cool washes do not clear the residue that feeds the smell |
| Biofilm in the drawer and seal | Wipe the seal and its folds; pull the drawer out and rinse it if it releases by hand | Resident-safe |
| Blocked or standing pump filter | Open the flap — towel and bowl first — and clear it | Stagnant water |
| Residue in drum and hoses | Run a hot maintenance wash empty, no load | Usually decisive alongside the above |
| Drain smell rather than appliance smell | Ask whether the sink smells too | Household drainage. Route to ops |

A burning or electrical smell is not this fault — switch off at the socket and escalate.

**Engineer-only signals:** any burning, electrical or chemical smell (escalate, not route); smell persisting after a filter clean, a seal and drawer wipe and a hot maintenance wash.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `washer_dryer_pausing_mid_cycle` — Pausing Mid Cycle

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Normal soak or anti-crease phase | Ask how long it sat still and whether the timer kept counting | Designed behaviour, routinely reported as a stall. Say so factually rather than routing |
| Unbalanced load | Ask whether it tries to spin, slows and tries again; redistribute by hand and re-run | Repeated redistribution stretches a cycle considerably |
| Thermal cut-out on the drying phase | Ask whether it pauses only during drying and whether the machine felt very hot | Clear the filter and retry once. Repeated cut-out is an engineer job — a protection device doing its job |
| Supply interruption | Check the tap is fully open, and the socket switch and plug | Mid-cycle fill failures stall the programme |
| Door not latched, or opened mid-cycle | Push firmly closed and resume | |
| Board, motor or sensor fault | — | Engineer |

Repeated genuine stalls — same point, more than once, load balanced and filter clear — route to an engineer. Do not keep re-running the cycle.

**Engineer-only signals:** repeated thermal cut-out; stalling at the same point across cycles; any burning smell; a machine that stops and will not restart.

*Newly drafted — no prior content in the reference; needs engineer review.*

---

## `washer_dryer_other` — Other

Confirm the symptom in the resident's own words, verbatim, and establish which half it concerns. Only these checks are safe for any washer-dryer fault.

| Likely cause | Resident-safe check | Notes |
|---|---|---|
| Programme or setting | Confirm programme, temperature, spin and drying selection | A large share resolve here |
| Pump filter | Open the flap by hand or coin-turn, towel and bowl first, and clear it | The most useful check on this appliance type |
| Water supply | Ask whether the tap is fully open | Affects filling and, on most models, drying |
| Power and door | Check the socket switch, the plug, and that the door is latched | |
| Load size and composition | Ask what was in the drum | Drying capacity is roughly half wash capacity |

Route early rather than improvising.

**Engineer-only signals:** anything the five checks above do not answer; any burning smell — escalate.

---

## Replace-leaning faults

Flagged so triage can stop early. These do not mean "recommend replacement" — that is `iterum-repair-vs-replace`'s call — but further resident troubleshooting will not help.

- Control board failure — takes out both functions, and the board is a significant proportion of unit cost
- Motor failure
- Drum bearing failure on a sealed drum — labour typically exceeds the value of a mid-range domestic machine
- Condenser or heating failure on the drying side of an older unit
- Tank or chassis corrosion, cabinet or drum damage
- Any fault where both wash and dry functions are affected at once
- A second significant fault within twelve months — combined units that start failing tend to keep failing

## Typical service life

6–8 years, shorter than either standalone appliance, because the same components do roughly twice the work. A washer-dryer reaches the end of its expected life sooner than the equivalent washing machine, so the same fault at the same age leans replace more readily here. Validate against Iterum's own replacement data when it exists.
