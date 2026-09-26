# cracked_hob run 4

Commit ca1faca, finished 2026-09-25T23:01:00. Routing: Replacement booked: engineer confirmed. Checks 14/14, $0.59.

### Triage loop

`get_appliance` {"appliance_id": "app_005"}

`check_warranty` {"appliance_id": "app_005"}

`get_property_data` {"property_id": "prop_bmy"}

**Agent:**
> Hi Leila, I'm the issue resolution agent for Iterum - we look after the appliances at Box Makers Yard. Your property manager logged a crack in the hob surface in flat 0905. Can you tell me what it looks like now, and did anything happen just before it appeared (something dropped, a pan boiling over, anything like that)?

**Resident (simulated):**
> yeah so there's a dark line across the front right zone, maybe 10cm long? a pan of cold water boiled over onto it two days ago and i heard a sharp crack noise. i haven't used it since, switched it off at the wall to be safe

**Agent:**
> That's thermal shock from the cold water - and switching it off at the wall was exactly the right call. Please keep it off and don't use any of the zones until an engineer has seen it.
> 
> Two things that help me get the right person out: does the crack go all the way through (can you feel a step or catch a fingernail in it), and is any of the glass loose, lifted or chipped at the edges?

**Resident (simulated):**
> honestly i can't really tell if my nail catches in an actual crack or if i'm just feeling a scorch mark - it's hard to say. and the edges look fine to me, nothing loose or lifted or chipped

**Agent:**
> No problem, that's a genuinely hard one to call by touch. Could you send a photo of the area? And before this happened, were all four zones working normally?

**Resident (simulated):**
> i can't take photos - i've got a basic phone, no camera. but i can describe it more if that helps? and yeah, all four zones were working fine before this happened

**Agent:**
> That's fine, describing it works. With the hob cold and still off at the wall, give the line a wipe with a damp cloth - does any of it lift or fade, or does it stay exactly the same?

**Resident (simulated):**
> okay, wiped it with a damp cloth - the line's still there exactly the same, didn't lift or fade at all

**Agent:**
> Thanks Leila - that tells me it's in the glass rather than a mark on top, so this needs an engineer rather than anything you can fix. Keep it off at the wall in the meantime.
> 
> I'm passing it on now and I'll come back to you shortly to sort out a visit time.

`complete_triage` {"outcome": "needs_assessment", "fault_slug": "hob_surface_damage", "findings": "CDA HN6111FR hob, app_005, flat 0905. Out of warranty (expired 2024-07-12), 4.16 years old, Iterum price £305.\n\nPM description confirmed and expanded by resident. Resident reports a dark line approx 10cm across the front-right zone. Onset: a pan of cold water boiled over onto the hot zone two days ago and she heard \"a sharp crack noise\" at that moment - consistent with thermal shock. All four zones were working normally before the event.\n\nResident observations:\n- Cannot tell whether a fingernail catches in 

*exit triage: needs_assessment*

### Repair vs. replace loop

`assess_repair_vs_replace` {"issue_id": "ISS-4408", "appliance_id": "app_005", "troubleshooting": [{"step": "Asked resident to run a fingernail over the line to check whether it catches or whether a step can be felt", "result": "Resident could not tell whether her nail catches in an actual crack or whether she is feeling a scorch mark"}, {"step": "Asked resident to inspect the edges of the glass for glass that is loose, lifted or chipped", "result": "Edges look fine to the resident - nothing loose, lifted or chipped"}, {"step": "Asked resident to wipe the line with a damp cloth, hob cold and switched off at the wall", "

`get_appliance` {"appliance_id": "app_005"}

`search_similar_issues` {"appliance_type": "Hob", "issue_description": "cracked ceramic hob surface, dark line across zone after thermal shock from boiled-over cold water"}

`submit_assessment` {"code": "A", "confidence": 0.6, "determinative": true, "rationale": "Reported hob surface damage on a CDA ceramic/induction hob: `hob_surface_damage` is a determinative code A, so age (4.2 years, well inside service life) and the 42% cost ratio do not enter the reasoning. The mechanism described is textbook thermal shock — cold water boiling over onto a hot zone, with an audible sharp crack at the moment of the event, and a 10cm dark line that did not lift with a damp cloth. Confidence is held at the no-photo ceiling because the resident has no camera and could not distinguish a crack from a 

`submit_recommendation` {"assessment_id": "ISS-4408-RVR-1"}

*exit decision: A*

### Booking loop

`check_inventory` {"appliance_type": "Hob"}

`send_engineer_message` {"engineer_id": "eng_dad_01", "recommendation": "Code A - beyond economic repair, replace. CDA HN6111FR hob, app_005, Box Makers Yard flat 0905 (ISS-4408). Confidence 0.60, BELOW the 0.70 threshold - please confirm or override.", "rationale": "Provisional routing only, not a diagnosis. Out of warranty (expired 2024-07-12), 4.16 years old. Est. repair GBP 165 vs replacement GBP 389 (42% ratio) - but hob_surface_damage is treated as determinative, so age and economics were not weighed.\n\nResident's account: a pan of cold water boiled over onto a hot zone two days ago and she heard \"a sharp cra

*gate opened: engineer  *

*gate closed: engineer confirm Confirmed on site - it is a crack, not a heat mark. Hob needs replacing.*

`find_available_technician` {"property_id": "prop_bmy", "earliest_date": "2026-09-25"}

*slot proposed: 2026-09-29 (attempt 1)*

**Agent:**
> Hi Leila - update. Our engineer Marcus has confirmed it is a crack in the glass rather than a heat mark, so the hob will be replaced rather than repaired. Nothing for you to pay.
> 
> Can he come on Tuesday 29 September? The concierge holds keys, so you don't have to be in if that's easier. Keep it off at the wall until then.

**Resident (simulated):**
> yeah tuesday works, that's fine. thanks for sorting it quickly. i'll leave it switched off like you said

`book_visit` {"issue_id": "ISS-4408", "slot_date": "2026-09-29", "visit_type": "replacement"}

`confirm_visit` {"visit_id": "VIS-001-4408"}

`send_ops_message` {"issue_id": "ISS-4408", "category": "scheduling_handoff", "request": "FYI / spec check ahead of a confirmed visit - no action needed on scheduling.\n\nVisit VIS-001-4408 confirmed for Tue 29 Sep, Box Makers Yard flat 0905, engineer Marcus Ellery (eng_dad_01). Type: replacement. CDA HN6111FR hob, app_005. Out of warranty. Replacement GBP 389, under the GBP 400 PM threshold, so no PM approval was required.\n\nGating done: assessment ISS-4408-RVR-1 came back code A at confidence 0.60, below the 0.70 threshold. Marcus was sent the full evidence including the contra-indicators and CONFIRMED on sit

**To ops (scheduling_handoff):**
> FYI / spec check ahead of a confirmed visit - no action needed on scheduling.
> 
> Visit VIS-001-4408 confirmed for Tue 29 Sep, Box Makers Yard flat 0905, engineer Marcus Ellery (eng_dad_01). Type: replacement. CDA HN6111FR hob, app_005. Out of warranty. Replacement GBP 389, under the GBP 400 PM threshold, so no PM approval was required.
> 
> Gating done: assessment ISS-4408-RVR-1 came back code A at confidence 0.60, below the 0.70 threshold. Marcus was sent the full evidence including the contra-indicators and CONFIRMED on site - his note: "Confirmed on site - it is a crack, not a heat mark. Hob needs replacing." His confirmation resolves the no-photo gap that was capping confidence.
> 
> One open item for the replacement spec: the assessor flagged that hob technology is not confirmed as induction vs ceramic-electric from the record for the CDA HN6111FR. It does not change the replacement decision, but please confirm the correct unit type is allocated before Marcus travels, so he is not on site with the wrong hob.
> 
> Note also that the only hob part held in inventory is SKU-HOB-INDMOD (induction generator module, stock 0, 9-day lead time). Not required for a whole-unit swap, so nothing has been ordered.
> 
> Resident context: Leila Haddad has kept the hob isolated at the wall since the event and has been told to leave it off until the visit. She has a basic phone with no camera, so no photo evidence exists on file. Concierge holds keys.

**Agent:**
> All booked - Marcus will fit a new hob on Tuesday 29 September. He'll sign in with the concierge and collect keys, so you don't need to be there.
> 
> Please keep it off at the wall until he's been. Thanks for being so thorough with the checks, it's what got this moving quickly.

`close_job` {"issue_id": "ISS-4408", "resolution": "visit_booked", "summary": "CDA HN6111FR hob, app_005, Box Makers Yard flat 0905. Out of warranty (expired 2024-07-12), 4.16 years old.\n\nFault: dark line approx 10cm across the front-right zone. Resident reported a pan of cold water boiled over onto a hot zone two days prior with an audible sharp crack at that moment. All four zones worked normally beforehand. Resident isolated the hob at the wall unprompted and did not use it again.\n\nResident-led checks: fingernail over the line - could not tell whether it catches in a crack or is a scorch mark. Glas

`conclude_booking` {"outcome": "booked", "detail": "Visit VIS-001-4408 booked and confirmed: replacement hob, Tuesday 29 September 2026, Box Makers Yard flat 0905, engineer Marcus Ellery (eng_dad_01).\n\nReplacement gate satisfied: Marcus was sent the code A recommendation together with the sub-threshold confidence (0.60 v 0.70) and the assessor's contra-indicators, and confirmed it - \"Confirmed on site - it is a crack, not a heat mark. Hob needs replacing.\" That also closes the no-photo evidence gap that had capped confidence. Replacement cost GBP 389 sits under the GBP 400 PM threshold, so no PM email was re

*exit booking: booked*
