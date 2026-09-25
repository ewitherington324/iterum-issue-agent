# Iterum Issue Resolution Agent — working notes

Prototype of the agentic system in `docs/PRD.md`,
built for an AI course. Its job is to make
the vision legible to instructors and eventually to integrate with Iterum IQ. Currently every external
system (IQ, Airtable, WhatsApp, Mailgun) is mocked.

Read `docs/PROJECT_MAP.md` for the one-page orientation, then `README.md` for the demo script and the architecture rationale. This file is the
short version plus the things that will bite you.
Module 3 work follows docs/module3/SUBAGENT_SPEC.md. If the code and the spec disagree, stop and ask. Don't resolve it silently.

## Commands

```bash
./run.sh                              # http://localhost:8000
.venv/bin/python selftest.py          # 44 checks, no API key, ~1s — use this constantly
.venv/bin/python verify.py            # all 8 scenarios against the real model (~$3)
.venv/bin/python verify.py self_fix   # one scenario, verbose trace (~$0.15–0.70)
```

`verify.py` and `run.sh` spend real money. `selftest.py` doesn't — it covers the gates,
the guardrails and the slot limit directly, which is most of what you'd want to check
while editing.

## Invariants — do not break these without meaning to

These are the design, not incidental implementation. Each is load-bearing for the claim the
prototype makes.

1. **`tools=[]` and `setting_sources=[]` in `agent/runner.py`.** Together they mean the agent
   sees only the Iterum tool surface, on any machine. Remove either and built-ins (Read,
   Bash, WebSearch) or a stray local `CLAUDE.md` leak into the agent. `selftest.py` and every
   `verify.py` run assert no built-in was ever reached.

2. **`book_visit` is deliberately absent from `AUTONOMOUS_TOOLS`** (`agent/tools.py`). That
   omission is the entire replacement gate: tools in `allowed_tools` are auto-approved and
   never reach `can_use_tool`, so adding `book_visit` there would silently disable the
   engineer and PM approvals while everything still appeared to work.

3. **Guardrails live in the `PreToolUse` hook** (`agent/trace.py`), not in the prompt. Hooks
   run first in the SDK's permission order, so the warranty block cannot be reasoned around.
   `agent/prompts.py` describes the rules so the agent behaves sensibly; the hook makes them
   true. Don't migrate one to the other.

4. **Never pass `kind`, `seq` or `at` as a payload key to `BUS.publish()`** (`agent/events.py`).
   `publish(kind, **payload)` takes `kind` positionally, so `publish("x", kind="y")` raises
   `TypeError` at runtime. This shipped as a live bug once — every gate crashed the moment it
   opened, and it went unnoticed because the default scenario has no gates. Gate events use
   `gate=` for this reason.

5. **Loop exits are explicit tool calls** — `complete_triage`, `submit_recommendation`,
   `conclude_booking`. `agent/runner.py` branches on them. An agent that finishes a phase
   without calling one produces a `run_incomplete` event rather than silently continuing.

6. **Skills are loaded explicitly, never discovered** (`agent/skills.py`). Invariant 1's
   `setting_sources=[]` disables the SDK's on-disk skill discovery, so a `SKILL.md` under
   `.claude/skills` would load *nothing* — and the reasoning call would still return
   plausible steps, with none of the safety constraints applied and nothing in the trace to
   show it. `agent/skills.py` reads `skills/*/SKILL.md` itself and passes each as the system
   prompt of its reasoning call. That is stronger than discovery anyway: the skill is in
   context on every call rather than whenever the model judges it relevant, which is not a
   property to leave to judgement on resident-safety instructions. A missing skill raises
   `SkillNotFound` at import rather than degrading quietly.

   The escalation skill is the exception and is compiled by hand into `SYSTEM` in
   `prompts.py`. It has to be in context from the first token; a guardrail that loads once
   the model decides it is relevant has already failed. Rebuild that section when
   `skills/iterum-escalation/SKILL.md` changes. Per invariant 3 it still only *describes* —
   the `PreToolUse` hook is what enforces.

## Layout

```
agent/runner.py     orchestration: one ClaudeSDKClient per issue, three loop phases
agent/tools.py      the 15 PRD tools + 3 exit tools -> one in-process MCP server
agent/gates.py      can_use_tool — the engineer/PM approval gate on book_visit
agent/trace.py      PreToolUse/PostToolUse hooks — trace, guardrails, decision log
agent/prompts.py    system prompt + per-loop instructions
agent/fallbacks.py  rules-based path for the A/B (fault lookup + age/cost heuristic)
agent/reasoning.py  the two LLM reasoning calls, structured output via Pydantic
agent/config.py     KNOBS — the PRD's open questions, live-editable from the UI
agent/skills.py     loads skills/ — system prompts for the two reasoning calls, plus the
                    per-fault reference section selected by fault_slug
skills/             the Module 2 skill files: three SKILL.md, plus ten appliance fault
                    references under iterum-triage-steps/references/
server.py           FastAPI: SSE stream + the human-actor endpoints
docs/               PRD, project map, and docs/module2/ (submitted write-up, evidence,
                    pre-skills baseline prompts)
static/             the three-pane UI (vanilla JS, roadmap-green palette)
scenarios/*.json    the 8 test cases; "order" drives both the UI dropdown and verify.py
```

**Generated — don't hand-edit:** `data/store.json` (rebuilt per scenario run),
`data/taxonomy.json` (regenerate with `data/extract_taxonomy.py`), `logs/decision_log.jsonl`.

## Gotchas

- **Python 3.10+.** `/usr/bin/python3` is 3.9 and will fail on `str | None` annotations. Use
  `.venv/bin/python`.
- **The Agent SDK does not read `.env`.** `server.py` and `verify.py` load it explicitly with
  `python-dotenv`. Anything new with an entry point must do the same.
- **Verify SDK shapes against the installed package, not the docs page.** The published
  `HookMatcher` example differs from `claude_agent_sdk` 0.2.152: the real shape is
  `HookMatcher(matcher=..., hooks=[fn])` with callbacks taking
  `(input_data, tool_use_id, context)`. `inspect.getsource` on the installed class is the
  fastest way to check.
- **`CanUseToolShadowedWarning` is expected** and silenced in `runner.py` with a comment. It
  fires because the autonomous tools are meant to bypass the callback. If it ever names
  `book_visit`, invariant 2 has been broken.
- **Model is `claude-opus-5`** (`agent/config.py`). The resident simulator runs on
  `claude-haiku-4-5` — it plays a person, it isn't the agent under test.

## Data provenance

The fault taxonomy (55 categories with their real `label_slug` keys), property names,
operators, brands and supply-chain partners are **real Iterum data**, extracted from
`../Issue Category Analysis.xlsx` and the onboarding CSVs. Individual people — residents,
engineers, property managers — are invented.

Emma chose real names deliberately for authenticity in the coursework. Keep that in mind
before publishing anything from this repo anywhere public.

## Known open items

- §5.1's slot rule permits same-day booking when parts are in stock, and does so in practice.
  Implemented as written rather than silently fixed; a real v1 needs a minimum notice period.
- The PM cost threshold (£400), the engineer channel, and what underlies the 75% confidence
  figure are all unresolved in the PRD and exposed as UI dials rather than decided here.
- The LLM path self-reports confidence; the heuristic computes it from distance to its
  decision boundaries. These are different quantities — `confidence_basis` records which.
- Six of the ten appliance reference files are keyed by real `label_slug` values. The other
  four — washing machine, tumble dryer, microwave, wine cooler — are in PRD scope but have no
  category in `data/taxonomy.json`, so no `fault_slug` will ever match them and only the file
  preamble reaches the model. Either the portfolio has these types and they have logged no
  issues, or the scope list is wider than reality. Unresolved.
- `FAULT_PATTERNS` in `fallbacks.py` and the slug-keyed reference files are now keyed the same
  way but remain two separate sources. Deriving the former from the latter is what would make
  PRD 4.1's "one source, cannot drift" claim literally true.
- The fault content under `skills/iterum-triage-steps/references/` is general appliance
  knowledge, not Iterum service data — every file carries a status banner saying so. It needs
  engineer sign-off before it reaches a resident, the engineer-only signal rows most of all.
