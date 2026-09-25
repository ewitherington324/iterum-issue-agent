"""The Iterum tool surface (PRD section 4.3).

Every tool the agent can reach. Registered as a single in-process SDK MCP server, which
means the agent sees them as `mcp__iterum__<name>`. Combined with `tools=[]` in
ClaudeAgentOptions, this is the *only* thing the agent can do - no filesystem, no shell,
no web.

Two tools are LLM reasoning calls with a rules-based fallback, per PRD 4.1, switchable
live from the UI so the demo can A/B the model against the heuristic.
"""

import asyncio
import json
from datetime import date, timedelta

from claude_agent_sdk import ToolAnnotations, create_sdk_mcp_server, tool

from . import assessments, session, subagent, trace
from .config import KNOBS
from .events import BUS
from .fallbacks import assess_heuristic, lookup_triage_steps
from .reasoning import llm_triage_steps
from .store import STORE

RESIDENT_REPLY_TIMEOUT_S = 180
READ_ONLY = ToolAnnotations(readOnlyHint=True)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def ok(payload) -> dict:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, default=str)
    return {"content": [{"type": "text", "text": text}]}


def err(message: str) -> dict:
    return {"content": [{"type": "text", "text": message}], "is_error": True}


# =====================================================================================
# Resident communication
# =====================================================================================

@tool(
    "send_resident_message",
    "Send a WhatsApp message to the resident and wait for their reply. This is the only "
    "channel to the resident. Set expect_reply to false for a closing message that needs "
    "no response. Returns the resident's reply, or tells you they did not respond.",
    {
        "type": "object",
        "properties": {
            "resident_id": {"type": "string", "description": "Resident id from the issue record"},
            "message": {"type": "string", "description": "The message text, written for WhatsApp"},
            "expect_reply": {"type": "boolean", "description": "Whether to wait for a reply"},
        },
        "required": ["resident_id", "message", "expect_reply"],
    },
)
async def send_resident_message(args):
    s = session.current()
    message = args["message"]
    BUS.publish("resident_message", direction="out", text=message)
    STORE.append_conversation("agent", message)

    if not args.get("expect_reply", True):
        return ok("Message delivered. No reply awaited.")

    fut = s.open_resident_wait()
    BUS.publish("awaiting_resident", auto_play=s.auto_play)

    if s.auto_play:
        from .resident_sim import schedule_reply
        schedule_reply(s)

    try:
        reply = await asyncio.wait_for(asyncio.shield(fut), timeout=RESIDENT_REPLY_TIMEOUT_S)
    except asyncio.TimeoutError:
        # Clear the pending wait, or the UI stays stuck showing "awaiting resident" and a
        # late reply would resolve a future nobody is listening to.
        s.clear_resident_wait()
        BUS.publish("resident_timeout")
        BUS.publish("state", state=s.snapshot())
        return ok("The resident has not replied within the waiting window. Treat them as "
                  "unresponsive for now.")

    STORE.append_conversation("resident", reply)
    return ok(f"Resident replied: {reply}")


# =====================================================================================
# Iterum DB reads
# =====================================================================================

@tool("get_appliance",
      "Look up an appliance: make, model, install date, age, price, and the issue history "
      "for that specific unit.",
      {"appliance_id": str}, annotations=READ_ONLY)
async def get_appliance(args):
    appliance = STORE.appliance(args["appliance_id"])
    if not appliance:
        return err(f"No appliance found with id {args['appliance_id']!r}.")
    return ok(STORE.appliance_view(appliance))


@tool("check_warranty",
      "Check whether an appliance is inside its manufacturer warranty. Run this during "
      "triage: in-warranty jobs must leave the automated flow entirely and be handled by "
      "the OEM's own service process.",
      {"appliance_id": str}, annotations=READ_ONLY)
async def check_warranty(args):
    appliance = STORE.appliance(args["appliance_id"])
    if not appliance:
        return err(f"No appliance found with id {args['appliance_id']!r}.")
    result = STORE.warranty(appliance)
    if result["in_warranty"]:
        session.current().warranty_blocked = True
        BUS.publish("guardrail", rule="warranty",
                    detail=f"In warranty until {result['expiry']} ({result['oem']}). "
                           "Booking, quoting and scheduling are now blocked for this issue.")
    return ok(result)


# search_similar_issues belongs to the repair-vs-replace subagent (agent/subagent.py).
# The main agent never forms a repair-vs-replace view, so it has no use for comparables.


@tool("get_property_data",
      "Property details: operator, assigned engineer, which days that engineer services the "
      "property, and access notes.",
      {"property_id": str}, annotations=READ_ONLY)
async def get_property_data(args):
    prop = STORE.property(args["property_id"])
    if not prop:
        return err(f"No property found with id {args['property_id']!r}.")
    engineer = STORE.engineer_for_property(args["property_id"])
    pm = STORE.property_manager(args["property_id"])
    return ok({**prop, "engineer": engineer, "property_manager": pm})


@tool("check_inventory",
      "Check stock and lead time for a part. Pass a sku if you know it, otherwise pass "
      "appliance_type to list every part held for that appliance. Read-only: the agent never "
      "orders anything.",
      {"type": "object",
       "properties": {
           "appliance_type": {"type": "string", "description": "e.g. Oven, Hob, Dishwasher"},
       },
       "required": ["appliance_type"]},
      annotations=READ_ONLY)
async def check_inventory(args):
    sku = args.get("sku")
    if sku:
        item = STORE.inventory(sku)
        return ok(item) if item else err(f"No stock line for sku {sku!r}.")
    items = STORE.inventory_for_type(args["appliance_type"])
    if not items:
        return ok(f"No parts held for {args['appliance_type']}.")
    return ok({"appliance_type": args["appliance_type"], "parts": items})


# =====================================================================================
# Reasoning calls (LLM, with rules-based fallback - PRD 4.1)
# =====================================================================================

@tool("get_triage_steps",
      "Get troubleshooting steps a resident can safely carry out themselves for this "
      "specific fault. Steps must never involve electrical work, disassembly, or tools "
      "beyond the obvious.",
      {"appliance_type": str, "brand": str, "issue_description": str, "fault_slug": str})
async def get_triage_steps(args):
    use_llm = KNOBS.use_llm_for_triage_steps
    BUS.publish("reasoning_path", tool="get_triage_steps",
                path="llm" if use_llm else "fallback")
    if use_llm:
        try:
            result = await llm_triage_steps(
                appliance_type=args["appliance_type"], brand=args["brand"],
                issue_description=args["issue_description"], fault_slug=args["fault_slug"],
            )
        except Exception as exc:  # noqa: BLE001 - fall back rather than fail the loop
            BUS.publish("reasoning_path", tool="get_triage_steps", path="fallback",
                        detail=f"LLM call failed, fell back to pattern lookup: {exc}")
            result = lookup_triage_steps(args["fault_slug"], args["appliance_type"])
    else:
        result = lookup_triage_steps(args["fault_slug"], args["appliance_type"])
    return ok(result)


@tool("assess_repair_vs_replace",
      "Hand the fault evidence to the repair-vs-replace subagent, which assesses it "
      "separately from you. Pass only evidence about the appliance and the fault: each "
      "troubleshooting step with what the resident observed, the resident's own words "
      "about the appliance copied exactly (shorten a quote to the part about the fault if "
      "needed), and any known gaps. Pass what the resident observed and what was tried, not "
      "what you think it means. Leave out complaints, scheduling and your own view of the "
      "outcome. Warranty and costs are added from Iterum records. The "
      "result is logged with an assessment_id; submit it with submit_recommendation. This "
      "is provisional routing, not a diagnosis.",
      subagent.INPUT_SCHEMA)
async def assess_repair_vs_replace(args):
    issue = STORE.active_issue()

    # The input filter (spec: "Inputs"). Refused input goes back to the main agent with
    # every reason at once, so it can correct and call again.
    problems = subagent.check_input(issue, args, STORE.data["conversation_log"])
    if problems:
        trace.log_decision("assessment_input_rejected", problems=problems, tool_input=args)
        return err("The assessment input was not accepted:\n- " + "\n- ".join(problems))

    appliance = STORE.appliance(issue["appliance_id"])

    # The precondition guard (spec: "Responsibilities"). Deliberately here rather than in
    # the PreToolUse hook - see CLAUDE.md invariant 3.
    reason = subagent.refusal_reason(issue, appliance)
    if reason:
        assessment = assessments.record(issue, appliance["id"], subagent.refused(reason),
                                        status="refused")
        STORE.save()
        BUS.publish("guardrail", rule="assessment_refused", tool="assess_repair_vs_replace",
                    detail=f"{assessment['assessment_id']}: {reason}")
        return ok({**assessment, "next": (
            "No recommendation was made, so there is nothing to submit. Hand the thread to "
            "ops with send_ops_message (category 'escalation', or 'warranty_handoff' if in "
            "warranty), tell the resident ops will be in touch, and close the job as "
            "'handed_to_ops'.")})

    brief = subagent.build_brief(issue, appliance, args)
    age = STORE.appliance_age_years(appliance)
    repair, replace = brief["estimated_repair_cost"], brief["estimated_replacement_cost"]

    use_llm = KNOBS.use_llm_for_decision_analysis
    BUS.publish("reasoning_path", tool="assess_repair_vs_replace",
                path="llm" if use_llm else "fallback")

    if use_llm:
        try:
            result = await subagent.run(brief)
        except Exception as exc:  # noqa: BLE001 - fall back rather than fail the loop
            BUS.publish("reasoning_path", tool="assess_repair_vs_replace", path="fallback",
                        detail=f"Subagent failed, fell back to the heuristic: "
                               f"{type(exc).__name__}: {exc}")
            result = assess_heuristic(age, repair, replace, brief["in_warranty"])
    else:
        result = assess_heuristic(age, repair, replace, brief["in_warranty"])

    result["estimated_repair_cost"] = repair
    result["estimated_replacement_cost"] = replace
    # Exactly what the subagent was given, so the log shows what the judgement rests on.
    result["brief"] = brief
    assessment = assessments.record(issue, appliance["id"], result)
    STORE.save()
    return ok(assessment)


# =====================================================================================
# Scheduling
# =====================================================================================

@tool("find_available_technician",
      "Find the next appointment slot for this property's assigned engineer, on or after "
      "earliest_date. Slot selection is deterministic: the first day on or after "
      "earliest_date that the assigned engineer already services this property.",
      {"property_id": str, "earliest_date": str})
async def find_available_technician(args):
    prop = STORE.property(args["property_id"])
    if not prop:
        return err(f"No property found with id {args['property_id']!r}.")
    engineer = STORE.engineer_for_property(args["property_id"])
    if not engineer:
        return err(f"No engineer assigned to {prop['name']}.")

    try:
        earliest = date.fromisoformat(args["earliest_date"])
    except ValueError:
        return err(f"earliest_date must be ISO format (YYYY-MM-DD), got {args['earliest_date']!r}.")

    earliest = max(earliest, STORE.today)
    s = session.current()

    # PRD 5.1: one slot at a time; after N rejections the thread goes to ops. Enforced
    # here rather than left to the prompt, so the loop cannot propose indefinitely.
    if s.proposed_slots:
        s.slot_rejections = len(s.proposed_slots)
        if s.slot_rejections >= KNOBS.max_slot_rejections:
            BUS.publish("guardrail", rule="slot_rejections", tool="find_available_technician",
                        detail=f"{s.slot_rejections} slots already rejected "
                               f"(limit {KNOBS.max_slot_rejections}).")
            return err(
                f"The resident has now rejected {s.slot_rejections} slots, which is the "
                f"limit of {KNOBS.max_slot_rejections}. Stop proposing dates. Hand the "
                "thread to ops with send_ops_message, tell the resident ops will be in "
                "touch to arrange a time, and conclude the booking loop with outcome "
                "'handed_to_ops'."
            )

    cursor = earliest
    for _ in range(60):
        if WEEKDAYS[cursor.weekday()] in engineer["service_days"] \
                and cursor.isoformat() not in s.proposed_slots:
            s.proposed_slots.append(cursor.isoformat())
            BUS.publish("slot_proposed", slot=cursor.isoformat(),
                        attempt=len(s.proposed_slots),
                        rejections_so_far=s.slot_rejections)
            return ok({
                "slot_date": cursor.isoformat(),
                "weekday": WEEKDAYS[cursor.weekday()],
                "engineer": {"id": engineer["id"], "name": engineer["name"],
                             "partner": engineer["partner"]},
                "property": prop["name"],
                "access_notes": prop["access_notes"],
                "selection_rule": (f"First {'/'.join(engineer['service_days'])} on or after "
                                   f"{earliest.isoformat()} not already proposed."),
                "slots_proposed_so_far": len(s.proposed_slots),
                "rejection_limit": KNOBS.max_slot_rejections,
            })
        cursor += timedelta(days=1)
    return err("No qualifying slot found within 60 days.")


@tool("book_visit",
      "Create a visit against this issue in Iterum IQ. For a replacement this needs "
      "engineer confirmation first, and property manager approval if the cost is over "
      "threshold - the system will hold the call until those are in place.",
      {"issue_id": str, "slot_date": str, "visit_type": str})
async def book_visit(args):
    issue = STORE.issue(args["issue_id"])
    visit = {
        "id": f"VIS-{len(issue['visits']) + 1:03d}-{issue['id'].split('-')[-1]}",
        "issue_id": issue["id"],
        "type": args["visit_type"],
        "slot_date": args["slot_date"],
        "status": "provisional",
    }
    STORE.add_visit(visit)
    BUS.publish("visit", action="booked", visit=visit)
    return ok({"booked": visit, "next": "Call confirm_visit once the resident has accepted."})


@tool("confirm_visit",
      "Lock the slot once the resident has accepted it.",
      {"visit_id": str})
async def confirm_visit(args):
    issue = STORE.active_issue()
    for visit in issue["visits"]:
        if visit["id"] == args["visit_id"]:
            visit["status"] = "confirmed"
            STORE.save()
            BUS.publish("visit", action="confirmed", visit=visit)
            return ok({"confirmed": visit})
    return err(f"No visit found with id {args['visit_id']!r}.")


# =====================================================================================
# Ops, engineer and PM channels
# =====================================================================================

@tool("send_ops_message",
      "Send a request to the Iterum ops team: a parts order, a warranty handoff, or a "
      "thread the agent should not continue handling. Ops executes; the agent never orders "
      "parts itself. Use category 'parts_order', 'warranty_handoff', 'scheduling_handoff' "
      "or 'escalation'.",
      {"issue_id": str, "category": str, "request": str})
async def send_ops_message(args):
    entry = STORE.add_ops_request(args["request"], args["category"])
    BUS.publish("ops_message", category=args["category"], request=args["request"])
    return ok({"delivered_to": "Iterum Ops", **entry})


@tool("send_engineer_message",
      "Ask the property's engineer to confirm or override a replacement recommendation "
      "before the visit. Blocks until the engineer responds.",
      {"engineer_id": str, "recommendation": str, "rationale": str})
async def send_engineer_message(args):
    s = session.current()
    engineer = STORE.engineer(args["engineer_id"])
    if not engineer:
        return err(f"No engineer found with id {args['engineer_id']!r}.")

    STORE.add_engineer_message(args["engineer_id"], args["recommendation"])
    gate = s.open_gate(
        kind="engineer", tool_name="send_engineer_message", tool_input=args,
        context={
            "engineer": engineer, "channel": KNOBS.engineer_channel,
            "recommendation": args["recommendation"], "rationale": args["rationale"],
            "issue_id": s.issue_id,
        },
    )
    BUS.publish("gate_opened", gate="engineer", context=gate.context)
    await gate.event.wait()
    decision, note = gate.decision, gate.note
    s.engineer_decision = {"decision": decision, "note": note, "engineer": engineer["name"]}
    STORE.add_approval("engineer", decision, engineer["name"], note)
    s.clear_gate()
    BUS.publish("gate_closed", gate="engineer", decision=decision, note=note)
    BUS.publish("state", state=s.snapshot())

    if decision == "override":
        return ok(f"{engineer['name']} OVERRODE the recommendation. Their assessment: "
                  f"{note or 'no note given'}. Their call takes precedence over yours - "
                  "re-plan on that basis.")
    return ok(f"{engineer['name']} CONFIRMED the recommendation."
              + (f" Note: {note}" if note else ""))


@tool("send_email",
      "Email the property manager for cost approval on a replacement. This is the one point "
      "the flow leaves WhatsApp. Blocks until the PM responds.",
      {"pm_email": str, "subject": str, "body": str, "estimated_cost": float})
async def send_email(args):
    s = session.current()
    STORE.add_email(args["pm_email"], args["subject"], args["body"])
    gate = s.open_gate(
        kind="pm", tool_name="send_email", tool_input=args,
        context={
            "to": args["pm_email"], "subject": args["subject"], "body": args["body"],
            "estimated_cost": args["estimated_cost"],
            "threshold": KNOBS.pm_cost_threshold_gbp,
            "over_threshold": args["estimated_cost"] > KNOBS.pm_cost_threshold_gbp,
            "issue_id": s.issue_id,
        },
    )
    BUS.publish("gate_opened", gate="pm", context=gate.context)
    await gate.event.wait()
    decision, note = gate.decision, gate.note
    s.pm_decision = {"decision": decision, "note": note}
    STORE.add_approval("pm", decision, args["pm_email"], note)
    s.clear_gate()
    BUS.publish("gate_closed", gate="pm", decision=decision, note=note)
    BUS.publish("state", state=s.snapshot())

    if decision == "approve":
        return ok(f"Property manager APPROVED the replacement cost."
                  + (f" Note: {note}" if note else ""))
    return ok(f"Property manager REJECTED the replacement cost."
              + (f" Reason: {note}" if note else "")
              + " Do not book. Hand the thread to ops.")


@tool("close_job",
      "Close the issue. Use resolution 'self_resolved', 'warranty_handoff', "
      "'visit_booked', 'handed_to_ops' or 'halted'.",
      {"issue_id": str, "resolution": str, "summary": str})
async def close_job(args):
    issue = STORE.issue(args["issue_id"])
    issue["status"] = "closed"
    issue["resolution"] = {"type": args["resolution"], "summary": args["summary"]}
    STORE.save()
    BUS.publish("job_closed", resolution=args["resolution"], summary=args["summary"])
    return ok({"closed": issue["id"], "resolution": args["resolution"]})


# =====================================================================================
# Loop exit tools
#
# The three loops in PRD 3.2 are defined by their exit conditions. Making the exit an
# explicit tool call keeps those conditions intact while making the loop boundary
# observable - you can see exactly where model judgement ends and control returns to
# the orchestrator.
# =====================================================================================

@tool("complete_triage",
      "Exit the triage loop. outcome must be one of: 'self_resolved' (the resident fixed "
      "it), 'in_warranty' (OEM handles it), 'needs_assessment' (enough signal for a "
      "repair-vs-replace call), 'resident_unresponsive', or 'halted' (you hit something "
      "you should not handle).",
      {"outcome": str, "fault_slug": str, "findings": str})
async def complete_triage(args):
    s = session.current()
    payload = {"outcome": args["outcome"], "fault_slug": args["fault_slug"],
               "findings": args["findings"], "iterations": s.loop_iteration}
    s.record_exit(session.TRIAGE, payload)
    issue = STORE.active_issue()
    issue["triage_transcript"] = [m for m in STORE.data["conversation_log"]]
    issue["fault_slug_confirmed"] = args["fault_slug"]
    STORE.save()
    BUS.publish("loop_exit", loop=session.TRIAGE, **payload)
    return ok(f"Triage loop closed with outcome '{args['outcome']}'.")


@tool("submit_recommendation",
      "Exit the repair-vs-replace loop by submitting the latest assessment for this issue. "
      "Takes the assessment_id from assess_repair_vs_replace and nothing else - the code, "
      "confidence and rationale are read from the assessment log, exactly as assessed.",
      {"type": "object",
       "properties": {"assessment_id": {"type": "string",
                                        "description": "From assess_repair_vs_replace"}},
       "required": ["assessment_id"],
       "additionalProperties": False})
async def submit_recommendation(args):
    # The schema already rejects extra arguments; this repeats it in the handler so the
    # rule holds however the tool is reached, and so the refusal says why.
    extra = sorted(set(args) - {"assessment_id"})
    if extra:
        return err(f"submit_recommendation takes only assessment_id, not {extra}. The "
                   "assessment's code, confidence and rationale are final and are read "
                   "from the assessment log.")

    issue = STORE.active_issue()
    assessment_id = str(args.get("assessment_id", "")).strip()
    assessment = assessments.find(issue, assessment_id)
    if assessment is None:
        return err(f"No assessment {assessment_id!r} exists for issue {issue['id']}. Call "
                   "assess_repair_vs_replace and submit the assessment_id it returns.")
    newest = assessments.latest(issue)
    if assessment is not newest:
        return err(f"{assessment_id} is not the latest assessment for this issue. Only "
                   f"the latest can be submitted: {newest['assessment_id']}.")
    if assessment["status"] != "assessed":
        return err(f"{assessment_id} has status '{assessment['status']}' and carries no "
                   "recommendation to submit.")

    s = session.current()
    code, confidence = assessment["code"], assessment["confidence"]
    payload = {"assessment_id": assessment_id, "source": assessment["source"],
               "code": code, "confidence": confidence,
               "rationale": assessment["rationale"],
               "code_meaning": assessment["code_meaning"],
               "meets_threshold": confidence >= KNOBS.confidence_threshold,
               "threshold": KNOBS.confidence_threshold,
               "iterations": s.loop_iteration}
    s.record_exit(session.DECISION, payload)
    issue["recommendation"] = code
    issue["confidence"] = confidence
    issue["recommendation_rationale"] = assessment["rationale"]
    issue["recommendation_assessment_id"] = assessment_id
    STORE.save()
    BUS.publish("loop_exit", loop=session.DECISION, **payload)
    return ok(f"Assessment {assessment_id} submitted: code {code} at confidence "
              f"{confidence:.2f} (threshold {KNOBS.confidence_threshold:.2f}).")


@tool("conclude_booking",
      "Exit the booking loop. outcome must be one of: 'booked', 'handed_to_ops' (the "
      "resident rejected too many slots, or approval was refused), or 'blocked'.",
      {"outcome": str, "detail": str})
async def conclude_booking(args):
    s = session.current()
    payload = {"outcome": args["outcome"], "detail": args["detail"],
               "slot_rejections": s.slot_rejections, "iterations": s.loop_iteration}
    s.record_exit(session.BOOKING, payload)
    BUS.publish("loop_exit", loop=session.BOOKING, **payload)
    return ok(f"Booking loop closed with outcome '{args['outcome']}'.")


ALL_TOOLS = [
    send_resident_message,
    get_appliance, check_warranty, get_property_data, check_inventory,
    get_triage_steps, assess_repair_vs_replace,
    find_available_technician, book_visit, confirm_visit,
    send_ops_message, send_engineer_message, send_email, close_job,
    complete_triage, submit_recommendation, conclude_booking,
]

ITERUM_SERVER = create_sdk_mcp_server(name="iterum", version="1.0.0", tools=ALL_TOOLS)


def qualified(name: str) -> str:
    return f"mcp__iterum__{name}"


# Tools the repair path may use without any human in the loop (PRD 3.4). Everything NOT
# in this list falls through to the can_use_tool gate - which is how the replacement path
# is held. book_visit is deliberately absent.
AUTONOMOUS_TOOLS = [qualified(n) for n in [
    "send_resident_message", "get_appliance", "check_warranty", "get_property_data",
    "check_inventory", "get_triage_steps", "assess_repair_vs_replace",
    "find_available_technician", "confirm_visit", "send_ops_message",
    "send_engineer_message", "close_job",
    "complete_triage", "submit_recommendation", "conclude_booking",
]]

GATED_TOOLS = [qualified("book_visit"), qualified("send_email")]
