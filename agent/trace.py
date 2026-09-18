"""Observability and the hard guardrails.

Hooks run FIRST in the SDK's permission evaluation order - before deny rules, before the
permission mode, before allow rules, before can_use_tool. That makes PreToolUse the only
place a check is guaranteed to run on every single tool call, which is why both the
warranty branch and the decision log live here rather than in a prompt.

A guardrail enforced by the harness is one the model cannot talk its way past. A guardrail
that is only an instruction in the system prompt is not really a guardrail.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_agent_sdk import HookMatcher

from . import session
from .events import BUS

LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "decision_log.jsonl"

# Whether log entries are coming from a live scenario run or from selftest.py driving the
# hooks directly. selftest sets this to "selftest" at import. Without it the two are
# indistinguishable in decision_log.jsonl, and they are not equivalent evidence: every
# guardrail_block in the log to date was written by selftest exercising the hook
# synthetically, while no guardrail has yet fired in a live run. A reader with no way to
# tell them apart would reasonably conclude the guardrails fire in production.
RUN_SOURCE = "live"

PREFIX = "mcp__iterum__"

# PRD 5.2: in-warranty repairs are activated and managed through the OEM. The agent does
# not book, quote, or schedule these - so once check_warranty comes back in-warranty,
# these tools are hard-blocked for the rest of the thread.
WARRANTY_BLOCKED_TOOLS = {
    "book_visit", "confirm_visit", "find_available_technician", "send_email",
}

# Calls worth writing to the permanent decision log (PRD section 7).
LOGGED_TOOLS = {
    "assess_repair_vs_replace", "submit_recommendation", "send_engineer_message",
    "send_email", "book_visit", "confirm_visit", "close_job", "complete_triage",
    "conclude_booking", "send_ops_message",
    # Logged for its `reference_matched` flag: it is the only record of whether the
    # triage skill's fault reference actually reached the model. Without it a skill
    # that silently stopped matching would still produce plausible steps (invariant 6).
    "get_triage_steps",
}


def short_name(tool_name: str) -> str:
    return tool_name[len(PREFIX):] if tool_name.startswith(PREFIX) else tool_name


def log_decision(event: str, **payload: Any) -> None:
    """Append-only. This file is the dataset that would eventually validate the model."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {"at": datetime.utcnow().isoformat() + "Z", "event": event,
              "run_source": RUN_SOURCE, **payload}
    try:
        s = session.current()
        record.setdefault("issue_id", s.issue_id)
        record.setdefault("loop", s.loop)
    except RuntimeError:
        pass
    with LOG_PATH.open("a") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


async def pre_tool_use(input_data, tool_use_id, context):
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {}) or {}
    name = short_name(tool_name)

    try:
        s = session.current()
    except RuntimeError:
        s = None

    is_iterum = tool_name.startswith(PREFIX)

    if s is not None:
        s.tick()
        s.tool_calls.append({"tool": name, "input": tool_input, "loop": s.loop})

    BUS.publish(
        "tool_call",
        tool=name,
        qualified=tool_name,
        iterum_tool=is_iterum,
        input=tool_input,
        loop=s.loop if s else None,
        iteration=s.loop_iteration if s else None,
        tool_use_id=tool_use_id,
    )

    # --- Guardrail: a tool outside the Iterum surface should not exist at all. ---------
    # tools=[] already removes the built-ins from Claude's context; this is belt and
    # braces, and it makes any leak visible in the trace rather than silent.
    if not is_iterum:
        reason = (f"{tool_name} is outside the Iterum tool surface and is not available "
                  "to this agent.")
        BUS.publish("guardrail", rule="tool_surface", detail=reason, tool=name)
        log_decision("guardrail_block", rule="tool_surface", tool=tool_name)
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }

    # --- Guardrail: warranty branch (PRD 5.2) -----------------------------------------
    if s is not None and s.warranty_blocked and name in WARRANTY_BLOCKED_TOOLS:
        reason = (
            "This appliance is in warranty. In-warranty repairs must be activated and "
            "managed through the OEM, who dispatches their own engineer. You must not "
            f"book, quote or schedule anything, so {name} is blocked. Notify ops with "
            "send_ops_message, tell the resident the manufacturer's service process is "
            "handling it, and close your loop."
        )
        BUS.publish("guardrail", rule="warranty", detail=reason, tool=name)
        log_decision("guardrail_block", rule="warranty", tool=name, tool_input=tool_input)
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }

    if name in LOGGED_TOOLS:
        log_decision("tool_call", tool=name, tool_input=tool_input)

    return {}


async def post_tool_use(input_data, tool_use_id, context):
    tool_name = input_data.get("tool_name", "")
    name = short_name(tool_name)
    response = input_data.get("tool_response")

    text = _response_text(response)
    BUS.publish("tool_result", tool=name, result=text, tool_use_id=tool_use_id)

    if name in LOGGED_TOOLS:
        log_decision("tool_result", tool=name, result=text[:4000])
    return {}


def _response_text(response: Any) -> str:
    """Tool responses arrive in a few shapes depending on the transport; normalise them."""
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        content = response.get("content")
        if isinstance(content, list):
            parts = [b.get("text", "") for b in content
                     if isinstance(b, dict) and b.get("type") == "text"]
            if parts:
                return "\n".join(parts)
        return json.dumps(response, default=str)[:8000]
    if isinstance(response, list):
        parts = [b.get("text", "") for b in response
                 if isinstance(b, dict) and b.get("type") == "text"]
        if parts:
            return "\n".join(parts)
    return str(response)[:8000]


HOOKS = {
    "PreToolUse": [HookMatcher(hooks=[pre_tool_use])],
    "PostToolUse": [HookMatcher(hooks=[post_tool_use])],
}
