"""Per-issue session state: loop phase, exit signals, pending human interactions.

One of these exists per issue thread, alongside one ClaudeSDKClient (PRD section 4.4).
It is the shared ground between the tool handlers, the permission gate, the trace hooks
and the web server.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

TRIAGE = "triage"
DECISION = "decision"
BOOKING = "booking"
DONE = "done"

LOOP_LABELS = {
    TRIAGE: "Triage loop",
    DECISION: "Repair vs. replace loop",
    BOOKING: "Booking loop",
    DONE: "Complete",
}


@dataclass
class PendingGate:
    """A tool call parked at a human gate (PRD section 3.4)."""
    kind: str                      # "engineer" | "pm"
    tool_name: str
    tool_input: dict
    context: dict
    event: asyncio.Event = field(default_factory=asyncio.Event)
    decision: str | None = None    # "approve" | "override" | "reject"
    note: str = ""


class IssueSession:
    def __init__(self, scenario: dict):
        self.scenario = scenario
        self.issue_id = scenario["issue"]["id"]

        self.loop: str = TRIAGE
        self.loop_iteration: int = 0

        # Exit payloads, keyed by loop. Populated when the agent calls an exit tool.
        self.exits: dict[str, dict] = {}

        # Resident conversation
        self._resident_reply: asyncio.Future | None = None
        self.auto_play: bool = True
        self.resident_turns: int = 0

        # Human gates
        self.pending_gate: PendingGate | None = None
        self.engineer_decision: dict | None = None
        self.pm_decision: dict | None = None

        # Guardrail state, set by tool handlers and read by the PreToolUse hook
        self.warranty_blocked: bool = False
        self.halted_reason: str | None = None
        # Set when a third re-assessment request sends the thread to ops (Module 3 step 3).
        self.assessment_escalated: bool = False

        self.slot_rejections: int = 0
        self.proposed_slots: list[str] = []
        # Slots the resident answered with new fault information (the reply led to a
        # re-invocation) - not rejections, so not counted towards the slot limit.
        self.slots_not_rejected: set[str] = set()
        self.tool_calls: list[dict] = []
        self.cost_usd: float = 0.0
        # The subagent is a separate session with its own bill; cost_usd is the main
        # agent's running total as reported by its ResultMessage.
        self.subagent_cost_usd: float = 0.0
        self.finished = asyncio.Event()

    # --- loop control ---------------------------------------------------------------
    def enter_loop(self, loop: str) -> None:
        self.loop = loop
        self.loop_iteration = 0

    def tick(self) -> int:
        self.loop_iteration += 1
        return self.loop_iteration

    def record_exit(self, loop: str, payload: dict) -> None:
        self.exits[loop] = payload

    # --- resident round-trip ---------------------------------------------------------
    def open_resident_wait(self) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        self._resident_reply = loop.create_future()
        return self._resident_reply

    def deliver_resident_reply(self, text: str) -> bool:
        """Called by the web server (manual mode) or the resident simulator."""
        fut = self._resident_reply
        if fut is None or fut.done():
            return False
        fut.set_result(text)
        self._resident_reply = None
        self.resident_turns += 1
        return True

    def clear_resident_wait(self) -> None:
        fut = self._resident_reply
        self._resident_reply = None
        if fut is not None and not fut.done():
            fut.cancel()

    @property
    def awaiting_resident(self) -> bool:
        return self._resident_reply is not None and not self._resident_reply.done()

    # --- gates -----------------------------------------------------------------------
    def open_gate(self, kind: str, tool_name: str, tool_input: dict, context: dict) -> PendingGate:
        self.pending_gate = PendingGate(kind=kind, tool_name=tool_name,
                                        tool_input=tool_input, context=context)
        return self.pending_gate

    def resolve_gate(self, decision: str, note: str = "") -> bool:
        gate = self.pending_gate
        if gate is None or gate.event.is_set():
            return False
        gate.decision = decision
        gate.note = note
        gate.event.set()
        return True

    def clear_gate(self) -> None:
        self.pending_gate = None

    # --- snapshot for the UI ----------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "loop": self.loop,
            "loop_label": LOOP_LABELS[self.loop],
            "loop_iteration": self.loop_iteration,
            "exits": self.exits,
            "awaiting_resident": self.awaiting_resident,
            "auto_play": self.auto_play,
            "pending_gate": (
                {"kind": self.pending_gate.kind, "tool": self.pending_gate.tool_name,
                 "context": self.pending_gate.context}
                if self.pending_gate and not self.pending_gate.event.is_set() else None
            ),
            "engineer_decision": self.engineer_decision,
            "pm_decision": self.pm_decision,
            "slot_rejections": self.slot_rejections,
            "warranty_blocked": self.warranty_blocked,
            "halted_reason": self.halted_reason,
            "assessment_escalated": self.assessment_escalated,
            "cost_usd": round(self.cost_usd, 4),
        }


# The demo runs one issue at a time.
CURRENT: IssueSession | None = None


def set_current(session: IssueSession) -> IssueSession:
    global CURRENT
    CURRENT = session
    return session


def current() -> IssueSession:
    if CURRENT is None:
        raise RuntimeError("No issue session is running.")
    return CURRENT
