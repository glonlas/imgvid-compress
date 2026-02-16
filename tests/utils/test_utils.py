from pathlib import Path

import pytest

from src.utils.path_utils import PathUtils
from src.utils.size_formatter import SizeFormatter


def test_get_destination_path_changes_extension(tmp_path: Path):
    source_root = tmp_path / "source"
    dest_root = tmp_path / "dest"
    file_path = source_root / "sub" / "file.jpg"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("data")

    dest_path = PathUtils.get_destination_path(
        file_path,
        dest_root,
        source_root,
        new_extension=".avif",
    )

    assert dest_path == dest_root / "sub" / "file.avif"


def test_get_destination_path_preserves_extension(tmp_path: Path):
    source_root = tmp_path / "source"
    dest_root = tmp_path / "dest"
    file_path = source_root / "file.txt"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("data")

    dest_path = PathUtils.get_destination_path(file_path, dest_root, source_root)

    assert dest_path == dest_root / "file.txt"


def test_ensure_parent_dir_creates(tmp_path: Path):
    target = tmp_path / "nested" / "folder" / "file.txt"

    PathUtils.ensure_parent_dir(target)

    assert target.parent.is_dir()


def test_ensure_parent_dir_raises_when_parent_is_file(tmp_path: Path):
    file_parent = tmp_path / "parent"
    file_parent.write_text("not a dir")
    target = file_parent / "child.txt"

    with pytest.raises(FileExistsError):
        PathUtils.ensure_parent_dir(target)


def test_format_size_bytes_and_petabytes():
    assert SizeFormatter.format_size(1) == "1.00 B"
    petabytes = 1024**5
    assert SizeFormatter.format_size(petabytes).endswith(" PB")
