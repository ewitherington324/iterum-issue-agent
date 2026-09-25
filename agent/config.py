"""Runtime knobs for the prototype.

Every value here is one of the PRD's open questions (section 8) or an explicitly
provisional threshold. They are exposed as dials in the demo UI rather than buried
as constants, because "we have not decided this yet" is part of what the prototype
is meant to communicate.
"""

from dataclasses import dataclass, asdict, field


@dataclass
class Knobs:
    # --- PRD section 8: open questions -------------------------------------------------
    pm_cost_threshold_gbp: float = 400.0
    """Replacement cost above which the PM must approve by email. PLACEHOLDER - the PRD
    records this as needing a real number."""

    confidence_threshold: float = 0.7
    """Confidence at or above which a repair routes autonomously. The PRD's working value
    (section 8; Module 3 spec, "Constraints"), with the caveat that what underlies the percentage is
    itself undecided - see `confidence_basis` in the decision log."""

    max_slot_rejections: int = 3
    """After this many rejected slots the booking loop hands the thread to ops (PRD 5.1)."""

    engineer_channel: str = "whatsapp"
    """'whatsapp' or 'airtable' - PRD section 8 records this as undecided, so the demo
    simulates both."""

    # --- PRD section 4.1: LLM path vs rules-based fallback, for A/B ---------------------
    use_llm_for_triage_steps: bool = True
    use_llm_for_decision_analysis: bool = True

    # --- Loop safety --------------------------------------------------------------------
    max_turns_per_loop: int = 24
    max_budget_usd: float = 2.00
    """Hard cap per issue thread so a runaway loop stops rather than burning credit."""

    # --- Model --------------------------------------------------------------------------
    model: str = "claude-opus-5"
    effort: str = "medium"
    resident_sim_model: str = "claude-haiku-4-5"
    """A cheaper model plays the resident in auto-play mode. It is not part of the agent
    under test - it stands in for a human on WhatsApp."""

    def to_dict(self):
        return asdict(self)

    def update(self, patch: dict):
        for key, value in patch.items():
            if not hasattr(self, key):
                continue
            current = getattr(self, key)
            if isinstance(current, bool):
                value = bool(value)
            elif isinstance(current, float):
                value = float(value)
            elif isinstance(current, int):
                value = int(value)
            setattr(self, key, value)
        return self


KNOBS = Knobs()


# Recommendation vocabulary - Iterum's own A/B/C/D codes.
RECOMMENDATION_CODES = {
    "A": "Beyond economic repair - replace",
    "B": "Repairable - repair",
    "C": "Repairable but low future value - replace",
    "D": "In warranty - OEM handles",
}

REPLACE_CODES = {"A", "C"}

# Heuristic constants for the rules-based fallback (PRD 4.1). Sourced from Iterum's own
# decision-analysis brief: repair above ~70% of replacement is beyond economic repair,
# and an appliance older than 7 years has low remaining future value.
BER_COST_RATIO = 0.70
LOW_FUTURE_VALUE_AGE_YEARS = 7
