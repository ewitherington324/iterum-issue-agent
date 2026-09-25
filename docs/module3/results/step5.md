# Module 3 step 5 - verify.py results

Generated 2026-09-25T19:30:25 from `step5.jsonl`. Commits: 7a9b1c4, 7a9b1c4-dirty, 893b73d, d87ae41. Confidence threshold: 0.7. Model claude-opus-5, resident simulator claude-haiku-4-5.

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
| new_fault_info | 2 | A | 0.60 | subagent | yes (1, 2) | 2 assessed (B->A) | Replacement booked: engineer confirmed, PM approved | 10/10 | $1.07 |
| new_fault_info | 3 | A | 0.55 | subagent | yes (1, 2) | 2 assessed (B->A) | Replacement booked: engineer confirmed, PM approved | 10/10 | $0.95 |
| new_fault_info | 4 | A | 0.60 | subagent | yes (1, 2) | 2 assessed (B->A) | Replacement booked: engineer confirmed, PM approved | 10/10 | $0.93 |
| irrelevant_info | 1 | B | 0.78 | subagent | yes (1, 2) | 2 assessed (B->B) | Repair booked: autonomous, meets threshold | 9/12 | $0.76 |
| irrelevant_info | 2 | B | 0.78 | subagent | yes (1) | 2 no_change | Repair booked: autonomous, meets threshold | 12/12 | $0.74 |
| irrelevant_info | 3 | B | 0.85 | subagent | yes (1) | 2 no_change | Repair booked: autonomous, meets threshold | 12/12 | $0.69 |
| irrelevant_info | 4 | B | 0.85 | subagent | yes (1) | 2 no_change | Repair booked: autonomous, meets threshold | 12/12 | $0.64 |
| irrelevant_info | 5 | B | 0.80 | subagent | yes (1) | not exercised | Repair booked: autonomous, meets threshold | 11/11 + 1 not exercised | $0.63 |
| reassessment_cap | 1 | B | 0.85 | subagent | yes (1) | none | ENVIRONMENT FAILURE | — | $0.60 |
| reassessment_cap | 2 | B | 0.60 | subagent | yes (1, 2, 3) | 2 assessed (B->B); 3 assessed (B->B) | Ops: slots rejected | 7/9 | $1.10 |
| reassessment_cap | 3 | B | 0.76 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 5/9 | $0.60 |
| reassessment_cap | 4 | B | 0.78 | subagent | yes (1) | 2 no_change | Repair booked: autonomous, meets threshold | 5/9 | $0.71 |
| reassessment_cap | 5 | B | 0.78 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 5/9 | $0.57 |
| fallback_repair | 1 | — | — | — | n/a (nothing submitted) | none | ENVIRONMENT FAILURE | — | $0.00 |
| fallback_repair | 2 | B | 0.89 | fallback | yes (1) | none | Repair booked: autonomous, engineer told uncertain (backup rules) | 13/13 | $0.47 |
| fallback_repair | 3 | B | 0.89 | fallback | yes (1) | none | Repair booked: autonomous, engineer told uncertain (backup rules) | 13/13 | $0.46 |
| fallback_repair | 4 | B | 0.89 | fallback | yes (1) | none | Repair booked: autonomous, engineer told uncertain (backup rules) | 13/13 | $0.44 |
| fallback_repair | 5 | B | 0.89 | fallback | yes (1) | none | Repair booked: autonomous, engineer told uncertain (backup rules) | 13/13 | $0.50 |
| frustrated_repair | 1 | — | — | — | n/a (nothing submitted) | none | ENVIRONMENT FAILURE | — | $0.00 |
| frustrated_repair | 2 * | B | 0.87 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 12/12 | $0.58 |
| frustrated_repair | 3 * | B | 0.85 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 12/12 | $0.60 |
| frustrated_repair | 4 * | B | 0.86 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 12/12 | $0.58 |
| frustrated_repair | 5 * | B | 0.85 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 12/12 | $0.55 |
| messy_resident | 1 * | B | 0.60 | subagent | yes (1, 2, 3) | 2 assessed (B->B); 3 assessed (B->B) | Ops: slots rejected | 7/7 | $0.00 |
| messy_resident | 2 * | B | 0.76 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 7/7 | $0.00 |
| messy_resident | 3 * | B | 0.78 | subagent | yes (1) | 2 no_change | Repair booked: autonomous, meets threshold | 7/7 | $0.00 |
| messy_resident | 4 * | B | 0.78 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 7/7 | $0.00 |

\* Re-scored against the current checks from `logs/decision_log.jsonl`, without re-running; the row's `rescored` field in the jsonl says how and keeps the original result. A messy_resident row re-scored from a reassessment_cap run is the same run: its cost is counted once, under reassessment_cap.

## Consistency (every scenario that reaches repair-vs-replace)

Routing should match across three runs on the same code. Only runs on each scenario's latest commit (the commit of its most recent run) are counted; runs on older commits are listed as pre-fix and not counted. Environment failures are excluded.

- **clear_repair**: incomplete (1 run of 3 on d87ae41). Routing: run 1: Repair booked: autonomous, meets threshold. Code/confidence: B 0.85.
- **likely_replacement**: incomplete (1 run of 3 on d87ae41). Routing: run 1: Replacement booked: engineer confirmed, PM approved. Code/confidence: A 0.82.
- **cracked_hob**: incomplete (1 run of 3 on d87ae41). Routing: run 1: Replacement booked: engineer confirmed. Code/confidence: A 0.60.
- **parts_delayed**: incomplete (1 run of 3 on d87ae41). Routing: run 1: Repair booked: autonomous, meets threshold. Code/confidence: B 0.80.
- **resident_rejects**: incomplete (1 run of 3 on d87ae41). Routing: run 1: Ops: slots rejected. Code/confidence: B 0.85.
- **new_fault_info**: **consistent** across 3 runs on 893b73d. Routing: run 2: Replacement booked: engineer confirmed, PM approved; run 3: Replacement booked: engineer confirmed, PM approved; run 4: Replacement booked: engineer confirmed, PM approved. Code/confidence: A 0.60, A 0.55, A 0.60. Pre-fix, not counted: run 1 (d87ae41): Replacement booked: engineer confirmed, PM approved.
- **irrelevant_info**: **consistent** across 3 runs on 893b73d. Routing: run 3: Repair booked: autonomous, meets threshold; run 4: Repair booked: autonomous, meets threshold; run 5: Repair booked: autonomous, meets threshold. Code/confidence: B 0.85, B 0.85, B 0.80. Pre-fix, not counted: run 1 (d87ae41): Repair booked: autonomous, meets threshold; run 2 (7a9b1c4): Repair booked: autonomous, meets threshold.
- **reassessment_cap**: **consistent** across 3 runs on 893b73d. Routing: run 3: Repair booked: autonomous, meets threshold; run 4: Repair booked: autonomous, meets threshold; run 5: Repair booked: autonomous, meets threshold. Code/confidence: B 0.76, B 0.78, B 0.78. Pre-fix, not counted: run 2 (7a9b1c4-dirty): Ops: slots rejected.
- **fallback_repair**: **consistent** across 3 runs on 893b73d. Routing: run 3: Repair booked: autonomous, engineer told uncertain (backup rules); run 4: Repair booked: autonomous, engineer told uncertain (backup rules); run 5: Repair booked: autonomous, engineer told uncertain (backup rules). Code/confidence: B 0.89, B 0.89, B 0.89. Pre-fix, not counted: run 2 (7a9b1c4-dirty): Repair booked: autonomous, engineer told uncertain (backup rules).
- **frustrated_repair**: **consistent** across 3 runs on 893b73d. Routing: run 3: Repair booked: autonomous, meets threshold; run 4: Repair booked: autonomous, meets threshold; run 5: Repair booked: autonomous, meets threshold. Code/confidence: B 0.85, B 0.86, B 0.85. Pre-fix, not counted: run 2 (7a9b1c4-dirty): Repair booked: autonomous, meets threshold.
- **messy_resident**: **consistent** across 3 runs on 893b73d. Routing: run 2: Repair booked: autonomous, meets threshold; run 3: Repair booked: autonomous, meets threshold; run 4: Repair booked: autonomous, meets threshold. Code/confidence: B 0.76, B 0.78, B 0.78. Pre-fix, not counted: run 1 (7a9b1c4-dirty): Ops: slots rejected.

## Failed or not exercised

- irrelevant_info run 1: FAIL - the subagent judged the remark not about the fault (no_change)
- irrelevant_info run 1: FAIL - nothing new was submitted - the original assessment stands
- irrelevant_info run 1: FAIL - the engineer note on the visit comes from the original assessment
- irrelevant_info run 5: NOT EXERCISED - the subagent judged the remark could not change the judgement (no_change)
- reassessment_cap run 1: ENVIRONMENT FAILURE - the SDK reported is_error on the booking loop (stop_reason='stop_sequence') (not evidence about the agent)
- reassessment_cap run 2: FAIL - the third was stopped by the cap in code
- reassessment_cap run 2: FAIL - ops received the escalation with the full assessment history attached
- reassessment_cap run 3: FAIL - two re-invocations reached the subagent
- reassessment_cap run 3: FAIL - the third was stopped by the cap in code
- reassessment_cap run 3: FAIL - ops received the escalation with the full assessment history attached
- reassessment_cap run 3: FAIL - no visit was booked
- reassessment_cap run 4: FAIL - two re-invocations reached the subagent
- reassessment_cap run 4: FAIL - the third was stopped by the cap in code
- reassessment_cap run 4: FAIL - ops received the escalation with the full assessment history attached
- reassessment_cap run 4: FAIL - no visit was booked
- reassessment_cap run 5: FAIL - two re-invocations reached the subagent
- reassessment_cap run 5: FAIL - the third was stopped by the cap in code
- reassessment_cap run 5: FAIL - ops received the escalation with the full assessment history attached
- reassessment_cap run 5: FAIL - no visit was booked
- fallback_repair run 1: ENVIRONMENT FAILURE - the SDK reported is_error on the triage loop (stop_reason='stop_sequence') (not evidence about the agent)
- frustrated_repair run 1: ENVIRONMENT FAILURE - the SDK reported is_error on the triage loop (stop_reason='stop_sequence') (not evidence about the agent)

## Totals

36 runs (3 environment failures), 321/338 checks passed, total cost $18.81.
