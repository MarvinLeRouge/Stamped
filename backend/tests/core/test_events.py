import asyncio

import pytest

from stamped.core.events import EventBus, _now


def test_now_returns_iso_string() -> None:
    result = _now()
    assert result.endswith("Z")
    assert len(result) == 20


def test_subscribe_returns_queue() -> None:
    bus = EventBus()
    q = bus.subscribe()
    assert isinstance(q, asyncio.Queue)
    assert q in bus._queues


def test_unsubscribe_removes_queue() -> None:
    bus = EventBus()
    q = bus.subscribe()
    bus.unsubscribe(q)
    assert q not in bus._queues


def test_publish_puts_payload_in_queue() -> None:
    bus = EventBus()
    q = bus.subscribe()
    bus.publish("test_event", {"key": "value"})
    payload = q.get_nowait()
    assert payload["event"] == "test_event"
    assert payload["data"]["key"] == "value"
    assert "timestamp" in payload["data"]


def test_publish_ignores_full_queue() -> None:
    bus = EventBus()
    q = bus.subscribe()
    for _ in range(q.maxsize):
        q.put_nowait({"event": "dummy", "data": {}})
    bus.publish("overflow", {"key": "val"})  # should not raise


@pytest.mark.asyncio
async def test_stream_first_event_is_connected() -> None:
    bus = EventBus()
    q = bus.subscribe()
    gen = bus.stream(q)
    first = await gen.__anext__()
    await gen.aclose()
    assert "event: connected" in first


@pytest.mark.asyncio
async def test_stream_yields_published_event() -> None:
    bus = EventBus()
    q = bus.subscribe()
    bus.publish("photo_imported", {"count": 3})
    gen = bus.stream(q)
    await gen.__anext__()  # connected
    event_str = await gen.__anext__()
    await gen.aclose()
    assert "event: photo_imported" in event_str
    assert "count" in event_str


@pytest.mark.asyncio
async def test_stream_unsubscribes_on_close() -> None:
    bus = EventBus()
    q = bus.subscribe()
    bus.publish("dummy", {})  # pre-fill so second __anext__ returns immediately
    gen = bus.stream(q)
    await gen.__anext__()  # connected (outside try block)
    await gen.__anext__()  # published event (generator now suspended inside try block)
    await gen.aclose()  # GeneratorExit thrown inside try → finally runs → unsubscribe
    assert q not in bus._queues


@pytest.mark.asyncio
async def test_stream_yields_ping_on_timeout() -> None:
    bus = EventBus()
    q = bus.subscribe()

    original_wait_for = asyncio.wait_for

    async def fast_timeout(coro: object, timeout: float) -> object:  # noqa: ARG001
        if hasattr(coro, "close"):
            coro.close()
        raise TimeoutError

    gen = bus.stream(q)
    await gen.__anext__()  # connected

    import unittest.mock as mock

    with mock.patch("stamped.core.events.asyncio.wait_for", side_effect=fast_timeout):
        ping = await gen.__anext__()

    await gen.aclose()
    assert ping.startswith(": ping")
    _ = original_wait_for
