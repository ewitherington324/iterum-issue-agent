"""Judge scoring for Set B transcripts, and the judge's own checks (Module 5).

    .venv/bin/python -m evals.score_transcripts            # score every unscored run, twice
    .venv/bin/python -m evals.score_transcripts --planted  # the planted-fault test only

Reads the end-to-end runs written by verify.py (docs/module5/results/tier_b*.jsonl, which
carry the conversation and the engineer note) and appends judge scores to
docs/module5/results/judge_b.jsonl.

Repeat scoring: every transcript is scored twice; the report lists every criterion where
the two scores differ.

Planted faults: copies of real transcripts with one known defect edited in. Each must drop
the matching criterion to the expected score. A criterion whose planted fault is missed is
reported as unreliable and left out of the pass/fail verdict. This is mutation testing
applied to the judge: it shows the judge CAN fail a bad transcript, which agreeing with a
good one never shows.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import sys

from evals import judge
from evals.common import RESULTS, Spend, append_row, now, read_rows

SOURCES = ["tier_b.jsonl", "tier_b_baseline.jsonl"]
OUT = RESULTS / "judge_b.jsonl"
PLANTED_OUT = RESULTS / "judge_planted.jsonl"


def _runs() -> list[dict]:
    rows = []
    for name in SOURCES:
        for r in read_rows(RESULTS / name):
            if r.get("conversation") and not r.get("env_failure"):
                rows.append({**r, "source_file": name})
    return rows


def _note_text(note) -> str | None:
    if not note:
        return None
    if isinstance(note, str):
        return note
    return "\n".join(f"{k}: {v}" for k, v in note.items())


# --- planted faults ------------------------------------------------------------------

def _agent_idx(conv):
    return [i for i, m in enumerate(conv) if m["role"] == "agent"]


def plant(kind: str, conv: list[dict], note):
    conv = copy.deepcopy(conv)
    idx = _agent_idx(conv)
    last = idx[-1]
    if kind == "CM-1":
        conv[last]["text"] += ("\n\nTo be clear, your drain pump is definitely broken and the "
                               "engineer will replace it.")
    elif kind == "CM-2":
        conv[last]["text"] += ("\n\nJust so you know, you'll be charged £80 for the callout "
                               "because the filter should have been cleaned.")
    elif kind == "CM-4":
        first_q = next(conv[i]["text"] for i in idx if "?" in conv[i]["text"])
        conv.insert(last, {"role": "agent", "text": first_q})
        conv.insert(last + 1, {"role": "resident",
                               "text": "i literally already told you that, scroll up"})
    elif kind == "CM-5":
        conv[last]["text"] += ("\n\nThanks for the photo - I can see the fault clearly from it, "
                               "which confirms what you described.")
    elif kind == "HO-2":
        note = "Resident says it's broken. Please attend."
    return conv, note


PLANTS = {"CM-1": 1, "CM-2": 1, "CM-4": 2, "CM-5": 1, "HO-2": 1}  # max acceptable score


async def planted(spend: Spend, n_bases: int) -> None:
    # Bases: clean booked runs, so the engineer note exists and the original scores are good.
    bases = [r for r in _runs() if r.get("engineer_note")][:n_bases]
    if not bases:
        print("no booked runs with an engineer note to plant into")
        return
    for b in bases:
        for kind, max_ok in PLANTS.items():
            conv, note = plant(kind, b["conversation"], b.get("engineer_note"))
            scores, cost = await judge.transcript(conv, _note_text(note))
            spend.add(cost)
            got = scores.get(kind, {}).get("score")
            row = {"at": now(), "base": f"{b['scenario']} run {b['run']}", "planted": kind,
                   "score": got, "max_ok": max_ok, "caught": got is not None and got <= max_ok,
                   "reason": scores.get(kind, {}).get("reason"), "cost_usd": cost}
            append_row(PLANTED_OUT, row)
            print(f"planted {kind} into {row['base']}: score {got} -> "
                  f"{'caught' if row['caught'] else 'MISSED'}  (${spend.total:.2f})", flush=True)


async def score_all(spend: Spend, repeats: int) -> None:
    done = {(r["scenario"], r["run"], r["source_file"], r["repeat"]) for r in read_rows(OUT)}
    for r in _runs():
        for rep in range(1, repeats + 1):
            key = (r["scenario"], r["run"], r["source_file"], rep)
            if key in done:
                continue
            if not spend.can_start(0.05):
                print("stopping at the cost cap")
                return
            scores, cost = await judge.transcript(r["conversation"], _note_text(r.get("engineer_note")))
            spend.add(cost)
            append_row(OUT, {"at": now(), "scenario": r["scenario"], "run": r["run"],
                             "source_file": r["source_file"], "repeat": rep,
                             "scores": scores, "cost_usd": cost})
            short = " ".join(f"{k}={v['score']}" for k, v in sorted(scores.items()))
            print(f"{r['scenario']} run {r['run']} #{rep}: {short}  (${spend.total:.2f})", flush=True)


async def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--planted", action="store_true")
    p.add_argument("--bases", type=int, default=2)
    p.add_argument("--repeats", type=int, default=2)
    p.add_argument("--max-cost", type=float, default=3.0)
    a = p.parse_args(argv)
    spend = Spend(a.max_cost)
    if a.planted:
        await planted(spend, a.bases)
    else:
        await score_all(spend, a.repeats)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
