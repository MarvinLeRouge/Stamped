from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from stamped.api.main import app
from stamped.core.config import settings


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


def test_lifespan_initializes_db() -> None:
    with TestClient(app) as client:
        r = client.get("/api/status")
        assert r.status_code == 200


def test_sse_events_returns_streaming_response(monkeypatch: pytest.MonkeyPatch) -> None:
    from stamped.core import events as events_mod

    async def _finite_stream(
        q: object,
    ) -> AsyncGenerator[str, None]:
        yield 'event: connected\ndata: {"timestamp": "2024-01-01T00:00:00Z"}\n\n'

    monkeypatch.setattr(events_mod.bus, "stream", _finite_stream)

    with TestClient(app) as client, client.stream("GET", "/api/events") as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        line = next(r.iter_lines())
        assert "connected" in line


def test_dev_notice_when_no_frontend(monkeypatch: pytest.MonkeyPatch) -> None:
    from stamped.api import main as main_mod

    monkeypatch.setattr(main_mod, "_FRONTEND_DIST", Path("/nonexistent/dist"))

    with TestClient(app) as client:
        r = client.get("/")
        assert r.status_code in (200, 404)
