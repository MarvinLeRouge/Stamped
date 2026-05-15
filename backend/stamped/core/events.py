import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator
from typing import Any


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
        payload = {"event": event, "data": data}
        for q in list(self._queues):
            with contextlib.suppress(asyncio.QueueFull):
                q.put_nowait(payload)

    async def stream(self, q: asyncio.Queue[dict[str, Any]]) -> AsyncGenerator[str, None]:
        try:
            while True:
                payload = await q.get()
                yield f"event: {payload['event']}\ndata: {json.dumps(payload['data'])}\n\n"
        finally:
            self.unsubscribe(q)


bus = EventBus()
