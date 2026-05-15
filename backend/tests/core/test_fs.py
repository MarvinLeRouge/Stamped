from pathlib import Path

import pytest

from stamped.core.config import settings
from stamped.core.fs import get_data_dir, get_thumb_path, get_thumbs_dir, get_tiles_dir


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


def test_get_data_dir_creates_directory() -> None:
    path = get_data_dir()
    assert path.exists()
    assert path.is_dir()


def test_get_thumbs_dir_creates_directory() -> None:
    path = get_thumbs_dir()
    assert path.exists()
    assert path.name == "thumbs"


def test_get_tiles_dir_creates_directory() -> None:
    path = get_tiles_dir()
    assert path.exists()
    assert path.name == "tiles"


def test_get_thumb_path_structure() -> None:
    file_hash = "abcdef1234567890"
    thumb = get_thumb_path(file_hash)
    assert thumb.parent.name == "ab"
    assert thumb.name == f"{file_hash}.jpg"


def test_get_thumb_path_different_hashes_use_different_buckets() -> None:
    assert get_thumb_path("aa111").parent != get_thumb_path("bb222").parent
