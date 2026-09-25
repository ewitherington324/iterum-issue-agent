"""Orchestration: one ClaudeSDKClient per issue thread, driving the three loops.

The three loops from PRD 3.2 run as sequential phases inside ONE session, so everything
triage learned is still in context when the booking loop runs. Each phase ends when the
agent calls that loop's exit tool, which is what makes the boundary between model
judgement and deterministic control visible in the trace.

Tool surface note: `tools=[]` removes every built-in (Read, Write, Bash, Grep, WebSearch,
...) from Claude's context, and `setting_sources=[]` stops any user or project settings
leaking in. The agent can reach the Iterum tools and nothing else, on any machine.
"""

import asyncio
import warnings
from pathlib import Path

from claude_agent_sdk import (
    CanUseToolShadowedWarning,
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
)

from . import assessments, gates, prompts, session, trace
from .config import KNOBS, RECOMMENDATION_CODES
from .events import BUS
from .store import STORE
from .tools import AUTONOMOUS_TOOLS, ITERUM_SERVER

ROOT = Path(__file__).resolve().parents[1]

# The SDK warns that can_use_tool is shadowed for every tool named in allowed_tools.
# That is precisely the design here, not a mistake: the autonomous repair-path tools are
# meant to be auto-approved and to never reach the callback, while book_visit and
# send_email are deliberately left out of allowed_tools so they do. Silenced so the
# expected case does not read as an error during a demo.
warnings.filterwarnings("ignore", category=CanUseToolShadowedWarning)

# Triage outcomes that end the thread without a repair-vs-replace call.
TERMINAL_TRIAGE = {"self_resolved", "in_warranty", "resident_unresponsive", "halted"}


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model=KNOBS.model,
        system_prompt=prompts.SYSTEM,

        # The Iterum tool surface, and only the Iterum tool surface.
        mcp_servers={"iterum": ITERUM_SERVER},
        tools=[],
        allowed_tools=AUTONOMOUS_TOOLS,
        setting_sources=[],

        # 'default' so anything not auto-approved reaches the gate rather than being
        # waved through or hard-denied.
        permission_mode="default",
        can_use_tool=gates.can_use_tool,
        hooks=trace.HOOKS,

        effort=KNOBS.effort,
        thinking={"type": "adaptive", "display": "summarized"},
        max_turns=KNOBS.max_turns_per_loop,
        max_budget_usd=KNOBS.max_budget_usd,

        cwd=str(ROOT),
        stderr=lambda line: BUS.publish("stderr", line=line.rstrip()),
    )


async def _drain(client, s) -> None:
    """Consume one phase's worth of messages, streaming them to the UI."""
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    BUS.publish("agent_text", text=block.text, loop=s.loop)
                elif isinstance(block, ThinkingBlock) and block.thinking.strip():
                    BUS.publish("agent_thinking", text=block.thinking, loop=s.loop)
        elif isinstance(message, ResultMessage):
            if message.total_cost_usd:
                s.cost_usd = message.total_cost_usd
            BUS.publish("phase_result", loop=s.loop, subtype=message.subtype,
                        turns=message.num_turns, cost_usd=s.cost_usd,
                        is_error=message.is_error,
                        stop_reason=message.stop_reason,
                        state=s.snapshot())


async def _phase(client, s, loop_name: str, prompt: str) -> dict | None:
    s.enter_loop(loop_name)
    BUS.publish("loop_enter", loop=loop_name, label=session.LOOP_LABELS[loop_name],
                state=s.snapshot())
    await client.query(prompt)
    await _drain(client, s)
    return s.exits.get(loop_name)


def _triage_prompt(s) -> str:
    issue = STORE.active_issue()
    appliance = STORE.appliance(issue["appliance_id"])
    prop = STORE.property(issue["property_id"])
    resident = STORE.resident(issue["resident_id"])
    return prompts.TRIAGE.format(
        issue_id=issue["id"], property_name=prop["name"], operator=prop["operator"],
        flat=resident["flat"], resident_name=resident["name"], resident_id=resident["id"],
        brand=appliance["brand"], model=appliance["model"],
        appliance_type=appliance["appliance_type"], appliance_id=appliance["id"],
        property_id=prop["id"], description=issue["description"],
        fault_slug=issue["fault_slug_reported"],
    )


async def run_scenario(scenario_id: str, auto_play: bool = True) -> dict:
    BUS.reset()
    scenario = STORE.load_scenario(scenario_id)
    s = session.set_current(session.IssueSession(scenario))
    s.auto_play = auto_play

    BUS.publish("scenario_started", scenario={
        "id": scenario["id"], "title": scenario["title"],
        "summary": scenario["summary"], "expected": scenario["expected"],
    }, issue=STORE.active_issue(), knobs=KNOBS.to_dict(), state=s.snapshot())

    trace.log_decision("scenario_started", scenario=scenario_id, knobs=KNOBS.to_dict())

    try:
        async with ClaudeSDKClient(options=build_options()) as client:
            # --- Loop 1: triage -------------------------------------------------------
            triage = await _phase(client, s, session.TRIAGE, _triage_prompt(s))
            if triage is None:
                BUS.publish("run_incomplete", loop=session.TRIAGE,
                            detail="The triage loop ended without calling complete_triage.")
                return _finish(s)
            if triage["outcome"] in TERMINAL_TRIAGE:
                return _finish(s)

            # --- Loop 2: repair vs replace --------------------------------------------
            decision = await _phase(client, s, session.DECISION, prompts.DECISION.format(
                findings=triage["findings"]))
            if decision is None:
                # A refused assessment (in warranty, or no fault reference) has nothing to
                # submit; the main agent is told to hand to ops. That is a proper ending.
                # So is a third re-assessment request, which code has already sent to ops.
                issue = STORE.active_issue()
                latest = assessments.latest(issue)
                if not ((latest and latest["status"] == "refused")
                        or issue.get("assessment_escalated")):
                    BUS.publish("run_incomplete", loop=session.DECISION,
                                detail="The decision loop ended without calling "
                                       "submit_recommendation.")
                return _finish(s)

            # --- Loop 3: booking ------------------------------------------------------
            await _phase(client, s, session.BOOKING, prompts.BOOKING.format(
                assessment_id=decision["assessment_id"],
                code=decision["code"],
                code_meaning=RECOMMENDATION_CODES.get(decision["code"], "unknown"),
                confidence=decision["confidence"],
                threshold_status=(
                    "from the backup rules, so treated as below the threshold"
                    if decision["source"] == "fallback" else
                    "meets the threshold" if decision["meets_threshold"] else
                    "below the threshold"),
                threshold=KNOBS.confidence_threshold,
                rationale=decision["rationale"],
                pm_threshold=KNOBS.pm_cost_threshold_gbp,
                max_rejections=KNOBS.max_slot_rejections,
            ))
            return _finish(s)

    except asyncio.CancelledError:
        BUS.publish("run_cancelled")
        raise
    except Exception as exc:  # noqa: BLE001 - surface it in the UI rather than dying silently
        BUS.publish("error", where="runner", detail=f"{type(exc).__name__}: {exc}")
        trace.log_decision("run_error", error=str(exc))
        return _finish(s)


def _finish(s) -> dict:
    s.enter_loop(session.DONE)
    issue = STORE.active_issue()
    summary = {
        "issue_id": s.issue_id,
        "status": issue["status"],
        "resolution": issue.get("resolution"),
        "recommendation": issue.get("recommendation"),
        "confidence": issue.get("confidence"),
        "visits": issue["visits"],
        "exits": s.exits,
        "engineer_decision": s.engineer_decision,
        "pm_decision": s.pm_decision,
        "tool_calls": len(s.tool_calls),
        "cost_usd": round(s.cost_usd + s.subagent_cost_usd, 4),
        "subagent_cost_usd": round(s.subagent_cost_usd, 4),
        "non_iterum_tool_calls": [c["tool"] for c in s.tool_calls
                                  if c["tool"] in {"Read", "Write", "Edit", "Bash", "Grep",
                                                   "Glob", "WebSearch", "WebFetch"}],
    }
    BUS.publish("run_complete", summary=summary, state=s.snapshot())
    trace.log_decision("run_complete", **summary)
    s.finished.set()
    return summary
