import io
from pathlib import Path

import piexif
import pytest
from PIL import Image


def _decimal_to_dms(value: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    degrees = int(value)
    minutes_f = (value - degrees) * 60
    minutes = int(minutes_f)
    seconds_f = (minutes_f - minutes) * 60
    seconds = round(seconds_f * 1000)
    return (degrees, 1), (minutes, 1), (seconds, 1000)


def make_jpeg(
    path: Path,
    lat: float | None = None,
    lon: float | None = None,
    dt_str: str | None = None,
    make: str = "TestCam",
    model: str = "TestModel",
) -> Path:
    """Create a minimal JPEG with optional GPS and datetime EXIF."""
    exif_dict: dict[str, dict[int, object]] = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

    exif_dict["0th"][piexif.ImageIFD.Make] = make.encode()
    exif_dict["0th"][piexif.ImageIFD.Model] = model.encode()

    if dt_str:
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = dt_str.encode()

    if lat is not None and lon is not None:
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b"N" if lat >= 0 else b"S"
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = _decimal_to_dms(abs(lat))
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b"E" if lon >= 0 else b"W"
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = _decimal_to_dms(abs(lon))

    exif_bytes = piexif.dump(exif_dict)
    img = Image.new("RGB", (64, 64), color=(80, 120, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif_bytes)
    path.write_bytes(buf.getvalue())
    return path


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
