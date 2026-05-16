from pathlib import Path

from stamped.workers.gpx_worker import parse_gpx

_GPX_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk><trkseg>
    <trkpt lat="{lat0}" lon="{lon0}">
      <ele>{ele0}</ele><time>{t0}</time>
    </trkpt>
    <trkpt lat="{lat1}" lon="{lon1}">
      <ele>{ele1}</ele><time>{t1}</time>
    </trkpt>
    <trkpt lat="{lat2}" lon="{lon2}">
      <ele>{ele2}</ele><time>{t2}</time>
    </trkpt>
  </trkseg></trk>
</gpx>"""

_GPX_NO_TIME = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk><trkseg>
    <trkpt lat="45.0" lon="6.0"><ele>1000</ele></trkpt>
    <trkpt lat="45.1" lon="6.1"><ele>1100</ele></trkpt>
  </trkseg></trk>
</gpx>"""


def _make_gpx(path: Path) -> Path:
    content = _GPX_TEMPLATE.format(
        lat0="45.832",
        lon0="6.865",
        ele0="1200",
        t0="2024-07-14T08:00:00Z",
        lat1="45.840",
        lon1="6.872",
        ele1="1350",
        t1="2024-07-14T09:00:00Z",
        lat2="45.851",
        lon2="6.880",
        ele2="1480",
        t2="2024-07-14T10:30:00Z",
    )
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_gpx_returns_correct_point_count(tmp_path: Path) -> None:
    gpx = _make_gpx(tmp_path / "track.gpx")
    result = parse_gpx(gpx)
    assert result is not None
    assert result.point_count == 3


def test_parse_gpx_returns_correct_time_range(tmp_path: Path) -> None:
    gpx = _make_gpx(tmp_path / "track.gpx")
    result = parse_gpx(gpx)
    assert result is not None
    assert result.recorded_at_start == "2024-07-14T08:00:00Z"
    assert result.recorded_at_end == "2024-07-14T10:30:00Z"


def test_parse_gpx_trackpoints_have_correct_coords(tmp_path: Path) -> None:
    gpx = _make_gpx(tmp_path / "track.gpx")
    result = parse_gpx(gpx)
    assert result is not None
    assert abs(result.trackpoints[0].lat - 45.832) < 0.001
    assert abs(result.trackpoints[0].lon - 6.865) < 0.001


def test_parse_gpx_trackpoints_have_elevation(tmp_path: Path) -> None:
    gpx = _make_gpx(tmp_path / "track.gpx")
    result = parse_gpx(gpx)
    assert result is not None
    assert result.trackpoints[0].alt == 1200.0


def test_parse_gpx_without_timestamps_returns_none(tmp_path: Path) -> None:
    gpx_path = tmp_path / "no_time.gpx"
    gpx_path.write_text(_GPX_NO_TIME, encoding="utf-8")
    result = parse_gpx(gpx_path)
    assert result is None


def test_parse_gpx_missing_file_returns_none(tmp_path: Path) -> None:
    result = parse_gpx(tmp_path / "nonexistent.gpx")
    assert result is None


def test_parse_gpx_computes_positive_distance(tmp_path: Path) -> None:
    gpx = _make_gpx(tmp_path / "track.gpx")
    result = parse_gpx(gpx)
    assert result is not None
    assert result.total_distance_m > 0


def test_parse_gpx_computes_positive_elevation_gain(tmp_path: Path) -> None:
    gpx = _make_gpx(tmp_path / "track.gpx")
    result = parse_gpx(gpx)
    assert result is not None
    assert result.elevation_gain_m > 0
