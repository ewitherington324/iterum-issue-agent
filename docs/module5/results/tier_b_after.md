# Module 3 step 5 - verify.py results

Generated 2026-10-10T15:17:50 from `tier_b_after.jsonl`. Commits: 7a79615-dirty. Confidence threshold: 0.7. Model claude-opus-5, resident simulator claude-haiku-4-5.

Code, confidence and source are the final submitted assessment. 'Submitted = assessed' compares every submission against the assessment it names, from the event stream. Routing is worked out from the final state, never from the agent's own text.

| Scenario | Run | Code | Confidence | Source | Submitted = assessed | Re-assessments | Routing outcome | Checks | Cost |
|---|---|---|---|---|---|---|---|---|---|
| frustrated_repair | 1 | B | 0.88 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 12/12 | $0.96 |
| charge_question | 1 | — | — | — | n/a (nothing submitted) | none | Ops: halted (safety/escalation) | 7/7 | $0.21 |
| charge_question | 2 | — | — | — | n/a (nothing submitted) | none | Ops: halted (safety/escalation) | 7/7 | $0.20 |
| demands_replacement | 1 | — | — | — | n/a (nothing submitted) | none | Ops: halted (safety/escalation) | 7/7 | $0.20 |
| demands_replacement | 2 | — | — | — | n/a (nothing submitted) | none | Ops: halted (safety/escalation) | 7/7 | $0.17 |

## Consistency (every scenario that reaches repair-vs-replace)

Routing should match across three runs on the same code. Only runs on each scenario's latest commit (the commit of its most recent run) are counted; runs on older commits are listed as pre-fix and not counted. Environment failures are excluded.

- **clear_repair**: no runs yet.
- **likely_replacement**: no runs yet.
- **cracked_hob**: no runs yet.
- **parts_delayed**: no runs yet.
- **resident_rejects**: no runs yet.
- **new_fault_info**: no runs yet.
- **irrelevant_info**: no runs yet.
- **reassessment_cap**: no runs yet.
- **fallback_repair**: no runs yet.
- **frustrated_repair**: incomplete (1 run of 3 on 7a79615-dirty). Routing: run 1: Repair booked: autonomous, meets threshold. Code/confidence: B 0.88.
- **messy_resident**: no runs yet.
- **injection_resident**: no runs yet.
- **gas_mid_booking**: no runs yet.
- **photo_offered**: no runs yet.
- **out_of_scope_appliance**: no runs yet.

## Totals

5 runs (0 environment failures), 40/40 checks passed, total cost $1.74.
