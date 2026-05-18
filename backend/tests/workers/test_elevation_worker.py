from unittest.mock import MagicMock, patch

from stamped.workers.elevation_worker import _BATCH_SIZE, fetch_elevation


def _mock_response(elevations: list[float | None]) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {
        "results": [{"elevation": e} for e in elevations],
        "status": "OK",
    }
    return resp


def test_fetch_elevation_empty_returns_empty() -> None:
    assert fetch_elevation([]) == []


def test_fetch_elevation_returns_altitudes() -> None:
    points = [(45.0, 6.0), (46.0, 7.0)]
    with patch("stamped.workers.elevation_worker.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = _mock_response(
            [1200.0, 1500.0]
        )
        result = fetch_elevation(points)
    assert result == [1200.0, 1500.0]


def test_fetch_elevation_handles_null_elevation() -> None:
    points = [(45.0, 6.0)]
    with patch("stamped.workers.elevation_worker.httpx.Client") as mock_client:
        resp = MagicMock()
        resp.json.return_value = {"results": [{"elevation": None}], "status": "OK"}
        mock_client.return_value.__enter__.return_value.post.return_value = resp
        result = fetch_elevation(points)
    assert result == [None]


def test_fetch_elevation_returns_none_on_network_error() -> None:
    points = [(45.0, 6.0), (46.0, 7.0)]
    with patch("stamped.workers.elevation_worker.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = OSError(
            "network unreachable"
        )
        result = fetch_elevation(points)
    assert result == [None, None]


def test_fetch_elevation_returns_none_on_http_error() -> None:
    points = [(45.0, 6.0)]
    with patch("stamped.workers.elevation_worker.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value.raise_for_status.side_effect = Exception(
            "503"
        )
        result = fetch_elevation(points)
    assert result == [None]


def test_fetch_elevation_splits_into_batches() -> None:
    n = _BATCH_SIZE + 10
    points = [(float(i), float(i)) for i in range(n)]
    call_count = 0

    def fake_post(url: str, json: dict[str, str]) -> MagicMock:  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        count = len(json["locations"].split("|"))
        return _mock_response([float(i) for i in range(count)])

    with patch("stamped.workers.elevation_worker.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = fake_post
        result = fetch_elevation(points)

    assert call_count == 2
    assert len(result) == n


def test_fetch_elevation_second_batch_none_on_error() -> None:
    n = _BATCH_SIZE + 5
    points = [(float(i), float(i)) for i in range(n)]

    responses = [_mock_response([100.0] * _BATCH_SIZE), OSError("fail")]

    with patch("stamped.workers.elevation_worker.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = responses
        result = fetch_elevation(points)

    assert len(result) == n
    assert all(r == 100.0 for r in result[:_BATCH_SIZE])
    assert all(r is None for r in result[_BATCH_SIZE:])
