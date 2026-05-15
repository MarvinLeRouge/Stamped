from pathlib import Path

from stamped.core.config import settings


def get_data_dir() -> Path:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir


def get_thumbs_dir() -> Path:
    path = settings.data_dir / "thumbs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_tiles_dir() -> Path:
    path = settings.data_dir / "tiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_thumb_path(file_hash: str) -> Path:
    bucket = file_hash[:2]
    return get_thumbs_dir() / bucket / f"{file_hash}.jpg"
