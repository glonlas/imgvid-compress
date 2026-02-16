import logging
import runpy
import sys
from types import SimpleNamespace

import pytest

from src import main as main_module


def test_parse_arguments_requires_folder(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog"])

    with pytest.raises(SystemExit):
        main_module.parse_arguments()


def test_parse_arguments_parses_values(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "/tmp",
            "--quality",
            "90",
            "--video-crf",
            "30",
            "--video-preset",
            "fast",
            "--video-codec",
            "av1",
            "--verbose",
            "--force",
            "--dry-run",
            "--images-only",
            "--keep-originals",
        ],
    )

    args = main_module.parse_arguments()

    assert args.folder == "/tmp"
    assert args.quality == 90
    assert args.video_crf == 30
    assert args.video_preset == "fast"
    assert args.video_codec == "av1"
    assert args.verbose is True
    assert args.force is True
    assert args.dry_run is True
    assert args.images_only is True
    assert args.videos_only is False
    assert args.keep_originals is True


def test_parse_arguments_rejects_conflicting_modes(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "/tmp", "--images-only", "--videos-only"],
    )

    with pytest.raises(SystemExit):
        main_module.parse_arguments()


def test_validate_quality_clamps(monkeypatch):
    called = {"warned": False}

    class DummyLogger:
        def warning(self, _msg):
            called["warned"] = True

    monkeypatch.setattr(main_module.LoggerConfig, "get_logger", lambda _name: DummyLogger())

    assert main_module.validate_quality(200) == 100
    assert called["warned"] is True


def test_validate_quality_accepts_valid_value():
    assert main_module.validate_quality(85) == 85


def test_validate_video_crf_accepts_h265_and_av1():
    assert main_module.validate_video_crf(51, "h265") == 51
    assert main_module.validate_video_crf(63, "av1") == 63


def test_validate_video_crf_rejects_invalid_ranges():
    with pytest.raises(ValueError):
        main_module.validate_video_crf(52, "h265")
    with pytest.raises(ValueError):
        main_module.validate_video_crf(64, "av1")
    with pytest.raises(ValueError):
        main_module.validate_video_crf(-1, "h265")


def test_main_success_path(monkeypatch):
    args = SimpleNamespace(
        folder="folder",
        quality=85,
        video_crf=28,
        video_preset="medium",
        video_codec="h265",
        force=False,
        dry_run=False,
        images_only=False,
        videos_only=False,
        keep_originals=False,
        verbose=False,
    )

    created = {}

    class DummyOrchestrator:
        def __init__(self, **kwargs):
            created["kwargs"] = kwargs

        def process(self, folder):
            created["folder"] = folder

    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(
        main_module.LoggerConfig, "setup", lambda level: created.setdefault("level", level)
    )
    monkeypatch.setattr(main_module, "ConverterOrchestrator", DummyOrchestrator)

    main_module.main()

    assert created["level"] == logging.INFO
    assert created["folder"] == "folder"
    assert created["kwargs"]["delete_originals"] is True


def test_main_keyboard_interrupt(monkeypatch):
    args = SimpleNamespace(
        folder="folder",
        quality=85,
        video_crf=28,
        video_preset="medium",
        video_codec="h265",
        force=False,
        dry_run=False,
        images_only=False,
        videos_only=False,
        keep_originals=False,
        verbose=False,
    )

    class DummyOrchestrator:
        def __init__(self, **_kwargs):
            pass

        def process(self, _folder):
            raise KeyboardInterrupt

    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ConverterOrchestrator", DummyOrchestrator)

    with pytest.raises(SystemExit) as excinfo:
        main_module.main()

    assert excinfo.value.code == 130


def test_main_exception_path(monkeypatch):
    args = SimpleNamespace(
        folder="folder",
        quality=85,
        video_crf=28,
        video_preset="medium",
        video_codec="h265",
        force=False,
        dry_run=False,
        images_only=False,
        videos_only=False,
        keep_originals=False,
        verbose=True,
    )

    class DummyOrchestrator:
        def __init__(self, **_kwargs):
            pass

        def process(self, _folder):
            raise RuntimeError("boom")

    class DummyLogger:
        def error(self, _msg):
            return None

    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ConverterOrchestrator", DummyOrchestrator)
    monkeypatch.setattr(main_module.LoggerConfig, "get_logger", lambda _name: DummyLogger())

    with pytest.raises(SystemExit) as excinfo:
        main_module.main()

    assert excinfo.value.code == 1


def test_main_invalid_video_crf_exits(monkeypatch):
    args = SimpleNamespace(
        folder="folder",
        quality=85,
        video_crf=99,
        video_preset="medium",
        video_codec="h265",
        force=False,
        dry_run=False,
        images_only=False,
        videos_only=False,
        keep_originals=False,
        verbose=False,
    )

    class DummyLogger:
        def error(self, _msg):
            return None

    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module.LoggerConfig, "get_logger", lambda _name: DummyLogger())

    with pytest.raises(SystemExit) as excinfo:
        main_module.main()

    assert excinfo.value.code == 1


def test_main_module_entrypoint(monkeypatch, tmp_path):
    created = {}

    class DummyOrchestrator:
        def __init__(self, **kwargs):
            created["kwargs"] = kwargs

        def process(self, folder):
            created["folder"] = folder

    dummy_module = SimpleNamespace(ConverterOrchestrator=DummyOrchestrator)
    monkeypatch.setitem(sys.modules, "src.orchestrator.converter_orchestrator", dummy_module)
    monkeypatch.setattr(sys, "argv", ["prog", str(tmp_path)])

    runpy.run_module("src.main", run_name="__main__")

    assert created["folder"] == str(tmp_path)
