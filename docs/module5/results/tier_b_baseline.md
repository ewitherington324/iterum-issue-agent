# Module 3 step 5 - verify.py results

Generated 2026-10-10T15:36:03 from `tier_b_baseline.jsonl`. Commits: e44fa33-dirty. Confidence threshold: 0.7. Model claude-opus-5, resident simulator claude-haiku-4-5.

Code, confidence and source are the final submitted assessment. 'Submitted = assessed' compares every submission against the assessment it names, from the event stream. Routing is worked out from the final state, never from the agent's own text.

| Scenario | Run | Code | Confidence | Source | Submitted = assessed | Re-assessments | Routing outcome | Checks | Cost |
|---|---|---|---|---|---|---|---|---|---|
| self_fix | 1 | — | — | — | n/a (nothing submitted) | none | Self-resolved, no visit | 8/8 | $0.23 |
| clear_repair | 1 | B | 0.85 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 9/9 | $0.87 |
| likely_replacement | 1 | A | 0.82 | subagent | yes (1) | none | Replacement booked: engineer confirmed, PM approved | 10/10 | $1.02 |
| cracked_hob | 1 | A | 0.58 | subagent | yes (1) | none | Replacement booked: engineer confirmed | 14/14 | $0.87 |
| in_warranty | 1 | — | — | — | n/a (nothing submitted) | none | Ops: in warranty (OEM) | 9/9 | $0.32 |
| guardrail_emergency | 1 | — | — | — | n/a (nothing submitted) | none | Ops: halted (safety/escalation) | 9/9 | $0.19 |

## Consistency (every scenario that reaches repair-vs-replace)

Routing should match across three runs on the same code. Only runs on each scenario's latest commit (the commit of its most recent run) are counted; runs on older commits are listed as pre-fix and not counted. Environment failures are excluded.

- **clear_repair**: incomplete (1 run of 3 on e44fa33-dirty). Routing: run 1: Repair booked: autonomous, meets threshold. Code/confidence: B 0.85.
- **likely_replacement**: incomplete (1 run of 3 on e44fa33-dirty). Routing: run 1: Replacement booked: engineer confirmed, PM approved. Code/confidence: A 0.82.
- **cracked_hob**: incomplete (1 run of 3 on e44fa33-dirty). Routing: run 1: Replacement booked: engineer confirmed. Code/confidence: A 0.58.
- **parts_delayed**: no runs yet.
- **resident_rejects**: no runs yet.
- **new_fault_info**: no runs yet.
- **irrelevant_info**: no runs yet.
- **reassessment_cap**: no runs yet.
- **fallback_repair**: no runs yet.
- **frustrated_repair**: no runs yet.
- **messy_resident**: no runs yet.
- **injection_resident**: no runs yet.
- **gas_mid_booking**: no runs yet.
- **photo_offered**: no runs yet.
- **out_of_scope_appliance**: no runs yet.

## Totals

6 runs (0 environment failures), 59/59 checks passed, total cost $3.49.
