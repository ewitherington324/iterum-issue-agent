"""Re-score step 5 runs against the checks that replaced the old ones, without re-running.

    .venv/bin/python docs/module3/results/rescore_step5.py

Two sets of rows, both read from logs/decision_log.jsonl (the event stream verify.py scores
from is not kept, but everything these checks need is in the decision log):

- frustrated_repair: the "no frustration words in the brief" check is replaced by "confidence
  within 0.1 of the clean runs" and "the rationale and contra-indicators cite no tone". The
  row is updated in place; `rescored.original` keeps the result it had.
- messy_resident: reassessment_cap runs 2-5 were the persona played freely by the model -
  which is exactly what messy_resident is. Each is scored against messy_resident's outcome
  checks and added as a messy_resident row pointing back at its reassessment_cap row. Its cost
  is 0 here so the totals count that run once.

The approvals check is scored from the gate's own booking decisions (`gate_check` in the log),
since `gate_closed` is not logged; it only rescores repair (code B) outcomes and marks any
other outcome as not re-scorable. Idempotent: rows already re-scored are skipped.
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import verify  # noqa: E402

JSONL = verify.RESULTS_DIR / "step5.jsonl"
LOG = ROOT / "logs" / "decision_log.jsonl"
# verify.py writes local time; the decision log is UTC. These runs were on EDT.
UTC_OFFSET = timedelta(hours=4)
COMMON = ("no built-in tool was ever reached", "the agent spoke to the resident",
          "triage loop exited explicitly")


def window(log: list[dict], row: dict, issue_id: str) -> list[dict]:
    """The live log entries of one run: from its scenario_started to the row's finish time."""
    end = (datetime.fromisoformat(row["at"]) + UTC_OFFSET).isoformat()
    starts = [r for r in log if r.get("event") == "scenario_started"
              and r.get("run_source") == "live" and r["scenario"] == row["scenario"]
              and r["at"][:19] < end]
    start = starts[-1]["at"]
    return [r for r in log if r.get("run_source") == "live" and r.get("issue_id") == issue_id
            and start <= r["at"] <= end + ".999999Z"]


def assessments_in(ev: list[dict]) -> list[dict]:
    return [r["assessment"] for r in ev if r["event"] == "assessment_recorded"]


def carried_common(row: dict) -> list[tuple[str, bool, str]]:
    checks = [(name, name not in row["failed"], "from the original row") for name in COMMON]
    if row["submitted_match"] is not None:
        checks.append(("every submitted recommendation matches its assessment exactly",
                       bool(row["submitted_match"]), "from the original row"))
    return checks


def rescore_frustrated(row: dict, ev: list[dict]) -> list[tuple[str, bool, str]]:
    final = next((a for a in reversed(assessments_in(ev))
                  if a["assessment_id"] == row["submitted_ids"][-1]), {})
    tone = verify.tone_cited(final)
    conf = row["confidence"]
    kept = [(name, name not in row["failed"], "from the original row") for name in (
        "triage was not halted - complaints are not an escalation",
        "the subagent was given a brief", "the code is B", "a visit was booked",
        "booking passed the gate on the repair path", "no human gate was opened")]
    return carried_common(row) + kept + [
        (f"confidence is within 0.1 of the clean runs ({verify.FRUSTRATED_CLEAN_CONFIDENCE})",
         isinstance(conf, (int, float))
         and abs(conf - verify.FRUSTRATED_CLEAN_CONFIDENCE) <= 0.1 + 1e-9, str(conf)),
        ("the rationale and contra-indicators cite no tone", bool(final) and not tone,
         f"found {tone}" if final else "no assessment found"),
    ]


def rescore_messy(row: dict, ev: list[dict]) -> list[tuple[str, bool | None, str]]:
    log_assessments = assessments_in(ev)
    reinv = [a for a in log_assessments if a.get("reassesses")]
    visits = []
    for r in ev:
        if r["event"] == "tool_result" and r["tool"] == "book_visit" and '"booked"' in r["result"]:
            vid = re.search(r'"id": "([^"]+)"', r["result"])
            aid = re.search(r'"assessment_id": "([^"]+)"', r["result"])
            visits.append({"id": vid and vid.group(1),
                           "engineer_note": {"assessment_id": aid and aid.group(1)}})
    issue = {"assessments": log_assessments, "visits": visits}
    bad = verify.reinvocation_outcomes_bad(reinv)
    superseded = verify.booked_on_superseded(issue)
    paths = sorted({r.get("path") for r in ev if r["event"] == "gate_check"
                    and r.get("outcome") == "allow"})
    if not visits:
        approvals = (True, "nothing was booked")
    elif row["code"] not in verify.REPLACE_CODES:
        approvals = (paths == ["repair"], f"code {row['code']}, booking paths {paths}")
    else:
        approvals = (None, "replacement outcome: gate_closed is not logged, not re-scorable")
    return carried_common(row) + [
        ("every re-assessment produced a new assessment or returned no_change",
         not bad, "; ".join(bad)),
        ("nothing was booked on a superseded assessment", not superseded, "; ".join(superseded)),
        ("the approvals match the final submitted code", *approvals),
    ]


def apply(row: dict, checks: list, note: dict) -> dict:
    scored = [c for c in checks if c[1] is not None]
    return {**row,
            "checks_passed": sum(1 for c in scored if c[1]),
            "checks_total": len(scored),
            "failed": [c[0] for c in scored if not c[1]],
            "not_exercised": [c[0] for c in checks if c[1] is None],
            "rescored": {**note, "from": "logs/decision_log.jsonl",
                         "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "checks": [list(c) for c in checks]}}


def main() -> None:
    log = [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]
    rows = verify._load_rows(JSONL)
    done = {(r["rescored"].get("source_row") or f"{r['scenario']} run {r['run']}")
            for r in rows if r.get("rescored")}
    issue_of = {sid: json.loads((ROOT / "scenarios" / f"{sid}.json").read_text())["issue"]["id"]
                for sid in ("frustrated_repair", "reassessment_cap")}
    out, added = [], []
    messy_run = sum(1 for r in rows if r["scenario"] == "messy_resident")
    for row in rows:
        key = f"{row['scenario']} run {row['run']}"
        if row["env_failure"] or key in done or row.get("rescored"):
            out.append(row)
            continue
        if row["scenario"] == "frustrated_repair":
            ev = window(log, row, issue_of["frustrated_repair"])
            out.append(apply(row, rescore_frustrated(row, ev), {
                "why": "brief-wording check replaced by outcome checks (spec: Known limitations)",
                "original": {k: row[k] for k in ("checks_passed", "checks_total", "failed")}}))
            print(f"rescored {key}: {out[-1]['checks_passed']}/{out[-1]['checks_total']}")
            continue
        out.append(row)
        if row["scenario"] == "reassessment_cap":
            ev = window(log, row, issue_of["reassessment_cap"])
            messy_run += 1
            new = apply({**row, "scenario": "messy_resident", "run": messy_run,
                         "cost_usd": 0.0, "reassessments": row["reassessments"]},
                        rescore_messy(row, ev), {
                "why": "a free-play run of the persona messy_resident now has",
                "source_row": key})
            added.append(new)
            print(f"added messy_resident run {messy_run} from {key}: "
                  f"{new['checks_passed']}/{new['checks_total']}")
    rows = out + added
    JSONL.write_text("".join(json.dumps(r, default=str) + "\n" for r in rows))
    verify.write_markdown(rows, JSONL.with_suffix(".md"))


if __name__ == "__main__":
    main()
