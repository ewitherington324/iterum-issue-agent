# Module 2 — what the skills changed

Submission note for the Module 2 assignment. Evidence for every claim below is in
`docs/module2-verification.md`; the skills themselves are in `skills/`, and the system
prompts they replaced are preserved verbatim in `skills/BASELINE.md`.

> **Figures below are from the composite run documented in §1 of the verification doc.**
> Update after the single clean eight-scenario sweep.

---

## What was there before

The prototype already made two discrete LLM reasoning calls — `get_triage_steps` and
`assess_repair_vs_replace` — each with a hard-coded system prompt and a rules-based
fallback. Those prompts were not bad. `DECISION_SYSTEM` already carried Iterum's A/B/C/D
codes and the real 70% and 7-year reference points from the decision-analysis brief.

What they carried was *policy*. What they did not carry was *knowledge*. `TRIAGE_SYSTEM`
told the model what a resident must never be asked to do, and then left it to generate
troubleshooting steps entirely from its own priors about appliances. Every step a resident
received was invented at request time, with nothing to check it against and no way for an
Iterum engineer to review, correct or version what the agent was telling people to do.

## What changed

**Three skills, chosen on one test.** Deterministic work stays code; judgment-under-policy
becomes a skill. Warranty lookups, slot arithmetic and inventory checks were left alone —
making them skills would have added nothing. The three that became skills are the three
places the PRD already identified as loops rather than steps: resident-safe troubleshooting,
the repair-versus-replace call, and knowing when to stop.

**Fault knowledge became a reviewable asset.** Ten appliance reference files, six of them
keyed by Iterum's real taxonomy slugs — 55 categories extracted from the issue history.
Because the reasoning call already receives `fault_slug`, the lookup is exact: the model is
handed the documented pattern for *that* fault on *that* appliance type, not twelve thousand
words to search. In the verification run every scenario that sought triage steps received
its matching section, 6/6. The one that did not call for steps was the emergency scenario,
which halted before troubleshooting — the designed behaviour.

The reference files are also what the rules-based fallback reads, so the LLM path and the
degraded path now share one source and cannot drift apart. That was a claim in the PRD
before; it is closer to literally true now.

**The decision became auditable.** The biggest single change is `contra_indicators` — the
assessment must now argue against its own conclusion. In the run it was populated in all
four assessed scenarios with substantive counter-arguments, not filler. On the replacement
case it attacked its own key factor directly, noting that a 74% cost ratio is only
marginally over the 70% reference point and that if the fault turned out to be the
thermostat alone the true cost would fall well inside it. Two scenarios surfaced a
data-quality problem nobody asked about: two different replacement prices on record for the
same appliance.

That matters beyond neatness. Every recommendation is logged against what the engineer
later finds, and that log is what will eventually validate — or fail to validate — the
model. A log that records only the conclusion tells you an override happened. A log that
records the counter-argument tells you whether the model had already seen the reason it was
overruled. The second is the one you can learn from.

**Escalation stopped being a single stop button.** The first draft halted the conversation
on any complaint. That would have been wrong in a way that quietly destroys the product:
most residents contacting a maintenance service are unhappy, so an agent that treats
dissatisfaction as a stop condition hands ops the exact work it was built to absorb. The
skill now separates halting from flagging. Distress means acknowledge, stop asking the
resident to do things, route to an engineer and prioritise the slot — with a human notified
and the record flagged, but the issue still being solved. The test for halting is narrow:
would the next message commit Iterum on money, fault or the tenancy?

## What it made easier

Reuse is the obvious one — the same policy now serves the reasoning call, the fallback and
any future path, from one file. But the more useful change is that the agent's behaviour
became **reviewable by the people who know the domain.** A safety constraint buried in a
Python string constant is invisible to an Iterum engineer. A markdown file with a status
banner asking for their sign-off is something they can actually mark up. Every reference
file carries that banner, because the fault content is currently general appliance knowledge
rather than Iterum service data.

## What I got wrong, and the thing most worth knowing

The intended integration was the obvious one: drop the SKILL.md files into `.claude/skills/`
and let the SDK discover them. That would have loaded nothing. `setting_sources=[]` in
`runner.py` — there to keep built-in tools and stray local config out of the agent — also
disables on-disk skill discovery. The files would have sat in the repo looking correct while
the reasoning calls ran unconstrained, returning plausible steps with none of the safety
rules applied and nothing in the trace to show it.

The fix was to stop relying on discovery. `agent/skills.py` reads the files and passes each
as the system prompt of its call. That turned out to be stronger than discovery anyway: the
skill is in context on *every* call rather than whenever the model judges it relevant, which
is not a property worth leaving to judgement on instructions about what a resident may
safely touch. The escalation skill goes further and is compiled into the base system prompt,
because a guardrail that loads once the model decides it is relevant has already failed.

The general lesson, and the thing I would tell anyone starting Module 2: a skill is a file
plus a loading strategy, and the loading strategy is a design decision rather than a
default. Getting the file right is the easy half.

## What this does not yet show

Stated plainly, because the verification doc does the same.

The `determinative` branch — the fixed-outcome path for a cracked hob — has no evidence. It
returned `false` in every scenario, which is also its default, and no scenario in the suite
carries that fault. An eighth scenario closes this.

The guardrails were never reached in a live run. The agent routed correctly in both the
warranty and emergency scenarios and never attempted the blocked tool, so the only evidence
those backstops work comes from `selftest.py` exercising them synthetically. Good outcome,
weak evidence, and both halves should be said together.

Every result is one generation per scenario. Nothing here demonstrates consistency across
repeat runs.

And the fault content itself is unvalidated. It is general appliance knowledge organised
against Iterum's real taxonomy, not Iterum service data, and it needs engineer sign-off
before it goes anywhere near a resident — the engineer-only signal rows most of all.
