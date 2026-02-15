from pathlib import Path
from types import SimpleNamespace

import pytest

from src.processors.base_processor import BaseProcessor
from src.processors.copy_processor import CopyProcessor
from src.processors.image_processor import ImageProcessor
from src.processors.video_processor import VideoProcessor
from src.utils.path_utils import PathUtils


class DummyTracker:
    def __init__(self):
        self.calls = []

    def update(self, increment: int = 1, success: bool = True):
        self.calls.append((increment, success))


class DummyProcessor(BaseProcessor):
    def __init__(self, skip_names=None, execute_results=None):
        self.skip_names = skip_names or set()
        self.execute_results = execute_results or {}

    def get_destination_path(self, source_path: Path, dest_root: Path, source_root: Path) -> Path:
        return dest_root / source_path.name

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        return source_path.name in self.skip_names

    def execute(self, source_path: Path, dest_path: Path, force: bool) -> bool:
        return self.execute_results.get(source_path.name, True)


def test_base_processor_process_files_with_skip_and_failures(tmp_path: Path):
    files = [tmp_path / "a.txt", tmp_path / "b.txt", tmp_path / "c.txt"]
    for path in files:
        path.write_text("data")

    processor = DummyProcessor(
        skip_names={"a.txt"},
        execute_results={"b.txt": True, "c.txt": False},
    )
    tracker = DummyTracker()

    stats = processor.process_files(
        files,
        tmp_path / "dest",
        tmp_path,
        tracker,
        dry_run=False,
        force=False,
    )

    assert stats == {"converted": 1, "skipped": 1, "failed": 1}
    assert len(tracker.calls) == 3


def test_base_processor_process_files_dry_run(tmp_path: Path):
    files = [tmp_path / "a.txt", tmp_path / "b.txt"]
    for path in files:
        path.write_text("data")

    processor = DummyProcessor()

    def fail_execute(*_args, **_kwargs):
        raise AssertionError("execute should not be called during dry run")

    processor.execute = fail_execute
    tracker = DummyTracker()

    stats = processor.process_files(
        files,
        tmp_path / "dest",
        tmp_path,
        tracker,
        dry_run=True,
        force=False,
    )

    assert stats == {"converted": 2, "skipped": 0, "failed": 0}


def test_base_processor_abstract_methods_raise(tmp_path: Path):
    base = BaseProcessor()

    with pytest.raises(NotImplementedError):
        base.get_destination_path(tmp_path, tmp_path, tmp_path)
    with pytest.raises(NotImplementedError):
        base.should_skip(tmp_path, tmp_path)
    with pytest.raises(NotImplementedError):
        base.execute(tmp_path, tmp_path, force=False)


def test_copy_processor_delegates_to_dependencies(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.txt"
    dest_root = tmp_path / "dest"
    sentinel = tmp_path / "sentinel.txt"

    monkeypatch.setattr(PathUtils, "get_destination_path", lambda *_args, **_kwargs: sentinel)

    validator = SimpleNamespace(should_skip=lambda _s, _d: True)
    copier = SimpleNamespace(copy=lambda _s, _d, force=False: False)

    processor = CopyProcessor(copier=copier, validator=validator)

    assert processor.get_destination_path(source, dest_root, tmp_path) == sentinel
    assert processor.should_skip(source, sentinel) is True
    assert processor.execute(source, sentinel, force=True) is False


def test_image_processor_execute_invalid_image(tmp_path: Path):
    source = tmp_path / "source.jpg"
    dest = tmp_path / "dest.avif"

    validator = SimpleNamespace(is_valid_image=lambda _p: False, should_skip=lambda _s, _d: False)
    converter = SimpleNamespace(convert=lambda _s, _d, force=False: True)

    processor = ImageProcessor(converter=converter, validator=validator)

    assert processor.execute(source, dest, force=False) is False


def test_image_processor_execute_valid_image(tmp_path: Path):
    source = tmp_path / "source.jpg"
    dest = tmp_path / "dest.avif"

    validator = SimpleNamespace(is_valid_image=lambda _p: True, should_skip=lambda _s, _d: False)
    converter = SimpleNamespace(convert=lambda _s, _d, force=False: True)

    processor = ImageProcessor(converter=converter, validator=validator)

    assert processor.execute(source, dest, force=False) is True


def test_image_processor_paths_and_skip(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.jpg"
    dest_root = tmp_path / "dest"
    source_root = tmp_path
    sentinel = tmp_path / "dest" / "source.avif"

    monkeypatch.setattr(PathUtils, "get_destination_path", lambda *_args, **_kwargs: sentinel)

    validator = SimpleNamespace(is_valid_image=lambda _p: True, should_skip=lambda _s, _d: True)
    converter = SimpleNamespace(convert=lambda _s, _d, force=False: True)
    processor = ImageProcessor(converter=converter, validator=validator)

    assert processor.get_destination_path(source, dest_root, source_root) == sentinel
    assert processor.should_skip(source, sentinel) is True


def test_video_processor_target_codec_cache(tmp_path: Path):
    source = tmp_path / "video.mp4"
    calls = {"count": 0}

    def is_target(_path):
        calls["count"] += 1
        return True

    converter = SimpleNamespace(is_target_codec=is_target, convert=lambda *_args, **_kwargs: True)
    copier = SimpleNamespace(copy=lambda *_args, **_kwargs: True)

    processor = VideoProcessor(converter=converter, copier=copier)

    assert processor._is_target_codec(source) is True
    assert processor._is_target_codec(source) is True
    assert calls["count"] == 1


def test_video_processor_routing_and_destination(tmp_path: Path, monkeypatch):
    source = tmp_path / "video.mov"
    dest_root = tmp_path / "dest"
    source_root = tmp_path

    converter = SimpleNamespace(
        is_target_codec=lambda _p: False, convert=lambda *_args, **_kwargs: True
    )
    copier = SimpleNamespace(copy=lambda *_args, **_kwargs: True)
    video_validator = SimpleNamespace(should_skip=lambda _s, _d: False)
    copy_validator = SimpleNamespace(should_skip=lambda _s, _d: True)

    processor = VideoProcessor(
        converter=converter,
        copier=copier,
        video_validator=video_validator,
        copy_validator=copy_validator,
    )

    captured = {}

    def fake_get_destination_path(_s, _d, _r, new_extension=None):
        captured["ext"] = new_extension
        return dest_root / "out.mp4"

    monkeypatch.setattr(PathUtils, "get_destination_path", fake_get_destination_path)

    assert processor.get_destination_path(source, dest_root, source_root).name == "out.mp4"
    assert captured["ext"] == ".mp4"
    assert processor.should_skip(source, dest_root / "out.mp4") is False
    assert processor.execute(source, dest_root / "out.mp4", force=False) is True

    processor._target_codec_cache[str(source)] = True
    captured.clear()
    assert processor.get_destination_path(source, dest_root, source_root).name == "out.mp4"
    assert captured["ext"] is None
    assert processor.should_skip(source, dest_root / "out.mp4") is True
    assert processor.execute(source, dest_root / "out.mp4", force=True) is True
