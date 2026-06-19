import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.converters.file_copier import FileCopier
from src.converters.image_converter import ImageConverter
from src.converters.video_converter import VideoConverter
from src.utils.path_utils import PathUtils


class DummyImage:
    def __init__(self, mode="RGB", exif=None, info=None):
        self.mode = mode
        self.size = (1, 1)
        self._exif = exif or {}
        self.info = info or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def split(self):
        return [None, None, None, None]

    def paste(self, _img, mask=None):
        return None

    def convert(self, _mode):
        self.mode = _mode
        return self

    def save(self, dest_path, _fmt, quality=None, exif=None):
        Path(dest_path).write_bytes(b"data")

    def getexif(self):
        return self._exif


def test_file_copier_missing_source(tmp_path: Path):
    copier = FileCopier()
    source = tmp_path / "missing.txt"
    dest = tmp_path / "dest.txt"

    assert copier.copy(source, dest, force=False) is False


def test_file_copier_copy_size_mismatch(tmp_path: Path, monkeypatch):
    copier = FileCopier()
    source = tmp_path / "source.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("data")

    def fake_copy(_src, dst):
        Path(dst).write_text("short")

    monkeypatch.setattr("shutil.copy2", fake_copy)

    assert copier.copy(source, dest, force=False) is False


def test_file_copier_copy_success(tmp_path: Path):
    copier = FileCopier()
    source = tmp_path / "source.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("data")

    assert copier.copy(source, dest, force=False) is True


def test_file_copier_copy_exception(tmp_path: Path, monkeypatch):
    copier = FileCopier()
    source = tmp_path / "source.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("data")

    def fake_copy(_src, _dst):
        raise OSError("boom")

    monkeypatch.setattr("shutil.copy2", fake_copy)

    assert copier.copy(source, dest, force=False) is False


def test_image_converter_quality_clamps():
    converter = ImageConverter(quality=150)

    assert converter.quality == 100


def test_image_converter_convert_invalid_output(tmp_path: Path, monkeypatch):
    converter = ImageConverter()
    source = tmp_path / "source.png"
    dest = tmp_path / "dest.avif"
    source.write_text("data")

    dummy = DummyImage(mode="RGB")

    def fake_open(_path):
        return dummy

    def fake_save(_self, dest_path, _fmt, quality=None):
        Path(dest_path).write_bytes(b"")

    monkeypatch.setattr("src.converters.image_converter.Image.open", fake_open)
    monkeypatch.setattr(DummyImage, "save", fake_save, raising=False)

    assert converter.convert(source, dest, force=False) is False
    assert dest.exists() is False


def test_image_converter_convert_rgba_success(tmp_path: Path, monkeypatch):
    converter = ImageConverter()
    source = tmp_path / "source.png"
    dest = tmp_path / "dest.avif"
    source.write_text("data")

    monkeypatch.setattr(
        "src.converters.image_converter.Image.open", lambda _p: DummyImage(mode="RGBA")
    )
    monkeypatch.setattr(
        "src.converters.image_converter.Image.new", lambda *_args, **_kwargs: DummyImage()
    )

    assert converter.convert(source, dest, force=False) is True
    assert dest.exists() is True


def test_image_converter_convert_la_success(tmp_path: Path, monkeypatch):
    converter = ImageConverter()
    source = tmp_path / "source.png"
    dest = tmp_path / "dest.avif"
    source.write_text("data")

    monkeypatch.setattr(
        "src.converters.image_converter.Image.open", lambda _p: DummyImage(mode="LA")
    )
    monkeypatch.setattr(
        "src.converters.image_converter.Image.new", lambda *_args, **_kwargs: DummyImage()
    )

    assert converter.convert(source, dest, force=False) is True
    assert dest.exists() is True


def test_image_converter_convert_non_rgb_success(tmp_path: Path, monkeypatch):
    converter = ImageConverter()
    source = tmp_path / "source.png"
    dest = tmp_path / "dest.avif"
    source.write_text("data")

    monkeypatch.setattr(
        "src.converters.image_converter.Image.open", lambda _p: DummyImage(mode="L")
    )

    assert converter.convert(source, dest, force=False) is True
    assert dest.exists() is True


def test_image_converter_preserves_timestamps_and_writes_xmp(tmp_path: Path, monkeypatch):
    converter = ImageConverter()
    source = tmp_path / "source.jpg"
    dest = tmp_path / "dest.avif"
    source.write_bytes(b"data")
    os.utime(source, (1234567890, 1234567890))

    exif = {36867: "2021:01:28 18:52:37", 37521: "779", 36881: "+00:00"}
    monkeypatch.setattr(
        "src.converters.image_converter.Image.open", lambda _p: DummyImage(mode="RGB", exif=exif)
    )

    assert converter.convert(source, dest, force=False) is True
    assert dest.exists() is True

    xmp_path = dest.with_suffix(".xmp")
    assert xmp_path.exists() is True
    xmp_text = xmp_path.read_text(encoding="utf-8")
    assert (
        "<exif:DateTimeOriginal>2021-01-28T18:52:37.779+00:00</exif:DateTimeOriginal>" in xmp_text
    )
    assert (
        "<photoshop:DateCreated>2021-01-28T18:52:37.779+00:00</photoshop:DateCreated>" in xmp_text
    )

    assert int(dest.stat().st_mtime) == int(source.stat().st_mtime)
    assert int(xmp_path.stat().st_mtime) == int(source.stat().st_mtime)


def test_image_converter_uses_oldest_filesystem_timestamp():
    converter = ImageConverter()
    stat_like = SimpleNamespace(st_mtime=2000.0, st_birthtime=1000.0, st_ctime=3000.0)
    assert converter._get_oldest_filesystem_timestamp(stat_like) == 1000.0

    stat_like_no_birth = SimpleNamespace(st_mtime=2000.0, st_ctime=1500.0)
    assert converter._get_oldest_filesystem_timestamp(stat_like_no_birth) == 1500.0


def test_image_converter_passes_exif_to_avif_save(tmp_path: Path, monkeypatch):
    converter = ImageConverter()
    source = tmp_path / "source.jpg"
    dest = tmp_path / "dest.avif"
    source.write_bytes(b"data")

    captured = {}

    class ExifImage(DummyImage):
        def save(self, dest_path, _fmt, quality=None, exif=None):
            captured["exif"] = exif
            Path(dest_path).write_bytes(b"data")

    monkeypatch.setattr(
        "src.converters.image_converter.Image.open",
        lambda _p: ExifImage(mode="RGB", info={"exif": b"raw-exif-bytes"}),
    )

    assert converter.convert(source, dest, force=False) is True
    assert captured["exif"] == b"raw-exif-bytes"


def test_image_converter_convert_exception_cleanup(tmp_path: Path, monkeypatch):
    converter = ImageConverter()
    source = tmp_path / "source.png"
    dest = tmp_path / "dest.avif"
    source.write_text("data")
    dest.write_text("partial")

    def fake_open(_path):
        raise OSError("bad image")

    monkeypatch.setattr("src.converters.image_converter.Image.open", fake_open)

    assert converter.convert(source, dest, force=False) is False
    assert dest.exists() is False


def test_image_converter_convert_cleanup_unlink_failure(tmp_path: Path, monkeypatch):
    converter = ImageConverter()
    source = tmp_path / "source.png"
    dest = tmp_path / "dest.avif"
    source.write_text("data")
    dest.write_text("partial")

    def fake_open(_path):
        raise OSError("bad image")

    original_unlink = Path.unlink

    def fake_unlink(self: Path):
        if self == dest:
            raise OSError("cannot remove")
        return original_unlink(self)

    monkeypatch.setattr("src.converters.image_converter.Image.open", fake_open)
    monkeypatch.setattr(Path, "unlink", fake_unlink)

    assert converter.convert(source, dest, force=False) is False
    assert dest.exists() is True


def test_video_converter_init_invalid_codec(monkeypatch):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)

    converter = VideoConverter(codec="weird")

    assert converter.codec == "h265"


def test_video_converter_init_missing_ffmpeg(monkeypatch):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: False)

    with pytest.raises(RuntimeError):
        VideoConverter()


def test_video_converter_check_ffmpeg(monkeypatch):
    converter = VideoConverter.__new__(VideoConverter)

    monkeypatch.setattr("shutil.which", lambda _cmd: None)
    assert converter._check_ffmpeg() is False

    monkeypatch.setattr("shutil.which", lambda _cmd: "/usr/bin/ffmpeg")
    assert converter._check_ffmpeg() is True


def test_video_converter_get_video_info_success(monkeypatch):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter()
    info = {"streams": [{"codec_type": "video", "codec_name": "h264"}]}
    result = SimpleNamespace(returncode=0, stdout=json.dumps(info))

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: result)

    assert converter._get_video_info(Path("video.mp4")) == info


def test_video_converter_get_video_info_failure(monkeypatch):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter()
    result = SimpleNamespace(returncode=1, stdout="")

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: result)

    assert converter._get_video_info(Path("video.mp4")) == {}


def test_video_converter_get_video_info_exception(monkeypatch):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter()

    def fake_run(*_args, **_kwargs):
        raise OSError("ffprobe error")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert converter._get_video_info(Path("video.mp4")) == {}


def test_video_converter_get_current_codec(monkeypatch):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter()

    converter._get_video_info = lambda _p: {
        "streams": [{"codec_type": "video", "codec_name": "hevc"}]
    }
    assert converter._get_current_codec(Path("video.mp4")) == "hevc"

    converter._get_video_info = lambda _p: {}
    assert converter._get_current_codec(Path("video.mp4")) == ""


def test_video_converter_is_target_codec(monkeypatch):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter(codec="h265")
    converter._get_current_codec = lambda _p: "hevc"

    assert converter.is_target_codec(Path("video.mp4")) is True

    converter.codec = "av1"
    converter._get_current_codec = lambda _p: "h265"

    assert converter.is_target_codec(Path("video.mp4")) is False

    converter.codec = "unknown"
    assert converter.is_target_codec(Path("video.mp4")) is False


def test_video_converter_map_av1_preset(monkeypatch):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter(codec="av1")

    assert converter._map_av1_preset("slow") == 5
    assert converter._map_av1_preset("not-a-preset") == 6


def test_video_converter_convert_missing_source(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter()

    assert converter.convert(tmp_path / "missing.mp4", tmp_path / "dest.mp4") is False


def test_video_converter_convert_ffmpeg_error(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter()
    source = tmp_path / "source.mp4"
    dest = tmp_path / "dest.mp4"
    source.write_bytes(b"data")
    dest.write_text("partial")

    result = SimpleNamespace(returncode=1, stderr="bad")
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: result)

    assert converter.convert(source, dest) is False
    assert dest.exists() is False


def test_video_converter_convert_invalid_output(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter()
    source = tmp_path / "source.mp4"
    dest = tmp_path / "dest.mp4"
    source.write_bytes(b"data")
    dest.write_bytes(b"")

    result = SimpleNamespace(returncode=0, stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: result)

    assert converter.convert(source, dest) is False
    assert dest.exists() is False


def test_video_converter_convert_success(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter()
    source = tmp_path / "source.mp4"
    dest = tmp_path / "dest.mp4"
    source.write_bytes(b"data-data")
    os.utime(source, (1234567890, 1234567890))
    captured = {}

    def fake_run(cmd, *_args, **_kwargs):
        captured["cmd"] = cmd
        Path(cmd[-1]).write_bytes(b"data")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert converter.convert(source, dest) is True
    assert dest.exists() is True
    assert int(dest.stat().st_mtime) == int(source.stat().st_mtime)

    cmd = captured["cmd"]
    assert "-map" in cmd and "0" in cmd
    assert "-map_metadata" in cmd
    assert "-map_chapters" in cmd
    assert cmd[cmd.index("-c:a") + 1] == "copy"
    assert cmd[cmd.index("-c:s") + 1] == "copy"
    assert cmd[cmd.index("-c:d") + 1] == "copy"
    assert cmd[cmd.index("-c:t") + 1] == "copy"


def test_video_converter_convert_av1_fallback(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter(codec="av1", preset="slow")
    source = tmp_path / "source.mp4"
    dest = tmp_path / "dest.mp4"
    source.write_bytes(b"data-data")

    calls = {"count": 0}

    def fake_run(cmd, *_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=1)
        assert "libaom-av1" in cmd
        preset_idx = cmd.index("-preset") + 1
        assert cmd[preset_idx] == "slow"
        Path(cmd[-1]).write_bytes(b"data")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert converter.convert(source, dest) is True
    assert calls["count"] == 2


def test_video_converter_convert_timeout(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter(codec="h265")
    source = tmp_path / "source.mp4"
    dest = tmp_path / "dest.mp4"
    source.write_bytes(b"data")
    dest.write_text("partial")

    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="ffmpeg", timeout=1)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert converter.convert(source, dest) is False
    assert dest.exists() is False


def test_video_converter_convert_unexpected_exception(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter(codec="h265")
    source = tmp_path / "source.mp4"
    dest = tmp_path / "dest.mp4"
    source.write_bytes(b"data")
    dest.write_text("partial")

    def fake_ensure(_path):
        raise OSError("nope")

    monkeypatch.setattr(PathUtils, "ensure_parent_dir", fake_ensure)

    assert converter.convert(source, dest) is False
    assert dest.exists() is False


def test_video_converter_convert_cleanup_unlink_failure(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter(codec="h265")
    source = tmp_path / "source.mp4"
    dest = tmp_path / "dest.mp4"
    source.write_bytes(b"data")
    dest.write_text("partial")

    result = SimpleNamespace(returncode=1, stderr="bad")
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: result)

    original_unlink = Path.unlink

    def fake_unlink(self: Path):
        if self == dest:
            raise OSError("cannot remove")
        return original_unlink(self)

    monkeypatch.setattr(Path, "unlink", fake_unlink)

    assert converter.convert(source, dest) is False
    assert dest.exists() is True


def test_video_converter_cleanup_no_output_file(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(VideoConverter, "_check_ffmpeg", lambda _self: True)
    converter = VideoConverter(codec="h265")
    missing_dest = tmp_path / "missing.mp4"

    converter._cleanup_partial_output(missing_dest)

    assert missing_dest.exists() is False
