# Module 3 step 5 - verify.py results

Generated 2026-09-25T17:06:32 from `step5.jsonl`. Commits: 7a9b1c4, 7a9b1c4-dirty, d87ae41. Confidence threshold: 0.7. Model claude-opus-5, resident simulator claude-haiku-4-5.

Code, confidence and source are the final submitted assessment. 'Submitted = assessed' compares every submission against the assessment it names, from the event stream. Routing is worked out from the final state, never from the agent's own text.

| Scenario | Run | Code | Confidence | Source | Submitted = assessed | Re-assessments | Routing outcome | Checks | Cost |
|---|---|---|---|---|---|---|---|---|---|
| self_fix | 1 | — | — | — | n/a (nothing submitted) | none | Self-resolved, no visit | 8/8 | $0.17 |
| clear_repair | 1 | B | 0.85 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 9/9 | $0.64 |
| likely_replacement | 1 | A | 0.82 | subagent | yes (1) | none | Replacement booked: engineer confirmed, PM approved | 10/10 | $0.65 |
| cracked_hob | 1 | A | 0.60 | subagent | yes (1) | none | Replacement booked: engineer confirmed | 14/14 | $0.59 |
| in_warranty | 1 | — | — | — | n/a (nothing submitted) | none | Ops: in warranty (OEM) | 9/9 | $0.19 |
| parts_delayed | 1 | B | 0.80 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 8/8 | $0.57 |
| resident_rejects | 1 | B | 0.85 | subagent | yes (1) | none | Ops: slots rejected | 8/8 | $0.65 |
| guardrail_emergency | 1 | — | — | — | n/a (nothing submitted) | none | Ops: halted (safety/escalation) | 9/9 | $0.16 |
| new_fault_info | 1 | A | 0.60 | subagent | yes (1, 2) | 2 assessed (B->A) | Replacement booked: engineer confirmed, PM approved | 10/10 | $1.03 |
| irrelevant_info | 1 | B | 0.78 | subagent | yes (1, 2) | 2 assessed (B->B) | Repair booked: autonomous, meets threshold | 9/12 | $0.76 |
| irrelevant_info | 2 | B | 0.78 | subagent | yes (1) | 2 no_change | Repair booked: autonomous, meets threshold | 12/12 | $0.74 |
| reassessment_cap | 1 | B | 0.85 | subagent | yes (1) | none | ENVIRONMENT FAILURE | — | $0.60 |
| reassessment_cap | 2 | B | 0.60 | subagent | yes (1, 2, 3) | 2 assessed (B->B); 3 assessed (B->B) | Ops: slots rejected | 7/9 | $1.10 |
| fallback_repair | 1 | — | — | — | n/a (nothing submitted) | none | ENVIRONMENT FAILURE | — | $0.00 |
| fallback_repair | 2 | B | 0.89 | fallback | yes (1) | none | Repair booked: autonomous, engineer told uncertain (backup rules) | 13/13 | $0.47 |
| frustrated_repair | 1 | — | — | — | n/a (nothing submitted) | none | ENVIRONMENT FAILURE | — | $0.00 |
| frustrated_repair | 2 | B | 0.87 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 11/11 | $0.58 |

## Consistency (the five new scenarios)

Routing should match across three runs on the same code. Only runs on each scenario's latest commit (the commit of its most recent run) are counted; runs on older commits are listed as pre-fix and not counted. Environment failures are excluded.

- **new_fault_info**: incomplete (1 run of 3 on d87ae41). Routing: run 1: Replacement booked: engineer confirmed, PM approved. Code/confidence: A 0.60.
- **irrelevant_info**: incomplete (1 run of 3 on 7a9b1c4). Routing: run 2: Repair booked: autonomous, meets threshold. Code/confidence: B 0.78. Pre-fix, not counted: run 1 (d87ae41): Repair booked: autonomous, meets threshold.
- **reassessment_cap**: incomplete (1 run of 3 on 7a9b1c4-dirty). Routing: run 2: Ops: slots rejected. Code/confidence: B 0.60.
- **fallback_repair**: incomplete (1 run of 3 on 7a9b1c4-dirty). Routing: run 2: Repair booked: autonomous, engineer told uncertain (backup rules). Code/confidence: B 0.89.
- **frustrated_repair**: incomplete (1 run of 3 on 7a9b1c4-dirty). Routing: run 2: Repair booked: autonomous, meets threshold. Code/confidence: B 0.87.

Existing scenarios were run once each; see their rows above.

## Failed or not exercised

- irrelevant_info run 1: FAIL - the subagent judged the remark not about the fault (no_change)
- irrelevant_info run 1: FAIL - nothing new was submitted - the original assessment stands
- irrelevant_info run 1: FAIL - the engineer note on the visit comes from the original assessment
- reassessment_cap run 1: ENVIRONMENT FAILURE - the SDK reported is_error on the booking loop (stop_reason='stop_sequence') (not evidence about the agent)
- reassessment_cap run 2: FAIL - the third was stopped by the cap in code
- reassessment_cap run 2: FAIL - ops received the escalation with the full assessment history attached
- fallback_repair run 1: ENVIRONMENT FAILURE - the SDK reported is_error on the triage loop (stop_reason='stop_sequence') (not evidence about the agent)
- frustrated_repair run 1: ENVIRONMENT FAILURE - the SDK reported is_error on the triage loop (stop_reason='stop_sequence') (not evidence about the agent)

## Totals

17 runs (3 environment failures), 137/142 checks passed, total cost $8.90.
