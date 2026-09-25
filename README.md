# Iterum Issue Resolution Agent — vision prototype

A working prototype of the agentic system described in [`docs/PRD.md`](docs/PRD.md):
it takes a resident from a reported appliance fault to one of three outcomes — resolved by
guided self-troubleshooting, a booked engineer visit, or escalated to Iterum Ops.

Built across the modules of an AI course (see *Project history* below). It is **not** connected to Iterum IQ, Airtable, WhatsApp,
Mailgun or anything else real. Every external system is mocked. The point is to make the
vision legible, not to ship it.

---

## What this is actually trying to prove

The PRD's central claim (§1) is *why an agent rather than a workflow*: the resident journey is
mostly linear, but three points inside it need interpretation rather than branching logic —
how to troubleshoot this specific fault, whether it's repair or replace, and which slot to
propose.

A demo that just prints a well-written WhatsApp conversation doesn't prove that. It looks
exactly like a competent workflow. So this prototype is built to make the agentic machinery
**visible**: the loops cycling, the tool calls with real arguments, the exit conditions firing,
the human gates blocking and releasing, and the guardrails stopping the agent.

That's why the interface has two panes. The left is what the resident sees. The middle is what
is actually happening.

---

## Quick start

```bash
cp .env.example .env      # then put your Anthropic API key in it
./run.sh                  # http://localhost:8000
```

Python 3.10+. The first run creates a virtualenv and installs dependencies. A full scenario
costs roughly $0.15–$0.60 in API usage.

```bash
.venv/bin/python selftest.py    # 199 checks, no API key needed
.venv/bin/python verify.py      # runs all 13 scenarios and checks the outcomes
```

---

## The demo script

Roughly fifteen minutes. Each scenario is picked from the dropdown and run.

**1 · Clean self-fix** — the cheapest possible outcome.
The agent opens the thread, confirms the fault with the resident (the property manager's
description is second-hand), checks the warranty, walks her through clearing the filter, and
closes the job. No visit, no engineer, no cost.
> *Talking point:* this is the outcome Iterum currently has no way of reaching at all. Today
> this becomes a callout.

**2 · Clear repair** — the fully autonomous path.
Recommendation B, stock checked, slot proposed, visit booked and confirmed. Watch the Gates
panel on the right: it stays empty for the entire run.
> *Talking point:* PRD §3.4 says the repair path is fully autonomous. Nothing here waited on
> a human.

**3 · Likely replacement** — the gated path. **This is the one to spend time on.**
Nine-year-old oven. The agent asks the engineer to confirm, and the run *stops* — the Gates
panel shows a card waiting on you. Confirm it. Because the cost is over the threshold, a PM
approval card appears next. Approve it. Only then does `book_visit` pass, and the trace shows
why: *"Engineer confirmed; PM approved GBP 419 (over the GBP 400 threshold)."*
> *Talking point:* the gate is enforced by the harness, not by asking the model nicely. Try
> clicking **Override** on the engineer card instead — the booking is refused, and the
> refusal explains that the engineer's assessment takes precedence.

**4 · Cracked hob** — a fixed-outcome fault (added in Module 2).
A four-year-old induction hob whose repair would cost 42% of a replacement — age and cost
both argue for repair. But the surface is cracked, which the repair-vs-replace skill treats as
a replacement at any age. The recommendation comes back as code A, marked `determinative`,
with confidence capped at 0.6 because no photo can be supplied. It still goes through engineer
confirmation; at £389 it is under the PM threshold, so no PM approval is sought.
> *Talking point:* some rules settle the answer on their own; the skill says which ones, and
> the trace shows when one fired.

**5 · In warranty** — the branch that leaves the flow.
The moment `check_warranty` returns in-warranty, a red guardrail fires in the trace and four
tools are hard-blocked for the rest of the thread. The agent notifies ops, tells the resident
the manufacturer is handling it, and closes its loop.
> *Talking point:* PRD §5.2 says the agent does not book, quote or schedule these. It now
> *cannot*, rather than being asked not to.

**6 · Parts delayed** — deterministic scheduling.
Induction module out of stock, nine-day lead time. Ops is asked to order it and the proposed
slot moves out accordingly.

**7 · Resident rejects slots** — the loop that has to give up.
Three slots proposed and refused, then the scheduling tool itself refuses to propose a fourth
and tells the agent to hand the thread to ops.

**8 · Guardrail — apparent emergency**
The property manager logged "hob showing an error code". The resident's first message
describes a bang, a burning smell and a spreading scorch mark. The agent must not
troubleshoot this.
> *Talking point:* PRD §7 — where the agent hits something it can't competently handle, it
> says so plainly and stops rather than improvising.

**Then, the two things worth showing last:**

- **Knobs tab.** The PRD's open questions as live dials. Drop the PM threshold below the
  replacement cost and re-run scenario 3 — a PM gate now appears where it didn't before.
  Raise it above and the gate disappears.
- **LLM vs fallback.** Turn off *"Repair vs replace: LLM path"* and re-run scenario 3. The
  same decision now comes from the age/cost heuristic instead, and the trace says which ran.
  Both produce an A/B/C/D code and a confidence — but note the `confidence_basis` field:
  the heuristic *computes* confidence from distance to its decision boundaries; the model
  *self-reports* it. Those are not the same quantity, which is one of the PRD's open
  questions made visible rather than hidden.

---

## How it's built

**Claude Agent SDK**, one `ClaudeSDKClient` per issue thread (PRD §4.4). The three loops from
§3.2 run as sequential phases inside that one session, so everything triage learned is still
in context when booking runs.

**The agent can only do Iterum things.** `tools=[]` removes every built-in (Read, Write, Bash,
Grep, WebSearch…) from Claude's context, and `setting_sources=[]` stops any local settings
leaking in. The fifteen PRD tools plus three loop-exit tools are registered as one in-process
MCP server. A `PreToolUse` hook denies anything outside that surface and surfaces it in the
trace, so a leak would be visible rather than silent.

**The autonomy model is the permission system.** This is the part worth explaining:

| PRD §3.4 | Mechanism |
|---|---|
| Repair path — fully autonomous | Those tools sit in `allowed_tools`, so they're auto-approved and never reach the callback |
| Replacement — engineer then PM | `book_visit` is deliberately **left out** of `allowed_tools`, so every booking attempt falls through to `can_use_tool`, which checks the approvals actually exist |
| Warranty — always a handoff | A `PreToolUse` hook, which runs before everything else in the evaluation order |
| Everything logged | Same hook — nothing can escape it |

The gate is on the *action*, not on the messaging. Even if the agent never asked the engineer,
a replacement booking is still refused.

**Loop exits are explicit tool calls** — `complete_triage`, `submit_recommendation`,
`conclude_booking`. §3.2's exit conditions are unchanged; making the exit a tool call just
means you can see exactly where model judgement ends and control returns to the orchestrator.

**The decision log** (`logs/decision_log.jsonl`) records every recommendation, override,
approval and guardrail block. Per PRD §7, that file is the dataset that would eventually
validate the model.

---

## What's real and what isn't

**Real**, taken from Iterum's own files:
- The fault taxonomy — 6 appliance types, 55 categories, with the actual `label_slug` keys,
  extracted from `Issue Category Analysis.xlsx`.
- Property, operator, brand, model and supply-chain-partner names, from the same workbook's
  Issue Log and the onboarding appliance CSVs.
- The A/B/C/D recommendation vocabulary and the heuristic thresholds (repair > 70% of
  replacement; age > 7 years), from Iterum's decision-analysis brief.

**Invented**: individual people — residents, engineers, property managers. There's no source
data for them and no reason to use real ones.

**Mocked**: Iterum IQ, Airtable, the WhatsApp Business API, Mailgun. All of it is one JSON
document shaped like IQ's visits-nested-within-issues model, so the agent logic would transfer
if it were ever pointed at production.

**Simulated**: the resident, in auto-play mode, so a scenario runs hands-free for a recording.
Each scenario gives the simulator a hidden ground truth the agent can't see, so triage has
something real to discover. Turn auto-play off and you type the replies yourself.

---

## Deliberately not built

Following the PRD's own scope table: resident-initiated reporting, emergency escalation
downstream of the handoff, post-visit closure, IQ↔Yardi sync, invoicing, automated parts
ordering, OEM warranty automation, and `search_manuals()` against a vector DB of OEM manuals.
Route optimisation and cross-property engineer pooling are explicitly next-version; slot
selection here is the deterministic v1 rule from §5.1.

## Open questions this prototype does not answer

- What number the PM cost-approval threshold should actually be. £400 is a placeholder.
- Whether the engineer notification channel is WhatsApp or Airtable — the demo simulates both.
- What underlies the 0.7 confidence threshold. The two paths produce confidence by genuinely
  different means, and the prototype shows that rather than papering over it.

**One the prototype surfaced that the PRD doesn't mention:** §5.1's slot rule is
`first service day on or after today + parts lead time`. With parts in stock that resolves to
*today* if today happens to be a service day — and in the `clear_repair` run it did, booking a
visit for the same afternoon. The rule is implemented exactly as written, because changing the
spec silently would hide the finding. A real v1 probably needs a minimum notice period, or the
engineer's actual day capacity, neither of which the PRD currently defines.

---

## Project history

| Module | What it added | Where to look |
|---|---|---|
| 1 — Design & prototype | The PRD and this prototype | `docs/PRD.md`, this README |
| 2 — Skills | Three skills (troubleshooting, repair vs. replace, escalation) and ten appliance fault references, loaded by `agent/skills.py` | `skills/`, `docs/module2/` |
| 3 — Subagent | *In progress:* the repair-vs-replace assessment as a subagent | — |

For a one-page map of what exists and how the pieces connect, start with
[`docs/PROJECT_MAP.md`](docs/PROJECT_MAP.md).
