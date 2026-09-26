# Project map

One page. What exists, what's real, how it fits together, and what's still open.
For the demo script see `README.md`; for design rules that must not break see `CLAUDE.md`.

## What this is

A working prototype of Iterum's issue resolution agent. A property manager logs an appliance
fault; the agent talks to the resident (simulated WhatsApp), and the issue ends in one of three
places: fixed by the resident, an engineer visit booked, or handed to Iterum ops.

Everything external is mocked — no real WhatsApp, Iterum IQ, Airtable or email. The resident
is played by a second, cheaper model that knows the "true" fault and the agent doesn't.

## How one issue flows

```
PM logs issue (scenario file)
   │
   ▼
Main agent — one session per issue (agent/runner.py)
   │
   ├─ 1. TRIAGE ─────── talks to the resident, checks warranty
   │     └─ calls get_triage_steps ──► separate AI call, instructions = triage skill
   │                                    + the matching section of one appliance reference file
   │     ends with complete_triage → resolved / in warranty / halted / needs engineer
   │
   ├─ 2. REPAIR VS REPLACE
   │     └─ calls assess_repair_vs_replace with fault evidence only (verbatim resident quotes,
   │        checked in code) ──► code refuses if in warranty or no reference file, else runs
   │        the SUBAGENT: its own session, instructions = repair-vs-replace skill + reference,
   │        tools = get_appliance, search_similar_issues; warranty and costs added by code
   │     ends with submit_recommendation (the assessment's ID — code and confidence come from the log)
   │
   └─ 3. BOOKING ────── checks stock, proposes slots (fixed rule), books
         book_visit is held by a gate until the engineer (and PM, if over £400) approve;
         the gate reads the submitted code, not the visit type the main agent passes
         new fault info from the resident → reassess_repair_vs_replace (max 2; the
         subagent may answer "no change"; if it fails, the earlier assessment stands and the
         new info goes to the engineer on the visit; a 3rd goes to ops with the history)
```

The escalation skill isn't a separate call. Its rules are copied by hand into the main agent's
own instructions (`agent/prompts.py`) so they apply from the first message.

## What's where

| Path | What it is |
|---|---|
| `agent/runner.py` | Runs the three phases in order |
| `agent/tools.py` | The 18 tools the main agent can use (14 from the PRD, `reassess_repair_vs_replace`, and 3 "I'm done with this phase" tools) |
| `agent/subagent.py` | The repair-vs-replace subagent: checks what the main agent passes it, refuses in-warranty jobs, runs with its own two lookups |
| `agent/reasoning.py` | The troubleshooting-steps AI call, and the shape every repair-vs-replace answer must have |
| `agent/skills.py` | Reads the skill files and hands them to those calls |
| `agent/assessments.py` | The assessment log. Each repair-vs-replace answer gets an ID; the main agent submits the ID, never its own numbers |
| `agent/fallbacks.py` | Rules-based backup for both calls, used if the AI path is switched off or fails. Its results never count as confident, and the engineer is told they came from it. Not used on re-assessment |
| `agent/gates.py` | The engineer / PM approval gate on booking |
| `agent/trace.py` | Guardrails (e.g. the warranty block) and the decision log |
| `agent/prompts.py` | Main agent instructions, including the escalation rules |
| `skills/` | The three Module 2 skills + ten appliance fault references |
| `scenarios/` | The 14 test cases (8 from Module 2, 6 added in Module 3 step 5) |
| `selftest.py` | 215 quick checks, free, no API key |
| `verify.py` | Runs scenarios against the real model — costs money |
| `static/`, `server.py` | The browser demo |
| `docs/` | PRD, this map, and `module2/` (submitted write-up, evidence, old prompts) |

## Real vs invented

**Real Iterum data:** the 55 fault categories, property and operator names, brands and suppliers.
Because of this, **the GitHub repo should stay private.**
**Invented:** all people — residents, engineers, property managers.
**General knowledge, not Iterum data:** the appliance fault references. They need engineer sign-off.

## Open issues

Most relevant to Module 3 first.

1. ~~**The main agent can overwrite the assessment.**~~ **Resolved (Module 3):** `submit_recommendation` now takes an assessment ID only; code and confidence come from the log.
2. ~~**Confidence threshold doesn't match the PRD.**~~ **Resolved (Module 3 step 5):** the code now uses the PRD's 0.7.
3. **Photos can't be supplied.** Nothing in the system handles them, so the "crack confirmed by
   photo" path in the skill can't be reached.
4. **No guardrail has fired in a live run.** Routing was correct every time, so the backstops are untested.
5. **The backup isn't truly "one source".** `fallbacks.py` keeps its own copy of the triage fault
   patterns (11 faults; the reference files cover 55). A selftest now fails if a key has no
   matching reference section, so the keys can't drift, but the steps themselves can. Deriving
   them from the reference files would need either (a) a parser that turns the "Resident-safe
   check" column into resident steps and filters out the unsafe rows, which are marked only in
   wording ("—", "None — do not troubleshoot", gas rows on hobs when the hob type is unknown), or
   (b) a structured "fallback steps" block added to each reference section and signed off by an
   engineer, so the file holds the exact wording the fallback sends. (b) is safer; both touch
   content that needs engineer review. The repair-vs-replace fallback already reads the
   skill's determinative table directly (Module 3 step 4).
6. **Four appliance types have no fault categories** in Iterum's data (washing machine, tumble
   dryer, microwave, wine cooler), so only their general guidance ever reaches the model.
7. **Same-day booking.** The PRD's slot rule allows booking for this afternoon; a real version needs notice.
8. ~~**One run per scenario.**~~ **Resolved (Module 3 step 5):** each repair-vs-replace scenario run 3× on one commit; results in `docs/module3/results/step5.md`.

## Next

- **Module 3 is done** (tag `module-3`): repair vs. replace is a subagent whose answer the main
  agent cannot change. Spec: `docs/module3/SUBAGENT_SPEC.md`; summary: `docs/module3/FACTS.md`;
  results: `docs/module3/results/step5.md`.
- **Fire drill still leans on the simulator in triage.** In `reassessment_cap` runs 7 and 8 the
  simulated resident reported the grill cold during triage, against its script, so the first
  scripted symptom wasn't new and the cap was never needed. The outcomes were correct; the
  scenario needs the triage answers pinned too before it reliably tests the cap.
- **Next steps, noted not built:** scheduling as a reasoning subagent (replacing the fixed slot
  rule); an engineer brief writer; photo handling (open issue #3).
