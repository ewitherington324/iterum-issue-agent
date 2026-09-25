"""The two LLM reasoning calls behind get_triage_steps and assess_repair_vs_replace.

PRD 4.3 lists both as "LLM reasoning call", each with a rules-based fallback. These are
separate, structured Claude API calls rather than something the agent free-forms, so the
output shape is guaranteed and the same contract holds on both the LLM and the fallback
path - which is what makes the A/B in the demo a fair comparison.
"""

import json
from typing import Literal

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field, model_validator

from .config import KNOBS
from .skills import DECISION_SKILL, TRIAGE_SKILL, fault_reference, load_skill

_client: AsyncAnthropic | None = None


def client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()
    return _client


class TriageSteps(BaseModel):
    steps: list[str] = Field(description="Ordered troubleshooting steps the resident can do "
                                         "themselves. Three to six steps.")
    diagnostic_question: str = Field(description="The single most useful thing to ask the "
                                                 "resident to report back after trying these.")
    safety_note: str = Field(description="Anything the resident must not do. Empty string if "
                                         "nothing applies.")


class ConfidenceLimit(BaseModel):
    limit: float = Field(ge=0.0, le=1.0, description="The ceiling your instructions set.")
    reason: str = Field(description="Which rule set it and what evidence was missing.")


class RepairVsReplace(BaseModel):
    code: Literal["A", "B", "C", "D"]
    confidence: float = Field(description="0 to 1.", ge=0.0, le=1.0)
    rationale: str
    key_factors: list[str] = Field(description="The specific facts that drove this call.")
    contra_indicators: list[str] = Field(
        default_factory=list,
        description="What argues against this code, put as strongly as you can. Required "
                    "unless the call was determinative. This is what makes an engineer "
                    "override readable later - it shows whether the model had already "
                    "seen the reason it was overruled.")
    evidence_gaps: list[str] = Field(
        default_factory=list,
        description="Facts that were missing and would have firmed up or changed the call.")
    determinative: bool = Field(
        default=False,
        description="True when the code came from the fixed-outcome list (e.g. cracked hob "
                    "glass) rather than from weighing the six factors.")
    limits_applied: list[ConfidenceLimit] = Field(
        default_factory=list,
        description="Every confidence ceiling from your instructions that applied to this "
                    "assessment because evidence was missing (for example, no photo of a "
                    "reported crack). Empty if none applied. Your confidence must not "
                    "exceed any limit listed here.")

    @model_validator(mode="after")
    def _contra_required_unless_determinative(self):
        """A weighed call must argue against itself.

        The requirement was previously only in the `contra_indicators` description, which
        makes it advisory: an empty list parsed cleanly and was indistinguishable from the
        model having genuinely found nothing to say. Since the field exists to make an
        engineer override readable later - did the model already see the reason it was
        overruled? - an empty list is a silent loss of exactly the signal being collected.

        Determinative calls are exempt by design: there the fault settles the code on its
        own and there is no counter-argument to make.

        Raising here surfaces as a fallback to the heuristic in assess_repair_vs_replace,
        with the reason on the reasoning_path event, rather than as a failed run.
        """
        if not self.determinative and not self.contra_indicators:
            raise ValueError(
                "contra_indicators must be non-empty when determinative is False - a "
                "weighed recommendation has to state what argues against it."
            )
        return self


# The two system prompts are the Module 2 skill files, read from skills/ at the repo
# root rather than discovered by the SDK. setting_sources=[] (runner.py invariant 1)
# disables on-disk skill discovery, so a SKILL.md in .claude/skills would load nothing
# and the call would quietly run unconstrained. See agent/skills.py.
#
# Loaded at import so a missing or malformed skill fails at startup, not mid-thread.
TRIAGE_SYSTEM = load_skill(TRIAGE_SKILL)
DECISION_SYSTEM = load_skill(DECISION_SKILL)


async def llm_triage_steps(appliance_type: str, brand: str, issue_description: str,
                           fault_slug: str) -> dict:
    # Level 3 of the skill: one fault section, chosen by slug, rather than all ten
    # reference files. `fault_reference` also carries the file preamble, which is where
    # the hob gas restrictions live - they apply across every section of that file.
    reference = fault_reference(appliance_type, fault_slug)
    content = (
        f"Appliance: {brand} {appliance_type}\n"
        f"Fault category: {fault_slug}\n"
        f"Reported issue: {issue_description}\n\n"
        "Produce resident-safe troubleshooting steps for this specific fault."
    )
    if reference:
        content += f"\n\n--- Fault pattern reference ---\n{reference}"
    else:
        content += (
            "\n\nThere is no fault pattern reference for this appliance type. Do not "
            "improvise beyond the universally safe checks your instructions permit - say "
            "so plainly and route to an engineer."
        )

    response = await client().messages.parse(
        model=KNOBS.model,
        max_tokens=4000,
        output_config={"effort": "low"},
        system=TRIAGE_SYSTEM,
        messages=[{"role": "user", "content": content}],
        output_format=TriageSteps,
    )
    parsed: TriageSteps = response.parsed_output
    return {
        "source": "llm_reasoning_call",
        "model": KNOBS.model,
        "skill": TRIAGE_SKILL,
        "fault_slug": fault_slug,
        "reference_matched": reference is not None,
        "steps": parsed.steps,
        "diagnostic_question": parsed.diagnostic_question,
        "safety_note": parsed.safety_note,
    }


async def llm_assess_repair_vs_replace(appliance: dict, age_years: float, warranty: dict,
                                       repair_cost: float, replacement_cost: float,
                                       issue_description: str, triage_findings: str,
                                       comparable_jobs: list[dict]) -> dict:
    ratio = repair_cost / replacement_cost if replacement_cost else 0.0
    response = await client().messages.parse(
        model=KNOBS.model,
        max_tokens=4000,
        output_config={"effort": "medium"},
        system=DECISION_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f"Appliance: {appliance['brand']} {appliance['model']} "
                f"({appliance['appliance_type']})\n"
                f"Installed: {appliance['installation_date']}  |  Age: {age_years} years\n"
                f"Warranty: {'IN WARRANTY until ' + warranty['expiry'] if warranty['in_warranty'] else 'out of warranty'}"
                f" ({warranty['oem']})\n"
                f"Estimated repair: GBP {repair_cost:.0f}\n"
                f"Estimated replacement: GBP {replacement_cost:.0f}\n"
                f"Repair as share of replacement: {ratio:.0%}\n"
                f"Confidence threshold currently set to {KNOBS.confidence_threshold:.2f}\n\n"
                f"Reported issue: {issue_description}\n\n"
                f"What triage established:\n{triage_findings}\n\n"
                f"Comparable past jobs:\n{json.dumps(comparable_jobs, indent=2)}"
            ),
        }],
        output_format=RepairVsReplace,
    )
    parsed: RepairVsReplace = response.parsed_output
    return assessment_from_model(parsed, inputs={
        "age_years": age_years, "repair_cost": repair_cost,
        "replacement_cost": replacement_cost, "cost_ratio": round(ratio, 3),
        "in_warranty": warranty["in_warranty"],
        "comparable_jobs_considered": len(comparable_jobs),
    })


def assessment_from_model(parsed: RepairVsReplace, inputs: dict) -> dict:
    """Map the model's structured output onto the spec's output table.

    Separate from the call so selftest can check the mapping without an API key.
    """
    return {
        "source": "subagent",
        "model": KNOBS.model,
        "skill": DECISION_SKILL,
        "code": parsed.code,
        "confidence": round(parsed.confidence, 2),
        "rationale": parsed.rationale,
        "evidence_used": parsed.key_factors,
        "evidence_missing": parsed.evidence_gaps,
        "limits_applied": [l.model_dump() for l in parsed.limits_applied],
        "contra_indicators": parsed.contra_indicators,
        "determinative": parsed.determinative,
        "confidence_basis": "self-reported by the model, not a computed quantity",
        "inputs": inputs,
    }
