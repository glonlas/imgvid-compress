from pathlib import Path
from types import SimpleNamespace

import pytest

from src.analysis.folder_stats import FolderStats
from src.orchestrator import converter_orchestrator
from src.orchestrator.converter_orchestrator import ConverterOrchestrator


class DummyProgressTracker:
    def __init__(self, total_files, console=None):
        self.total_files = total_files
        self.console = console

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def update(self, increment: int = 1, success: bool = True):
        return None


class DummyScanner:
    def __init__(self, image_files, video_files, other_files):
        self._result = (image_files, video_files, other_files)

    def scan(self, _source_path, dry_run=False, delete_originals=True):
        return self._result


class DummyAnalyzer:
    def __init__(self, original_stats, new_stats=None):
        self.original_stats = original_stats
        self.new_stats = new_stats or original_stats
        self.calls = []

    def analyze(self, _path):
        self.calls.append(_path)
        if len(self.calls) == 1:
            return self.original_stats
        return self.new_stats

    def calculate_savings(self, original_size, new_size):
        return (original_size - new_size, 50.0)


class DummyProcessor:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def process_files(self, files, dest_path, source_path, tracker, dry_run, force):
        self.calls.append(
            {
                "files": list(files),
                "dest": dest_path,
                "source": source_path,
                "dry_run": dry_run,
                "force": force,
            }
        )
        return self.result


class DummyVideoConverter:
    def __init__(self, *_args, **_kwargs):
        return None


def _make_orchestrator(monkeypatch, **kwargs):
    monkeypatch.setattr(converter_orchestrator, "VideoConverter", DummyVideoConverter)
    return ConverterOrchestrator(**kwargs)


def test_orchestrator_init_video_disabled(monkeypatch):
    def raise_converter(*_args, **_kwargs):
        raise RuntimeError("ffmpeg missing")

    monkeypatch.setattr(converter_orchestrator, "VideoConverter", raise_converter)

    orchestrator = ConverterOrchestrator()

    assert orchestrator.video_converter is None
    assert orchestrator.video_processor is None


def test_orchestrator_validate_source(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)

    assert orchestrator.validate_source(tmp_path / "missing") is False

    file_path = tmp_path / "file.txt"
    file_path.write_text("data")
    assert orchestrator.validate_source(file_path) is False

    assert orchestrator.validate_source(tmp_path) is True


def test_orchestrator_get_destination_path(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)

    dest_path = orchestrator.get_destination_path(tmp_path)

    assert dest_path.name.endswith("_compressed")


def test_orchestrator_handle_existing_destination(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    dest_path = tmp_path / "dest"
    dest_path.mkdir()

    orchestrator.force = False
    assert orchestrator.handle_existing_destination(dest_path) is True

    orchestrator.force = True
    assert orchestrator.handle_existing_destination(dest_path) is True


def test_orchestrator_display_header_modes(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    orchestrator.console = SimpleNamespace(print=lambda *_args, **_kwargs: None)

    source = tmp_path / "source"
    dest = tmp_path / "dest"

    orchestrator.images_only = True
    orchestrator.display_header(source, dest)

    orchestrator.images_only = False
    orchestrator.videos_only = True
    orchestrator.display_header(source, dest)

    orchestrator.videos_only = False
    orchestrator.video_converter = None
    orchestrator.delete_originals = False
    orchestrator.display_header(source, dest)


def test_orchestrator_display_scan_results_modes(monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    orchestrator.console = SimpleNamespace(print=lambda *_args, **_kwargs: None)
    original_stats = FolderStats(size_bytes=10, file_count=1)

    orchestrator.videos_only = True
    orchestrator.display_scan_results(1, 2, 3, original_stats)

    orchestrator.videos_only = False
    orchestrator.images_only = True
    orchestrator.display_scan_results(1, 2, 3, original_stats)

    orchestrator.images_only = False
    orchestrator.video_converter = None
    orchestrator.display_scan_results(1, 2, 3, original_stats)


def test_orchestrator_display_results_branches(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    orchestrator.console = SimpleNamespace(print=lambda *_args, **_kwargs: None)
    orchestrator.analyzer = DummyAnalyzer(FolderStats(size_bytes=10, file_count=1))

    orchestrator.dry_run = True
    orchestrator.display_results(
        {"converted": 1, "skipped": 1, "failed": 1},
        10,
        5,
        tmp_path,
    )

    orchestrator.dry_run = False
    orchestrator.display_results(
        {"converted": 1, "skipped": 1, "failed": 1},
        10,
        5,
        tmp_path,
    )


def test_orchestrator_merge_stats(monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)

    base = {"converted": 1, "skipped": 2, "failed": 3}
    update = {"converted": 2, "skipped": 1, "failed": 0}

    assert orchestrator._merge_stats(base, update) == {"converted": 3, "skipped": 3, "failed": 3}


def test_orchestrator_log_phase_adds_spacer_and_logs(monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    printed = {"count": 0}
    logged = {"message": None}

    orchestrator.console = SimpleNamespace(
        print=lambda *_args, **_kwargs: printed.__setitem__("count", printed["count"] + 1)
    )
    orchestrator.logger = SimpleNamespace(info=lambda msg: logged.__setitem__("message", msg))

    message = "[cyan]Phase 1/3: Copying non-processable files...[/cyan]"
    orchestrator._log_phase(message)

    assert printed["count"] == 1
    assert logged["message"] == message


def test_orchestrator_process_invalid_source_exits(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    monkeypatch.setattr(orchestrator, "validate_source", lambda _path: False)

    with pytest.raises(SystemExit) as excinfo:
        orchestrator.process(str(tmp_path))

    assert excinfo.value.code == 1


def test_orchestrator_process_no_files_exits(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    orchestrator.console = SimpleNamespace(print=lambda *_args, **_kwargs: None)
    orchestrator.scanner = DummyScanner([], [], [])
    orchestrator.analyzer = DummyAnalyzer(FolderStats(size_bytes=0, file_count=0))

    monkeypatch.setattr(orchestrator, "display_header", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "handle_existing_destination", lambda _path: True)

    with pytest.raises(SystemExit) as excinfo:
        orchestrator.process(str(tmp_path))

    assert excinfo.value.code == 0


def test_orchestrator_process_existing_destination_exits(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    orchestrator.console = SimpleNamespace(print=lambda *_args, **_kwargs: None)

    monkeypatch.setattr(orchestrator, "handle_existing_destination", lambda _path: False)
    monkeypatch.setattr(orchestrator, "display_header", lambda *_args, **_kwargs: None)

    with pytest.raises(SystemExit) as excinfo:
        orchestrator.process(str(tmp_path))

    assert excinfo.value.code == 0


def test_orchestrator_process_videos_only_dry_run(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch, dry_run=True, videos_only=True)
    orchestrator.console = SimpleNamespace(print=lambda *_args, **_kwargs: None)

    image_files = [tmp_path / "image.jpg"]
    image_files[0].write_text("img")
    orchestrator.scanner = DummyScanner(image_files, [], [])
    orchestrator.analyzer = DummyAnalyzer(FolderStats(size_bytes=1, file_count=1))

    copy_processor = DummyProcessor({"converted": 1, "skipped": 0, "failed": 0})
    orchestrator.copy_processor = copy_processor

    monkeypatch.setattr(orchestrator, "display_header", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "display_scan_results", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "display_results", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(converter_orchestrator, "ProgressTracker", DummyProgressTracker)

    orchestrator.process(str(tmp_path))

    assert copy_processor.calls


def test_orchestrator_process_images_only(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch, images_only=True)
    orchestrator.console = SimpleNamespace(print=lambda *_args, **_kwargs: None)

    image_files = [tmp_path / "image.jpg"]
    video_files = [tmp_path / "video.mp4"]
    image_files[0].write_text("img")
    video_files[0].write_text("vid")

    orchestrator.scanner = DummyScanner(image_files, video_files, [])
    orchestrator.analyzer = DummyAnalyzer(FolderStats(size_bytes=1, file_count=2))

    orchestrator.copy_processor = DummyProcessor({"converted": 1, "skipped": 0, "failed": 0})
    orchestrator.image_processor = DummyProcessor({"converted": 1, "skipped": 0, "failed": 0})

    monkeypatch.setattr(orchestrator, "display_header", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "display_scan_results", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "display_results", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(converter_orchestrator, "ProgressTracker", DummyProgressTracker)

    orchestrator.process(str(tmp_path))

    assert orchestrator.image_processor.calls
    assert orchestrator.copy_processor.calls


def test_orchestrator_process_video_processor_missing(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    orchestrator.console = SimpleNamespace(print=lambda *_args, **_kwargs: None)

    video_files = [tmp_path / "video.mp4"]
    video_files[0].write_text("vid")

    orchestrator.scanner = DummyScanner([], video_files, [])
    orchestrator.analyzer = DummyAnalyzer(FolderStats(size_bytes=1, file_count=1))
    orchestrator.copy_processor = DummyProcessor({"converted": 1, "skipped": 0, "failed": 0})
    orchestrator.video_processor = None

    monkeypatch.setattr(orchestrator, "display_header", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "display_scan_results", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "display_results", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(converter_orchestrator, "ProgressTracker", DummyProgressTracker)

    orchestrator.process(str(tmp_path))

    assert orchestrator.copy_processor.calls


def test_orchestrator_process_normal_flow(tmp_path: Path, monkeypatch):
    orchestrator = _make_orchestrator(monkeypatch)
    orchestrator.console = SimpleNamespace(print=lambda *_args, **_kwargs: None)

    image_files = [tmp_path / "image.jpg"]
    video_files = [tmp_path / "video.mp4"]
    other_files = [tmp_path / "note.txt"]
    image_files[0].write_text("img")
    video_files[0].write_text("vid")
    other_files[0].write_text("note")

    orchestrator.scanner = DummyScanner(image_files, video_files, other_files)
    orchestrator.analyzer = DummyAnalyzer(
        FolderStats(size_bytes=3, file_count=3),
        FolderStats(size_bytes=1, file_count=3),
    )

    orchestrator.copy_processor = DummyProcessor({"converted": 1, "skipped": 0, "failed": 0})
    orchestrator.image_processor = DummyProcessor({"converted": 1, "skipped": 0, "failed": 0})
    orchestrator.video_processor = DummyProcessor({"converted": 1, "skipped": 0, "failed": 0})

    monkeypatch.setattr(orchestrator, "display_header", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "display_scan_results", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orchestrator, "display_results", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(converter_orchestrator, "ProgressTracker", DummyProgressTracker)

    orchestrator.process(str(tmp_path))

    assert orchestrator.copy_processor.calls
    assert orchestrator.image_processor.calls
    assert orchestrator.video_processor.calls
