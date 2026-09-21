"""Verifies everything that does not need an API key.

The gates, the guardrails and the slot limit are the parts of this prototype that must be
true rather than merely prompted for, so they are worth checking directly rather than only
observing them in a demo run.

    .venv/bin/python selftest.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent import gates, session, trace  # noqa: E402
from agent.config import KNOBS  # noqa: E402
from agent.fallbacks import assess_heuristic  # noqa: E402
from agent.runner import build_options  # noqa: E402
from agent.store import STORE  # noqa: E402
from agent.tools import ALL_TOOLS, AUTONOMOUS_TOOLS, qualified  # noqa: E402

# This file drives the hooks and gates directly rather than through a scenario run, so its
# log entries must be distinguishable from live ones. Set before any check runs.
trace.RUN_SOURCE = "selftest"

PASS, FAIL = "  PASS", "  FAIL"
results = []


def check(name, condition, detail=""):
    results.append(bool(condition))
    print(f"{PASS if condition else FAIL}  {name}" + (f"\n          {detail}" if detail and not condition else ""))


def section(title):
    print(f"\n\033[1m{title}\033[0m")


async def pre_hook(tool, tool_input=None):
    return await trace.pre_tool_use(
        {"tool_name": tool, "tool_input": tool_input or {}}, "tu_test", {"signal": None})


def denied(hook_result):
    hso = (hook_result or {}).get("hookSpecificOutput", {})
    return hso.get("permissionDecision") == "deny", hso.get("permissionDecisionReason", "")


async def main():
    # ---------------------------------------------------------------- tool surface
    section("Tool surface")
    opts = build_options()
    check("tools=[] removes every built-in from Claude's context", opts.tools == [])
    check("setting_sources=[] so no user/project settings leak in", opts.setting_sources == [])
    check("permission_mode is 'default' so gated calls reach can_use_tool",
          opts.permission_mode == "default")
    check("18 tools registered (15 PRD tools + 3 loop exits)", len(ALL_TOOLS) == 18,
          f"got {len(ALL_TOOLS)}")
    check("book_visit is NOT auto-approved (it must reach the gate)",
          qualified("book_visit") not in AUTONOMOUS_TOOLS)
    check("send_resident_message IS auto-approved (repair path is autonomous)",
          qualified("send_resident_message") in AUTONOMOUS_TOOLS)

    # ---------------------------------------------------------------- scenarios load
    section("Scenarios")
    ids = sorted(p.stem for p in Path("scenarios").glob("*.json"))
    check("all eight scenarios present", len(ids) == 8, str(ids))
    orders = [json.loads(Path(f"scenarios/{i}.json").read_text())["order"] for i in ids]
    check("scenario orders are unique", len(set(orders)) == len(orders), str(sorted(orders)))
    for sid in ids:
        try:
            STORE.load_scenario(sid)
            issue = STORE.active_issue()
            app = STORE.appliance(issue["appliance_id"])
            check(f"{sid} loads with a valid appliance", app is not None)
        except Exception as exc:  # noqa: BLE001
            check(f"{sid} loads", False, str(exc))

    # ---------------------------------------------------------------- hook: tool surface
    section("PreToolUse hook - tool surface guardrail")
    STORE.load_scenario("clear_repair")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/clear_repair.json").read_text())))
    d, reason = denied(await pre_hook("Bash", {"command": "ls"}))
    check("a built-in tool (Bash) is denied by the hook", d, reason)
    d, _ = denied(await pre_hook(qualified("get_appliance"), {"appliance_id": "app_002"}))
    check("an Iterum tool passes the hook", not d)

    # ---------------------------------------------------------------- hook: warranty
    section("PreToolUse hook - warranty branch (PRD 5.2)")
    STORE.load_scenario("in_warranty")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/in_warranty.json").read_text())))
    d, _ = denied(await pre_hook(qualified("book_visit"), {}))
    check("before the warranty check, booking is not yet blocked", not d)
    s.warranty_blocked = True  # what check_warranty sets on an in-warranty appliance
    for tool in ["book_visit", "confirm_visit", "find_available_technician", "send_email"]:
        d, reason = denied(await pre_hook(qualified(tool), {}))
        check(f"in warranty: {tool} is blocked", d, reason)
    d, _ = denied(await pre_hook(qualified("send_ops_message"), {}))
    check("in warranty: send_ops_message still allowed (the handoff must work)", not d)

    # ---------------------------------------------------------------- gate: repair path
    section("can_use_tool - repair path is fully autonomous")
    STORE.load_scenario("clear_repair")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/clear_repair.json").read_text())))
    r = await gates.can_use_tool(qualified("book_visit"),
                                 {"visit_type": "repair", "slot_date": "2026-09-16"}, None)
    check("repair booking allowed with no human in the loop", r.behavior == "allow")

    # ---------------------------------------------------------------- gate: replacement
    section("can_use_tool - replacement path is sequentially gated (PRD 3.4)")
    STORE.load_scenario("likely_replacement")
    scn = json.loads(Path("scenarios/likely_replacement.json").read_text())
    cost = STORE.active_issue()["estimated_replacement_cost"]
    check(f"replacement cost £{cost:.0f} is over the £{KNOBS.pm_cost_threshold_gbp:.0f} threshold",
          cost > KNOBS.pm_cost_threshold_gbp)

    s = session.set_current(session.IssueSession(scn))
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "replacement"}, None)
    check("blocked with no engineer confirmation", r.behavior == "deny")
    check("  ...and the refusal says what is missing", "engineer" in r.message.lower())

    s.engineer_decision = {"decision": "override", "note": "Element only, worth repairing",
                           "engineer": "Tomas Novak"}
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "replacement"}, None)
    check("blocked when the engineer OVERRODE the recommendation", r.behavior == "deny")

    s.engineer_decision = {"decision": "confirm", "note": "", "engineer": "Tomas Novak"}
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "replacement"}, None)
    check("still blocked with engineer confirmed but no PM approval", r.behavior == "deny")
    check("  ...and the refusal names the threshold", "threshold" in r.message.lower())

    s.pm_decision = {"decision": "reject", "note": "Get a second quote"}
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "replacement"}, None)
    check("blocked when the PM REJECTED the cost", r.behavior == "deny")

    s.pm_decision = {"decision": "approve", "note": ""}
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "replacement"}, None)
    check("allowed once engineer confirmed AND PM approved", r.behavior == "allow")

    # threshold knob actually bites
    original = KNOBS.pm_cost_threshold_gbp
    KNOBS.pm_cost_threshold_gbp = 1000.0
    s2 = session.set_current(session.IssueSession(scn))
    s2.engineer_decision = {"decision": "confirm", "note": "", "engineer": "Tomas Novak"}
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "replacement"}, None)
    check("raising the threshold above the cost removes the PM gate", r.behavior == "allow")
    KNOBS.pm_cost_threshold_gbp = original

    # ---------------------------------------------------------------- slot limit
    section("Slot rejection limit (PRD 5.1)")
    from agent.tools import find_available_technician
    STORE.load_scenario("resident_rejects")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/resident_rejects.json").read_text())))
    handler = find_available_technician.handler
    slots = []
    for attempt in range(KNOBS.max_slot_rejections + 1):
        out = await handler({"property_id": "prop_canalside",
                             "earliest_date": STORE.today.isoformat()})
        text = out["content"][0]["text"]
        if out.get("is_error"):
            check(f"attempt {attempt + 1} refused after {KNOBS.max_slot_rejections} rejections",
                  attempt == KNOBS.max_slot_rejections, text[:120])
            check("  ...and the refusal tells the agent to hand to ops",
                  "ops" in text.lower())
            break
        slots.append(json.loads(text)["slot_date"])
    else:
        check(f"loop stops after {KNOBS.max_slot_rejections} rejections", False,
              "it kept proposing")
    check("each proposed slot is distinct", len(slots) == len(set(slots)), str(slots))
    check("slots fall on the engineer's service days (Tue/Thu for prop_canalside)",
          all(__import__("datetime").date.fromisoformat(d).weekday() in (1, 3) for d in slots),
          str(slots))

    # ---------------------------------------------------------------- heuristic
    section("Rules-based fallback (PRD 4.1)")
    expectations = {
        "self_fix": "B", "clear_repair": "B", "likely_replacement": "A",
        "in_warranty": "D", "parts_delayed": "B", "resident_rejects": "B",
    }
    for sid, expected in expectations.items():
        STORE.load_scenario(sid)
        issue = STORE.active_issue()
        app = STORE.appliance(issue["appliance_id"])
        res = assess_heuristic(STORE.appliance_age_years(app),
                               issue["estimated_repair_cost"],
                               issue["estimated_replacement_cost"],
                               STORE.warranty(app)["in_warranty"])
        check(f"{sid}: heuristic gives {expected} (conf {res['confidence']})",
              res["code"] == expected, f"got {res['code']}")

    # ---------------------------------------------------------------- summary
    total, passed = len(results), sum(results)
    print(f"\n\033[1m{passed}/{total} checks passed\033[0m")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
