# Module 5 — Key failures and improvements

The full numbers are in `results/RESULTS.md`. Total spend was $23.69, against a $30 cap. The most useful findings were contradictions between documents the agent relies on, which no single test would have exposed on its own.

## What held up

- **Repair-or-replace calls were accurate and consistent.** All 34 assessments gave an acceptable code, every case gave the same code on both runs, and every confidence cap was respected.
- **Planted instructions never changed a decision.** That held in the component tests and end to end.
- **A gas smell reported mid-booking stopped the booking.**
- **No regressions.** The 6 earlier scenarios re-run on today's code passed all 59 checks.

## Failures found

1. **Unsafe gas advice.** The troubleshooting step generator told a resident with a gas hob to lift, dry and reseat the burner caps, in both runs. The product rules allow no resident action on gas. The cause was the hob guidance file, which explicitly allowed it, and the model followed the more specific document.
2. **Escalation rules lost in copying.** When asked "will I have to pay?", or faced with a demand for a replacement, the agent should hand over to a person. Instead it deflected and booked a repair, in all four runs. The skill lists these triggers, but the hand-copied version in the agent's instructions had dropped them.
3. **Volunteering who pays.** In three scenarios the agent said things like "at no cost to you" and "this is ours to sort". Only the judge caught this.
4. **Accepting a photo it can't receive.** The agent said "yes please to the photo", then went on as if it had seen one. The keyword check passed and the judge caught it.
5. **Smaller issues:**
   - a crash when cost estimates are missing;
   - confidence of 0.75–0.82 despite contradictory symptoms;
   - improvised steps for an unsupported appliance;
   - bundled questions.

## Fixed and re-tested

| Fix | Before | After |
|---|---|---|
| Hob guidance aligned with the rules (no resident action on gas) | Cap lifting in 2/2 runs | No cap lifting in 2/2. The judge still flags narrower points (below) |
| Escalation triggers restored, plus a selftest that blocks future drift | 0/4 runs handed over | 4/4 handed over; the frustrated-resident scenario still books its repair |
| Missing costs shown as "unknown" | Crash in 2/2 runs | Completes: repair, 0.65, below the threshold |

## What the evaluation itself taught

- My first unsafe-phrase screen flagged 8 runs, and only 2 were real. Most flags were the agent's own warnings ("please don't tilt it"). The second version ignores negated phrases.
- One end-to-end check wrongly failed a correct gas run. That run was re-scored from its transcript, and the check is fixed.
- The judge agreed with itself only 82% of the time, mostly on clarity. It also can't see approvals, so after an engineer had confirmed a replacement it still marked firm language as overconfident.

## Next improvements

- Get a Gas Safe registered engineer's ruling on two unclear safety rules: operating a gas hob's controls in order to describe it, and unlocking a control lock.
- Stop the agent discussing who pays, with a code check added alongside the judge.
- Have the agent say plainly that it can't receive photos.
- Lower confidence when a resident contradicts themselves.
- Give the judge the approval history, and tighten the clarity rubric.
- Add the likely part and what to check first to the engineer note.
- Have an Iterum engineer review the saved transcripts and labels before deployment.
