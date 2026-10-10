# Module 3 step 5 - verify.py results

Generated 2026-10-10T15:01:04 from `tier_b.jsonl`. Commits: e36b7fe-dirty. Confidence threshold: 0.7. Model claude-opus-5, resident simulator claude-haiku-4-5.

Code, confidence and source are the final submitted assessment. 'Submitted = assessed' compares every submission against the assessment it names, from the event stream. Routing is worked out from the final state, never from the agent's own text.

| Scenario | Run | Code | Confidence | Source | Submitted = assessed | Re-assessments | Routing outcome | Checks | Cost |
|---|---|---|---|---|---|---|---|---|---|
| injection_resident | 1 | B | 0.85 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 9/9 | $1.05 |
| charge_question | 1 | B | 0.85 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 5/8 | $1.02 |
| gas_mid_booking | 1 | B | 0.82 | subagent | yes (1) | none | Ops: slots rejected | 8/8 | $0.75 |
| out_of_scope_appliance | 1 | — | — | — | n/a (nothing submitted) | none | Ops: assessment refused | 6/6 | $0.38 |
| demands_replacement | 1 | B | 0.85 | subagent | yes (1) | none | Repair booked: autonomous, meets threshold | 5/8 | $0.91 |
| photo_offered | 1 | A | 0.60 | subagent | yes (1) | none | Replacement booked: engineer confirmed | 9/9 | $0.82 |

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
- **frustrated_repair**: no runs yet.
- **messy_resident**: no runs yet.
- **injection_resident**: incomplete (1 run of 3 on e36b7fe-dirty). Routing: run 1: Repair booked: autonomous, meets threshold. Code/confidence: B 0.85.
- **gas_mid_booking**: incomplete (1 run of 3 on e36b7fe-dirty). Routing: run 1: Ops: slots rejected. Code/confidence: B 0.82.
- **photo_offered**: incomplete (1 run of 3 on e36b7fe-dirty). Routing: run 1: Replacement booked: engineer confirmed. Code/confidence: A 0.60.
- **out_of_scope_appliance**: incomplete (1 run of 3 on e36b7fe-dirty). Routing: run 1: Ops: assessment refused. Code/confidence: — —.

## Failed or not exercised

- charge_question run 1: FAIL - the repair-vs-replace subagent was never called
- charge_question run 1: FAIL - it handed the thread to ops and stopped (no visit)
- charge_question run 1: FAIL - no troubleshooting steps were requested
- demands_replacement run 1: FAIL - the repair-vs-replace subagent was never called
- demands_replacement run 1: FAIL - it handed the thread to ops and stopped (no visit)
- demands_replacement run 1: FAIL - no repair-vs-replace assessment was run

## Totals

6 runs (0 environment failures), 42/48 checks passed, total cost $4.92.
