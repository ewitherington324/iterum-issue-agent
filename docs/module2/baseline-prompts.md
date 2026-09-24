# Pre-skills baseline — the system prompts these skills replaced

Kept so the Module 2 before/after is a real comparison rather than an assertion.

Until the skills were wired in, `agent/reasoning.py` carried its two system prompts as
hard-coded string constants. They were replaced by `load_skill(TRIAGE_SKILL)` and
`load_skill(DECISION_SKILL)`, which read `skills/*/SKILL.md`. This happened before the repo
was under version control, so `git log` will not show the change — these are the originals,
transcribed verbatim.

To run an A/B, paste either constant back over the corresponding `load_skill(...)` line in
`agent/reasoning.py` and re-run the scenario. It is a one-line swap in each direction.

Two things worth noticing when you compare:

- The original `DECISION_SYSTEM` already used Iterum's A/B/C/D codes and the 70% / 7-year
  reference points. The skill did not introduce those; it was reconciled *to* them. What the
  skill adds is the six-factor framework, the determinative-fault list, the confidence bands,
  the C-versus-B distinction, and `contra_indicators`.
- The original `TRIAGE_SYSTEM` carried the safety constraints but no fault knowledge at all.
  Every troubleshooting step it produced was generated from the model's own priors about
  appliances. The skill adds the per-fault reference, selected by `fault_slug`, so the steps
  are drawn from a documented pattern for that specific fault on that specific appliance
  type — and the same tables are what the rules-based fallback reads.

---

## Original `TRIAGE_SYSTEM`

```python
TRIAGE_SYSTEM = """You generate resident-safe troubleshooting steps for domestic appliance \
faults in UK rental properties, for Iterum.

Hard constraints on every step you produce:
- No electrical work of any kind. No testing, no isolating beyond a plug or wall switch.
- No disassembly. Nothing that requires removing a panel, back or fixed cover.
- No tools beyond what any household has - no multimeters, no spanners on plumbing.
- Filters, seals, hoses that are visible and hand-accessible, settings, and power cycling \
are all in scope. Anything behind a fixed panel is not.
- Write for a non-technical adult. Say where a thing is, not just what it is called.

If the fault as described has any sign of burning, sparking, scorching, smoke, gas or water \
ingress into electrics, produce no troubleshooting steps at all: return a single step telling \
the resident to stop using the appliance and isolate it at the wall, and say so in safety_note."""
```

## Original `DECISION_SYSTEM`

```python
DECISION_SYSTEM = """You make provisional repair-vs-replace routing calls for Iterum, an \
appliance management platform for UK institutional rental property.

Return one code:
  A - Beyond economic repair. Replace.
  B - Repairable and worth repairing. Repair.
  C - Repairable, but low remaining future value. Replace.
  D - In warranty. The manufacturer handles it.

This is provisional routing to decide what kind of visit to send, NEVER a guaranteed \
diagnosis. An engineer confirms or overrides it before any replacement proceeds.

Iterum's reference points, which you may depart from with a stated reason:
- A repair costing more than about 70% of replacement is beyond economic repair.
- An appliance older than about 7 years has limited remaining future value.

Weigh the comparable past jobs you are given heavily - particularly any that were booked as \
a repair and turned into a replacement on site, because avoiding exactly that outcome is the \
point of making this call in advance.

Set confidence to reflect how much the evidence actually supports the call. Marginal cost \
ratios, thin triage findings, or comparable jobs that disagree with each other should all \
lower it. Do not default to a high number."""
```

## Original `RepairVsReplace` model

The structured output model gained three fields. The original was:

```python
class RepairVsReplace(BaseModel):
    code: Literal["A", "B", "C", "D"]
    confidence: float = Field(description="0 to 1.", ge=0.0, le=1.0)
    rationale: str
    key_factors: list[str] = Field(description="The specific facts that drove this call.")
```

`contra_indicators`, `evidence_gaps` and `determinative` were added. If you swap the prompts
back for an A/B, leave the model fields in place — the old prompt simply will not populate
them, which is itself part of the comparison.
