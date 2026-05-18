import io
from pathlib import Path

import piexif
from PIL import Image

from stamped.workers.thumb_worker import generate_thumbnail


def _make_jpeg(path: Path, width: int = 64, height: int = 64, orientation: int = 1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color=(80, 120, 160))
    exif_dict: dict[str, dict[int, object]] = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
    exif_dict["0th"][piexif.ImageIFD.Orientation] = orientation
    exif_bytes = piexif.dump(exif_dict)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif_bytes)
    path.write_bytes(buf.getvalue())
    return path


def test_generate_thumbnail_creates_file(tmp_path: Path) -> None:
    src = _make_jpeg(tmp_path / "src.jpg")
    dest = tmp_path / "thumbs" / "th.jpg"
    assert generate_thumbnail(src, dest) is True
    assert dest.exists()


def test_generate_thumbnail_result_is_jpeg(tmp_path: Path) -> None:
    src = _make_jpeg(tmp_path / "src.jpg")
    dest = tmp_path / "th.jpg"
    generate_thumbnail(src, dest)
    with Image.open(dest) as img:
        assert img.format == "JPEG"


def test_generate_thumbnail_respects_max_size(tmp_path: Path) -> None:
    src = _make_jpeg(tmp_path / "src.jpg", width=800, height=400)
    dest = tmp_path / "th.jpg"
    generate_thumbnail(src, dest, size=400)
    with Image.open(dest) as img:
        assert max(img.size) <= 400


def test_generate_thumbnail_preserves_aspect_ratio(tmp_path: Path) -> None:
    src = _make_jpeg(tmp_path / "src.jpg", width=800, height=400)
    dest = tmp_path / "th.jpg"
    generate_thumbnail(src, dest, size=400)
    with Image.open(dest) as img:
        w, h = img.size
        assert abs(w / h - 2.0) < 0.01


def test_generate_thumbnail_small_image_not_upscaled(tmp_path: Path) -> None:
    src = _make_jpeg(tmp_path / "src.jpg", width=64, height=64)
    dest = tmp_path / "th.jpg"
    generate_thumbnail(src, dest, size=400)
    with Image.open(dest) as img:
        assert max(img.size) <= 64


def test_generate_thumbnail_applies_exif_orientation(tmp_path: Path) -> None:
    # Orientation 6 = 90° CW → portrait becomes landscape after correction
    src = _make_jpeg(tmp_path / "src.jpg", width=200, height=100, orientation=6)
    dest = tmp_path / "th.jpg"
    generate_thumbnail(src, dest, size=400)
    with Image.open(dest) as img:
        w, h = img.size
        assert h > w  # rotated: originally landscape, now portrait


def test_generate_thumbnail_creates_parent_dirs(tmp_path: Path) -> None:
    src = _make_jpeg(tmp_path / "src.jpg")
    dest = tmp_path / "a" / "b" / "c" / "th.jpg"
    assert generate_thumbnail(src, dest) is True
    assert dest.exists()


def test_generate_thumbnail_returns_false_on_missing_source(tmp_path: Path) -> None:
    result = generate_thumbnail(tmp_path / "missing.jpg", tmp_path / "dest.jpg")
    assert result is False


def test_generate_thumbnail_original_untouched(tmp_path: Path) -> None:
    src = _make_jpeg(tmp_path / "src.jpg")
    original_bytes = src.read_bytes()
    dest = tmp_path / "th.jpg"
    generate_thumbnail(src, dest)
    assert src.read_bytes() == original_bytes
