"""The repair-vs-replace assessment log (docs/module3/SUBAGENT_SPEC.md, "Outputs").

Every assessment is recorded here with its own ID before the main agent sees it, and
submit_recommendation accepts nothing but that ID. That is what makes the assessment's
answer final: the code, confidence and rationale that reach booking are read from this
log, never typed by the main agent. In Module 2 the main agent restated them itself and
once turned a 0.6 into a 0.78, crossing the threshold with nothing noticing.

The log lives on the issue record (`issue["assessments"]`, oldest first) and every entry
is also written to decision_log.jsonl.
"""

from __future__ import annotations

from datetime import datetime

from . import trace
from .config import KNOBS, RECOMMENDATION_CODES
from .events import BUS

# The spec's output table. Both paths - subagent and fallback - must fill every field.
TABLE_FIELDS = (
    "assessment_id", "status", "code", "confidence", "rationale",
    "evidence_used", "evidence_missing", "limits_applied", "source",
    "contra_indicators", "determinative", "confidence_basis",
)

# reassessment_failed: a re-invocation whose subagent run failed. No fallback runs on
# re-invocation, so the previous assessment stands and nothing new can be submitted.
STATUSES = {"assessed", "no_change", "refused", "reassessment_failed"}
SOURCES = {"subagent", "fallback"}

# Spec, "When it's called": at most two re-invocations per issue; a third goes to ops.
MAX_REASSESSMENTS = 2


class AssessmentShapeError(ValueError):
    """An assessment is missing fields from the output table."""


def history(issue: dict) -> list[dict]:
    return issue.setdefault("assessments", [])


def latest(issue: dict) -> dict | None:
    log = history(issue)
    return log[-1] if log else None


def find(issue: dict, assessment_id: str) -> dict | None:
    return next((a for a in history(issue) if a["assessment_id"] == assessment_id), None)


def latest_assessed(issue: dict) -> dict | None:
    """The newest assessment that carries a recommendation. A no_change does not replace it."""
    return next((a for a in reversed(history(issue)) if a["status"] == "assessed"), None)


def reassessment_count(issue: dict) -> int:
    """Re-invocations that reached the subagent: assessed, no_change or reassessment_failed.

    Input the filter rejected is never recorded, so it cannot count.
    """
    return sum(1 for a in history(issue) if a.get("reassesses"))


def meets_threshold(assessment: dict) -> bool:
    """Whether a submitted recommendation may route as confident, at the current threshold.

    A fallback result never does, whatever its computed confidence (spec: "Fallback"): a
    lookup table cannot judge its own certainty the way the subagent can.
    """
    return (assessment.get("status") == "assessed"
            and assessment.get("source") != "fallback"
            and assessment["confidence"] >= KNOBS.confidence_threshold)


FALLBACK_BELOW_THRESHOLD = ("From the backup rules (rules-based fallback), so treated as below "
                            "the threshold whatever its computed confidence.")


def unassessed_information(issue: dict) -> list[dict]:
    """New information from failed re-invocations since the submitted assessment.

    The subagent never judged it, so the engineer needs to see it as it was said.
    """
    log = history(issue)
    submitted = issue.get("recommendation_assessment_id")
    idx = next((i for i, a in enumerate(log) if a["assessment_id"] == submitted), -1)
    return [{"assessment_id": a["assessment_id"], "failure": a.get("failure_reason"),
             "new_information": list(a["brief"].get("new_information") or [])}
            for a in log[idx + 1:] if a["status"] == "reassessment_failed"]


def summary(assessment: dict) -> dict:
    """What the engineer is told about a recommendation - built by code, never the main agent."""
    fallback = assessment["source"] == "fallback"
    meets = meets_threshold(assessment)
    if fallback:
        headline = ("UNCERTAIN - from the backup rules, not the subagent. " +
                    FALLBACK_BELOW_THRESHOLD)
    elif not meets:
        headline = (f"UNCERTAIN - confidence {assessment['confidence']:.2f} is below the "
                    f"{KNOBS.confidence_threshold:.2f} threshold.")
    else:
        headline = (f"Confidence {assessment['confidence']:.2f} meets the "
                    f"{KNOBS.confidence_threshold:.2f} threshold.")
    return {
        "headline": headline,
        "assessment_id": assessment["assessment_id"],
        "source": assessment["source"],
        "from_backup_rules": fallback,
        "code": assessment["code"],
        "code_meaning": RECOMMENDATION_CODES.get(assessment["code"], "unknown"),
        "confidence": assessment["confidence"],
        "meets_threshold": meets,
        "determinative": assessment.get("determinative", False),
        "rationale": assessment["rationale"],
        "evidence_missing": list(assessment.get("evidence_missing") or []),
        "limits_applied": list(assessment.get("limits_applied") or []),
        "provisional": "Provisional routing, not a diagnosis.",
    }


def engineer_note(issue: dict) -> dict | None:
    """The note book_visit attaches to a visit: the submitted assessment's summary plus any
    new information a failed re-invocation could not assess."""
    submitted = find(issue, issue.get("recommendation_assessment_id") or "")
    if submitted is None:
        return None
    note = summary(submitted)
    unassessed = unassessed_information(issue)
    if unassessed:
        note["not_assessed"] = {
            "detail": ("The resident said this after the assessment. The re-assessment could "
                       "not be run, so it has not been assessed - check it on site."),
            # A later failed attempt carries the earlier one's quotes forward, so dedupe.
            "new_information": list(dict.fromkeys(q for u in unassessed
                                                  for q in u["new_information"])),
            "attempts": [u["assessment_id"] for u in unassessed],
        }
    return note


def escalate(issue: dict, attempted: dict) -> dict:
    """Record that the cap was reached. The ops request itself is raised by the caller."""
    record = {
        "reason": (f"The resident gave new information a third time; the assessment has "
                   f"already been revisited {MAX_REASSESSMENTS} times, which is the limit."),
        "attempted": attempted,
        "history": [dict(a) for a in history(issue)],
        "at": datetime.utcnow().isoformat() + "Z",
    }
    issue["assessment_escalated"] = record
    trace.log_decision("reassessment_cap_reached", attempted=attempted,
                       assessment_ids=[a["assessment_id"] for a in record["history"]])
    return record


def enforce_reported_limits(assessment: dict) -> dict | None:
    """Hold confidence at or below every limit the assessment itself reported.

    Deliberately narrow. Whether a limit *should* have applied is the skill's judgement
    and stays there; this only makes sure a limit the assessment did apply is actually
    respected in the number. Returns the cap record if one was needed, else None.
    """
    limits = [float(l["limit"]) for l in assessment.get("limits_applied") or []
              if isinstance(l, dict) and isinstance(l.get("limit"), (int, float))]
    if not limits:
        return None
    ceiling = min(limits)
    reported = float(assessment["confidence"])
    if reported <= ceiling:
        return None
    cap = {"reported": reported, "capped_to": ceiling,
           "reason": "confidence exceeded a limit the assessment itself reported in "
                     "limits_applied; held at the lowest reported limit"}
    assessment["confidence"] = ceiling
    assessment["confidence_capped"] = cap
    return cap


def record(issue: dict, appliance_id: str, result: dict,
           status: str = "assessed") -> dict:
    """Give an assessment its ID, apply the reported-limit cap, log it and return it."""
    missing = [f for f in TABLE_FIELDS if f not in result and f not in ("assessment_id", "status")]
    if missing:
        raise AssessmentShapeError(f"Assessment is missing {missing}")
    if status not in STATUSES:
        raise AssessmentShapeError(f"Unknown status {status!r}")
    if result["source"] not in SOURCES:
        raise AssessmentShapeError(f"Unknown source {result['source']!r}")

    log = history(issue)
    assessment = {
        "assessment_id": f"{issue['id']}-RVR-{len(log) + 1}",
        "issue_id": issue["id"],
        "appliance_id": appliance_id,
        "status": status,
        "created_at": datetime.utcnow().isoformat() + "Z",
        **result,
    }
    assessment["limits_applied"] = list(assessment["limits_applied"] or [])

    assessment["confidence_threshold"] = KNOBS.confidence_threshold
    if status == "assessed":
        cap = enforce_reported_limits(assessment)
        assessment["code_meaning"] = RECOMMENDATION_CODES.get(assessment["code"], "unknown")
        assessment["meets_threshold"] = meets_threshold(assessment)
        if assessment["source"] == "fallback":
            assessment["threshold_note"] = FALLBACK_BELOW_THRESHOLD
    else:
        # A refusal, a no-change or a failed re-assessment carries no recommendation of its own.
        cap = None
        assessment["code_meaning"] = None
        assessment["meets_threshold"] = False

    log.append(assessment)
    trace.log_decision("assessment_recorded", assessment=assessment)
    if cap:
        detail = (f"{assessment['assessment_id']}: confidence {cap['reported']:.2f} is above "
                  f"the {cap['capped_to']:.2f} limit the assessment reported, so it was "
                  f"held at {cap['capped_to']:.2f}.")
        BUS.publish("guardrail", rule="confidence_limit", detail=detail,
                    tool="assess_repair_vs_replace")
        trace.log_decision("confidence_capped", assessment_id=assessment["assessment_id"], **cap)
    return assessment
