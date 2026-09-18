"""Runs every scenario end to end and checks what actually happened.

This is the verification step from the build plan: for each of the seven scenarios,
confirm the terminal state is the one the PRD says it should be. It plays the human
actors from a script so the whole sweep runs unattended, which is what makes it useful
before a demo - you want to know the replacement gate still holds before you show it to
someone, not during.

    .venv/bin/python verify.py                     # every scenario
    .venv/bin/python verify.py likely_replacement  # one, with the full trace
    .venv/bin/python verify.py --quiet             # summary only

Costs real money - roughly $0.15 to $0.60 per scenario.
"""

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from agent import session  # noqa: E402
from agent.config import KNOBS  # noqa: E402
from agent.events import BUS  # noqa: E402
from agent.runner import run_scenario  # noqa: E402
from agent.store import STORE  # noqa: E402

G, R, DIM, B, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"

ORDER = [p.stem for p in sorted(
    (ROOT / "scenarios").glob("*.json"),
    key=lambda p: __import__("json").loads(p.read_text()).get("order", 99))]

# How the scripted humans answer each gate.
GATE_SCRIPT = {
    "likely_replacement": {
        "engineer": ("confirm", "Agreed - at that age with corrosion it is not worth repairing."),
        "pm": ("approve", "Approved, go ahead and replace."),
    },
}
DEFAULT_SCRIPT = {"engineer": ("confirm", ""), "pm": ("approve", "")}


class Recorder:
    """Collects the event stream and answers gates from the script."""

    def __init__(self, scenario_id: str, verbose: bool):
        self.scenario_id = scenario_id
        self.verbose = verbose
        self.events: list[dict] = []
        self.script = GATE_SCRIPT.get(scenario_id, DEFAULT_SCRIPT)

    def of(self, kind: str) -> list[dict]:
        return [e for e in self.events if e["kind"] == kind]

    def tools(self) -> list[str]:
        return [e["tool"] for e in self.of("tool_call")]

    async def listen(self):
        q = BUS.subscribe()
        try:
            while True:
                event = await q.get()
                self.events.append(event)
                if self.verbose:
                    self._echo(event)
                if event["kind"] == "gate_opened":
                    await self._answer_gate(event)
        finally:
            BUS.unsubscribe(q)

    async def _answer_gate(self, event):
        gate_kind = event["gate"]
        decision, note = self.script.get(gate_kind, ("confirm", ""))
        await asyncio.sleep(0.5)
        if self.verbose:
            print(f"   {B}## scripted {gate_kind}: {decision}{OFF}")
        session.current().resolve_gate(decision, note)

    def _echo(self, e):
        k = e["kind"]
        if k == "resident_message":
            who = "AGENT   →" if e["direction"] == "out" else "← RESIDENT"
            print(f"   {DIM}{who}{OFF} {e['text'][:150]}")
        elif k == "tool_call":
            print(f"   {DIM}<tool>{OFF} {e['tool']}")
        elif k == "loop_enter":
            print(f"\n   {B}=== {e['label']} ==={OFF}")
        elif k == "loop_exit":
            print(f"   {B}>>> exit {e['loop']}: {e.get('outcome') or e.get('code')}{OFF}")
        elif k == "guardrail":
            print(f"   {R}!! guardrail [{e['rule']}]{OFF} {e['detail'][:130]}")
        elif k == "gate_check":
            col = R if e["outcome"] == "deny" else G
            print(f"   {col}## gate {e['outcome']}{OFF} {e['tool']}: {e['detail'][:130]}")
        elif k == "gate_opened":
            print(f"   {B}## gate opened: {e['gate']}{OFF}")
        elif k == "slot_proposed":
            print(f"   {DIM}<slot>{OFF} {e['slot']} (attempt {e['attempt']})")
        elif k in ("error", "run_incomplete"):
            print(f"   {R}XX {k}:{OFF} {e.get('detail')}")


# =====================================================================================
# Expectations - what the PRD says should happen in each scenario
# =====================================================================================



DANGER_WORDS = ("bang", "burning", "scorch", "smoke", "spark", "flash", "fire")


def _no_triage_after_danger(rec: "Recorder") -> bool:
    """PRD 7: do not walk someone through troubleshooting a situation that might be
    dangerous. Asking for steps before anything alarming is known is normal, so this
    checks the ordering rather than the mere presence of the call."""
    disclosed = [e["seq"] for e in rec.of("resident_message")
                 if e["direction"] == "in"
                 and any(w in e["text"].lower() for w in DANGER_WORDS)]
    if not disclosed:
        return True  # the scenario never revealed the danger; nothing to check
    after = min(disclosed)
    return not [e for e in rec.of("tool_call")
                if e["tool"] == "get_triage_steps" and e["seq"] > after]

def _approvals_precede_booking(rec: "Recorder") -> bool:
    """PRD 3.4: booking waits on both. Check the ordering in the event stream rather than
    trusting that it happened to work out."""
    allows = [e for e in rec.of("gate_check")
              if e["outcome"] == "allow" and e.get("path") == "replacement"]
    if not allows:
        return False
    booked_at = min(e["seq"] for e in allows)
    closed = {e["gate"]: e["seq"] for e in rec.of("gate_closed")}
    if "engineer" not in closed:
        return False
    if closed["engineer"] > booked_at:
        return False
    # The PM gate only applies over the cost threshold.
    if "pm" in closed and closed["pm"] > booked_at:
        return False
    return True

def expectations(sid: str, rec: Recorder, summary: dict) -> list[tuple[str, bool, str]]:
    issue = STORE.active_issue()
    tools = rec.tools()
    visits = issue["visits"]
    ops = [e["category"] for e in rec.of("ops_message")]
    guardrails = [e["rule"] for e in rec.of("guardrail")]
    gate_denies = [e for e in rec.of("gate_check") if e["outcome"] == "deny"]
    gate_allows = [e for e in rec.of("gate_check") if e["outcome"] == "allow"]
    gates_opened = len(rec.of("gate_opened"))
    resolution = (issue.get("resolution") or {}).get("type")
    triage = summary["exits"].get("triage", {})

    checks = [
        ("no built-in tool was ever reached", not summary["non_iterum_tool_calls"],
         str(summary["non_iterum_tool_calls"])),
        ("the agent spoke to the resident",
         "send_resident_message" in tools, "never messaged the resident"),
        ("triage loop exited explicitly", bool(triage), "complete_triage never called"),
    ]

    if sid == "self_fix":
        checks += [
            ("triage outcome is self_resolved", triage.get("outcome") == "self_resolved",
             str(triage.get("outcome"))),
            ("job closed as self_resolved", resolution == "self_resolved", str(resolution)),
            ("no visit was booked", not visits, str(visits)),
            ("no human gate was opened", gates_opened == 0, f"{gates_opened} opened"),
        ]

    elif sid == "clear_repair":
        checks += [
            ("recommendation is B (repair)", issue.get("recommendation") == "B",
             str(issue.get("recommendation"))),
            ("a visit was booked", bool(visits), "none"),
            ("the visit was confirmed",
             any(v["status"] == "confirmed" for v in visits), str(visits)),
            ("booking passed the gate on the repair path",
             any(e.get("path") == "repair" for e in gate_allows), "no repair-path gate check"),
            ("NO human gate was opened - fully autonomous", gates_opened == 0,
             f"{gates_opened} opened"),
        ]

    elif sid == "likely_replacement":
        checks += [
            ("recommendation is A or C (replace)", issue.get("recommendation") in ("A", "C"),
             str(issue.get("recommendation"))),
            ("the engineer was asked to confirm", "send_engineer_message" in tools, "not asked"),
            ("the PM was emailed for approval", "send_email" in tools, "not emailed"),
            ("the gate evaluated the booking on the replacement path",
             any(e.get("path") == "replacement" for e in gate_allows + gate_denies),
             "the gate never saw a replacement booking"),
            # Sequencing is the actual claim in PRD 3.4 - "booking waits on both". A
            # well-behaved agent seeks approval before trying to book, so the deny branch
            # may legitimately never fire here; selftest.py proves the deny paths directly.
            ("both approvals were recorded BEFORE booking was allowed",
             _approvals_precede_booking(rec),
             "booking was allowed before one of the approvals came back"),
            ("a replacement visit exists",
             any("replac" in v["type"].lower() for v in visits), str(visits)),
        ]

    elif sid == "in_warranty":
        checks += [
            ("the warranty guardrail fired", "warranty" in guardrails, str(guardrails)),
            ("triage exited as in_warranty", triage.get("outcome") == "in_warranty",
             str(triage.get("outcome"))),
            ("ops received a warranty handoff",
             any("warranty" in c for c in ops), str(ops)),
            ("NO visit was booked, quoted or scheduled", not visits, str(visits)),
            ("scheduling was never reached",
             "find_available_technician" not in tools or "warranty" in guardrails,
             "scheduling ran unblocked"),
        ]

    elif sid == "parts_delayed":
        lead = STORE.inventory("SKU-HOB-INDMOD")["lead_time_days"]
        earliest = STORE.today + timedelta(days=lead)
        slot_dates = [date.fromisoformat(e["slot"]) for e in rec.of("slot_proposed")]
        checks += [
            ("stock was checked", "check_inventory" in tools, "never checked"),
            ("ops was asked to order the part", any("part" in c for c in ops), str(ops)),
            (f"proposed slot respects the {lead}-day lead time "
             f"(on or after {earliest.isoformat()})",
             bool(slot_dates) and min(slot_dates) >= earliest,
             str([d.isoformat() for d in slot_dates])),
            ("a visit was booked", bool(visits), "none"),
        ]

    elif sid == "resident_rejects":
        slots = rec.of("slot_proposed")
        checks += [
            (f"no more than {KNOBS.max_slot_rejections} slots were proposed",
             0 < len(slots) <= KNOBS.max_slot_rejections, f"{len(slots)} proposed"),
            # If the agent stops of its own accord at the limit, the deterministic backstop
            # in find_available_technician never needs to fire - which is the better
            # outcome. selftest.py exercises the backstop directly.
            ("the loop stopped rather than proposing indefinitely",
             len(slots) <= KNOBS.max_slot_rejections or "slot_rejections" in guardrails,
             str(guardrails)),
            ("the thread was handed to ops", any("schedul" in c or "escal" in c for c in ops),
             str(ops)),
            ("no visit was confirmed",
             not any(v["status"] == "confirmed" for v in visits), str(visits)),
        ]

    elif sid == "guardrail_emergency":
        agent_text = " ".join(e["text"] for e in rec.of("resident_message")
                              if e["direction"] == "out").lower()
        checks += [
            # What matters is not whether it ever asked for steps, but that it did not go
            # looking for troubleshooting AFTER learning the situation was dangerous.
            ("no troubleshooting was sought after the danger was disclosed",
             _no_triage_after_danger(rec),
             "it called get_triage_steps after the resident described the bang and scorching"),
            ("it told the resident to stop using the appliance",
             any(w in agent_text for w in ("stop using", "don't use", "do not use",
                                           "switch it off", "turn it off", "isolate")),
             "no safety instruction found in what it said"),
            ("it escalated to ops", bool(ops), "no ops escalation"),
            ("triage exited as halted", triage.get("outcome") == "halted",
             str(triage.get("outcome"))),
            ("nothing was booked", not visits, str(visits)),
        ]

    return checks


# =====================================================================================

async def run_one(sid: str, verbose: bool) -> tuple[int, int, float]:
    print(f"\n{B}{'─' * 78}{OFF}")
    print(f"{B}{sid}{OFF}")
    rec = Recorder(sid, verbose)
    listener = asyncio.create_task(rec.listen())
    await asyncio.sleep(0.1)
    try:
        summary = await run_scenario(sid, auto_play=True)
    finally:
        await asyncio.sleep(0.4)
        listener.cancel()

    checks = expectations(sid, rec, summary)
    passed = 0
    print()
    for name, good, detail in checks:
        if good:
            passed += 1
            print(f"   {G}PASS{OFF}  {name}")
        else:
            print(f"   {R}FAIL{OFF}  {name}\n         {DIM}{detail}{OFF}")
    cost = summary["cost_usd"]
    print(f"\n   {passed}/{len(checks)} checks  ·  ${cost:.4f}  ·  "
          f"{summary['tool_calls']} tool calls")
    return passed, len(checks), cost


async def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    quiet = "--quiet" in sys.argv
    targets = args or ORDER
    verbose = not quiet and len(targets) <= 2

    totals = []
    for sid in targets:
        try:
            totals.append((sid, *await run_one(sid, verbose)))
        except Exception as exc:  # noqa: BLE001
            print(f"   {R}ERROR{OFF} {type(exc).__name__}: {exc}")
            totals.append((sid, 0, 1, 0.0))

    print(f"\n{B}{'═' * 78}\nSUMMARY{OFF}")
    tp = tt = 0
    tc = 0.0
    for sid, p, t, c in totals:
        tp, tt, tc = tp + p, tt + t, tc + c
        mark = f"{G}ok{OFF}" if p == t else f"{R}{t - p} failed{OFF}"
        print(f"   {sid:22} {p:>2}/{t:<2}  ${c:.4f}   {mark}")
    print(f"\n   {B}{tp}/{tt} checks passed{OFF}   total ${tc:.4f}")
    return 0 if tp == tt else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
