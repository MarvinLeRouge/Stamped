from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from stamped.api.main import app
from stamped.core.config import settings
from stamped.core.db import init_db


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


@pytest.fixture()
def client() -> TestClient:
    init_db()
    return TestClient(app)


def _fake_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


def test_legacy_url_redirects_to_osm_layer(client: TestClient) -> None:
    r = client.get("/tiles/5/16/11.png", follow_redirects=False)
    assert r.status_code in (301, 302, 307, 308)
    assert "osm" in r.headers["location"]


def test_tile_fetches_from_osm_on_cache_miss(client: TestClient) -> None:
    mock_response = MagicMock()
    mock_response.content = _fake_png()
    mock_response.raise_for_status = MagicMock()

    with patch("stamped.api.tiles.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.get = AsyncMock(return_value=mock_response)

        r = client.get("/tiles/osm/5/16/11")

    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_tile_cached_after_first_fetch(client: TestClient, tmp_path: Path) -> None:
    mock_response = MagicMock()
    mock_response.content = _fake_png()
    mock_response.raise_for_status = MagicMock()

    with patch("stamped.api.tiles.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.get = AsyncMock(return_value=mock_response)

        client.get("/tiles/osm/5/16/11")
        tile_path = settings.data_dir / "tiles" / "osm" / "5" / "16" / "11.png"
        assert tile_path.exists()

        mock_client.return_value.get.reset_mock()
        r = client.get("/tiles/osm/5/16/11")
        mock_client.return_value.get.assert_not_called()

    assert r.status_code == 200


def test_tile_topo_layer_fetches_and_caches(client: TestClient) -> None:
    mock_response = MagicMock()
    mock_response.content = _fake_png()
    mock_response.raise_for_status = MagicMock()

    with patch("stamped.api.tiles.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.get = AsyncMock(return_value=mock_response)

        r = client.get("/tiles/topo/5/16/11")
        tile_path = settings.data_dir / "tiles" / "topo" / "5" / "16" / "11.png"
        assert tile_path.exists()

    assert r.status_code == 200


def test_tile_satellite_layer_returns_jpeg(client: TestClient) -> None:
    mock_response = MagicMock()
    mock_response.content = b"\xff\xd8\xff" + b"\x00" * 8
    mock_response.raise_for_status = MagicMock()

    with patch("stamped.api.tiles.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.get = AsyncMock(return_value=mock_response)

        r = client.get("/tiles/satellite/5/16/11")

    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"


def test_tile_unknown_layer_returns_404(client: TestClient) -> None:
    r = client.get("/tiles/unknown/5/16/11")
    assert r.status_code == 404


def test_tile_returns_502_on_fetch_error(client: TestClient) -> None:
    import httpx

    with patch("stamped.api.tiles.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.get = AsyncMock(
            side_effect=httpx.NetworkError("connection failed")
        )

        r = client.get("/tiles/osm/5/16/11")

    assert r.status_code == 502
