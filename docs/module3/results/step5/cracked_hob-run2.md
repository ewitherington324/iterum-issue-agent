# cracked_hob run 2

Commit ca1faca, finished 2026-09-25T22:55:18. Routing: Replacement booked: engineer confirmed. Checks 14/14, $0.77.

### Triage loop

`get_appliance` {"appliance_id": "app_005"}

`check_warranty` {"appliance_id": "app_005"}

`get_property_data` {"property_id": "prop_bmy"}

**Agent:**
> Hi Leila, I'm from Iterum - we look after the appliances at Box Makers Yard. Your property manager logged a crack in your hob (a dark line across the front-right zone). Can I check a couple of things: is it an actual crack in the glass surface, or more of a mark or scratch? And did anything happen just before it appeared - something dropped on it, or a pan boiling over?

**Resident (simulated):**
> hi, yeah so a pan of boiling water went over it two days ago - there was a sharp crack sound when it happened. there's definitely a dark line there now, maybe 10cm long, but honestly i can't tell if my nail catches on it or if it's just a burn mark? it's hard to say for sure

`get_triage_steps` {"appliance_type": "Hob", "brand": "CDA", "fault_slug": "hob_surface_damage", "issue_description": "Dark line ~10cm across front-right zone, appeared with a sharp cracking sound when a pan of boiling water spilled over it two days ago. Resident unsure whether it is a crack or a burn mark. Hob unused since."}

**Agent:**
> Thanks - that's really helpful. First thing: please don't run your finger or nail along the line. If it is a crack the edge can be sharp. And please don't use the hob at all, any ring, until someone's looked at it. If there's a wall switch above or beside the worktop that controls it, switch that off.
> 
> Two things that would help me: could you send a photo of the dark line close up, taken at a slight angle so the light catches along it? And when the water went over, did any of it seem to soak into or vanish along that line, rather than just sit on top?

**Resident (simulated):**
> ok got it, i'll leave it alone. i've already switched it off at the wall so that's done.
> 
> i can't take a photo - i've only got a basic phone, no camera. but i can tell you it's a thin dark line, maybe 10cm long, running across the front-right zone. when the water went over it, it all just sat there and ran off like normal water would - i didn't notice anything soaking in or anything like that

**Agent:**
> That's great - switching it off at the wall was exactly the right thing. No problem about the photo.
> 
> There's nothing safe for you to test yourself here, so I'm arranging for an engineer to come and look at it. Someone will be in touch shortly with a time. Please keep it off at the wall and keep the surface dry until then. Are you managing okay for cooking in the meantime?

**Resident (simulated):**
> yeah that's fine, thanks. i can use the other rings or the oven so no problem there. i'll keep it switched off and make sure it stays dry. cheers

**Agent:**
> Just to be clear on one thing - please don't use any of the rings on the hob, not even the ones away from the mark. The whole surface is a single sheet of glass, so heat anywhere on it can travel through and make a crack worse. The oven is completely fine to use.
> 
> Sorry to make things harder - it's just until the engineer has seen it.

**Resident (simulated):**
> ah right, got it - i'll stay off the whole hob then and just use the oven. no worries, makes sense. cheers for letting me know

`complete_triage` {"outcome": "needs_assessment", "fault_slug": "hob_surface_damage", "findings": "CDA HN6111FR ceramic hob, app_005, installed 2022-07-13, age 4.16 yrs. OUT OF WARRANTY (expired 2024-07-12, 24-month CDA term) - stays in the Iterum flow.\n\nConfirmed with resident, and the PM's second-hand description was incomplete on cause. A pan of boiling water spilled over the hob two days ago and there was a sharp cracking sound at that moment - thermal shock, not an impact or a gradual fault. A thin dark line approx 10cm now runs across the front-right zone. Hob not used since.\n\nResident cannot confirm 

*exit triage: needs_assessment*

### Repair vs. replace loop

`assess_repair_vs_replace` {"issue_id": "ISS-4408", "appliance_id": "app_005", "troubleshooting": [{"step": "Asked the resident whether the mark is a crack in the glass surface or a mark/scratch, and whether anything happened just before it appeared", "result": "Resident reported a pan of boiling water went over the hob two days ago with a sharp crack sound at that moment, and a dark line approx 10cm is now present across the front-right zone. Resident could not say whether it is a crack or a burn mark."}, {"step": "Asked the resident to stop using the hob entirely - the damaged zone and all other rings - until it is in

`get_appliance` {"appliance_id": "app_005"}

`search_similar_issues` {"appliance_type": "Hob", "issue_description": "Cracked or damaged hob glass surface - dark line across zone after boiling water spill, thermal shock suspected"}

`submit_assessment` {"code": "A", "confidence": 0.55, "determinative": true, "rationale": "Reported damage to a glass hob surface (`hob_surface_damage`) is a determinative code A — the glass is most of the unit cost, rarely available separately, and a crack admits moisture to live components beneath. The 42% cost ratio and the hob's young age (4.2 years) do not enter the reasoning. The mechanism described is classic thermal shock: boiling water over a hot zone with an audible sharp crack at that moment, followed by a 10cm dark line across the front-right zone. Confidence is held at 0.55 because the evidence for t

`submit_recommendation` {"assessment_id": "ISS-4408-RVR-1"}

*exit decision: A*

### Booking loop

`check_inventory` {"appliance_type": "Hob"}

`send_engineer_message` {"engineer_id": "eng_dad_01", "recommendation": "Code A - beyond economic repair, replace. CDA HN6111FR ceramic hob, Box Makers Yard flat 0905, app_005. Out of warranty (expired 2024-07-12). Replacement GBP 389, repair estimate GBP 165. Confirm or override before I book.", "rationale": "Flagging up front that this recommendation is provisional routing and its confidence is 0.55 against a 0.70 threshold - it is below the bar, and I want your eyes on it rather than a rubber stamp.\n\nWhat happened: a pan of boiling water went over the hob two days ago and the resident heard a sharp crack sound a

*gate opened: engineer  *

*gate closed: engineer confirm Confirmed on site - it is a crack, not a heat mark. Hob needs replacing.*

`find_available_technician` {"property_id": "prop_bmy", "earliest_date": "2026-09-25"}

*slot proposed: 2026-09-29 (attempt 1)*

`send_ops_message` {"issue_id": "ISS-4408", "category": "parts_order", "request": "Replacement hob unit needed for ISS-4408, Box Makers Yard flat 0905, app_005. Existing unit: CDA HN6111FR ceramic hob, installed 2022-07-13, out of warranty (expired 2024-07-12). Iterum price GBP 305 / retail GBP 389 - under the GBP 400 PM threshold, so no PM approval required.\n\nAssessment ISS-4408-RVR-1 returned code A at confidence 0.55 (below the 0.70 threshold), but engineer Marcus Ellery (eng_dad_01) has since CONFIRMED on site that it is a genuine crack in the glass and not a heat mark, so the replacement is verified rathe

**To ops (parts_order):**
> Replacement hob unit needed for ISS-4408, Box Makers Yard flat 0905, app_005. Existing unit: CDA HN6111FR ceramic hob, installed 2022-07-13, out of warranty (expired 2024-07-12). Iterum price GBP 305 / retail GBP 389 - under the GBP 400 PM threshold, so no PM approval required.
> 
> Assessment ISS-4408-RVR-1 returned code A at confidence 0.55 (below the 0.70 threshold), but engineer Marcus Ellery (eng_dad_01) has since CONFIRMED on site that it is a genuine crack in the glass and not a heat mark, so the replacement is verified rather than provisional.
> 
> Please supply a like-for-like replacement hob. Note the parts inventory for Hob holds only SKU-HOB-INDMOD (induction generator module, stock 0, 9-day lead) which is not applicable to a full unit replacement - flagging in case the replacement unit itself needs procuring with a lead time I should factor into the visit date. If the unit cannot be with Marcus for the proposed date, tell me and I will re-propose to the resident.
> 
> Access: concierge holds keys, engineers sign in at the ground-floor desk. Resident has the hob isolated at the wall and is not using it; she has oven access so is not without cooking facilities.

**Agent:**
> Hi Leila - update. Our engineer Marcus has confirmed it is a genuine crack in the glass rather than a burn mark, so the hob is going to be replaced rather than repaired.
> 
> Can he come on Tuesday 29 September? The concierge holds keys, so you don't have to be in if that's easier. Keep it switched off at the wall until then.

**Resident (simulated):**
> yeah tuesday's fine, cheers. i can let him in if needed but it's easier if he just uses the concierge key - no problem either way. i'll keep it switched off

`book_visit` {"issue_id": "ISS-4408", "slot_date": "2026-09-29", "visit_type": "replacement"}

`confirm_visit` {"visit_id": "VIS-001-4408"}

**Agent:**
> All booked - Marcus will be there Tuesday 29 September to fit the new hob, and he'll pick up the key from the concierge so you don't need to be in.
> 
> Just keep it off at the wall and dry until then, and carry on using the oven as normal. Thanks for being so easy to work with on this, Leila - you did exactly the right thing switching it off straight away.

`close_job` {"issue_id": "ISS-4408", "resolution": "visit_booked", "summary": "Replacement visit VIS-001-4408 confirmed for Tuesday 29 September 2026, engineer Marcus Ellery (eng_dad_01), access via concierge key - resident does not need to be present.\n\nFault: CDA HN6111FR ceramic hob, app_005, Box Makers Yard flat 0905. A pan of boiling water went over the hob on approx 2026-09-23 with an audible sharp crack at that moment, leaving a thin dark line approx 10cm across the front-right zone. Out of warranty (expired 2024-07-12), so handled in the Iterum flow.\n\nAssessment ISS-4408-RVR-1 returned code A (

`conclude_booking` {"outcome": "booked", "detail": "Replacement visit VIS-001-4408 confirmed for Tuesday 29 September 2026 with Marcus Ellery (eng_dad_01) at Box Makers Yard flat 0905, access via concierge key. First slot offered was accepted - no rejections.\n\nGating: code A replacement required engineer confirmation. Marcus was sent the recommendation with its sub-threshold confidence (0.55 v 0.70) and the crack-versus-scorch doubt stated plainly, plus an explicit offer to book an inspection visit instead. He confirmed on site that it is a genuine crack in the glass, not a heat mark, so the replacement is now

*exit booking: booked*
