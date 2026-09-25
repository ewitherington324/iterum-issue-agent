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
   │     └─ calls assess_repair_vs_replace ──► separate AI call, instructions = repair-vs-replace skill
   │     ends with submit_recommendation (the assessment's ID — code and confidence come from the log)
   │
   └─ 3. BOOKING ────── checks stock, proposes slots (fixed rule), books
         book_visit is held by a gate until the engineer (and PM, if over £400) approve
```

The escalation skill isn't a separate call. Its rules are copied by hand into the main agent's
own instructions (`agent/prompts.py`) so they apply from the first message.

## What's where

| Path | What it is |
|---|---|
| `agent/runner.py` | Runs the three phases in order |
| `agent/tools.py` | The 18 tools the agent can use (15 from the PRD + 3 "I'm done with this phase" tools) |
| `agent/reasoning.py` | The two separate AI calls (troubleshooting steps, repair vs. replace) |
| `agent/skills.py` | Reads the skill files and hands them to those calls |
| `agent/assessments.py` | The assessment log. Each repair-vs-replace answer gets an ID; the main agent submits the ID, never its own numbers |
| `agent/fallbacks.py` | Rules-based backup for both calls, used if the AI path is switched off or fails |
| `agent/gates.py` | The engineer / PM approval gate on booking |
| `agent/trace.py` | Guardrails (e.g. the warranty block) and the decision log |
| `agent/prompts.py` | Main agent instructions, including the escalation rules |
| `skills/` | The three Module 2 skills + ten appliance fault references |
| `scenarios/` | The 8 test cases |
| `selftest.py` | 66 quick checks, free, no API key |
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

1. **The main agent can overwrite the assessment.** In the cracked-hob run, the repair-vs-replace
   call correctly capped confidence at 0.6 (no photo). The main agent then submitted 0.78, which
   crossed the threshold. Nothing checks that the two agree (`docs/module2/verification.md` §4.3).
2. **Confidence threshold doesn't match the PRD.** The PRD says 0.7; the code uses 0.75.
3. **Photos can't be supplied.** Nothing in the system handles them, so the "crack confirmed by
   photo" path in the skill can't be reached.
4. **No guardrail has fired in a live run.** Routing was correct every time, so the backstops are untested.
5. **The backup isn't truly "one source".** `fallbacks.py` keeps its own copy of the fault patterns.
6. **Four appliance types have no fault categories** in Iterum's data (washing machine, tumble
   dryer, microwave, wine cooler), so only their general guidance ever reaches the model.
7. **Same-day booking.** The PRD's slot rule allows booking for this afternoon; a real version needs notice.
8. **One run per scenario.** Nothing yet shows the results are consistent.

## Next

- **Module 3 (now):** repair vs. replace becomes a subagent.
- **Next steps, noted not built:** scheduling as a reasoning subagent (replacing the fixed slot
  rule); an engineer brief writer.
- module 3 sub-agent spec found here: docs/module3/SUBAGENT_SPEC.md
