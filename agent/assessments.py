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

STATUSES = {"assessed", "no_change", "refused"}
SOURCES = {"subagent", "fallback"}


class AssessmentShapeError(ValueError):
    """An assessment is missing fields from the output table."""


def history(issue: dict) -> list[dict]:
    return issue.setdefault("assessments", [])


def latest(issue: dict) -> dict | None:
    log = history(issue)
    return log[-1] if log else None


def find(issue: dict, assessment_id: str) -> dict | None:
    return next((a for a in history(issue) if a["assessment_id"] == assessment_id), None)


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
        assessment["meets_threshold"] = assessment["confidence"] >= KNOBS.confidence_threshold
    else:
        # A refusal or a no-change carries no recommendation of its own.
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
