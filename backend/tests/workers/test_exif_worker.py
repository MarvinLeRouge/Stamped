from pathlib import Path
from typing import Any

from stamped.workers.exif_worker import ExifData, _parse_datetime, _parse_gps, extract_exif
from tests.conftest import make_jpeg


def test_extract_exif_returns_correct_gps(tmp_path: Path) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg", lat=45.832, lon=6.865, dt_str="2024:07:14 10:30:00")
    result = extract_exif(jpeg)
    assert result.lat is not None
    assert result.lon is not None
    assert abs(result.lat - 45.832) < 0.001
    assert abs(result.lon - 6.865) < 0.001


def test_extract_exif_returns_correct_datetime(tmp_path: Path) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg", dt_str="2024:07:14 10:30:00")
    result = extract_exif(jpeg)
    assert result.captured_at == "2024-07-14T10:30:00Z"


def test_extract_exif_returns_correct_make_model(tmp_path: Path) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg", make="Canon", model="EOS R5")
    result = extract_exif(jpeg)
    assert result.camera_make == "Canon"
    assert result.camera_model == "EOS R5"


def test_extract_exif_without_gps_returns_none_coordinates(tmp_path: Path) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg", dt_str="2024:07:14 10:30:00")
    result = extract_exif(jpeg)
    assert result.lat is None
    assert result.lon is None


def test_extract_exif_southern_hemisphere_negative_lat(tmp_path: Path) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg", lat=-33.868, lon=151.209)
    result = extract_exif(jpeg)
    assert result.lat is not None
    assert result.lat < 0
    assert abs(result.lat - (-33.868)) < 0.001


def test_extract_exif_western_hemisphere_negative_lon(tmp_path: Path) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg", lat=48.858, lon=-2.294)
    result = extract_exif(jpeg)
    assert result.lon is not None
    assert result.lon < 0


def test_extract_exif_missing_file_returns_empty(tmp_path: Path) -> None:
    result = extract_exif(tmp_path / "nonexistent.jpg")
    assert result == ExifData(None, None, None, None, None)


def test_parse_gps_returns_none_on_malformed_rational() -> None:
    class BrokenRational:
        @property
        def num(self) -> float:
            raise AttributeError("broken")

        den: int = 1

    class FakeTag:
        values: list[Any] = [BrokenRational(), BrokenRational(), BrokenRational()]

    lat, lon = _parse_gps({"GPS GPSLatitude": FakeTag(), "GPS GPSLongitude": FakeTag()})
    assert lat is None
    assert lon is None


def test_parse_datetime_skips_malformed_value() -> None:
    class FakeTag:
        values = "not-a-valid-date"

    result = _parse_datetime({"EXIF DateTimeOriginal": FakeTag()})
    assert result is None
