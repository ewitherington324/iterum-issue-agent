"""In-process event bus feeding the demo UI over SSE.

Every event the UI renders - resident messages, tool calls, loop transitions, gate
requests, ops and email traffic - goes through here. A replay buffer means a browser
that connects late (or reloads mid-demo) still sees the whole run.
"""

import asyncio
import itertools
import time
from typing import Any

_seq = itertools.count(1)


class EventBus:
    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []
        self._history: list[dict] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(q)
        for event in self._history:
            q.put_nowait(event)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    RESERVED = ("seq", "kind", "at")

    def publish(self, kind: str, **payload: Any) -> dict:
        # Payload keys must never overwrite the envelope - a publish() with kind= in the
        # payload would otherwise silently rename the event and no subscriber would match it.
        for key in self.RESERVED:
            if key in payload:
                payload[f"{key}_"] = payload.pop(key)
        event = {**payload, "seq": next(_seq), "kind": kind, "at": time.time()}
        self._history.append(event)
        for q in self._subscribers:
            q.put_nowait(event)
        return event

    def reset(self) -> None:
        """Clear history at the start of a new scenario run, but keep subscribers so an
        open browser tab follows the new run without reconnecting."""
        self._history = []
        self.publish("reset")

    @property
    def history(self) -> list[dict]:
        return list(self._history)


BUS = EventBus()
