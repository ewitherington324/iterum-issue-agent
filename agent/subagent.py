"""The repair-vs-replace subagent (docs/module3/SUBAGENT_SPEC.md, build step 2).

An independent agent session, started from inside the assess_repair_vs_replace tool
handler. It is deliberately not an SDK `agents=` subagent: those are reached through the
built-in Task tool (which invariant 1 removes), their prompt is whatever the main agent
chooses to write, and their answer comes back to the main agent as text to relay. Here the
code builds the subagent's input, and its answer goes into the assessment log before the
main agent sees it.

Three things make the input filtered rather than merely requested:

  1. The tool schema. The main agent can pass troubleshooting steps and results, verbatim
     resident quotes and known gaps - nothing else. There is no free-text "findings" or
     summary field for a lean or a grievance to travel in. (A one-line "confirmed fault"
     summary was dropped after the first live runs: every fact in it was already in the
     quotes or the PM description, and the only thing it added was the main agent's own
     reading of the evidence - "consistent with a thermal-shock crack".)
  2. Checks in code (`check_input`). Every quote must appear in a resident message in the
     conversation log, so paraphrase is rejected; a shortened quote passes, which is how a
     grievance is trimmed off a sentence that also carries a symptom. Verdict phrases
     ("needs replacing", "beyond repair") are rejected in every field, so the main agent's
     provisional lean - or a resident's opinion - cannot arrive dressed as evidence.
  3. What code adds itself (`build_brief`): the PM's description, the confirmed fault
     category, warranty status and the cost estimates come from the store, not from the
     main agent.

What code cannot reliably tell apart - a complaint versus a symptom in the resident's own
words - is left to the main agent's instructions and to the subagent's, which say that
tone is not evidence.

The subagent's tool surface is two read-only lookups plus an exit tool, submit_assessment,
which is how its answer leaves (invariant 5: loop exits are explicit tool calls). The
exit tool validates against the same Pydantic model as before, so a weighed call with no
contra-indicators is refused and the subagent can correct it.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    PermissionResultDeny,
    ResultMessage,
    ToolAnnotations,
    create_sdk_mcp_server,
    tool,
)
from pydantic import ValidationError

from . import session, trace
from .config import KNOBS
from .events import BUS
from .reasoning import RepairVsReplace, assessment_from_model
from .skills import DECISION_SKILL, fault_reference, load_skill
from .store import STORE

ROOT = Path(__file__).resolve().parents[1]

SERVER_NAME = "rvr"
PREFIX = f"mcp__{SERVER_NAME}__"
TIMEOUT_S = 180
MAX_TURNS = 8
MAX_BUDGET_USD = 1.00

READ_ONLY = ToolAnnotations(readOnlyHint=True)


class SubagentError(RuntimeError):
    """The subagent did not produce a valid assessment. The caller falls back."""


# =====================================================================================
# Input filter
# =====================================================================================

INPUT_FIELDS = ("issue_id", "appliance_id", "troubleshooting", "resident_symptoms",
                "known_gaps")

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "issue_id": {"type": "string"},
        "appliance_id": {"type": "string"},
        "troubleshooting": {
            "type": "array",
            "description": "Each troubleshooting step the resident tried, and what "
                           "happened - what the resident observed, not what you think "
                           "it means.",
            "items": {"type": "object",
                      "properties": {"step": {"type": "string"},
                                     "result": {"type": "string"}},
                      "required": ["step", "result"],
                      "additionalProperties": False}},
        "resident_symptoms": {
            "type": "array",
            "minItems": 1,
            "description": "The resident's own words about the appliance or the fault, "
                           "copied exactly from their messages. You may shorten a quote "
                           "to the part about the appliance. Leave out complaints, "
                           "scheduling and anything else not about the fault.",
            "items": {"type": "string"}},
        "known_gaps": {
            "type": "array",
            "description": "Evidence that could not be obtained, e.g. 'no photo - the "
                           "resident has no camera'.",
            "items": {"type": "string"}},
    },
    "required": list(INPUT_FIELDS),
    "additionalProperties": False,
}

# Verdicts, not vocabulary. "I replaced the filter and it still leaks" is evidence and must
# pass; "it needs replacing" is a conclusion and must not reach the subagent as if it were.
VERDICT_PATTERNS = [
    r"\bneeds? replac\w*",
    r"\bneeds? (?:to be|a) replace\w*",
    r"\bshould be replaced\b",
    r"\breplace (?:it|the (?:whole )?(?:unit|appliance|machine|hob|oven))\b",
    r"\bbeyond (?:economic(?:al)? )?repair\b",
    r"\bnot worth\b",
    r"\bwrite[- ]?off\b",
    r"\bwritten off\b",
    r"\bnew one\b",
]
_VERDICT = re.compile("|".join(VERDICT_PATTERNS), re.I)

_QUOTE_CHARS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                              "–": "-", "—": "-"})


def normalise(text: str) -> str:
    """Case, whitespace and typographic quotes/dashes do not make a quote non-verbatim."""
    text = text.translate(_QUOTE_CHARS).casefold()
    return re.sub(r"\s+", " ", text).strip()


def _strip_quote(text: str) -> str:
    return normalise(text).strip(" \"'.,;:!?…-")


def verdicts_in(text: str) -> list[str]:
    return [m.group(0) for m in _VERDICT.finditer(text or "")]


def resident_messages(conversation: list[dict]) -> list[str]:
    return [m["text"] for m in conversation if m.get("role") == "resident"]


def is_verbatim(quote: str, conversation: list[dict]) -> bool:
    q = _strip_quote(quote)
    if len(q.split()) < 2:
        return False
    return any(q in normalise(msg) for msg in resident_messages(conversation))


def check_input(issue: dict, args: dict, conversation: list[dict]) -> list[str]:
    """Every reason this input cannot go to the subagent, or [] if it can."""
    problems = []
    extra = sorted(set(args) - set(INPUT_FIELDS))
    if extra:
        problems.append(f"Unexpected fields {extra}. Only {list(INPUT_FIELDS)} are accepted.")
    if args.get("issue_id") != issue["id"]:
        problems.append(f"issue_id must be the active issue, {issue['id']}.")
    if args.get("appliance_id") != issue["appliance_id"]:
        problems.append(f"appliance_id must be this issue's appliance, "
                        f"{issue['appliance_id']}.")

    quotes = args.get("resident_symptoms") or []
    if not quotes:
        problems.append("resident_symptoms needs at least one quote from the resident.")
    for q in quotes:
        if not is_verbatim(q, conversation):
            problems.append(f"Not found word for word in the resident's messages: {q!r}. "
                            "Copy their exact words, or a shortened part of them.")

    fields = [(f"troubleshooting[{i}]", f"{t.get('step', '')} {t.get('result', '')}")
               for i, t in enumerate(args.get("troubleshooting") or [])]
    fields += [("resident_symptoms", q) for q in quotes]
    fields += [("known_gaps", g) for g in args.get("known_gaps") or []]
    for name, text in fields:
        found = verdicts_in(text)
        if found:
            problems.append(f"{name} contains a verdict ({', '.join(found)!s}). Describe the "
                            "fault only - the repair-vs-replace judgement is not made here.")
    return problems


# =====================================================================================
# Preconditions - the guard in code (spec: "Responsibilities")
# =====================================================================================

def refusal_reason(issue: dict, appliance: dict) -> str | None:
    """Why the subagent must not run for this issue, or None.

    Read from the store, not from anything the main agent said: a missed or misread
    check_warranty in triage must not let an in-warranty job through.
    """
    warranty = STORE.warranty(appliance)
    if warranty["in_warranty"]:
        return (f"The appliance is in warranty until {warranty['expiry']} "
                f"({warranty['oem']}). In-warranty jobs go to the manufacturer and are not "
                "assessed.")
    if fault_reference(appliance["appliance_type"], _fault_slug(issue)) is None:
        return (f"There is no fault reference file for {appliance['appliance_type']}, so "
                "there is nothing to assess against. The PRD routes this to ops.")
    return None


def refused(reason: str) -> dict:
    """A refused assessment, carrying every table field but no recommendation."""
    return {
        "source": "subagent",
        "code": None, "confidence": None,
        "rationale": reason,
        "evidence_used": [], "evidence_missing": [], "limits_applied": [],
        "contra_indicators": [], "determinative": False,
        "confidence_basis": "not assessed: a precondition failed",
        "refusal_reason": reason,
    }


def _fault_slug(issue: dict) -> str:
    return issue.get("fault_slug_confirmed") or issue["fault_slug_reported"]


# =====================================================================================
# The subagent's input and instructions
# =====================================================================================

def build_brief(issue: dict, appliance: dict, args: dict) -> dict:
    """The complete input the subagent receives. Everything not from `args` is from the store."""
    warranty = STORE.warranty(appliance)
    repair, replace = issue["estimated_repair_cost"], issue["estimated_replacement_cost"]
    return {
        "issue_id": issue["id"],
        "appliance_id": appliance["id"],
        "appliance_type": appliance["appliance_type"],
        "fault_slug": _fault_slug(issue),
        "pm_description": issue["description"],
        "in_warranty": warranty["in_warranty"],
        "warranty_expiry": warranty["expiry"],
        "estimated_repair_cost": repair,
        "estimated_replacement_cost": replace,
        "cost_ratio": round(repair / replace, 3) if replace else None,
        "confidence_threshold": KNOBS.confidence_threshold,
        "troubleshooting": [{"step": t["step"], "result": t["result"]}
                            for t in args.get("troubleshooting") or []],
        "resident_symptoms": list(args["resident_symptoms"]),
        "known_gaps": list(args.get("known_gaps") or []),
    }


def render_brief(b: dict) -> str:
    def bullets(items):
        return "\n".join(f"  - {i}" for i in items) or "  (none)"

    ratio = f"{b['cost_ratio']:.0%}" if b["cost_ratio"] is not None else "unknown"
    return (
        f"Assess repair versus replace for issue {b['issue_id']}.\n\n"
        f"Appliance id: {b['appliance_id']} ({b['appliance_type']}) - look it up with "
        "get_appliance\n"
        f"Fault category: {b['fault_slug']}\n"
        f"Warranty (from Iterum records): "
        f"{'IN WARRANTY' if b['in_warranty'] else 'out of warranty'}, "
        f"expiry {b['warranty_expiry']}\n"
        f"Estimated repair: GBP {b['estimated_repair_cost']:.0f}\n"
        f"Estimated replacement: GBP {b['estimated_replacement_cost']:.0f}\n"
        f"Repair as share of replacement: {ratio}\n"
        f"Confidence threshold currently set to {b['confidence_threshold']:.2f}\n\n"
        f"Logged by the property manager (second-hand):\n  {b['pm_description']}\n\n"
        "Troubleshooting attempted:\n"
        + bullets(f"{t['step']} -> {t['result']}" for t in b["troubleshooting"]) + "\n\n"
        "The resident's own words about the appliance (verbatim):\n"
        + bullets(f'"{q}"' for q in b["resident_symptoms"]) + "\n\n"
        "Known gaps:\n" + bullets(b["known_gaps"])
    )


PREAMBLE = """You are the repair-vs-replace assessor for Iterum's issue resolution agent. \
You work separately from the agent that spoke to the resident. You see only the fault \
evidence you are given and what your own lookup tools return.

Before assessing, use get_appliance for the appliance record and search_similar_issues for \
comparable past jobs. Then call submit_assessment exactly once. Your assessment is logged as \
you submit it and nothing downstream can change it.

A resident's tone is not evidence. "It's completely useless" says how they feel, not what is \
wrong. If anything you are given is not about the appliance or the fault - a complaint, a \
scheduling preference, a remark about a previous engineer - leave it out of the assessment.

You do not talk to the resident, contact anyone, book anything or change any record."""


# Loaded at import so a missing skill fails at startup, not mid-thread (invariant 6).
SKILL = load_skill(DECISION_SKILL)


def system_prompt(appliance_type: str, fault_slug: str) -> str:
    parts = [PREAMBLE, SKILL]
    reference = fault_reference(appliance_type, fault_slug)
    if reference:
        parts.append(f"--- Fault pattern reference ---\n{reference}")
    return "\n\n".join(parts)


# =====================================================================================
# The subagent's tools
# =====================================================================================

# One issue runs at a time (session.CURRENT is the same assumption), so the submission is
# held at module level for the duration of one run.
_submission: RepairVsReplace | None = None


def _ok(payload) -> dict:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, default=str)
    return {"content": [{"type": "text", "text": text}]}


def _err(message: str) -> dict:
    return {"content": [{"type": "text", "text": message}], "is_error": True}


def _inline_refs(schema: dict) -> dict:
    """Pydantic puts ConfidenceLimit under $defs; tool input schemas are safer flat."""
    defs = schema.pop("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            ref = node.get("$ref", "")
            if ref.startswith("#/$defs/"):
                return walk(dict(defs[ref.split("/")[-1]]))
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema)


@tool("get_appliance",
      "Look up the appliance for this issue: make, model, install date, age and price.",
      {"appliance_id": str}, annotations=READ_ONLY)
async def get_appliance(args):
    expected = STORE.active_issue()["appliance_id"]
    if args["appliance_id"] != expected:
        return _err(f"Only this issue's appliance can be looked up: {expected}.")
    return _ok(STORE.appliance_view(STORE.appliance(expected)))


@tool("search_similar_issues",
      "Find comparable past jobs for this appliance type, with what they cost and how they "
      "were resolved.",
      {"appliance_type": str, "issue_description": str}, annotations=READ_ONLY)
async def search_similar_issues(args):
    matches = STORE.similar_issues(args["appliance_type"])
    if not matches:
        return _ok(f"No comparable historical jobs held for {args['appliance_type']}.")
    return _ok({"appliance_type": args["appliance_type"], "comparable_jobs": matches})


@tool("submit_assessment",
      "Submit your assessment. Call exactly once, after looking up the appliance and "
      "comparable jobs.",
      _inline_refs(RepairVsReplace.model_json_schema()))
async def submit_assessment(args):
    global _submission
    if _submission is not None:
        return _err("An assessment has already been submitted for this run.")
    try:
        _submission = RepairVsReplace.model_validate(args)
    except ValidationError as exc:
        return _err(f"Assessment rejected, correct it and submit again: {exc}")
    return _ok("Assessment submitted. You are done.")


TOOLS = [get_appliance, search_similar_issues, submit_assessment]
SERVER = create_sdk_mcp_server(name=SERVER_NAME, version="1.0.0", tools=TOOLS)
ALLOWED_TOOLS = [f"{PREFIX}{t.name}" for t in TOOLS]


# =====================================================================================
# Hooks: the subagent's own tool-surface guardrail and trace
# =====================================================================================

async def pre_tool_use(input_data, tool_use_id, context):
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {}) or {}
    name = tool_name[len(PREFIX):] if tool_name.startswith(PREFIX) else tool_name
    try:
        s = session.current()
        # Recorded so the run summary's built-in leak check covers the subagent too.
        s.tool_calls.append({"tool": name, "input": tool_input, "loop": s.loop,
                             "agent": "subagent"})
    except RuntimeError:
        pass

    allowed = tool_name in ALLOWED_TOOLS
    BUS.publish("tool_call", tool=name, qualified=tool_name, iterum_tool=allowed,
                input=tool_input, agent="subagent", tool_use_id=tool_use_id)
    trace.log_decision("subagent_tool_call", tool=name, tool_input=tool_input)
    if allowed:
        return {}

    reason = (f"{tool_name} is not available to the repair-vs-replace subagent. It has "
              "get_appliance, search_similar_issues and submit_assessment only.")
    BUS.publish("guardrail", rule="subagent_tool_surface", detail=reason, tool=name)
    trace.log_decision("guardrail_block", rule="subagent_tool_surface", tool=tool_name)
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


async def post_tool_use(input_data, tool_use_id, context):
    name = input_data.get("tool_name", "")
    name = name[len(PREFIX):] if name.startswith(PREFIX) else name
    text = trace._response_text(input_data.get("tool_response"))
    BUS.publish("tool_result", tool=name, result=text, agent="subagent",
                tool_use_id=tool_use_id)
    return {}


HOOKS = {
    "PreToolUse": [HookMatcher(hooks=[pre_tool_use])],
    "PostToolUse": [HookMatcher(hooks=[post_tool_use])],
}


async def _deny_all(tool_name, tool_input, context):
    return PermissionResultDeny(message=f"{tool_name} is not available to this subagent.")


def build_options(system: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model=KNOBS.model,
        system_prompt=system,
        # Same isolation as the main agent (invariant 1), with a smaller surface.
        mcp_servers={SERVER_NAME: SERVER},
        tools=[],
        allowed_tools=ALLOWED_TOOLS,
        setting_sources=[],
        permission_mode="default",
        can_use_tool=_deny_all,
        hooks=HOOKS,
        effort="medium",
        max_turns=MAX_TURNS,
        max_budget_usd=MAX_BUDGET_USD,
        cwd=str(ROOT),
        stderr=lambda line: BUS.publish("stderr", line=line.rstrip()),
    )


# =====================================================================================
# Running it
# =====================================================================================

async def _run(brief: dict) -> tuple[RepairVsReplace, float]:
    global _submission
    _submission = None
    cost = 0.0
    options = build_options(system_prompt(brief["appliance_type"], brief["fault_slug"]))
    async with ClaudeSDKClient(options=options) as client:
        await client.query(render_brief(brief))
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                cost = message.total_cost_usd or 0.0
                if message.is_error:
                    raise SubagentError(f"subagent session ended in error "
                                        f"({message.subtype}, {message.stop_reason})")
    if _submission is None:
        raise SubagentError("the subagent ended without calling submit_assessment")
    return _submission, cost


async def run(brief: dict) -> dict:
    """Run the subagent on a brief and return its assessment in the output-table shape."""
    BUS.publish("subagent_started", brief=brief)
    parsed, cost = await asyncio.wait_for(_run(brief), timeout=TIMEOUT_S)
    try:
        session.current().subagent_cost_usd += cost
    except RuntimeError:
        pass
    return assessment_from_model(parsed, inputs={
        "age_years": STORE.appliance_age_years(STORE.appliance(brief["appliance_id"])),
        "repair_cost": brief["estimated_repair_cost"],
        "replacement_cost": brief["estimated_replacement_cost"],
        "cost_ratio": brief["cost_ratio"],
        "in_warranty": brief["in_warranty"],
        "subagent_cost_usd": round(cost, 4),
    })
