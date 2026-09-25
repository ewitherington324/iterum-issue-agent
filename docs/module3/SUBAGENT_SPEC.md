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
- On re-invocation, decide whether the new information is about the appliance or fault. If it
  isn't, return "no change" with a reason rather than re-assessing.

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

## Inputs

Passed by the main agent at the end of triage:

- Issue ID and appliance ID
- The confirmed fault, in one or two sentences
- Troubleshooting steps attempted and what happened
- The resident's **symptom descriptions, verbatim** ("clicking but won't light", "smells of
  burning") — only statements about the appliance or fault
- Warranty status (must be out of warranty)
- Known gaps, e.g. no photo available

On re-invocation, additionally:

- The previous assessment ID
- The new information, quoted exactly as the resident said it

The filter for what counts as fault information is the same in both cases: about the appliance
or the fault goes in; scheduling preferences, logistics and unrelated grievances stay out.

## Outputs

One assessment, logged with its own ID:

| Field | What it holds |
|---|---|
| `assessment_id` | Unique per assessment |
| `status` | `assessed`, `no_change` or `refused` |
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

## Fallback

If the subagent fails — API error, timeout, or output that doesn't match the table above — the
rules-based fallback runs instead and returns the same fields, with two differences:

- `source` is `fallback`, so the log always shows which path produced the recommendation.
- Its recommendations are always treated as below the 0.7 threshold. A lookup table can't judge
  its own certainty the way the subagent can, so it shouldn't trigger autonomous routing. A
  fallback repair still books, but the engineer is told it came from the backup rules.

The fallback should read fault patterns from the same reference files rather than its own copy
(open issue #5). Check how structured those files are before changing this, and report back
if it's not straightforward.

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
4. Fallback returning the same fields; check the reference files for issue #5.
5. Threshold to 0.7; selftest checks; new scenarios; repeated `verify.py` runs.
