from pathlib import Path

from stamped.workers.exif_worker import ExifData, extract_exif
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
