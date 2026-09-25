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

from agent import assessments, gates, prompts, session, trace  # noqa: E402
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


def give_recommendation(code, source="subagent"):
    """Put a submitted recommendation on the active issue, as submit_recommendation would.

    The gate reads the submitted code (Module 3 step 3), so gate checks need one.
    """
    issue = STORE.active_issue()
    a = assessments.record(issue, issue["appliance_id"], {
        "source": source, "code": code, "confidence": 0.8, "rationale": "test",
        "evidence_used": [], "evidence_missing": [], "limits_applied": [],
        "contra_indicators": ["c"], "determinative": False, "confidence_basis": "test"})
    issue["recommendation"] = code
    issue["confidence"] = a["confidence"]
    issue["recommendation_assessment_id"] = a["assessment_id"]
    return a


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
    check("18 tools registered (14 PRD tools + reassess + 3 loop exits; "
          "search_similar_issues is the subagent's)", len(ALL_TOOLS) == 18,
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
    give_recommendation("B")
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
    give_recommendation("A")
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

    # ---------------------------------------------------------------- Module 3: output table
    section("Repair-vs-replace output table (Module 3)")
    from agent.reasoning import RepairVsReplace, assessment_from_model
    parsed = RepairVsReplace(code="A", confidence=0.6, rationale="r", key_factors=["k"],
                             evidence_gaps=["No photo"], determinative=True,
                             limits_applied=[{"limit": 0.6, "reason": "no photo"}])
    mapped = assessment_from_model(parsed, inputs={})
    table = [f for f in assessments.TABLE_FIELDS if f not in ("assessment_id", "status")]
    check("subagent output fills every field of the table",
          all(f in mapped for f in table), str([f for f in table if f not in mapped]))
    check("  ...with source 'subagent'", mapped["source"] == "subagent", mapped["source"])
    STORE.load_scenario("clear_repair")
    issue = STORE.active_issue()
    app = STORE.appliance(issue["appliance_id"])
    fb = assess_heuristic(STORE.appliance_age_years(app), issue["estimated_repair_cost"],
                          issue["estimated_replacement_cost"], False)
    check("fallback output fills every field of the table",
          all(f in fb for f in table), str([f for f in table if f not in fb]))
    check("  ...with source 'fallback'", fb["source"] == "fallback", fb["source"])

    # ---------------------------------------------------------------- Module 3: reported-limit cap
    section("Confidence never exceeds a limit the assessment reported (Module 3)")
    STORE.load_scenario("cracked_hob")
    issue = STORE.active_issue()
    over = dict(mapped, confidence=0.78,
                limits_applied=[{"limit": 0.6, "reason": "no photo"},
                                {"limit": 0.5, "reason": "no triage evidence"}])
    a = assessments.record(issue, issue["appliance_id"], over)
    check("0.78 with reported limits 0.6 and 0.5 is held at the lowest, 0.5",
          a["confidence"] == 0.5, f"confidence={a['confidence']}")
    check("  ...and the cap is recorded on the assessment",
          (a.get("confidence_capped") or {}).get("reported") == 0.78, str(a.get("confidence_capped")))
    check("  ...and meets_threshold uses the capped value", a["meets_threshold"] is False)
    under = assessments.record(issue, issue["appliance_id"], dict(mapped, confidence=0.55))
    check("confidence under its reported limit is left alone",
          under["confidence"] == 0.55 and "confidence_capped" not in under)
    none = assessments.record(issue, issue["appliance_id"],
                              dict(mapped, confidence=0.9, limits_applied=[]))
    check("no reported limit means no cap - the code does not invent one",
          none["confidence"] == 0.9 and "confidence_capped" not in none)

    # ---------------------------------------------------------------- Module 3: submit by ID
    section("submit_recommendation takes an assessment ID only (Module 3)")
    import jsonschema
    from agent.tools import assess_repair_vs_replace, submit_recommendation
    schema = submit_recommendation.input_schema
    check("schema has assessment_id as its only property",
          list(schema.get("properties", {})) == ["assessment_id"], str(schema))
    try:
        jsonschema.validate({"assessment_id": "x", "code": "B", "confidence": 0.9}, schema)
        check("schema rejects a code or confidence alongside the ID", False, "validated")
    except jsonschema.ValidationError:
        check("schema rejects a code or confidence alongside the ID", True)

    STORE.load_scenario("clear_repair")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/clear_repair.json").read_text())))
    s.enter_loop(session.DECISION)
    issue = STORE.active_issue()
    STORE.append_conversation("resident", "It hums when it should pump out, then nothing.")
    fault_args = {"issue_id": issue["id"], "appliance_id": issue["appliance_id"],
                  "troubleshooting": [{"step": "Cleaned filter", "result": "No change"}],
                  "resident_symptoms": ["It hums when it should pump out"],
                  "known_gaps": []}
    KNOBS.use_llm_for_decision_analysis = False  # no API key here: the fallback path
    out = await assess_repair_vs_replace.handler(fault_args)
    first = json.loads(out["content"][0]["text"])
    check("assess_repair_vs_replace returns an assessment_id",
          first.get("assessment_id") == f"{issue['id']}-RVR-1", str(first.get("assessment_id")))
    check("  ...and adds it to the issue's assessment log",
          assessments.latest(issue)["assessment_id"] == first["assessment_id"])
    out = await assess_repair_vs_replace.handler(fault_args)
    check("a second plain assess_repair_vs_replace call is refused - reassess is the only way "
          "back in", out.get("is_error") and len(assessments.history(issue)) == 1
          and "reassess_repair_vs_replace" in out["content"][0]["text"])
    STORE.append_conversation("resident", "Now there's water left in the drum after every cycle.")
    from agent.tools import reassess_repair_vs_replace
    out = await reassess_repair_vs_replace.handler({
        "issue_id": issue["id"], "appliance_id": issue["appliance_id"],
        "previous_assessment_id": first["assessment_id"],
        "new_information": ["water left in the drum after every cycle"]})
    second = json.loads(out["content"][0]["text"])
    KNOBS.use_llm_for_decision_analysis = True

    sub = submit_recommendation.handler
    r = await sub({"assessment_id": second["assessment_id"], "code": "B", "confidence": 0.99})
    check("handler refuses a code or confidence passed with the ID", r.get("is_error"))
    r = await sub({"assessment_id": "ISS-NOPE-RVR-9"})
    check("handler refuses an unknown assessment ID", r.get("is_error"))
    r = await sub({"assessment_id": first["assessment_id"]})
    check("handler refuses an assessment that is not the latest", r.get("is_error"),
          r["content"][0]["text"][:120])
    check("nothing was submitted by the refused calls", session.DECISION not in s.exits)
    r = await sub({"assessment_id": second["assessment_id"]})
    exit_ = s.exits.get(session.DECISION, {})
    check("the latest assessment is accepted", not r.get("is_error"), r["content"][0]["text"][:120])
    check("submitted code and confidence equal the assessment exactly",
          exit_.get("code") == second["code"] and exit_.get("confidence") == second["confidence"]
          and issue["recommendation"] == second["code"]
          and issue["confidence"] == second["confidence"],
          f"exit={exit_.get('code')}/{exit_.get('confidence')} "
          f"assessed={second['code']}/{second['confidence']}")
    check("  ...and the rationale is the assessment's, not restated",
          exit_.get("rationale") == second["rationale"])


    # ---------------------------------------------------------------- Module 3 step 2: input filter
    section("Subagent input is filtered: symptoms verbatim, no grievances or scheduling (Module 3)")
    from agent import subagent
    schema = assess_repair_vs_replace.input_schema
    check("assess_repair_vs_replace takes only the spec's fault fields",
          sorted(schema["properties"]) == sorted(subagent.INPUT_FIELDS)
          and schema.get("additionalProperties") is False, str(sorted(schema["properties"])))
    check("  ...with no free-text findings, warranty or cost field for the main agent to fill",
          not {"triage_findings", "findings", "issue_description", "warranty",
               "in_warranty", "repair_cost", "code", "confidence"} & set(schema["properties"]))

    STORE.load_scenario("clear_repair")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/clear_repair.json").read_text())))
    s.enter_loop(session.DECISION)
    issue = STORE.active_issue()
    said = [
        "There’s a low humming noise when it should pump out, then nothing happens.",
        "Honestly the last engineer was useless and I'm fed up with this.",
        "I can only do Tuesdays after 3pm because of work.",
        "I replaced the filter and it still leaks",
        "It's knackered, it needs replacing.",
    ]
    for line in said:
        STORE.append_conversation("resident", line)
    log = STORE.data["conversation_log"]
    good = {"issue_id": issue["id"], "appliance_id": issue["appliance_id"],
            "troubleshooting": [{"step": "Cleaned the filter", "result": "Filter was clean, "
                                 "no change"}],
            "resident_symptoms": ["There's a low humming noise when it should pump out, then "
                                  "nothing happens."],
            "known_gaps": ["No photo"]}
    probs = subagent.check_input(issue, good, log)
    check("a clean, verbatim input is accepted (curly vs straight apostrophe ignored)",
          not probs, str(probs))
    probs = subagent.check_input(issue, dict(good, resident_symptoms=[
        "The pump makes a humming sound and does not drain"]), log)
    check("a paraphrased quote is rejected", any("word for word" in p for p in probs), str(probs))
    probs = subagent.check_input(issue, dict(good, resident_symptoms=[
        "low humming noise when it should pump out"]), log)
    check("a shortened verbatim quote is accepted", not probs, str(probs))
    probs = subagent.check_input(issue, dict(good, resident_symptoms=[
        "I replaced the filter and it still leaks"]), log)
    check('"I replaced the filter and it still leaks" passes (evidence, not a verdict)',
          not probs, str(probs))
    for phrase in ["it needs replacing", "just replace it", "it's beyond repair",
                   "not worth fixing", "a write-off", "get a new one"]:
        check(f"verdict phrase caught: {phrase!r}", subagent.verdicts_in(phrase), phrase)
    check("there is no summary field for the main agent's interpretation",
          not {"confirmed_fault", "summary", "diagnosis"} & set(schema["properties"]))
    probs = subagent.check_input(issue, dict(good, confirmed_fault=
        "Presentation is consistent with a thermal-shock crack through the glass."), log)
    check("  ...and one passed anyway is rejected", any("Unexpected" in p for p in probs),
          str(probs))
    probs = subagent.check_input(issue, dict(good, troubleshooting=[
        {"step": "Cleaned the filter", "result": "No change, so it is not worth repairing"}]), log)
    check("the main agent's lean in a troubleshooting result is rejected",
          any("verdict" in p for p in probs), str(probs))
    probs = subagent.check_input(issue, dict(good, resident_symptoms=["it needs replacing"]), log)
    check("a resident's verdict is rejected even though it is verbatim",
          any("verdict" in p for p in probs), str(probs))
    probs = subagent.check_input(issue, dict(good, appliance_id="app_001"), log)
    check("another appliance's id is rejected", any("appliance_id" in p for p in probs), str(probs))
    probs = subagent.check_input(issue, dict(good, in_warranty=False), log)
    check("an extra field (e.g. warranty from the main agent) is rejected",
          any("Unexpected" in p for p in probs), str(probs))

    appliance = STORE.appliance(issue["appliance_id"])
    brief = subagent.build_brief(issue, appliance, good)
    prompt = subagent.render_brief(brief)
    check("the subagent's input carries the verbatim symptom",
          "low humming noise when it should pump out" in prompt)
    leaked = [w for w in ("useless", "fed up", "Tuesdays", "3pm", "knackered")
              if w.lower() in prompt.lower()]
    check("grievances and scheduling in the conversation never reach the subagent",
          not leaked, str(leaked))
    check("warranty and costs come from the store, not the main agent",
          brief["in_warranty"] is STORE.warranty(appliance)["in_warranty"]
          and brief["estimated_repair_cost"] == issue["estimated_repair_cost"]
          and brief["estimated_replacement_cost"] == issue["estimated_replacement_cost"]
          and "GBP 165" in prompt and "GBP 549" in prompt)
    system = subagent.system_prompt(appliance["appliance_type"], brief["fault_slug"])
    from agent.skills import DECISION_SKILL as _DS, load_skill as _ls
    check("the subagent's instructions are the skill plus the matching fault reference",
          _ls(_DS) in system and "Fault pattern reference" in system
          and "washer_dryer_not_draining" in system)
    check("  ...and say that a resident's tone is not evidence",
          "tone is not evidence" in system)

    # A stand-in for the model, so the success path and the fallback path run with no key.
    real_run = subagent.run
    calls = []
    from agent.reasoning import RepairVsReplace as _RVR, assessment_from_model as _afm

    async def fake_run(b):
        calls.append(b)
        return _afm(_RVR(code="B", confidence=0.82, rationale="Pump fault, repairable.",
                         key_factors=["k"], contra_indicators=["c"]), inputs={})

    subagent.run = fake_run
    KNOBS.use_llm_for_decision_analysis = True
    out = await assess_repair_vs_replace.handler(good)
    a = json.loads(out["content"][0]["text"])
    check("the handler runs the subagent on the filtered brief",
          len(calls) == 1 and calls[0] == brief, str(calls[:1]))
    check("  ...and logs its answer with source 'subagent' and the brief attached",
          a.get("source") == "subagent" and a.get("brief") == brief and a.get("code") == "B")

    async def broken_run(b):
        raise subagent.SubagentError("no submission")

    subagent.run = broken_run
    issue["assessments"] = []  # a fresh first assessment; a second call would be refused
    out = await assess_repair_vs_replace.handler(good)
    a = json.loads(out["content"][0]["text"])
    check("if the subagent fails, the fallback answers instead", a.get("source") == "fallback",
          str(a.get("source")))
    subagent.run = fake_run
    calls.clear()
    issue["assessments"] = []
    out = await assess_repair_vs_replace.handler(dict(good, resident_symptoms=["made up words here"]))
    check("rejected input returns an error and never reaches the subagent",
          out.get("is_error") and not calls)

    # ---------------------------------------------------------------- Module 3 step 2: guard
    section("Precondition guard: refuses in warranty or with no fault reference (Module 3)")
    STORE.load_scenario("in_warranty")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/in_warranty.json").read_text())))
    s.enter_loop(session.DECISION)
    issue = STORE.active_issue()
    STORE.append_conversation("resident", "The fridge is warm and the light is off.")
    wargs = {"issue_id": issue["id"], "appliance_id": issue["appliance_id"],
             "troubleshooting": [],
             "resident_symptoms": ["The fridge is warm"], "known_gaps": []}
    check("s.warranty_blocked is not set - the guard must not depend on check_warranty",
          not s.warranty_blocked)
    out = await assess_repair_vs_replace.handler(wargs)
    a = json.loads(out["content"][0]["text"])
    check("in warranty: the assessment is refused", a.get("status") == "refused", str(a.get("status")))
    check("  ...and says why", "warranty" in (a.get("refusal_reason") or "").lower())
    check("  ...without running the subagent", not calls)
    check("  ...and carries no code or confidence", a.get("code") is None
          and a.get("confidence") is None and a.get("meets_threshold") is False)
    r = await submit_recommendation.handler({"assessment_id": a["assessment_id"]})
    check("  ...so there is nothing to submit", r.get("is_error"))

    STORE.load_scenario("clear_repair")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/clear_repair.json").read_text())))
    issue = STORE.active_issue()
    STORE.appliance(issue["appliance_id"])["appliance_type"] = "Toaster"
    for line in said:
        STORE.append_conversation("resident", line)
    out = await assess_repair_vs_replace.handler(good)
    a = json.loads(out["content"][0]["text"])
    check("no fault reference file for the type: refused, and routed to ops",
          a.get("status") == "refused" and "reference" in a.get("refusal_reason", "")
          and "ops" in a.get("next", ""), str(a.get("refusal_reason")))
    check("  ...without running the subagent", not calls)
    subagent.run = real_run

    # ---------------------------------------------------------------- Module 3 step 2: surface
    section("The subagent's tool surface (Module 3)")
    sopts = subagent.build_options("x")
    check("subagent: tools=[] and setting_sources=[] (invariant 1)",
          sopts.tools == [] and sopts.setting_sources == [])
    check("subagent: its own MCP server only", list(sopts.mcp_servers) == ["rvr"])
    check("subagent: get_appliance, search_similar_issues and its two exits only",
          sorted(sopts.allowed_tools) == sorted(f"mcp__rvr__{n}" for n in
          ("get_appliance", "search_similar_issues", "submit_assessment", "submit_no_change")),
          str(sopts.allowed_tools))
    ro = {t.name: t.annotations for t in subagent.TOOLS}
    check("  ...and both lookups are read-only",
          all(ro[n] and ro[n].read_only_hint for n in ("get_appliance", "search_similar_issues")))

    async def sub_hook(tool):
        return await subagent.pre_tool_use({"tool_name": tool, "tool_input": {}}, "tu", {})
    for tool in ("Bash", "mcp__iterum__send_resident_message", "mcp__iterum__book_visit",
                 "mcp__iterum__check_warranty"):
        d, reason = denied(await sub_hook(tool))
        check(f"subagent hook denies {tool}", d, reason)
    d, _ = denied(await sub_hook("mcp__rvr__get_appliance"))
    check("subagent hook allows its own lookup", not d)

    STORE.load_scenario("clear_repair")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/clear_repair.json").read_text())))
    r = await subagent.get_appliance.handler({"appliance_id": "app_001"})
    check("subagent get_appliance is scoped to this issue's appliance", r.get("is_error"))
    r = await subagent.get_appliance.handler({"appliance_id": STORE.active_issue()["appliance_id"]})
    check("  ...and returns it", not r.get("is_error"))
    subagent._submission = None
    r = await subagent.submit_assessment.handler(
        {"code": "B", "confidence": 0.8, "rationale": "r", "key_factors": ["k"]})
    check("submit_assessment refuses a weighed call with no contra-indicators",
          r.get("is_error") and subagent._submission is None)
    r = await subagent.submit_assessment.handler(
        {"code": "B", "confidence": 0.8, "rationale": "r", "key_factors": ["k"],
         "contra_indicators": ["c"]})
    check("  ...and accepts a valid one", not r.get("is_error") and subagent._submission is not None)
    subagent._submission = None
    check("main agent no longer has search_similar_issues",
          qualified("search_similar_issues") not in AUTONOMOUS_TOOLS
          and "search_similar_issues" not in {t.name for t in ALL_TOOLS})

    # ---------------------------------------------------------------- Module 3 step 3: re-invocation
    section("Re-invocation: relevance check and the cap of two (Module 3)")
    from agent.tools import reassess_repair_vs_replace, send_ops_message  # noqa: F401
    reassess = reassess_repair_vs_replace.handler
    STORE.load_scenario("clear_repair")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/clear_repair.json").read_text())))
    s.enter_loop(session.DECISION)
    issue = STORE.active_issue()
    for line in ["There's a low humming noise when it should pump out, then nothing happens.",
                 "Oh and now it smells a bit musty and there's water left in the drum.",
                 "Also I can only do Tuesdays after 3pm because of work.",
                 "The door seal has a split in it, I just noticed."]:
        STORE.append_conversation("resident", line)

    mode = {"answer": "assessed"}
    calls = []

    async def fake_run(b):
        calls.append(b)
        if mode["answer"] == "no_change":
            return {"no_change_reason": "Scheduling preference, not about the fault."}
        return _afm(_RVR(code="B", confidence=0.74, rationale="Pump fault, repairable.",
                         key_factors=["k"], contra_indicators=["c"]), inputs={})

    subagent.run = fake_run
    KNOBS.use_llm_for_decision_analysis = True
    base = {"issue_id": issue["id"], "appliance_id": issue["appliance_id"]}
    out = await assess_repair_vs_replace.handler(dict(base,
        troubleshooting=[{"step": "Cleaned the filter", "result": "No change"}],
        resident_symptoms=["low humming noise when it should pump out"], known_gaps=[]))
    rvr1 = json.loads(out["content"][0]["text"])
    calls.clear()

    schema = reassess_repair_vs_replace.input_schema
    check("reassess takes only issue, appliance, previous assessment ID and new quotes",
          sorted(schema["properties"]) == sorted(subagent.REINVOKE_FIELDS)
          and schema.get("additionalProperties") is False, str(sorted(schema["properties"])))
    relevant = dict(base, previous_assessment_id=rvr1["assessment_id"],
                    new_information=["now it smells a bit musty and there's water left in the drum"])
    for label, args in [
        ("an unknown previous assessment ID", dict(relevant, previous_assessment_id="ISS-X-RVR-9")),
        ("a paraphrased quote", dict(relevant, new_information=["It has started to smell damp"])),
        ("a verdict", dict(relevant, new_information=["it needs replacing"])),
        ("earlier evidence re-sent by the main agent",
         dict(relevant, resident_symptoms=["low humming noise when it should pump out"])),
    ]:
        r = await reassess(args)
        check(f"rejected: {label}", r.get("is_error"), r["content"][0]["text"][:160])
    check("  ...none of them reached the subagent or counted towards the cap",
          not calls and assessments.reassessment_count(issue) == 0)

    out = await reassess(relevant)
    rvr2 = json.loads(out["content"][0]["text"])
    check("relevant new information: the subagent re-assesses",
          rvr2.get("status") == "assessed" and rvr2.get("reassesses") == rvr1["assessment_id"]
          and len(calls) == 1, str({k: rvr2.get(k) for k in ("status", "reassesses")}))
    b2 = calls[-1]
    check("  ...on the earlier evidence from the log plus the new quote, marked as new",
          b2["troubleshooting"] == rvr1["brief"]["troubleshooting"]
          and b2["resident_symptoms"] == rvr1["brief"]["resident_symptoms"]
          and b2["new_information"] == relevant["new_information"]
          and "NEW since the last assessment" in subagent.render_brief(b2))
    check("  ...without being shown its previous code or confidence",
          not {"code", "confidence", "rationale"} & set(b2)
          and "0.74" not in subagent.render_brief(b2))
    check("the re-assessment instructions carry the relevance check; a first assessment's do not",
          subagent.REINVOCATION in subagent.system_prompt("Washer Dryer", b2["fault_slug"], True)
          and subagent.REINVOCATION not in subagent.system_prompt("Washer Dryer", b2["fault_slug"]))
    r = await reassess(dict(relevant, new_information=["The door seal has a split in it"]))
    check("the superseded assessment cannot be re-assessed from", r.get("is_error"),
          r["content"][0]["text"][:160])

    mode["answer"] = "no_change"
    out = await reassess(dict(base, previous_assessment_id=rvr2["assessment_id"],
                              new_information=["I can only do Tuesdays after 3pm"]))
    rvr3 = json.loads(out["content"][0]["text"])
    check("irrelevant new information: logged as no_change with the subagent's reason",
          rvr3.get("status") == "no_change" and "Scheduling" in (rvr3.get("rationale") or ""),
          str({k: rvr3.get(k) for k in ("status", "rationale")}))
    check("  ...carrying the previous code and confidence for reference only",
          rvr3.get("code") == rvr2["code"] and rvr3.get("confidence") == rvr2["confidence"]
          and rvr3.get("meets_threshold") is False and rvr3.get("carried_from") == rvr2["assessment_id"])
    check("  ...and it counts towards the cap", assessments.reassessment_count(issue) == 2)
    nb = subagent.build_reinvocation_brief(issue, STORE.appliance(issue["appliance_id"]),
                                           assessments.latest(issue), ["x"])
    check("information judged not about the fault is not carried into later evidence",
          not any("Tuesdays" in q for q in nb["resident_symptoms"])
          and any("musty" in q for q in nb["resident_symptoms"]), str(nb["resident_symptoms"]))

    r = await submit_recommendation.handler({"assessment_id": rvr3["assessment_id"]})
    check("a no_change cannot be submitted", r.get("is_error"))
    r = await submit_recommendation.handler({"assessment_id": rvr2["assessment_id"]})
    check("  ...the newest assessed one still can, past a later no_change",
          not r.get("is_error") and issue["recommendation_assessment_id"] == rvr2["assessment_id"],
          r["content"][0]["text"][:160])

    calls.clear()
    ops_before = len(STORE.data["ops_queue"])
    s.enter_loop(session.BOOKING)
    out = await reassess(dict(base, previous_assessment_id=rvr3["assessment_id"],
                              new_information=["The door seal has a split in it"]))
    res = json.loads(out["content"][0]["text"])
    check("third re-invocation goes to ops instead", res.get("status") == "escalated_to_ops",
          str(res.get("status")))
    check("  ...without running the subagent or adding an assessment",
          not calls and len(assessments.history(issue)) == 3)
    ops = STORE.data["ops_queue"][ops_before:]
    check("  ...code raised the ops request itself, with the assessment history attached",
          len(ops) == 1 and ops[0]["category"] == "escalation"
          and all(a["assessment_id"] in ops[0]["request"] for a in (rvr1, rvr2, rvr3))
          and "door seal" in ops[0]["request"], str(ops)[:200])
    check("  ...and the escalation is recorded on the issue with the full history",
          len((issue.get("assessment_escalated") or {}).get("history", [])) == 3
          and s.assessment_escalated)
    for tool in ("book_visit", "find_available_technician", "submit_recommendation",
                 "reassess_repair_vs_replace", "assess_repair_vs_replace", "send_engineer_message"):
        d, reason = denied(await pre_hook(qualified(tool), {}))
        check(f"after escalation: {tool} is blocked by the hook", d, reason)
    for tool in ("send_resident_message", "send_ops_message", "close_job", "conclude_booking"):
        d, _ = denied(await pre_hook(qualified(tool), {}))
        check(f"after escalation: {tool} still allowed (the handoff must work)", not d)

    # Fallback and window, on a fresh issue.
    STORE.load_scenario("clear_repair")
    s = session.set_current(session.IssueSession(json.loads(Path("scenarios/clear_repair.json").read_text())))
    s.enter_loop(session.DECISION)
    issue = STORE.active_issue()
    STORE.append_conversation("resident", "It hums when it should pump out, then nothing.")
    STORE.append_conversation("resident", "There's water left in the drum as well.")
    KNOBS.use_llm_for_decision_analysis = False
    out = await assess_repair_vs_replace.handler(dict(base, issue_id=issue["id"],
        troubleshooting=[], resident_symptoms=["It hums when it should pump out"], known_gaps=[]))
    f1 = json.loads(out["content"][0]["text"])
    out = await reassess(dict(base, issue_id=issue["id"], previous_assessment_id=f1["assessment_id"],
                              new_information=["water left in the drum"]))
    f2 = json.loads(out["content"][0]["text"])
    check("fallback re-invocation: assessed, and says no relevance check was made",
          f2.get("status") == "assessed" and f2.get("source") == "fallback"
          and "not performed" in (f2.get("relevance_check") or ""),
          str({k: f2.get(k) for k in ("status", "source", "relevance_check")}))
    KNOBS.use_llm_for_decision_analysis = True
    STORE.add_visit({"id": "VIS-T", "issue_id": issue["id"], "type": "repair",
                     "slot_date": "2026-09-30", "status": "provisional"})
    r = await reassess(dict(base, issue_id=issue["id"], previous_assessment_id=f2["assessment_id"],
                            new_information=["water left in the drum"]))
    check("once a visit is booked, the assessment can no longer be revisited",
          r.get("is_error") and "visit" in r["content"][0]["text"].lower())
    subagent.run = real_run

    subagent._submission, subagent._no_change_reason, subagent._reinvocation = None, None, False
    r = await subagent.submit_no_change.handler({"reason": "scheduling"})
    check("subagent: submit_no_change is refused on a first assessment",
          r.get("is_error") and subagent._no_change_reason is None)
    subagent._reinvocation = True
    r = await subagent.submit_no_change.handler({"reason": "scheduling"})
    check("  ...and accepted on a re-assessment", not r.get("is_error")
          and subagent._no_change_reason == "scheduling")
    r = await subagent.submit_assessment.handler(
        {"code": "B", "confidence": 0.8, "rationale": "r", "key_factors": ["k"],
         "contra_indicators": ["c"]})
    check("  ...and only one answer per run", r.get("is_error"))
    subagent._submission, subagent._no_change_reason, subagent._reinvocation = None, None, False

    # ---------------------------------------------------------------- Module 3 step 3: gate
    section("The booking gate follows the submitted code, never visit_type (Module 3)")
    STORE.load_scenario("likely_replacement")
    s = session.set_current(session.IssueSession(scn))
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "repair"}, None)
    check("no submitted recommendation: booking refused", r.behavior == "deny", getattr(r, "message", ""))
    a1 = give_recommendation("A")
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "repair"}, None)
    check('code A booked as visit_type "repair" still hits the engineer gate',
          r.behavior == "deny" and "engineer" in r.message.lower(), getattr(r, "message", ""))
    s.engineer_decision = {"decision": "override", "note": "Element only", "engineer": "Tomas Novak"}
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "repair"}, None)
    check("  ...an engineer override is the one route to a repair booking", r.behavior == "allow")
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "replacement"}, None)
    check("  ...and after an override a replacement stays blocked", r.behavior == "deny")

    s.engineer_decision = {"decision": "confirm", "note": "", "engineer": "Tomas Novak"}
    s.pm_decision = {"decision": "approve", "note": ""}
    s.enter_loop(session.BOOKING)
    assessments.record(STORE.active_issue(), STORE.active_issue()["appliance_id"], {
        "source": "subagent", "code": "B", "confidence": 0.8, "rationale": "new info",
        "evidence_used": [], "evidence_missing": [], "limits_applied": [],
        "contra_indicators": ["c"], "determinative": False, "confidence_basis": "test",
        "reassesses": a1["assessment_id"]})
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "replacement"}, None)
    check("a booking on a superseded assessment is refused, approvals or not",
          r.behavior == "deny" and "superseded" in r.message.lower(), getattr(r, "message", ""))
    newest = assessments.latest(STORE.active_issue())
    r = await submit_recommendation.handler({"assessment_id": newest["assessment_id"]})
    check("submitting a different assessment clears the approvals given on the old one",
          not r.get("is_error") and s.engineer_decision is None and s.pm_decision is None)
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "replacement"}, None)
    check('code B booked as visit_type "replacement" is refused as a mismatch',
          r.behavior == "deny" and "code B" in r.message,
          getattr(r, "message", ""))
    r = await gates.can_use_tool(qualified("book_visit"), {"visit_type": "repair"}, None)
    check("  ...and books as a repair with no human in the loop", r.behavior == "allow")

    # ---------------------------------------------------------------- Module 3: skill isolation
    section("The repair-vs-replace skill never reaches the main agent (Module 3)")
    import re
    from agent.skills import DECISION_SKILL, load_skill

    def shingles(text, n=6):
        words = re.findall(r"[a-z0-9]+", text.lower())
        return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}

    skill = shingles(load_skill(DECISION_SKILL))
    main_agent_text = {name: getattr(prompts, name) for name in ("SYSTEM", "TRIAGE", "DECISION", "BOOKING")}
    main_agent_text.update({f"tool:{t.name}": t.description for t in ALL_TOOLS})
    leaks = {k: sorted(shingles(v) & skill)[:3] for k, v in main_agent_text.items()
             if shingles(v) & skill}
    check("no six-word run of the skill appears in any prompt or tool description",
          not leaks, str(leaks))
    check("the DECISION prompt no longer asks the main agent for its own judgement",
          "your judgement" not in prompts.DECISION and "your confidence" not in prompts.DECISION)

    # ---------------------------------------------------------------- summary
    total, passed = len(results), sum(results)
    print(f"\n\033[1m{passed}/{total} checks passed\033[0m")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
