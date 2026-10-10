"""Shared plumbing for the Module 5 evaluation: paths, cost tracking, result files."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

CASES = ROOT / "evals" / "cases"
RESULTS = ROOT / "docs" / "module5" / "results"

# Direct API calls (the troubleshooting-steps call and the judge) don't report a cost the
# way an Agent SDK session does, so it is estimated from token counts. These are the
# per-million-token list prices assumed for the configured model; agent sessions (the
# subagent, the end-to-end runs) use the SDK's own reported cost instead.
PRICE_IN_PER_M = 5.00
PRICE_OUT_PER_M = 25.00


def token_cost(usage) -> float:
    if usage is None:
        return 0.0
    inp = (getattr(usage, "input_tokens", 0) or 0) \
        + (getattr(usage, "cache_creation_input_tokens", 0) or 0) \
        + (getattr(usage, "cache_read_input_tokens", 0) or 0) * 0.1
    out = getattr(usage, "output_tokens", 0) or 0
    return inp / 1e6 * PRICE_IN_PER_M + out / 1e6 * PRICE_OUT_PER_M


class Spend:
    """Running total across a whole eval run, with a hard cap."""

    def __init__(self, cap_usd: float | None):
        self.cap = cap_usd
        self.total = 0.0

    def add(self, usd: float) -> None:
        self.total += usd or 0.0

    def can_start(self, next_estimate: float = 0.0) -> bool:
        return self.cap is None or self.total + next_estimate <= self.cap


def git_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "agent", "skills"],
                               cwd=ROOT, capture_output=True, text=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def load_cases(name: str) -> list[dict]:
    return json.loads((CASES / name).read_text())


def append_row(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")
