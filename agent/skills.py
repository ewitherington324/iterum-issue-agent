"""Loads the Module 2 skill files and serves them to the two reasoning calls.

The SDK's own skill discovery is deliberately not used. `setting_sources=[]` in runner.py
(invariant 1) stops the agent picking up anything on disk, and skill discovery is one of
the things that goes through setting sources - so a SKILL.md dropped in `.claude/skills`
would load nothing, silently, while the agent carried on improvising. Putting the files
in `skills/` at the repo root and reading them ourselves is both compatible with that invariant and stronger: the
skill is in context on every call rather than whenever the model judges it relevant, which
is not a property you want to leave to judgement on safety-critical instructions.

Three levels, matching how skills are meant to work:

  1. `SKILL.md` frontmatter - not sent to the model at all here, since we are not relying
     on description-matching to decide whether the skill applies.
  2. `SKILL.md` body - the system prompt for the reasoning call. Always sent.
  3. `references/<appliance>.md` - one fault section, selected by `fault_slug`. Sent with
     the user message. The other nine reference files cost nothing on this call.

Level 3 is why the reference files are keyed by Iterum's real taxonomy slugs: the caller
already knows the slug, so the lookup is exact rather than the model reading 12,000 words
of fault patterns to find the one paragraph that matters.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

TRIAGE_SKILL = "iterum-triage-steps"
DECISION_SKILL = "iterum-repair-vs-replace"
ESCALATION_SKILL = "iterum-escalation"

# Appliance type as it appears on the appliance record -> reference filename.
# The first six are Iterum taxonomy types and carry real `label_slug` keys. The last four
# are in scope per the PRD but have no category in the issue history, so no fault_slug will
# ever match them and only the file preamble is returned.
_REFERENCE_FILES = {
    "washer-dryer": "washer-dryer.md",
    "dishwasher": "dishwasher.md",
    "oven": "oven.md",
    "fridge-freezer": "fridge-freezer.md",
    "hob": "hob.md",
    "hood": "extractor-hood.md",
    "extractor hood": "extractor-hood.md",
    "washing machine": "washing-machine.md",
    "tumble dryer": "tumble-dryer.md",
    "microwave": "microwave.md",
    "wine cooler": "wine-cooler.md",
}

_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
_SLUG_HEADING = re.compile(r"^## `([a-z0-9_]+)`", re.M)


class SkillNotFound(RuntimeError):
    """Raised when a skill file is missing.

    Deliberately loud. A silently absent skill is the failure mode this whole module
    exists to avoid - the reasoning call would still return plausible-looking steps, with
    none of the safety constraints applied and nothing in the trace to show it.
    """


@lru_cache(maxsize=None)
def load_skill(name: str) -> str:
    """The SKILL.md body, frontmatter stripped, ready to use as a system prompt."""
    path = SKILLS_DIR / name / "SKILL.md"
    if not path.is_file():
        raise SkillNotFound(f"No SKILL.md at {path}")
    return _FRONTMATTER.sub("", path.read_text(encoding="utf-8")).strip()


@lru_cache(maxsize=None)
def _reference_text(appliance_type: str) -> str | None:
    filename = _REFERENCE_FILES.get(appliance_type.strip().lower())
    if not filename:
        return None
    path = SKILLS_DIR / TRIAGE_SKILL / "references" / filename
    return path.read_text(encoding="utf-8") if path.is_file() else None


def _split_sections(text: str) -> tuple[str, dict[str, str]]:
    """Return (preamble, {slug: section}).

    The preamble is everything before the first slug heading. It is not filler - it carries
    the status banner, the how-to-use note, and for hobs the gas restrictions, which apply
    across every section and must travel with whichever one is selected.
    """
    matches = list(_SLUG_HEADING.finditer(text))
    if not matches:
        return text.strip(), {}
    preamble = text[: matches[0].start()].strip()
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[m.group(1)] = text[m.start() : end].strip().rstrip("-").strip()
    return preamble, sections


def fault_reference(appliance_type: str, fault_slug: str | None) -> str | None:
    """The reference context for one fault: file preamble plus the matching section.

    Falls back to the file's `_other` section when the slug does not match, which is what
    happens for the four appliance types with no taxonomy coverage and for any slug the
    reference has not been written up yet. Returns None only when there is no reference
    file for the appliance type at all - the caller should route rather than improvise.
    """
    text = _reference_text(appliance_type)
    if text is None:
        return None

    preamble, sections = _split_sections(text)
    if not sections:
        return preamble

    section = sections.get(fault_slug or "")
    if section is None:
        other = next((v for k, v in sections.items() if k.endswith("_other")), None)
        section = other or ""

    return f"{preamble}\n\n{section}".strip()


def reference_coverage() -> dict[str, int]:
    """How many slug sections each reference file carries. Used by selftest."""
    out = {}
    for filename in sorted(set(_REFERENCE_FILES.values())):
        path = SKILLS_DIR / TRIAGE_SKILL / "references" / filename
        if path.is_file():
            _, sections = _split_sections(path.read_text(encoding="utf-8"))
            out[filename] = len(sections)
    return out
