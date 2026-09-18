"""The human gates (PRD section 3.4), enforced through the SDK permission callback.

The repair path is fully autonomous: its tools sit in `allowed_tools`, so they are
auto-approved and never reach this callback at all. `book_visit` is deliberately left OUT
of `allowed_tools`, which means every booking attempt falls through to here.

That placement is the whole design. The gate is on the *action*, not on the messaging -
so even if the agent never asked the engineer, or decided it had heard enough, a
replacement booking is still refused until the approvals actually exist in the record.
"""

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

from . import session
from .config import KNOBS
from .events import BUS
from .store import STORE
from .trace import log_decision, short_name


def _is_replacement(visit_type: str) -> bool:
    return "replac" in (visit_type or "").lower()


async def can_use_tool(tool_name, input_data, context):
    name = short_name(tool_name)

    try:
        s = session.current()
    except RuntimeError:
        return PermissionResultAllow(updated_input=input_data)

    # send_email carries its own gate inside the tool (it waits on the PM's reply), so
    # there is nothing to decide here.
    if name != "book_visit":
        return PermissionResultAllow(updated_input=input_data)

    visit_type = input_data.get("visit_type", "")
    issue = STORE.active_issue()
    cost = issue.get("estimated_replacement_cost") or 0.0
    over_threshold = cost > KNOBS.pm_cost_threshold_gbp

    # --- Repair path: fully autonomous (PRD 3.4) --------------------------------------
    if not _is_replacement(visit_type):
        BUS.publish("gate_check", tool=name, outcome="allow", path="repair",
                    detail="Repair path is fully autonomous - no human gate applies.")
        log_decision("gate_check", tool=name, path="repair", outcome="allow")
        return PermissionResultAllow(updated_input=input_data)

    # --- Replacement path: sequentially gated -----------------------------------------
    engineer = s.engineer_decision
    pm = s.pm_decision

    if engineer is None:
        reason = ("Blocked: this is a replacement booking and no engineer has confirmed the "
                  "recommendation yet. Call send_engineer_message first and wait for their "
                  "answer.")
        return _deny(name, "awaiting_engineer", reason, cost, over_threshold)

    if engineer.get("decision") == "override":
        reason = (f"Blocked: {engineer.get('engineer')} overrode the replacement "
                  f"recommendation ({engineer.get('note') or 'no note'}). Their assessment "
                  "takes precedence. Do not book a replacement - re-plan on their basis.")
        return _deny(name, "engineer_override", reason, cost, over_threshold)

    if over_threshold and pm is None:
        reason = (f"Blocked: the replacement is estimated at GBP {cost:.0f}, above the GBP "
                  f"{KNOBS.pm_cost_threshold_gbp:.0f} property manager approval threshold, and "
                  "no approval has been given. Email the property manager with send_email "
                  "and wait for their decision.")
        return _deny(name, "awaiting_pm", reason, cost, over_threshold)

    if over_threshold and pm.get("decision") != "approve":
        reason = (f"Blocked: the property manager rejected the replacement cost "
                  f"({pm.get('note') or 'no reason given'}). Do not book. Hand the thread to "
                  "ops with send_ops_message.")
        return _deny(name, "pm_rejected", reason, cost, over_threshold)

    detail = (f"Engineer confirmed; " +
              (f"PM approved GBP {cost:.0f} (over the GBP {KNOBS.pm_cost_threshold_gbp:.0f} "
               "threshold)." if over_threshold else
               f"GBP {cost:.0f} is under the GBP {KNOBS.pm_cost_threshold_gbp:.0f} threshold, "
               "so no PM approval was required."))
    BUS.publish("gate_check", tool=name, outcome="allow", path="replacement", detail=detail)
    log_decision("gate_check", tool=name, path="replacement", outcome="allow",
                 engineer=engineer, pm=pm, cost=cost, over_threshold=over_threshold)
    return PermissionResultAllow(updated_input=input_data)


def _deny(tool: str, rule: str, reason: str, cost: float, over_threshold: bool):
    BUS.publish("gate_check", tool=tool, outcome="deny", path="replacement",
                rule=rule, detail=reason)
    log_decision("gate_denied", tool=tool, rule=rule, reason=reason,
                 cost=cost, over_threshold=over_threshold)
    return PermissionResultDeny(message=reason, interrupt=False)
