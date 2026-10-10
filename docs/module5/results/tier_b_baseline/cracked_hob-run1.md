# cracked_hob run 1

Commit e44fa33-dirty, finished 2026-10-10T15:19:04. Routing: Replacement booked: engineer confirmed. Checks 14/14, $0.87.

### Triage loop

`get_appliance` {"appliance_id": "app_005"}

`check_warranty` {"appliance_id": "app_005"}

`get_property_data` {"property_id": "prop_bmy"}

**Agent:**
> Hi Leila, I'm the appliance support agent for Iterum — your property manager has logged a problem with the hob in flat 0905, so I'm picking it up.
> 
> I've got it noted as a crack across the front-right zone. Can you tell me what you're actually seeing? Is it a crack in the glass surface itself, or more of a mark or scratch on top?

**Resident (simulated):**
> hi, so there's definitely a dark line across that zone - it's about 10cm long. when i run my nail over it i can feel *something* but honestly i can't tell if it's an actual crack in the glass or just a scorch mark from where the water boiled over. it happened two days ago and there was a sharp cracking noise at the time, so i'm pretty sure something broke, but i can't be 100% certain what i'm looking at now

`get_triage_steps` {"appliance_type": "Hob", "brand": "CDA", "issue_description": "Dark line ~10cm across front-right zone of ceramic hob, appeared after a sharp cracking noise during a boil-over two days ago. Resident can feel something when running a nail over it. Hob unused since.", "fault_slug": "hob_surface_damage"}

**Agent:**
> Thanks — that's really helpful. A cracking noise during a boil-over usually does mean the glass has gone, so please keep the hob off completely, including the other zones, until an engineer has looked at it. A crack can let moisture reach live parts underneath. Keep it dry too — no damp cloth on it for now.
> 
> Two quick things so I can get the right visit booked:
> 
> 1. When you run a nail gently along the line, does it catch and drop into a groove, or does it feel more like a raised ridge or rough patch sitting on top?
> 2. Does the line run all the way to the edge of the glass, and can you see any chips or missing pieces along it?
> 
> If you're able to, a photo from a low angle across the surface in daylight would settle it.

**Resident (simulated):**
> ok good to know, i'll keep it completely off. so with my nail - it's hard to say really, it doesn't feel like it drops in deep or anything, but i can feel it catch a tiny bit. could be a groove or could just be the edge of a rough patch, i genuinely can't tell the difference.
> 
> the line doesn't go all the way to the edge - it stops short on both ends. i don't see any chips or missing bits, it's just that dark line. and i can't take a photo unfortunately - i've only got a basic phone without a camera. but i can describe anything else you need to know?

**Agent:**
> No problem at all — your description is doing the job.
> 
> Two last ones:
> 1. With a dry cloth (nothing damp), give it a firm wipe — does the dark line fade or smudge at all, or does it stay exactly the same?
> 2. Did the line appear in that exact spot straight after the cracking noise, and has it changed at all — got longer, darker — over the two days since?

**Resident (simulated):**
> ok so i just wiped it with a dry cloth - the line doesn't smudge or fade at all, it's still exactly the same dark mark. so that's not just surface stuff.
> 
> and yeah, the line was there right after i heard the crack, and honestly it looks the same now as it did then. hasn't got longer or darker that i can see

**Agent:**
> That tells me what I needed — a mark that won't wipe off and appeared at the moment of the crack is almost certainly damage to the glass itself, not a scorch.
> 
> So this one needs an engineer rather than anything you can fix. The hob is out of its manufacturer warranty, so we handle it. I'm getting the right type of visit sorted now and I'll come back to you shortly with dates.
> 
> In the meantime please keep it switched off entirely and dry. If you ever notice sparking, a burning smell, or water getting onto it, message me straight away.

`complete_triage` {"outcome": "needs_assessment", "fault_slug": "hob_surface_damage", "findings": "CDA HN6111FR ceramic hob (app_005), flat 0905, Box Makers Yard. Out of warranty — expired 2024-07-12; appliance 4.16 years old.\n\nPM description broadly confirmed by resident, with added detail. Resident reports a dark line approx 10cm across the front-right zone, appearing at the moment of a sharp cracking noise during a boil-over two days ago. Line stops short of the glass edge at both ends. No chips, missing pieces or loose fragments visible. Nail run along it \"catches a tiny bit\" but resident cannot tell wh

*exit triage: needs_assessment*

### Repair vs. replace loop

`assess_repair_vs_replace` {"issue_id": "ISS-4408", "appliance_id": "app_005", "troubleshooting": [{"step": "Resident ran a fingernail gently along the dark line to feel whether it drops into a groove or is a raised ridge on top of the glass", "result": "Resident felt it catch a tiny bit but could not tell whether it was a groove or the edge of a rough patch"}, {"step": "Resident looked at whether the line runs to the edge of the glass and whether there were chips, missing pieces or anything loose along it", "result": "Line stops short of the edge at both ends; no chips or missing bits seen, just the dark line"}, {"step

`get_appliance` {"appliance_id": "app_005"}

`search_similar_issues` {"appliance_type": "Hob", "issue_description": "Cracked / damaged ceramic hob surface - dark line across zone, possible crack or scorch mark"}

`submit_assessment` {"code": "A", "confidence": 0.58, "determinative": true, "rationale": "Reported crack to a ceramic/induction hob surface (hob_surface_damage), which is a determinative code A regardless of age or cost ratio — the glass is most of the unit cost, rarely available as a separate part, and a crack admits moisture to live components beneath. The uncertainty here is entirely evidential, not economic: no photograph is available (resident has no camera phone) and she cannot distinguish by touch between a groove through the glass and a raised ridge or scorch residue, so this could still be a cosmetic he

`submit_recommendation` {"assessment_id": "ISS-4408-RVR-1"}

*exit decision: A*

### Booking loop

`check_inventory` {"appliance_type": "Hob"}

`send_engineer_message` {"engineer_id": "eng_dad_01", "recommendation": "Code A - beyond economic repair, replace. CDA HN6111FR hob, app_005, flat 0905, Box Makers Yard (ISS-4408). Confidence 0.58, below the 0.70 threshold - your confirmation or override is needed before anything is booked.", "rationale": "Out of warranty (expired 2024-07-12), unit 4.16 years old. Est. repair £165, replacement £389.\n\nResident reports a dark line approx 10cm across the front-right zone that appeared at the moment of a sharp cracking noise during a boil-over two days ago. Her observations: the line stops short of the glass edge at bo

*gate opened: engineer  *

*gate closed: engineer confirm Confirmed on site - it is a crack, not a heat mark. Hob needs replacing.*

`find_available_technician` {"property_id": "prop_bmy", "earliest_date": "2026-10-10"}

*slot proposed: 2026-10-13 (attempt 1)*

**Agent:**
> Hi Leila — update. Our engineer Marcus has reviewed it and agrees it's a genuine crack in the glass rather than a heat mark, so the hob is going to be replaced rather than repaired.
> 
> I can get him out to you on Tuesday 13 October. Does that work?
> 
> He'll pick up keys from the concierge, but it's easier if you're in. Keep the hob off and dry until then.

**Resident (simulated):**
> tuesday the 13th works fine for me, i'll be in. thanks for sorting it quickly. i'll keep it off and dry like you said

`book_visit` {"issue_id": "ISS-4408", "slot_date": "2026-10-13", "visit_type": "replacement"}

`confirm_visit` {"visit_id": "VIS-001-4408"}

**Agent:**
> All booked — Marcus Ellery from DAD will come on Tuesday 13 October to replace the hob. He'll sign in at the concierge desk on the ground floor.
> 
> He'll check the unit over himself when he arrives and fit the replacement. Please keep the hob switched off and dry until he's been, and give us a shout straight away if you notice sparking, a burning smell or water getting onto it before then.
> 
> Thanks for being so clear describing it — that's what got this moving quickly.

`close_job` {"issue_id": "ISS-4408", "resolution": "visit_booked", "summary": "CDA HN6111FR hob (app_005), flat 0905, Box Makers Yard. Replacement visit VIS-001-4408 confirmed for Tuesday 13 October 2026 with Marcus Ellery (DAD). Resident accepted the first slot offered and will be in; concierge holds keys.\n\nFault: dark line approx 10cm across the front-right zone, appeared at the moment of a sharp cracking noise during a boil-over on 08/10. Does not wipe off with a dry cloth, nail catches slightly, stops short of the glass edge both ends, no chips or loose pieces, no propagation over two days. Not resi

`conclude_booking` {"outcome": "booked", "detail": "Replacement visit VIS-001-4408 confirmed for Tuesday 13 October 2026, Marcus Ellery (DAD), Box Makers Yard flat 0905. Engineer gate passed - Marcus confirmed the code A recommendation on site judgement (\"it is a crack, not a heat mark\"), which was required as assessment confidence was 0.58 against a 0.70 threshold. No PM approval needed: £389 replacement cost is under the £400 threshold. No parts order required - whole-unit replacement, and the only stocked hob part (induction generator module) is not relevant, so no lead time applied. Resident accepted the f

*exit booking: booked*
