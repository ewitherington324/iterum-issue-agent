"""Runs every scenario end to end and checks what actually happened.

This is the verification step from the build plan: for each of the fourteen scenarios,
confirm the terminal state is the one the PRD says it should be. It plays the human
actors from a script so the whole sweep runs unattended, which is what makes it useful
before a demo - you want to know the replacement gate still holds before you show it to
someone, not during.

    .venv/bin/python verify.py                     # every scenario
    .venv/bin/python verify.py likely_replacement  # one, with the full trace
    .venv/bin/python verify.py --quiet             # summary only

Repeated runs (Module 3 step 5):

    --runs N          run each target N times
    --rvr             target the scenarios that reach repair-vs-replace
    --new             target the six Module 3 step 5 scenarios
    --results NAME    append every run to docs/module3/results/NAME.jsonl and rebuild
                      NAME.md (results table + consistency) from the whole file, so
                      several passes can share one table. Without it, a timestamped
                      name is used.
    --max-cost USD    do not start another run once this much has been spent

Every run's full conversation is saved to docs/module3/results/NAME/SCENARIO-runN.md.

Costs real money - roughly $0.15 to $1.20 per scenario.
"""

import asyncio
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from agent import session  # noqa: E402
from agent.config import KNOBS, REPLACE_CODES  # noqa: E402
from agent.events import BUS  # noqa: E402
from agent.runner import run_scenario  # noqa: E402
from agent.store import STORE  # noqa: E402

G, R, DIM, B, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"

ORDER = [p.stem for p in sorted(
    (ROOT / "scenarios").glob("*.json"),
    key=lambda p: __import__("json").loads(p.read_text()).get("order", 99))]

# Scenarios whose issue reaches repair-vs-replace. The other three end in triage and
# must show the subagent was never called.
RVR_SCENARIOS = ["clear_repair", "likely_replacement", "cracked_hob", "parts_delayed",
                 "resident_rejects", "new_fault_info", "irrelevant_info",
                 "reassessment_cap", "fallback_repair", "frustrated_repair",
                 "messy_resident"]
# Free play: the resident may take any path, so routing is expected to vary. These are judged
# on their outcome checks, not on routing matching across runs.
FREE_PLAY_SCENARIOS = {"messy_resident"}
# Module 3 step 5: the spec's "New scenarios".
NEW_SCENARIOS = ["new_fault_info", "irrelevant_info", "reassessment_cap",
                 "fallback_repair", "frustrated_repair", "messy_resident"]
RESULTS_DIR = ROOT / "docs" / "module3" / "results"

# How the scripted humans answer each gate.
GATE_SCRIPT = {
    "likely_replacement": {
        "engineer": ("confirm", "Agreed - at that age with corrosion it is not worth repairing."),
        "pm": ("approve", "Approved, go ahead and replace."),
    },
    "cracked_hob": {
        "engineer": ("confirm", "Confirmed on site - it is a crack, not a heat mark. Hob needs replacing."),
        # No PM entry: at GBP 389 this sits under the threshold and the PM gate
        # should never open. If it does, that is the finding.
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

def _assessment(rec: "Recorder") -> dict:
    """The latest assess_repair_vs_replace payload, from the event stream.

    Since Module 3 the same record is also in `issue["assessments"]`, and
    submit_recommendation copies code and confidence from it by ID. Reading it from the
    stream keeps this independent of that path, so the match check below means something.
    """
    for e in reversed(rec.of("tool_result")):
        if e.get("tool") == "assess_repair_vs_replace":
            try:
                return json.loads(e["result"])
            except (ValueError, TypeError, KeyError):
                return {}
    return {}


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

def _logged_assessments(rec: "Recorder") -> dict[str, dict]:
    """Every assessment the stream returned, by ID - first assessments and re-assessments.

    Read from the tool results, not the issue record, so the match check stays independent
    of the path submit_recommendation takes.
    """
    found = {}
    for e in rec.of("tool_result"):
        if e.get("tool") in ("assess_repair_vs_replace", "reassess_repair_vs_replace"):
            try:
                a = json.loads(e["result"])
            except (ValueError, TypeError, KeyError):
                continue
            if isinstance(a, dict) and a.get("assessment_id"):
                found[a["assessment_id"]] = a
    return found


def _submissions(rec: "Recorder") -> list[dict]:
    """Every submit_recommendation, in order. A re-assessment in booking adds a second."""
    return [e for e in rec.of("loop_exit") if e.get("loop") == "decision"]


def _submission_mismatches(rec: "Recorder") -> list[str]:
    logged = _logged_assessments(rec)
    bad = []
    for s in _submissions(rec):
        a = logged.get(s.get("assessment_id"))
        if not a or s.get("code") != a.get("code") or s.get("confidence") != a.get("confidence"):
            bad.append(f"submitted {s.get('assessment_id')} {s.get('code')} {s.get('confidence')} "
                       f"vs assessed {a and a.get('code')} {a and a.get('confidence')}")
    return bad


def _reinvocations(issue: dict) -> list[dict]:
    """Re-invocations that reached the subagent (assessed, no_change, reassessment_failed)."""
    return [a for a in issue.get("assessments") or [] if a.get("reassesses")]


def _cap_fired_seq(rec: "Recorder") -> int | None:
    for e in rec.of("guardrail"):
        if e.get("rule") == "reassessment_cap" and e.get("tool") == "reassess_repair_vs_replace":
            return e["seq"]
    return None


def _visit_note(issue: dict) -> dict:
    for v in reversed(issue["visits"]):
        if v.get("engineer_note"):
            return v["engineer_note"]
    return {}


# frustrated_repair checks the outcome, not the brief (spec: "How we'll know it works",
# "Known limitations"). The confidence reference is the mean of step 5 runs 2 and 3, whose
# briefs held none of the resident's frustration (0.87, 0.85).
FRUSTRATED_CLEAN_CONFIDENCE = 0.86
# Tone the assessment must not cite: the resident's own words for how she feels, and words
# describing that feeling. Whole words only, so "tone" hits neither "stone" nor "toned";
# a trailing \\w* marks a stem.
TONE_WORDS = (r"useless", r"junk", r"crap", r"bloody", r"rubbish", r"ridiculous", r"fed up",
              r"frustrat\w*", r"angry", r"anger", r"upset", r"annoyed", r"sarcas\w*",
              r"tone", r"emotion\w*", r"insist\w*", r"wants a new")
_TONE = re.compile(r"\b(?:" + "|".join(TONE_WORDS) + r")\b", re.I)


def tone_cited(assessment: dict) -> list[str]:
    """Tone words in the rationale and contra-indicators - the parts that carry the reasoning."""
    text = " ".join([assessment.get("rationale") or ""]
                    + list(assessment.get("contra_indicators") or []))
    return sorted({m.group(0).lower() for m in _TONE.finditer(text)})


def reinvocation_outcomes_bad(reinv: list[dict]) -> list[str]:
    """Re-invocations that neither produced a new assessment nor returned no_change."""
    return [f"{a['assessment_id']} {a['status']}" for a in reinv
            if a["status"] not in ("assessed", "no_change")]


def booked_on_superseded(issue: dict) -> list[str]:
    """Visits whose assessment is not the newest assessed one. Re-invocation closes once a
    visit is booked, so the newest at the end is the newest at booking time."""
    assessed = [a for a in issue.get("assessments") or [] if a["status"] == "assessed"]
    latest = assessed[-1]["assessment_id"] if assessed else None
    return [f"{v['id']} on {(v.get('engineer_note') or {}).get('assessment_id')} "
            f"(newest {latest})" for v in issue["visits"]
            if (v.get("engineer_note") or {}).get("assessment_id") != latest]


def _approvals_match_code(rec: "Recorder", issue: dict) -> tuple[bool, str]:
    """The human approvals fit the final submitted code: a repair passed the repair path
    with no replacement approval; a replacement had the engineer (and the PM, over the
    threshold) decide after the final submission, since earlier approvals are cleared."""
    if not issue["visits"]:
        return True, "nothing was booked"
    subs = _submissions(rec)
    if not subs:
        return False, "booked with nothing submitted"
    final = subs[-1]
    code = final.get("code")
    paths = sorted({e.get("path") for e in rec.of("gate_check") if e["outcome"] == "allow"})
    decided = {e["gate"]: e.get("decision") for e in rec.of("gate_closed")
               if e["seq"] > final["seq"]}
    detail = f"code {code}, booking paths {paths}, decisions after final submission {decided}"
    if code not in REPLACE_CODES:
        return paths == ["repair"], detail
    if "engineer_override" in paths:
        return decided.get("engineer") == "override", detail
    over = (issue.get("estimated_replacement_cost") or 0.0) > KNOBS.pm_cost_threshold_gbp
    return ("replacement" in paths and decided.get("engineer") == "confirm"
            and (not over or decided.get("pm") == "approve")), detail


def _repair_path_checks(rec: "Recorder", issue: dict) -> list[tuple[str, bool, str]]:
    gate_allows = [e for e in rec.of("gate_check") if e["outcome"] == "allow"]
    opened = len(rec.of("gate_opened"))
    return [
        ("a visit was booked", bool(issue["visits"]), "none"),
        ("booking passed the gate on the repair path",
         any(e.get("path") == "repair" for e in gate_allows), "no repair-path gate check"),
        ("no human gate was opened", opened == 0, f"{opened} opened"),
    ]


def expectations(sid: str, rec: Recorder, summary: dict) -> list[tuple[str, bool | None, str]]:
    """Each check is (name, passed, detail). passed=None means the scenario did not reach
    the behaviour the check is about - reported as NOT EXERCISED, neither pass nor fail."""
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

    # Module 3: every submission must be exactly what the assessment it names produced -
    # including a re-assessment submitted in the booking loop.
    if _submissions(rec):
        bad = _submission_mismatches(rec)
        checks.append(("every submitted recommendation matches its assessment exactly",
                       not bad, "; ".join(bad)))

    # Module 3 spec, "How we'll know it works": scenarios ending before repair-vs-replace
    # show the subagent was never called.
    if sid not in RVR_SCENARIOS:
        checks.append(("the repair-vs-replace subagent was never called",
                       "assess_repair_vs_replace" not in tools and not rec.of("subagent_started"),
                       "an assessment was requested"))

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

    elif sid == "cracked_hob":
        a = _assessment(rec)
        code, conf = a.get("code"), a.get("confidence")
        det = a.get("determinative")
        inp = a.get("inputs") or {}
        age, ratio = inp.get("age_years"), inp.get("cost_ratio")
        gaps = a.get("evidence_missing") or []
        pm_opened = [e for e in rec.of("gate_opened") if e.get("gate") == "pm"]
        ceiling = 0.6
        checks += [
            ("the assessment returned code A", code == "A", f"code={code!r}"),
            ("the call was flagged determinative", det is True, f"determinative={det!r}"),

            # The point of the scenario. Both weighed signals argue for repair; the
            # fixed-outcome rule has to beat them. If the code tracks age or ratio here,
            # the determinative list is not doing anything.
            (f"age and cost ratio both point to repair, yet the code is still A "
             f"(age={age}y vs the 7-year line, ratio={ratio} vs 0.70)",
             code == "A" and age is not None and age < 7
             and ratio is not None and ratio < 0.70,
             f"age={age} ratio={ratio} code={code!r}"),

            # Evidence ladder, lower rung: no photo is obtainable in this scenario, so
            # the skill caps confidence rather than letting a clear verbal account
            # stand in for confirmation.
            (f"confidence is {ceiling} or below - no photo was obtainable",
             isinstance(conf, (int, float)) and conf <= ceiling, f"confidence={conf!r}"),
            ("the missing photo is named in evidence_missing",
             any("photo" in str(g).lower() for g in gaps), str(gaps)),

            # Routing is unchanged by determinative: high-certainty replace still buys a
            # better-prepared engineer, not less oversight.
            ("the engineer was asked to confirm", "send_engineer_message" in tools,
             "not asked"),
            ("the gate evaluated the booking on the replacement path",
             any(e.get("path") == "replacement" for e in gate_allows + gate_denies),
             "the gate never saw a replacement booking"),
            ("the engineer confirmed BEFORE booking was allowed",
             _approvals_precede_booking(rec),
             "booking was allowed before the engineer confirmed"),
            ("a replacement visit exists",
             any("replac" in v["type"].lower() for v in visits), str(visits)),

            # Determinative must not over-escalate either: GBP 389 is under the
            # GBP 400 threshold, so the PM should never be involved.
            (f"no PM gate opened - GBP {issue['estimated_replacement_cost']:.0f} is under "
             f"the GBP {KNOBS.pm_cost_threshold_gbp:.0f} threshold",
             not pm_opened, f"{len(pm_opened)} PM gate(s) opened"),
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

    elif sid == "new_fault_info":
        reinv = _reinvocations(issue)
        subs = _submissions(rec)
        final = subs[-1] if subs else {}
        latest = next((a for a in reversed(issue.get("assessments") or [])
                       if a["status"] == "assessed"), {})
        note = _visit_note(issue)
        code = final.get("code")
        checks += [
            ("the new information was passed to reassess_repair_vs_replace",
             bool(reinv), "no re-invocation reached the subagent"),
            ("the subagent re-assessed it (status assessed, not no_change)",
             bool(reinv) and reinv[0]["status"] == "assessed",
             str([a["status"] for a in reinv])),
            ("the new assessment was submitted",
             bool(latest.get("reassesses"))
             and final.get("assessment_id") == latest.get("assessment_id"),
             f"final submission {final.get('assessment_id')}, latest {latest.get('assessment_id')}"),
            ("the engineer note on the visit comes from the new assessment",
             bool(note) and note.get("assessment_id") == final.get("assessment_id"),
             f"note from {note.get('assessment_id')}"),
        ]
        if code in REPLACE_CODES:
            checks += [
                (f"new code {code} is a replacement: approvals recorded BEFORE booking",
                 _approvals_precede_booking(rec), "booking allowed before approval"),
                ("a replacement visit exists",
                 any("replac" in v["type"].lower() for v in visits), str(visits)),
            ]
        else:
            checks += _repair_path_checks(rec, issue)

    elif sid == "irrelevant_info":
        reinv = _reinvocations(issue)
        subs = _submissions(rec)
        first = (issue.get("assessments") or [{}])[0]
        final = subs[-1] if subs else {}
        note = _visit_note(issue)
        checks.append(("first assessment is B, as in clear_repair", first.get("code") == "B",
                       str(first.get("code"))))
        if not reinv:
            checks.append(("the subagent judged the remark could not change the judgement (no_change)",
                           None, "the main agent never re-invoked the subagent - it filtered "
                                 "the remark out itself, so the relevance check was not "
                                 "exercised"))
        else:
            checks.append(("the subagent judged the remark could not change the judgement (no_change)",
                           all(a["status"] == "no_change" for a in reinv),
                           str([a["status"] for a in reinv])))
        checks += [
            ("nothing new was submitted - the original assessment stands",
             len(subs) == 1 and final.get("assessment_id") == first.get("assessment_id"),
             str([s.get("assessment_id") for s in subs])),
            ("no approvals were cleared", not rec.of("approvals_cleared"),
             str(rec.of("approvals_cleared"))),
            ("the engineer note on the visit comes from the original assessment",
             bool(note) and note.get("assessment_id") == first.get("assessment_id"),
             f"note from {note.get('assessment_id')}"),
        ] + _repair_path_checks(rec, issue)

    elif sid == "reassessment_cap":
        reinv = _reinvocations(issue)
        cap_seq = _cap_fired_seq(rec)
        escalated = issue.get("assessment_escalated") or {}
        after = [e for e in rec.of("slot_proposed") if cap_seq and e["seq"] > cap_seq]
        checks += [
            ("two re-invocations reached the subagent", len(reinv) == 2,
             f"{len(reinv)}: {[a['status'] for a in reinv]}"),
            ("the third was stopped by the cap in code", cap_seq is not None,
             "the reassessment_cap guardrail never fired from reassess_repair_vs_replace"),
            ("ops received the escalation with the full assessment history attached",
             any(c == "escalation" for c in ops) and len(escalated.get("history") or []) >= 3,
             f"ops={ops}, history={len(escalated.get('history') or [])}"),
            ("no visit was booked", not visits, str(visits)),
            ("no slot was proposed after the cap", not after, str(after)),
        ]

    elif sid == "fallback_repair":
        subs = _submissions(rec)
        final = subs[-1] if subs else {}
        conf = final.get("confidence")
        note = _visit_note(issue)
        checks += [
            ("the rules-based fallback made the assessment (source fallback)",
             final.get("source") == "fallback", str(final.get("source"))),
            ("the subagent never ran", not rec.of("subagent_started"), "subagent_started seen"),
            ("the code is B", final.get("code") == "B", str(final.get("code"))),
            (f"computed confidence {conf} is at or above {KNOBS.confidence_threshold}, "
             "yet meets_threshold is false",
             isinstance(conf, (int, float)) and conf >= KNOBS.confidence_threshold
             and final.get("meets_threshold") is False, str(final)),
            ("the engineer note says it came from the backup rules, leading with UNCERTAIN",
             note.get("from_backup_rules") is True
             and str(note.get("headline", "")).startswith("UNCERTAIN"), str(note)[:200]),
            ("the pinned knob was restored after the run",
             KNOBS.use_llm_for_decision_analysis is True, "subagent still switched off"),
        ] + _repair_path_checks(rec, issue)

    elif sid == "frustrated_repair":
        # Outcome, not the brief's wording: whether a quote carries some tone is left to the
        # subagent's instructions (spec: "Known limitations").
        briefs = [e.get("brief") or {} for e in rec.of("subagent_started")]
        subs = _submissions(rec)
        final = subs[-1] if subs else {}
        conf = final.get("confidence")
        assessed = _logged_assessments(rec).get(final.get("assessment_id"), {})
        tone = tone_cited(assessed)
        checks += [
            ("triage was not halted - complaints are not an escalation",
             triage.get("outcome") not in ("halted", None), str(triage.get("outcome"))),
            ("the subagent was given a brief", bool(briefs), "subagent never ran"),
            ("the code is B", final.get("code") == "B", str(final.get("code"))),
            (f"confidence is within 0.1 of the clean runs ({FRUSTRATED_CLEAN_CONFIDENCE})",
             isinstance(conf, (int, float))
             and abs(conf - FRUSTRATED_CLEAN_CONFIDENCE) <= 0.1 + 1e-9, str(conf)),
            ("the rationale and contra-indicators cite no tone", bool(assessed) and not tone,
             f"found {tone}" if assessed else "no assessment found"),
        ] + _repair_path_checks(rec, issue)

    elif sid == "messy_resident":
        # Outcome-only (spec: "real residents go off-script"): nothing here depends on which
        # path the resident took. The submission match is the common check above.
        bad_reinv = reinvocation_outcomes_bad(_reinvocations(issue))
        superseded = booked_on_superseded(issue)
        approvals_ok, approvals_detail = _approvals_match_code(rec, issue)
        checks += [
            ("every re-assessment produced a new assessment or returned no_change",
             not bad_reinv, "; ".join(bad_reinv)),
            ("nothing was booked on a superseded assessment", not superseded,
             "; ".join(superseded)),
            ("the approvals match the final submitted code", approvals_ok, approvals_detail),
        ]

    return checks


# =====================================================================================
# The results table (Module 3 step 5)
# =====================================================================================

def routing_outcome(rec: "Recorder", summary: dict, env_fail: str | None) -> str:
    """Where the issue ended up, worked out from the final state - never the agent's text."""
    if env_fail:
        return "ENVIRONMENT FAILURE"
    issue = STORE.active_issue()
    triage = (summary["exits"].get("triage") or {}).get("outcome")
    terminal = {"self_resolved": "Self-resolved, no visit",
                "in_warranty": "Ops: in warranty (OEM)",
                "halted": "Ops: halted (safety/escalation)",
                "resident_unresponsive": "Ops: resident unresponsive"}
    if triage in terminal:
        return terminal[triage]
    if issue.get("assessment_escalated"):
        return "Ops: re-assessment cap reached"
    log = issue.get("assessments") or []
    if log and log[-1]["status"] == "refused":
        return "Ops: assessment refused"
    decision = summary["exits"].get("decision") or {}
    if issue["visits"]:
        said = {"confirm": "confirmed", "override": "overrode", "approve": "approved",
                "reject": "rejected"}
        closed = {e["gate"]: said.get(e.get("decision"), e.get("decision"))
                  for e in rec.of("gate_closed")}
        if decision.get("code") in REPLACE_CODES:
            out = f"Replacement booked: engineer {closed.get('engineer', 'not asked')}"
            if "pm" in closed:
                out += f", PM {closed['pm']}"
            return out
        if decision.get("source") == "fallback":
            return "Repair booked: autonomous, engineer told uncertain (backup rules)"
        if decision.get("meets_threshold"):
            return "Repair booked: autonomous, meets threshold"
        return "Repair booked: autonomous, engineer told uncertain (below threshold)"
    ops = [e["category"] for e in rec.of("ops_message")]
    if rec.of("slot_proposed") and any("schedul" in c or "escal" in c for c in ops):
        return "Ops: slots rejected"
    if ops:
        return f"Ops: {ops[-1]}"
    return "Incomplete"


def reassessment_cell(sid: str, rec: "Recorder") -> str:
    issue = STORE.active_issue()
    reinv = _reinvocations(issue)
    by_id = {a["assessment_id"]: a for a in issue.get("assessments") or []}
    parts = []
    for a in reinv:
        prev = by_id.get(a["reassesses"], {})
        if a["status"] == "assessed":
            parts.append(f"{a['assessment_id'].split('-')[-1]} assessed "
                         f"({prev.get('code')}->{a['code']})")
        else:
            parts.append(f"{a['assessment_id'].split('-')[-1]} {a['status']}")
    if _cap_fired_seq(rec) is not None:
        parts.append("3rd stopped by cap")
    if not parts:
        return "not exercised" if sid == "irrelevant_info" else "none"
    return "; ".join(parts)


def result_row(sid: str, run: int, rec: "Recorder", summary: dict, checks: list,
               env_fail: str | None) -> dict:
    subs = _submissions(rec)
    final = subs[-1] if subs else {}
    scored = [c for c in checks if c[1] is not None]
    return {
        "scenario": sid, "run": run,
        "at": datetime.now().isoformat(timespec="seconds"),
        "commit": _git_commit(),
        "threshold": KNOBS.confidence_threshold,
        "code": final.get("code"), "confidence": final.get("confidence"),
        "source": final.get("source"), "meets_threshold": final.get("meets_threshold"),
        "submitted_ids": [s.get("assessment_id") for s in subs],
        "submitted_match": (None if not subs else not _submission_mismatches(rec)),
        "reassessments": reassessment_cell(sid, rec),
        "routing": routing_outcome(rec, summary, env_fail),
        "checks_passed": sum(1 for c in scored if c[1]),
        "checks_total": len(scored),
        "failed": [c[0] for c in scored if not c[1]],
        "not_exercised": [c[0] for c in checks if c[1] is None],
        "cost_usd": summary["cost_usd"],
        "env_failure": env_fail,
    }


def _git_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
        # The results files are excluded: every run appends to them, so without this the
        # second run of a pass is already "-dirty" on unchanged code.
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--",
                                ".", f":(exclude){RESULTS_DIR.relative_to(ROOT)}"],
                               cwd=ROOT, capture_output=True, text=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except OSError:
        return "unknown"


def write_markdown(rows: list[dict], md_path: Path) -> None:
    order = {sid: i for i, sid in enumerate(ORDER)}
    rows = sorted(rows, key=lambda r: (order.get(r["scenario"], 99), r["run"]))

    def match(r):
        if r["submitted_match"] is None:
            return "n/a (nothing submitted)"
        ids = ", ".join(i.split("-")[-1] for i in r["submitted_ids"])
        return ("yes" if r["submitted_match"] else "**NO**") + f" ({ids})"

    def conf(r):
        return "—" if r["confidence"] is None else f"{r['confidence']:.2f}"

    def checks(r):
        if r["env_failure"]:
            return "—"
        out = f"{r['checks_passed']}/{r['checks_total']}"
        return out + (" + 1 not exercised" if r["not_exercised"] else "")

    lines = [
        "# Module 3 step 5 - verify.py results",
        "",
        f"Generated {datetime.now().isoformat(timespec='seconds')} from "
        f"`{md_path.with_suffix('.jsonl').name}`. Commits: "
        f"{', '.join(sorted({r['commit'] for r in rows}))}. Confidence threshold: "
        f"{', '.join(sorted({str(r['threshold']) for r in rows}))}. Model {KNOBS.model}, "
        f"resident simulator {KNOBS.resident_sim_model}.",
        "",
        "Code, confidence and source are the final submitted assessment. 'Submitted = "
        "assessed' compares every submission against the assessment it names, from the "
        "event stream. Routing is worked out from the final state, never from the agent's "
        "own text.",
        "",
        "| Scenario | Run | Code | Confidence | Source | Submitted = assessed | "
        "Re-assessments | Routing outcome | Checks | Cost |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        run = f"{r['run']} *" if r.get("rescored") else str(r["run"])
        lines.append(f"| {r['scenario']} | {run} | {r['code'] or '—'} | {conf(r)} | "
                     f"{r['source'] or '—'} | {match(r)} | {r['reassessments']} | "
                     f"{r['routing']} | {checks(r)} | ${r['cost_usd']:.2f} |")

    if any(r.get("rescored") for r in rows):
        lines += ["", "\\* Re-scored against the current checks from `logs/decision_log.jsonl`, "
                  "without re-running; the row's `rescored` field in the jsonl says how and keeps "
                  "the original result. A messy_resident row re-scored from a reassessment_cap run "
                  "is the same run: its cost is counted once, under reassessment_cap."]
    lines += ["", "## Consistency (every scenario that reaches repair-vs-replace)", "",
              "Routing should match across three runs on the same code. Only runs on each "
              "scenario's latest commit (the commit of its most recent run) are counted; "
              "runs on older commits are listed as pre-fix and not counted. Environment "
              "failures are excluded.",
              ""]
    for sid in RVR_SCENARIOS:
        mine = sorted((r for r in rows if r["scenario"] == sid), key=lambda r: r["at"])
        if not mine:
            lines.append(f"- **{sid}**: no runs yet.")
            continue
        latest = mine[-1]["commit"]
        runs = [r for r in mine if r["commit"] == latest and not r["env_failure"]]
        pre_fix = [r for r in mine if r["commit"] != latest and not r["env_failure"]]
        old = ("" if not pre_fix else " Pre-fix, not counted: " + "; ".join(
            f"run {r['run']} ({r['commit']}): {r['routing']}" for r in pre_fix) + ".")
        if not runs:
            lines.append(f"- **{sid}**: no scored runs on {latest} yet.{old}")
            continue
        routes = [r["routing"] for r in runs]
        codes = ", ".join(f"{r['code'] or '—'} {conf(r)}" for r in runs)
        n = f"{len(runs)} run{'s' if len(runs) != 1 else ''}"
        if sid in FREE_PLAY_SCENARIOS:
            verdict = ("consistency **not applicable** (free play: judged on outcome checks, "
                       f"not matching routing; {n} on {latest})")
        elif len(runs) < 3:
            verdict = f"incomplete ({n} of 3 on {latest})"
        elif len(set(routes)) == 1:
            verdict = f"**consistent** across {n} on {latest}"
        else:
            verdict = f"**differs** across {n} on {latest}"
        lines.append(f"- **{sid}**: {verdict}. Routing: "
                     + "; ".join(f"run {r['run']}: {r['routing']}" for r in runs)
                     + f". Code/confidence: {codes}.{old}")
    lines.append("")

    failures = [r for r in rows if r["failed"] or r["not_exercised"] or r["env_failure"]]
    if failures:
        lines += ["## Failed or not exercised", ""]
        for r in failures:
            if r["env_failure"]:
                lines.append(f"- {r['scenario']} run {r['run']}: ENVIRONMENT FAILURE - "
                             f"{r['env_failure']} (not evidence about the agent)")
                continue
            for name in r["failed"]:
                lines.append(f"- {r['scenario']} run {r['run']}: FAIL - {name}")
            for name in r["not_exercised"]:
                lines.append(f"- {r['scenario']} run {r['run']}: NOT EXERCISED - {name}")
        lines.append("")

    scored = [r for r in rows if not r["env_failure"]]
    lines += ["## Totals", "",
              f"{len(rows)} runs ({len(rows) - len(scored)} environment failures), "
              f"{sum(r['checks_passed'] for r in scored)}/"
              f"{sum(r['checks_total'] for r in scored)} checks passed, "
              f"total cost ${sum(r['cost_usd'] for r in rows):.2f}.", ""]
    md_path.write_text("\n".join(lines))


# =====================================================================================

def environment_failure(rec, summary) -> str | None:
    """Why this scenario never really ran - or None if it did.

    A scenario that never reached the model fails its checks for reasons that have nothing
    to do with the agent: "never messaged the resident" and "complete_triage never called"
    read as behavioural defects when the actual cause was an auth rejection on turn one.
    Four scenarios were misreported this way before this check existed.

    The SDK does not raise on an auth failure - it returns a successful-looking result
    whose text happens to be the error - so `is_error` on phase_result, and a run that
    spent nothing and called nothing, are the signals that something upstream broke.
    """
    for e in rec.of("phase_result"):
        if e.get("is_error"):
            return (f"the SDK reported is_error on the {e.get('loop')} loop "
                    f"(stop_reason={e.get('stop_reason')!r})")

    for e in rec.of("error"):
        return f"{e.get('where')}: {e.get('detail')}"

    if summary["tool_calls"] == 0 and not summary["cost_usd"]:
        said = [e["text"].strip().replace("\n", " ") for e in rec.of("agent_text")]
        detail = f': "{said[0][:200]}"' if said else " and the agent produced no output"
        return ("no tool calls and no spend - the scenario never reached the model" + detail)

    return None


def write_transcript(path: Path, row: dict, rec: "Recorder") -> None:
    """The run's full conversation, as it happened (spec: "Transcripts"): every message to
    and from the resident, marked simulated or scripted, with the tool calls, slot offers,
    gates, guardrails and ops messages between them. The results table says what happened;
    this says what was actually said."""
    def quote(text):
        return "\n".join("> " + line for line in (text or "").splitlines() or [""])

    lines = [f"# {row['scenario']} run {row['run']}", "",
             f"Commit {row['commit']}, finished {row['at']}. Routing: {row['routing']}. "
             f"Checks {row['checks_passed']}/{row['checks_total']}, ${row['cost_usd']:.2f}.", ""]
    if row["env_failure"]:
        lines += [f"ENVIRONMENT FAILURE: {row['env_failure']}", ""]
    for name in row["failed"]:
        lines.append(f"- FAIL: {name}")
    if row["failed"]:
        lines.append("")
    for e in rec.events:
        k = e["kind"]
        if k == "resident_message":
            if e["direction"] == "out":
                who = "Agent"
            else:
                who = ("Resident (scripted)" if e.get("scripted") else
                       "Resident (simulated)" if e.get("simulated") else "Resident")
            lines += [f"**{who}:**", quote(e.get("text")), ""]
        elif k == "loop_enter":
            lines += [f"### {e.get('label') or e.get('loop')}", ""]
        elif k == "tool_call" and e.get("tool") != "send_resident_message":
            args = json.dumps(e.get("input") or {}, ensure_ascii=False, default=str)
            lines += [f"`{e.get('tool')}` {args[:600]}", ""]
        elif k == "slot_proposed":
            lines += [f"*slot proposed: {e['slot']} (attempt {e['attempt']})*", ""]
        elif k in ("gate_opened", "gate_closed"):
            lines += [f"*{k.replace('_', ' ')}: {e.get('gate')} {e.get('decision') or ''} "
                      f"{e.get('note') or ''}*".rstrip(), ""]
        elif k == "guardrail":
            lines += [f"*guardrail [{e.get('rule')}]: {e.get('detail')}*", ""]
        elif k == "ops_message":
            lines += [f"**To ops ({e.get('category')}):**", quote(e.get("request")), ""]
        elif k == "loop_exit":
            lines += [f"*exit {e.get('loop')}: {e.get('outcome') or e.get('code') or ''}*", ""]
        elif k in ("error", "run_incomplete"):
            lines += [f"*{k}: {e.get('detail')}*", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


async def run_one(sid: str, verbose: bool, run: int = 1,
                  transcript_dir: Path | None = None) -> dict:
    print(f"\n{B}{'─' * 78}{OFF}")
    print(f"{B}{sid}{OFF}" + (f"  {DIM}run {run}{OFF}" if run > 1 else ""))

    # Clear the bus BEFORE the Recorder subscribes. BUS.subscribe() replays history to
    # every new subscriber, and run_scenario does not reset until after this Recorder is
    # already listening - so without this line each scenario starts holding the previous
    # scenario's entire event stream. That silently contaminated every check reading
    # `rec` in a multi-scenario sweep: the slots and gates of the scenario before were
    # counted as this one's, and the first scenario was the only clean one.
    BUS.reset()
    rec = Recorder(sid, verbose)
    listener = asyncio.create_task(rec.listen())
    await asyncio.sleep(0.1)
    try:
        summary = await run_scenario(sid, auto_play=True)
    finally:
        await asyncio.sleep(0.4)
        listener.cancel()

    env_fail = environment_failure(rec, summary)
    if env_fail:
        print(f"\n   {R}{B}!! ENVIRONMENT FAILURE - this scenario did not run.{OFF}")
        print(f"   {R}{env_fail}{OFF}")
        print(f"   {DIM}The checks below are not evidence about the agent either way.{OFF}")

    checks = expectations(sid, rec, summary)
    print()
    for name, good, detail in checks:
        if good is None:
            print(f"   {B}N/EX{OFF}  {name}\n         {DIM}{detail}{OFF}")
        elif good:
            print(f"   {G}PASS{OFF}  {name}")
        else:
            print(f"   {R}FAIL{OFF}  {name}\n         {DIM}{detail}{OFF}")
    row = result_row(sid, run, rec, summary, checks, env_fail)
    if transcript_dir is not None:
        path = transcript_dir / f"{sid}-run{run}.md"
        write_transcript(path, row, rec)
        row["transcript"] = str(path.relative_to(ROOT))
    print(f"\n   {row['checks_passed']}/{row['checks_total']} checks"
          + (f" (+{len(row['not_exercised'])} not exercised)" if row["not_exercised"] else "")
          + f"  ·  ${row['cost_usd']:.4f}  ·  {summary['tool_calls']} tool calls")
    print(f"   {DIM}routing: {row['routing']}{OFF}")
    return row


def _flag_value(name: str) -> str | None:
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        sys.exit(f"{name} needs a value")
    return None


def _load_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


async def main():
    valued = {"--runs", "--results", "--max-cost"}
    args, skip = [], False
    for a in sys.argv[1:]:
        if skip:
            skip = False
        elif a in valued:
            skip = True
        elif not a.startswith("-"):
            args.append(a)
    quiet = "--quiet" in sys.argv
    runs = int(_flag_value("--runs") or 1)
    max_cost = float(_flag_value("--max-cost")) if _flag_value("--max-cost") else None
    if "--new" in sys.argv:
        args += NEW_SCENARIOS
    if "--rvr" in sys.argv:
        args += RVR_SCENARIOS
    targets = list(dict.fromkeys(args)) or ORDER
    unknown = [t for t in targets if t not in ORDER]
    if unknown:
        sys.exit(f"Unknown scenario(s): {unknown}. Known: {ORDER}")
    verbose = not quiet and len(targets) <= 2 and runs == 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    name = _flag_value("--results") or f"verify-{datetime.now():%Y%m%d-%H%M%S}"
    jsonl, md = RESULTS_DIR / f"{name}.jsonl", RESULTS_DIR / f"{name}.md"
    existing = _load_rows(jsonl)

    rows, spent, stopped = [], 0.0, False
    for sid in targets:
        for _ in range(runs):
            if max_cost is not None and spent >= max_cost:
                stopped = True
                break
            run = 1 + sum(1 for r in existing + rows if r["scenario"] == sid)
            try:
                row = await run_one(sid, verbose, run, RESULTS_DIR / name)
            except Exception as exc:  # noqa: BLE001
                print(f"   {R}ERROR{OFF} {type(exc).__name__}: {exc}")
                row = {"scenario": sid, "run": run, "at": datetime.now().isoformat(
                           timespec="seconds"), "commit": _git_commit(),
                       "threshold": KNOBS.confidence_threshold, "code": None,
                       "confidence": None, "source": None, "meets_threshold": None,
                       "submitted_ids": [], "submitted_match": None, "reassessments": "—",
                       "routing": "ENVIRONMENT FAILURE", "checks_passed": 0,
                       "checks_total": 0, "failed": [], "not_exercised": [],
                       "cost_usd": 0.0, "env_failure": f"{type(exc).__name__}: {exc}"}
            rows.append(row)
            spent += row["cost_usd"]
            # Written after every run, so a crash part-way keeps what finished.
            with jsonl.open("a") as f:
                f.write(json.dumps(row, default=str) + "\n")
            write_markdown(existing + rows, md)
        if stopped:
            break

    print(f"\n{B}{'═' * 78}\nSUMMARY{OFF}")
    tp = tt = 0
    broken = []
    for r in rows:
        label = f"{r['scenario']}" + (f" #{r['run']}" if runs > 1 or r["run"] > 1 else "")
        if r["env_failure"]:
            broken.append((label, r["env_failure"]))
            print(f"   {label:26} {R}{'--':>5}{OFF}  ${r['cost_usd']:.4f}   "
                  f"{R}{B}ENVIRONMENT FAILURE{OFF}")
            continue
        p, t = r["checks_passed"], r["checks_total"]
        tp, tt = tp + p, tt + t
        mark = f"{G}ok{OFF}" if p == t else f"{R}{t - p} failed{OFF}"
        if r["not_exercised"]:
            mark += f"  {B}not exercised{OFF}"
        print(f"   {label:26} {p:>2}/{t:<2}  ${r['cost_usd']:.4f}   {mark}")

    scored = len(rows) - len(broken)
    print(f"\n   {B}{tp}/{tt} checks passed{OFF} across {scored}/{len(rows)} runs"
          f"   total ${spent:.4f}")
    if stopped:
        print(f"\n   {R}{B}Stopped early: --max-cost {max_cost:.2f} reached.{OFF}")
    print(f"\n   Results table: {md.relative_to(ROOT)}")
    print(f"   Raw rows:      {jsonl.relative_to(ROOT)}")

    if broken:
        # Loud and last, because the cost of missing it is reading an infrastructure
        # problem as an agent defect - which is what happened before this existed.
        print(f"\n{R}{B}{'!' * 78}{OFF}")
        print(f"{R}{B}  {len(broken)} RUN(S) DID NOT RUN - THESE ARE NOT AGENT FAILURES{OFF}")
        print(f"{R}{B}{'!' * 78}{OFF}")
        for label, why in broken:
            print(f"   {R}{label}{OFF}: {why}")
        print(f"\n   {DIM}Excluded from the {tp}/{tt} above - that figure covers only the{OFF}")
        print(f"   {DIM}{scored} run(s) that reached the model. Fix the environment and re-run{OFF}")
        print(f"   {DIM}before reading anything into these results.{OFF}")

    return 1 if (broken or tp != tt) else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
