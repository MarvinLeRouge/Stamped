import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class EventBus:
    def __init__(self) -> None:
        self._queues: list[asyncio.Queue[dict[str, Any]]] = []

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        self._queues.remove(q)

    def publish(self, event: str, data: dict[str, Any]) -> None:
        payload = {"event": event, "data": {**data, "timestamp": _now()}}
        for q in list(self._queues):
            with contextlib.suppress(asyncio.QueueFull):
                q.put_nowait(payload)

    async def stream(self, q: asyncio.Queue[dict[str, Any]]) -> AsyncGenerator[str, None]:
        yield f"event: connected\ndata: {json.dumps({'timestamp': _now()})}\n\n"
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=30)
                    yield f"event: {payload['event']}\ndata: {json.dumps(payload['data'])}\n\n"
                except TimeoutError:
                    yield f": ping {_now()}\n\n"
        finally:
            self.unsubscribe(q)


bus = EventBus()
