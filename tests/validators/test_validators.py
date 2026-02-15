import os
from pathlib import Path

import pytest
from PIL import Image

from src.validators.base_validator import BaseValidator
from src.validators.copy_validator import CopyValidator
from src.validators.image_validator import ImageValidator
from src.validators.video_validator import VideoValidator


def test_base_validator_should_skip_base_conditions(tmp_path: Path):
    source = tmp_path / "source.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("data")

    assert BaseValidator._should_skip_base(source, dest) is False

    dest.write_text("")
    assert BaseValidator._should_skip_base(source, dest) is False

    dest.write_text("different")
    assert BaseValidator._should_skip_base(source, dest, check_size_match=True) is False

    dest.write_text("data")
    os.utime(dest, (source.stat().st_atime, source.stat().st_mtime + 10))
    assert BaseValidator._should_skip_base(source, dest, check_size_match=True) is True


def test_base_validator_should_skip_not_implemented(tmp_path: Path):
    with pytest.raises(NotImplementedError):
        BaseValidator.should_skip(tmp_path / "a", tmp_path / "b")


def test_copy_validator_should_skip_size_mismatch(tmp_path: Path):
    source = tmp_path / "source.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("data")
    dest.write_text("other")

    assert CopyValidator.should_skip(source, dest) is False


def test_copy_validator_should_skip_when_newer_and_same_size(tmp_path: Path):
    source = tmp_path / "source.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("data")
    dest.write_text("data")
    os.utime(dest, (source.stat().st_atime, source.stat().st_mtime + 10))

    assert CopyValidator.should_skip(source, dest) is True


def test_video_validator_should_skip_when_newer(tmp_path: Path):
    source = tmp_path / "source.mp4"
    dest = tmp_path / "dest.mp4"
    source.write_text("data")
    dest.write_text("data")
    os.utime(dest, (source.stat().st_atime, source.stat().st_mtime + 10))

    assert VideoValidator.should_skip(source, dest) is True


def test_video_validator_should_not_skip_missing_destination(tmp_path: Path):
    source = tmp_path / "source.mp4"
    dest = tmp_path / "dest.mp4"
    source.write_text("data")

    assert VideoValidator.should_skip(source, dest) is False


def test_image_validator_is_valid_image_cases(tmp_path: Path):
    validator = ImageValidator()

    missing = tmp_path / "missing.jpg"
    assert validator.is_valid_image(missing) is False

    empty = tmp_path / "empty.jpg"
    empty.write_bytes(b"")
    assert validator.is_valid_image(empty) is False

    invalid = tmp_path / "invalid.jpg"
    invalid.write_text("not an image")
    assert validator.is_valid_image(invalid) is False

    valid = tmp_path / "valid.png"
    Image.new("RGB", (1, 1)).save(valid)
    assert validator.is_valid_image(valid) is True


def test_image_validator_should_skip_logic(tmp_path: Path):
    validator = ImageValidator()

    source = tmp_path / "source.png"
    Image.new("RGB", (1, 1)).save(source)

    dest = tmp_path / "dest.avif"
    Image.new("RGB", (1, 1)).save(dest)
    os.utime(dest, (source.stat().st_atime, source.stat().st_mtime + 10))

    assert validator.should_skip(source, dest) is True

    dest.unlink()
    assert validator.should_skip(source, dest) is False

    dest.write_text("not an image")
    os.utime(dest, (source.stat().st_atime, source.stat().st_mtime + 10))

    assert validator.should_skip(source, dest) is False
