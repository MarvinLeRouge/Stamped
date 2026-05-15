import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import exifread

logger = logging.getLogger(__name__)

_DT_FORMAT = "%Y:%m:%d %H:%M:%S"
_DT_KEYS = ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime")


@dataclass
class ExifData:
    captured_at: str | None
    lat: float | None
    lon: float | None
    camera_make: str | None
    camera_model: str | None


def _ratio_to_float(value: Any) -> float:
    return value.num / value.den if value.den != 0 else 0.0


def _dms_to_decimal(dms_values: Any, ref: str) -> float:
    degrees = _ratio_to_float(dms_values[0])
    minutes = _ratio_to_float(dms_values[1])
    seconds = _ratio_to_float(dms_values[2])
    decimal = degrees + minutes / 60.0 + seconds / 3600.0
    return -decimal if ref in ("S", "W") else decimal


def _parse_gps(tags: dict[str, Any]) -> tuple[float | None, float | None]:
    lat_tag = tags.get("GPS GPSLatitude")
    lon_tag = tags.get("GPS GPSLongitude")
    if not (lat_tag and lon_tag):
        return None, None
    try:
        lat_ref = str(tags.get("GPS GPSLatitudeRef", "N"))
        lon_ref = str(tags.get("GPS GPSLongitudeRef", "E"))
        return (
            _dms_to_decimal(lat_tag.values, lat_ref),
            _dms_to_decimal(lon_tag.values, lon_ref),
        )
    except Exception:
        logger.debug("GPS parse error in %s", exc_info=True)
        return None, None


def _parse_datetime(tags: dict[str, Any]) -> str | None:
    for key in _DT_KEYS:
        tag = tags.get(key)
        if not tag:
            continue
        try:
            dt = datetime.strptime(str(tag.values), _DT_FORMAT)  # noqa: DTZ007
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return None


def extract_exif(file_path: Path) -> ExifData:
    """Extract EXIF metadata from a JPEG file. Pure — no side effects."""
    try:
        with file_path.open("rb") as f:
            tags = exifread.process_file(f, stop_tag="GPS GPSLongitude", details=False)
    except OSError:
        logger.warning("Cannot open %s", file_path)
        return ExifData(None, None, None, None, None)

    lat, lon = _parse_gps(tags)
    make_tag = tags.get("Image Make")
    model_tag = tags.get("Image Model")

    return ExifData(
        captured_at=_parse_datetime(tags),
        lat=lat,
        lon=lon,
        camera_make=str(make_tag.values).strip() if make_tag else None,
        camera_model=str(model_tag.values).strip() if model_tag else None,
    )
