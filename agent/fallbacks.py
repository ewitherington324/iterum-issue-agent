"""Rules-based fallbacks for the two reasoning-heavy tools (PRD section 4.1).

The PRD specifies that both LLM calls have a deterministic fallback so the system can be
A/B'd against the LLM path: a lookup of common fault patterns per appliance type, and a
simple age/cost heuristic. The demo can switch between them live.

The heuristic constants are Iterum's own, from the decision-analysis brief: a repair
costing more than ~70% of replacement is beyond economic repair, and an appliance older
than 7 years has low remaining future value.
"""

from .config import BER_COST_RATIO, LOW_FUTURE_VALUE_AGE_YEARS

# --- Fault-pattern lookup ------------------------------------------------------------
# Every step must be resident-safe (PRD section 7): no electrical work, no disassembly,
# nothing needing tools beyond the obvious.

FAULT_PATTERNS: dict[str, list[str]] = {
    "dishwasher_not_draining": [
        "Open the door and look at the bottom of the machine. Twist the round filter anti-clockwise and lift it out.",
        "Rinse the filter under a running tap and clear any food debris from the recess it sits in.",
        "Refit the filter and twist clockwise until it locks.",
        "Check the waste hose behind the appliance is not kinked, as far as you can see without moving the machine.",
        "Run a short rinse cycle and tell me whether the water drains away.",
    ],
    "dishwasher_not_cleaning": [
        "Check the spray arms spin freely by turning them by hand.",
        "Look for blocked holes in the spray arms and clear them with a cocktail stick.",
        "Clean the filter at the base of the machine.",
        "Confirm rinse aid and salt are topped up if your model uses them.",
    ],
    "washer_dryer_not_draining": [
        "Find the small hatch at the bottom front of the machine and open it.",
        "Put a shallow tray and towel underneath, then unscrew the filter slowly to let water drain out.",
        "Clear any debris from the filter, then refit it firmly.",
        "Check the drain hose at the back is not kinked or pushed too far into the standpipe.",
        "Run a rinse-and-spin cycle and tell me what happens, including any noises.",
    ],
    "washer_dryer_leak": [
        "Run a short cycle and watch where the water appears from - front, underneath, or the back.",
        "Check the rubber door seal for trapped debris or visible tears.",
        "Check the detergent drawer is not overflowing and is not overfilled with detergent.",
        "Tell me exactly where the water appears and at what point in the cycle.",
    ],
    "washer_dryer_not_powering": [
        "Check the plug is pushed fully in and the socket switch is on.",
        "Try another appliance in the same socket to confirm the socket works.",
        "Check the door is fully closed - most machines will not start on an unlatched door.",
        "Check your consumer unit for a tripped breaker.",
    ],
    "oven_not_heating": [
        "Confirm the oven has power - does the light come on and the fan run?",
        "Check the oven is not left in a timer or delayed-start mode; set the clock to manual if there is a manual setting.",
        "Select a normal bake setting at 180C and wait ten minutes, then tell me whether it gets warm at all.",
        "Tell me whether the grill still works, and whether anything has changed about how it heats over the last few months.",
    ],
    "oven_door_issue": [
        "Open and close the door slowly and tell me where it stops sitting flush.",
        "Check nothing inside the oven - a shelf or tray - is stopping the door closing.",
        "Look at the hinges at the bottom of the door and tell me whether the door sags or feels loose.",
        "Do not attempt to remove the door.",
    ],
    "hob_single_zone_fault": [
        "Move a pan you know works on another zone onto the affected zone and tell me what happens.",
        "Tell me whether the affected zone beeps, shows anything on the display, or does nothing at all.",
        "Check the child lock or panel lock is not switched on.",
        "Switch the hob off at the wall for two minutes, switch it back on, and try the zone again.",
    ],
    "hob_error_code": [
        "Tell me exactly what the display shows, including any letter and number.",
        "Check the control panel is dry and clean - moisture across the touch controls causes false codes.",
        "Switch the hob off at the wall for two minutes, then back on, and tell me whether the code returns.",
    ],
    "fridge_not_cooling": [
        "Check the temperature setting has not been knocked - the fridge should be around 4C.",
        "Make sure the vents inside are not blocked by packed-in food.",
        "Check the door seal closes cleanly all the way round with no gaps.",
        "Tell me whether the freezer section is still working normally.",
    ],
    "hood_fan_not_working": [
        "Check the hood is switched on at its own isolator switch, usually on the wall nearby.",
        "Remove and clean the grease filters, which slide or clip out.",
        "Tell me whether the lights still work.",
    ],
}

GENERIC_STEPS = [
    "Check the appliance has power and its socket or isolator switch is on.",
    "Switch it off at the wall for two minutes and back on.",
    "Tell me exactly what the appliance does and does not do, including any noises, smells or display messages.",
]


def lookup_triage_steps(fault_slug: str, appliance_type: str) -> dict:
    steps = FAULT_PATTERNS.get(fault_slug)
    return {
        "source": "fault_pattern_lookup",
        "matched": steps is not None,
        "fault_slug": fault_slug,
        "steps": steps or GENERIC_STEPS,
        "note": ("Matched a known fault pattern." if steps else
                 f"No pattern held for {fault_slug!r}; returned generic safe checks."),
    }


# --- Age / cost heuristic -------------------------------------------------------------

def _confidence(margin: float) -> float:
    """Map a normalised distance-from-boundary onto a confidence.

    Square-rooted so that being comfortably inside a threshold reads as confident,
    while a call sitting right on a boundary reads as genuinely marginal. Capped below
    1.0 because a heuristic is never certain.
    """
    margin = max(0.0, min(margin, 1.0))
    return round(min(0.60 + 0.40 * (margin ** 0.5), 0.97), 2)


def assess_heuristic(age_years: float, repair_cost: float, replacement_cost: float,
                     in_warranty: bool) -> dict:
    """Deterministic repair-vs-replace call.

    Returns the A/B/C/D code plus a confidence derived from how far the inputs sit from
    the decision boundaries. That is a genuinely different quantity from a model's
    self-reported confidence, which is why the decision log records which basis was used.
    """

    if in_warranty:
        return {
            "source": "fallback",
            "code": "D", "confidence": 1.0,
            "confidence_basis": "deterministic: warranty status is a fact, not an estimate",
            "rationale": "Appliance is inside its manufacturer warranty, so the OEM handles it.",
            "evidence_used": ["Appliance is inside its manufacturer warranty"],
            "evidence_missing": [],
            "limits_applied": [],
            "contra_indicators": [],
            "determinative": False,
            "inputs": {"age_years": age_years, "in_warranty": True},
        }

    ratio = repair_cost / replacement_cost if replacement_cost else 0.0

    cost_says_replace = ratio > BER_COST_RATIO
    age_says_replace = age_years > LOW_FUTURE_VALUE_AGE_YEARS

    # How far past (or short of) each boundary we are, normalised.
    cost_over = (ratio - BER_COST_RATIO) / BER_COST_RATIO
    cost_under = (BER_COST_RATIO - ratio) / BER_COST_RATIO
    age_over = (age_years - LOW_FUTURE_VALUE_AGE_YEARS) / LOW_FUTURE_VALUE_AGE_YEARS
    age_under = (LOW_FUTURE_VALUE_AGE_YEARS - age_years) / LOW_FUTURE_VALUE_AGE_YEARS

    agreement = False

    if cost_says_replace and age_says_replace:
        # Two independent signals agree. Beyond-economic-repair is the stronger claim,
        # so it names the code, but confidence takes the better-supported margin.
        code, agreement = "A", True
        margin = max(cost_over, age_over)
        rationale = (f"Repair at GBP {repair_cost:.0f} is {ratio:.0%} of the GBP "
                     f"{replacement_cost:.0f} replacement cost, above the {BER_COST_RATIO:.0%} "
                     f"beyond-economic-repair threshold, and the appliance is {age_years:.1f} "
                     f"years old, past the {LOW_FUTURE_VALUE_AGE_YEARS}-year low-future-value "
                     "threshold. Both signals point to replacement.")
    elif cost_says_replace:
        code, margin = "A", cost_over
        rationale = (f"Repair at GBP {repair_cost:.0f} is {ratio:.0%} of the GBP "
                     f"{replacement_cost:.0f} replacement cost, above the {BER_COST_RATIO:.0%} "
                     "beyond-economic-repair threshold.")
    elif age_says_replace:
        code, margin = "C", age_over
        rationale = (f"Repair is economic at {ratio:.0%} of replacement, but the appliance is "
                     f"{age_years:.1f} years old, past the {LOW_FUTURE_VALUE_AGE_YEARS}-year "
                     "low-future-value threshold, so remaining value is limited.")
    else:
        code = "B"
        margin = min(cost_under, age_under)
        rationale = (f"Repair at GBP {repair_cost:.0f} is {ratio:.0%} of replacement and the "
                     f"appliance is {age_years:.1f} years old, inside both thresholds.")

    confidence = _confidence(margin)
    if agreement:
        confidence = round(min(confidence + 0.05, 0.97), 2)

    return {
        "source": "fallback",
        "code": code,
        "confidence": confidence,
        "confidence_basis": ("computed: distance from the cost-ratio and age decision "
                             "boundaries" + (", two signals in agreement" if agreement else "")),
        "rationale": rationale,
        "evidence_used": [
            f"{age_years:.1f} years old against the {LOW_FUTURE_VALUE_AGE_YEARS}-year line",
            f"Repair {ratio:.0%} of replacement against the {BER_COST_RATIO:.0%} boundary",
        ],
        # The rules-based path weighs age and cost only. Saying so is the honest version
        # of evidence_missing here - the fault itself was never looked at.
        "evidence_missing": [
            "Triage evidence and fault class - not considered by the rules-based path",
            "Comparable past jobs - not considered by the rules-based path",
        ],
        "limits_applied": [],
        "contra_indicators": [],
        "determinative": False,
        "inputs": {
            "age_years": age_years, "repair_cost": repair_cost,
            "replacement_cost": replacement_cost, "cost_ratio": round(ratio, 3),
            "ber_threshold": BER_COST_RATIO,
            "age_threshold_years": LOW_FUTURE_VALUE_AGE_YEARS,
            "cost_says_replace": cost_says_replace,
            "age_says_replace": age_says_replace,
        },
    }
