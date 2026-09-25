# Repair-vs-replace subagent — spec

Module 3. Written before any code. Lives at `docs/module3/SUBAGENT_SPEC.md`.
Decisions here are settled; if something needs to change during the build, change it here first.

## The task

Once triage decides an engineer is needed, someone has to judge whether the appliance is likely
a repair or a replacement, and how confident that judgement is. That call decides what happens
next: a confident repair books straight away; a likely replacement goes to the engineer (and the
PM, if over £400) before anything is booked.

This is the task being handed to a subagent.

## Why a subagent, not a prompt or a skill

Today the assessment is already a separate AI call, but its answer is only advisory. The main
agent reads it, then types its own version into `submit_recommendation`. In one Module 2 test
run, the assessment gave a confidence of 0.6; the main agent submitted 0.78, crossing the
threshold, and nothing noticed. Any scenario reaching this step carries the same risk.

That failure answers the "why" on all three counts:

- **Independent reasoning.** The judgement needs to be made without the main agent's momentum.
  By the time triage ends, the main agent has spent a whole conversation heading towards a
  conclusion. If the repair-vs-replace rules were loaded into the main agent as a skill, the
  judgement would happen in that same crowded context.
- **Dedicated context.** The assessment should see the fault evidence and nothing else: not the
  main agent's reasoning, not the resident's frustration, not scheduling chatter. A clean,
  filtered context is only possible if it runs separately.
- **Independent operation.** It gathers its own evidence (appliance record, similar past jobs)
  and its answer stands on its own. The main agent passes it on; it cannot rewrite it.

### How the skill and the subagent fit together

They are not two separate steps. The **skill** is the rulebook: the written method, the factors
to weigh, the faults where the answer is fixed, and the confidence limits. The **subagent** is the
independent worker that follows that rulebook. The skill is loaded only into the subagent. The
main agent never sees it and never produces a repair-vs-replace opinion of its own, so there is no
skill output feeding into the subagent.

The skill stays a separate file, rather than being written into the subagent's code, because it is
the part that engineers review and correct. Keeping it as a readable document means their edits
change the subagent's behaviour without touching code.

## Purpose

Give a provisional repair-vs-replace recommendation with an honest confidence score, based only
on evidence about the appliance and the fault, that the rest of the system cannot change.

## Responsibilities

- Check the precondition: the issue is out of warranty. If not, refuse and say why.
- Look up the appliance and comparable past jobs.
- Weigh the evidence using the repair-vs-replace skill.
- Say plainly what evidence was missing and how that limited its confidence.
- On re-invocation, decide whether the new information could change the repair-vs-replace
  judgement for this fault. If it couldn't, return "no change" with a reason rather than
  re-assessing.

It does **not** talk to the resident, contact anyone, book anything or change any record.

## Context

- **Instructions:** the repair-vs-replace skill, plus the matching appliance fault reference.
- **Sees:** only the inputs listed below and what its own tools return.
- **Does not see:** the main agent's reasoning or provisional lean, the full conversation,
  complaints or emotional framing, scheduling or logistics.
- **Stated in its instructions:** a resident's tone is not evidence. "It's completely useless"
  says how they feel, not what's wrong.

## Tools

Read-only:

- `get_appliance` — make, model, install date, past issues
- `search_similar_issues` — comparable jobs and their outcomes

Not `check_warranty`: warranty is settled in triage and in-warranty jobs never reach this point.
The precondition check above is a guard in code, not a second lookup.

It returns its answer by calling `submit_assessment`, an exit tool rather than a data tool
(CLAUDE.md invariant 5), which validates the answer against the output table. On
re-invocation only, it has a second exit, `submit_no_change`, taking a reason.

## Inputs

Passed by the main agent at the end of triage:

- Issue ID and appliance ID
- Troubleshooting steps attempted and what happened
- The resident's **symptom descriptions, verbatim** ("clicking but won't light", "smells of
  burning") — only statements about the appliance or fault
- Known gaps, e.g. no photo available

No summary of the fault is passed. An earlier "confirmed fault, in one or two sentences"
input was removed after the first live runs: everything it held was already in the quotes,
the PM description or the fault category, and the only thing it added was the main agent's
own interpretation ("consistent with a thermal-shock crack"), which is exactly what the
subagent must not see.

Supplied by code from Iterum records, not by the main agent:

- Warranty status (must be out of warranty), read from the store for the precondition guard
- Estimated repair and replacement costs, from the issue record — the skill weighs repair
  economics, and these are figures the system already knows

On re-invocation, additionally:

- The previous assessment ID
- The new information, quoted exactly as the resident said it

Re-invocation is its own main-agent tool, `reassess_repair_vs_replace`, whose schema holds only
the issue ID, appliance ID, previous assessment ID and the new quotes. The main agent does not
re-send the earlier evidence: code rebuilds the brief from the previous assessment's stored brief
and adds the new quotes, marked as new, so earlier evidence cannot be restated or dropped. The
subagent is not shown its previous code or confidence; it judges relevance, then (if relevant)
assesses the combined evidence afresh.

**Two relevance standards, deliberately different.**

- **What the main agent passes on (broad):** anything about the appliance or the fault goes in;
  scheduling preferences, logistics and unrelated grievances stay out. The same filter applies to
  a first assessment and a re-invocation. The main agent is not asked to judge what matters to
  the assessment - that would bring its own view of the outcome back in.
- **Whether the subagent re-assesses (narrow):** could this new information change the
  repair-vs-replace judgement for this fault? If not, it returns `no_change`, even when the
  information is about the appliance.

The gap between the two is intended. In the first `irrelevant_info` run (step 5), a long-standing
stiff soap drawer on a washer-dryer with a failed drain pump was about the appliance, so it was
rightly passed on - but the subagent, applying the same broad test, re-assessed instead of
answering `no_change`. It kept code B but produced a new assessment (confidence 0.85 → 0.78) that
replaced the submitted one on evidence that could not bear on the fault. A re-assessment is not
free: it supersedes the submitted recommendation, must be submitted before booking continues, and
clears any engineer or PM approval given on the one it replaces.

## Outputs

One assessment, logged with its own ID:

| Field | What it holds |
|---|---|
| `assessment_id` | Unique per assessment |
| `status` | `assessed`, `no_change`, `refused` or `reassessment_failed` |
| `code` | The recommendation code, as defined in `agent/config.py` |
| `confidence` | 0–1 |
| `rationale` | Plain-language reasoning, usable in the engineer brief |
| `evidence_used` | What the judgement rests on |
| `evidence_missing` | What would have changed it (e.g. a photo) |
| `limits_applied` | Any confidence limits from the skill, and why (see below) |
| `source` | `subagent` or `fallback` |
| `contra_indicators` | The strongest case against its own code. Required unless determinative |
| `determinative` | True when the code came from the skill's fixed-outcome list, not from weighing |
| `confidence_basis` | Where the confidence came from: self-reported (subagent) or computed (fallback) |

**Confidence limits.** Confidence can normally be anywhere from 0 to 1. The skill sets a ceiling
in a few specific situations where key evidence is missing — for example, a fault that should be
confirmed by photo can't score above a set level without one, however sure the reasoning feels.
The subagent records when one of these ceilings applied, so it's visible rather than buried.

One narrow check sits in code: confidence can never exceed a limit the assessment itself
reports in `limits_applied`. If it does, it is held at the lowest reported limit and the cap
is recorded on the assessment and in the log. The code does not decide whether a limit
*should* have applied — that stays with the skill.

## Constraints

- **Its answer is final.** The main agent submits by `assessment_id` only. `submit_recommendation`
  no longer accepts a code or confidence, so there is nothing to overwrite. Only the latest
  assessment for an issue can be submitted.
- **The booking gate follows the submitted code, never the visit type.** Whether a booking is a
  replacement is read from the submitted recommendation (codes A and C), not from the
  `visit_type` the main agent passes to `book_visit`, so a code A booked as "repair" still hits
  the engineer gate. The one way a replace code becomes a repair booking is an engineer
  override — a human, not the main agent. A code B booked as a replacement is refused as a
  mismatch. `book_visit` is also refused if no recommendation has been submitted, or if a newer
  assessment exists than the one submitted. Submitting a different assessment clears any
  engineer or PM decision given on the previous one.
- **The main agent has no route to disagree.** Its only lever is new information: if the resident
  says something new about the appliance or fault, it re-invokes the subagent. It cannot escalate
  because it prefers a different answer. The human check on the recommendation is the engineer,
  downstream — every replacement is confirmed by them, and every low-confidence repair reaches
  them with the uncertainty spelled out.
- **Recommendations are provisional routing, never a diagnosis**, in wording as well as intent.
- **Confidence threshold is 0.7** (matching the PRD; the code's 0.75 is changed). At or above, a
  repair routes autonomously. Below, it still books but the engineer brief leads with the
  uncertainty. A replacement goes to the engineer gate at any confidence.

Normal escalation rules still apply throughout (safety, a request for a person, and so on). They
are unrelated to the assessment.

## When it's called

**Called** when triage ends with "needs engineer", the appliance is out of warranty, and its type
has a fault reference file. (No reference file → ops, as per the PRD.)

**Not called** when triage ends resolved, in warranty or halted.

**Re-invoked** when the resident shares new information about the appliance or fault. At most
twice per issue. A third attempt goes to ops instead, with the assessment history attached.

- **Window.** Re-invocation is allowed in the decision and booking loops until a visit is booked.
  A plain second call to `assess_repair_vs_replace` is refused once an assessment exists, so the
  cap cannot be bypassed.
- **Relevance.** The subagent decides, not code, using the narrow standard above: if the new
  information could not change the repair-vs-replace judgement for this fault, it exits with
  `submit_no_change` and a reason; the log records
  `status: no_change`, carrying forward the previous code and confidence for reference. A
  `no_change` cannot be submitted, so the recommendation already submitted stands. If it is
  could, it re-assesses and exits with `submit_assessment` as usual.
- **What counts.** Every re-invocation that reaches the subagent counts towards the cap, whether
  it ends `assessed`, `no_change` or `reassessment_failed`. Input rejected by the filter (not verbatim, a verdict, a
  stale previous ID) never reached the subagent and does not count.
- **The cap.** On a third attempt the subagent is not run. Code raises the ops request itself,
  with the full assessment history attached, rather than relying on the main agent to include
  it. The thread is then marked escalated and the `PreToolUse` hook blocks booking, slot-finding
  and submitting for the rest of it.
- **A new assessment in booking** must be submitted with `submit_recommendation` before booking
  continues; the gate refuses a booking on a superseded assessment.
- **No fallback on re-invocation.** The rules-based fallback ignores resident statements, so
  re-running it on new information would produce a "new" assessment that never read the new
  information, and submitting it would clear approvals for nothing. So on re-invocation the
  fallback is not run. If the subagent fails (or the LLM path is switched off), the attempt is
  logged with status `reassessment_failed` and the reason; the previous assessment stands; no new
  assessment exists, so nothing needs resubmitting and no approvals are cleared. The attempt
  counts towards the cap. Its new information is not lost: it goes into the engineer note on the
  visit (see Fallback), and is carried into the next re-invocation as still-new information.

## Fallback

If the subagent fails — API error, timeout, or output that doesn't match the table above — the
rules-based fallback runs instead and returns the same fields, with two differences:

- `source` is `fallback`, so the log always shows which path produced the recommendation.
- Its recommendations are always treated as below the 0.7 threshold. A lookup table can't judge
  its own certainty the way the subagent can, so it shouldn't trigger autonomous routing. A
  fallback repair still books, but the engineer is told it came from the backup rules. Its
  computed confidence is kept as it is; `meets_threshold` is false whatever the number.

It weighs age and cost, with one exception: it reads the skill's **determinative faults** table
(`skills/iterum-repair-vs-replace/SKILL.md`) and, when the issue's fault category is listed there,
returns that code with `determinative: true` rather than weighing. Confidence is then capped per
the skill's limits for that fault; with no photo handling in Module 3, that is the skill's
"photo not supplied" limit (0.6), recorded in `limits_applied`. A cracked hob is code A on the
fallback path as on the subagent path. Like the subagent, it must give `contra_indicators` unless
determinative.

It is used for a first assessment only; on re-invocation it is not run (see "When it's called").

**Telling the engineer.** Code, not the main agent, writes what the engineer sees about the
assessment:

- **On the visit.** `book_visit` attaches an engineer note built from the submitted assessment:
  source, code, confidence and whether it met the threshold (leading with the uncertainty when it
  did not, and saying plainly when it came from the backup rules), evidence missing, limits
  applied, and any new information from a `reassessment_failed` attempt since that assessment,
  marked as not assessed.
- **At the engineer gate.** The gate context carries the same assessment summary, whatever the
  main agent wrote in its message.

**Reference files (open issue #5).** Checked in build step 4. The fallback's triage fault
patterns stay in `fallbacks.py`. The reference files' checks are guidance written for the model
("ask what the display shows"), and which rows are unsafe for a resident is marked only in
wording ("—", "None — do not troubleshoot", gas rows on hobs where the technology is unknown), so
deriving resident steps from them means filtering safety rules out of prose. Instead `selftest.py`
fails if any `FAULT_PATTERNS` key has no matching reference section. Real single-sourcing is
recorded as open issue #5 in `PROJECT_MAP.md`.

## How we'll know it works

- **`selftest.py` (free):** the submitted recommendation always matches the subagent's output
  exactly; `submit_recommendation` rejects anything but an assessment ID; the warranty guard
  refuses; the re-invocation cap holds; fallback results are treated as below threshold; the main
  agent's instructions contain none of the repair-vs-replace skill.
- **All 8 existing scenarios:** those reaching repair-vs-replace show an exact match between what
  the subagent produced and what was submitted; those ending earlier show the subagent was never
  called.
- **New scenarios:** new fault information arrives mid-conversation (re-assesses); irrelevant
  information arrives (no change); the cap is reached (goes to ops); the fallback path; a resident
  with heavy frustration but symptoms pointing to repair.
- **Consistency:** the same scenario can produce different results on different runs, because the
  model isn't fully predictable. So every scenario that reaches repair-vs-replace, existing and
  new, is run three times via `verify.py`. The routing should match across all three.

## Out of scope

- Photo handling. Faults that need photo confirmation stay capped in Module 3.
- Scheduling and engineer-brief subagents (noted in `PROJECT_MAP.md`, not built).

## Build order

One short Claude Code session per step, commit after each.

1. Output table, assessment log, and `submit_recommendation` taking an ID only. Confirm the
   repair-vs-replace skill is loaded only into the assessment, never the main agent.
2. Subagent with filtered inputs, its two tools and the warranty guard.
3. Re-invocation with the fault-relevance check and the cap of two.
4. Fallback returning the same fields, below threshold, reading the determinative table; engineer
   note on the visit and at the gate; no fallback on re-invocation; check the reference files for
   issue #5.
5. Threshold to 0.7; selftest checks; new scenarios; repeated `verify.py` runs.
