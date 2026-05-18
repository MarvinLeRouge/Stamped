import logging
from pathlib import Path

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


def generate_thumbnail(source_path: Path, dest_path: Path, size: int = 400) -> bool:
    """
    Generate a JPEG thumbnail from source_path and write it to dest_path.

    Applies EXIF orientation correction, resizes to fit within (size × size)
    while preserving aspect ratio. Creates parent directories as needed.
    Pure — no DB access. Returns True on success, False on any failure.
    """
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source_path) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail((size, size), Image.LANCZOS)
            img = img.convert("RGB")
            img.save(dest_path, format="JPEG", quality=85, optimize=True)
        return True
    except Exception:
        logger.warning("Failed to generate thumbnail for %s", source_path, exc_info=True)
        return False
