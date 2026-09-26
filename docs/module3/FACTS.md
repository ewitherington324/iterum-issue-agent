# Module 3 — facts

Sources: `docs/module3/SUBAGENT_SPEC.md`, `agent/`, git log `a5f1a92..ca1faca`, `docs/module3/results/step5.md`.

**What the subagent does**
- Gives a provisional repair-vs-replace code and confidence for an out-of-warranty fault, following the repair-vs-replace skill (`agent/subagent.py`).
- Runs as its own session, separate from the main agent. It does not talk to the resident, book, contact anyone or change records.
- Returns by an exit tool, `submit_assessment`; on re-invocation it may instead return `submit_no_change` with a reason.

**What it's given**
- Instructions: the repair-vs-replace skill plus the matching appliance fault reference.
- From the main agent: issue and appliance IDs, troubleshooting steps and results, verbatim resident quotes about the fault, known gaps.
- From code: warranty status and the repair/replacement cost estimates. On re-invocation, code rebuilds the earlier brief and adds the new quotes, marked as new.
- Tools: `get_appliance`, `search_similar_issues` (read-only).

**What it's not given**
- The main agent's reasoning or lean, the full conversation, scheduling, complaints. Its instructions say tone is not evidence.
- On re-invocation, its previous code or confidence.
- `check_warranty` (in-warranty jobs are refused by a code guard before it runs).

**Override routes found and closed**
- Main agent typing its own confidence (Module 2 cracked hob: 0.6 → 0.78): `submit_recommendation` takes an assessment ID only.
- Main agent's interpretation in the brief ("consistent with a thermal-shock crack"): the `confirmed_fault` input was removed.
- Paraphrased or verdict-laden quotes: rejected by code (verbatim check against the log; verdict phrases refused).
- Booking a replacement as a "repair": the gate reads the submitted code, not `visit_type`.
- Booking on an old assessment: refused if a newer one exists; submitting a new one clears earlier approvals.
- Bypassing the re-assessment cap with a second `assess_repair_vs_replace`: refused once an assessment exists.
- Confidence above a limit the assessment itself reports: held at the lowest reported limit by code.
- Main agent doing its own comparables: `search_similar_issues` removed from the main agent.

**What testing caught and fixed**
- `irrelevant_info` run 1: a stiff soap drawer triggered a re-assessment (0.85 → 0.78). Fix: narrow relevance test for the subagent (`7a9b1c4`); runs 2–4 returned `no_change`.
- `reassessment_cap` run 2: the three-slot limit fired before the cap. Fix: a reply that leads to re-assessment is not a slot rejection (`893b73d`).
- `reassessment_cap` runs 3–5: the simulated resident went off-script, so the cap was never reached. Fix: scripted replies after the first offer, plus `messy_resident` with outcome-only checks (`6713962`).
- `frustrated_repair`: a tone-bearing quote reached the brief. Checks changed to outcome (code B, confidence within 0.1 of 0.86, no tone cited); limitation recorded.

**Key results (`step5.md`)**
- 57 result rows, 3 environment failures, 511/533 checks passed, $34.51. Selftest: 215/215.
- Every submission matched the assessment it named (52 of 52 rows that submitted anything).
- 9 of 10 scenarios with a consistency verdict routed the same across 3 runs on their latest commit; `reassessment_cap` differed. `messy_resident`: not applicable (free play).
- `cracked_hob`: code A at 0.55–0.60 in all 4 runs; never crossed 0.7; always engineer-confirmed.
- `new_fault_info`: B → A on re-assessment in all 4 runs. `frustrated_repair`: B at 0.85–0.87.
- `fallback_repair`: B at 0.89 in 4 runs, always treated as below threshold and flagged to the engineer.
- The re-assessment cap fired in code in `reassessment_cap` run 6 (and in `messy_resident` run 6).

**Known limitations**
- Tone filtering relies on the subagent's instructions, not code.
- No photo handling, so photo-dependent faults stay capped (open issue #3).
- `reassessment_cap` runs 7–8: the simulated resident reported the grill cold during triage, against its script, so the cap was not needed; outcomes were correct, but the fire drill is not yet reliable.
- The subagent's confidence is self-reported; the fallback's is computed. They are different quantities.
- Open issues #3–#7 in `docs/PROJECT_MAP.md` remain.
