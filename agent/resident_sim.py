"""Simulated resident for hands-free demo runs.

Not part of the agent under test - it stands in for a human on WhatsApp so a scenario can
play through end to end for a recording. Each scenario gives the simulator a hidden
ground truth the agent cannot see, so triage has something real to discover. Turn
auto-play off in the UI and you type the resident's replies yourself.

Runs on a cheap model deliberately: it is playing a person, not reasoning about appliances.
"""

import asyncio

from anthropic import AsyncAnthropic

from .config import KNOBS
from .events import BUS
from .store import STORE

_client: AsyncAnthropic | None = None


def client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()
    return _client


SYSTEM = """You are role-playing a resident of a UK rental flat, texting on WhatsApp with \
your building's appliance support service about a broken appliance.

You are {name}.

WHAT IS ACTUALLY WRONG (you do not know this in these words - you only know what you can \
see and hear, but everything you say must be consistent with it):
{ground_truth}

HOW YOU BEHAVE:
{behaviour}

Rules:
- Reply as the resident, in one short WhatsApp message. Usually one to three sentences.
- Write like a real person texting: casual, occasional lower case, no bullet points, no \
headings, no sign-off.
- Only report what you could actually observe. Never use trade terminology you would not know.
- If asked to try something, say what happened when you tried it - consistent with the \
truth above. If it would not fix the real problem, it does not fix it.
- Never break character, never mention that you are an AI or a simulation.
- Do not be more helpful than the behaviour description says you are."""


def _history() -> list[dict]:
    messages = []
    for entry in STORE.data["conversation_log"]:
        role = "user" if entry["role"] == "agent" else "assistant"
        messages.append({"role": role, "content": entry["text"]})
    # The API needs the transcript to start with a user turn.
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    return messages


async def generate_reply(session) -> str:
    persona = session.scenario.get("resident_persona", {})
    system = SYSTEM.format(
        name=persona.get("name", "the resident"),
        ground_truth=persona.get("ground_truth", "Unspecified."),
        behaviour=persona.get("behaviour", "Cooperative and brief."),
    )
    messages = _history()
    if not messages:
        messages = [{"role": "user", "content": "(the support service has opened a chat)"}]

    response = await client().messages.create(
        model=KNOBS.resident_sim_model,
        max_tokens=300,
        system=system,
        messages=messages,
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()


def scripted_reply(session) -> str | None:
    """The next scripted reply once a date has been offered, or None to let the model play.

    For a scenario whose checks need one exact path (reassessment_cap, the fire drill), the
    persona's `scripted_after_offer` pins the resident's replies from the first date offer
    onwards: the model playing the resident went off-script in step 5 (a held-back symptom in
    triage, then accepting the first date), and the cap was never reached. "Offered" means a
    slot has been found; the agent's next message is the offer. Once the script runs out the
    model takes over again.
    """
    script = session.scenario.get("resident_persona", {}).get("scripted_after_offer") or []
    if not session.proposed_slots or session.scripted_replies_used >= len(script):
        return None
    reply = script[session.scripted_replies_used]
    session.scripted_replies_used += 1
    return reply


def schedule_reply(session) -> None:
    """Fire-and-forget the simulated reply so the tool handler stays awaiting."""

    async def _run():
        scripted = scripted_reply(session)
        try:
            await asyncio.sleep(0.6)  # let the outbound message render first
            reply = scripted or await generate_reply(session)
        except Exception as exc:  # noqa: BLE001
            BUS.publish("error", where="resident_sim", detail=str(exc))
            reply = "sorry, not sure - can you explain what you mean?"
        if session.awaiting_resident:
            BUS.publish("resident_message", direction="in", text=reply, simulated=True,
                        scripted=scripted is not None)
            session.deliver_resident_reply(reply)

    asyncio.create_task(_run())
