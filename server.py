"""Demo server: SSE event stream plus the endpoints the human actors act through.

The UI is a viewer onto the agent, not a participant. The only things a person can do
here are the things a person does in the real flow: reply as the resident, confirm or
override as the engineer, approve or reject as the property manager, and turn the
PRD's open questions up and down.
"""

import asyncio
import json
from contextlib import suppress
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

from agent import session  # noqa: E402
from agent.config import KNOBS  # noqa: E402
from agent.events import BUS  # noqa: E402
from agent.runner import run_scenario  # noqa: E402
from agent.store import STORE  # noqa: E402
from agent.trace import LOG_PATH  # noqa: E402

app = FastAPI(title="Iterum Issue Resolution Agent - prototype")

SCENARIO_DIR = ROOT / "scenarios"
STATIC_DIR = ROOT / "static"

_run_task: asyncio.Task | None = None


# --- models ---------------------------------------------------------------------------
class RunRequest(BaseModel):
    scenario_id: str
    auto_play: bool = True


class ReplyRequest(BaseModel):
    text: str


class GateRequest(BaseModel):
    decision: str
    note: str = ""


# --- static ---------------------------------------------------------------------------
@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- scenarios and runs -----------------------------------------------------------------
@app.get("/api/scenarios")
async def list_scenarios():
    out = []
    for path in SCENARIO_DIR.glob("*.json"):
        data = json.loads(path.read_text())
        out.append({"id": data["id"], "order": data.get("order", 99),
                    "title": data["title"], "summary": data["summary"],
                    "expected": data["expected"]})
    # Demo order, not alphabetical - it builds from the cheapest outcome to the gated one.
    return sorted(out, key=lambda s: s["order"])


@app.post("/api/run")
async def start_run(req: RunRequest):
    global _run_task
    if _run_task and not _run_task.done():
        _run_task.cancel()
        with suppress(asyncio.CancelledError):
            await _run_task
    _run_task = asyncio.create_task(run_scenario(req.scenario_id, auto_play=req.auto_play))
    return {"started": req.scenario_id, "auto_play": req.auto_play}


@app.post("/api/stop")
async def stop_run():
    global _run_task
    if _run_task and not _run_task.done():
        _run_task.cancel()
        with suppress(asyncio.CancelledError):
            await _run_task
        return {"stopped": True}
    return {"stopped": False}


# --- the event stream --------------------------------------------------------------------
@app.get("/api/events")
async def events():
    async def stream():
        queue = BUS.subscribe()
        try:
            yield ": connected\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                yield f"data: {json.dumps(event, default=str)}\n\n"
        finally:
            BUS.unsubscribe(queue)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


# --- human actors -------------------------------------------------------------------------
@app.post("/api/resident/reply")
async def resident_reply(req: ReplyRequest):
    try:
        s = session.current()
    except RuntimeError:
        raise HTTPException(409, "No run in progress.")
    if not s.awaiting_resident:
        raise HTTPException(409, "The agent is not waiting for the resident right now.")
    BUS.publish("resident_message", direction="in", text=req.text, simulated=False)
    s.deliver_resident_reply(req.text)
    return {"delivered": True}


@app.post("/api/gate/{kind}")
async def resolve_gate(kind: str, req: GateRequest):
    try:
        s = session.current()
    except RuntimeError:
        raise HTTPException(409, "No run in progress.")
    gate = s.pending_gate
    if gate is None or gate.kind != kind:
        raise HTTPException(409, f"No {kind} gate is open.")
    valid = {"engineer": {"confirm", "override"}, "pm": {"approve", "reject"}}
    if req.decision not in valid.get(kind, set()):
        raise HTTPException(400, f"decision for a {kind} gate must be one of "
                                 f"{sorted(valid.get(kind, set()))}")
    s.resolve_gate(req.decision, req.note)
    return {"resolved": req.decision}


@app.post("/api/autoplay")
async def set_autoplay(payload: dict):
    try:
        s = session.current()
    except RuntimeError:
        raise HTTPException(409, "No run in progress.")
    s.auto_play = bool(payload.get("auto_play", True))
    BUS.publish("state", state=s.snapshot())
    return {"auto_play": s.auto_play}


# --- knobs, record and log -------------------------------------------------------------
@app.get("/api/knobs")
async def get_knobs():
    return KNOBS.to_dict()


@app.post("/api/knobs")
async def set_knobs(patch: dict):
    KNOBS.update(patch)
    BUS.publish("knobs", knobs=KNOBS.to_dict())
    return KNOBS.to_dict()


@app.get("/api/record")
async def record():
    """The Iterum IQ record as it stands - issue with its nested visits."""
    try:
        data = STORE.data
    except RuntimeError:
        raise HTTPException(409, "No scenario loaded.")
    issue = STORE.active_issue()
    appliance = STORE.appliance(issue["appliance_id"])
    return {
        "issue": issue,
        "appliance": {**appliance, "age_years": STORE.appliance_age_years(appliance)},
        "property": STORE.property(issue["property_id"]),
        "resident": STORE.resident(issue["resident_id"]),
        "engineer": STORE.engineer_for_property(issue["property_id"]),
        "property_manager": STORE.property_manager(issue["property_id"]),
        "approvals": data["approvals"],
        "ops_queue": data["ops_queue"],
        "email_outbox": data["email_outbox"],
        "inventory": list(data["inventory"].values()),
    }


@app.get("/api/log")
async def decision_log(limit: int = 400):
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text().strip().splitlines()[-limit:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


@app.delete("/api/log")
async def clear_log():
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    return {"cleared": True}
