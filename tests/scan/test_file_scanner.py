from pathlib import Path

from src.scan.file_scanner import FileScanner


def _create_sample_files(base: Path) -> None:
    (base / "photo.jpg").write_text("jpg")
    (base / "photo.avif").write_text("avif")
    (base / "video.mp4").write_text("video")
    (base / "doc.txt").write_text("doc")


def test_scan_dry_run_keeps_originals(tmp_path: Path):
    _create_sample_files(tmp_path)
    scanner = FileScanner()

    image_files, video_files, other_files = scanner.scan(
        tmp_path,
        dry_run=True,
        delete_originals=True,
    )

    assert (tmp_path / "photo.jpg").exists() is True
    assert any(path.suffix == ".jpg" for path in image_files)
    assert len(video_files) == 1
    assert len(other_files) == 2


def test_scan_deletes_redundant_originals(tmp_path: Path):
    _create_sample_files(tmp_path)
    scanner = FileScanner()

    image_files, _, _ = scanner.scan(
        tmp_path,
        dry_run=False,
        delete_originals=True,
    )

    assert (tmp_path / "photo.jpg").exists() is False
    assert all(path.name != "photo.jpg" for path in image_files)


def test_scan_skip_deleting_originals(tmp_path: Path):
    _create_sample_files(tmp_path)
    scanner = FileScanner()

    image_files, video_files, other_files = scanner.scan(
        tmp_path,
        dry_run=False,
        delete_originals=False,
    )

    assert (tmp_path / "photo.jpg").exists() is True
    assert len(image_files) == 1
    assert len(video_files) == 1
    assert len(other_files) == 2


def test_remove_redundant_originals_dry_run(tmp_path: Path):
    scanner = FileScanner()
    jpg = tmp_path / "img.jpg"
    avif = tmp_path / "img.avif"
    jpg.write_text("jpg")
    avif.write_text("avif")

    folder_map = {"img": [jpg, avif]}

    deleted = scanner._remove_redundant_originals(folder_map, dry_run=True)

    assert deleted == 1
    assert jpg.exists() is True


def test_remove_redundant_originals_unlink_error(tmp_path: Path, monkeypatch):
    scanner = FileScanner()
    jpg = tmp_path / "bad.jpg"
    avif = tmp_path / "bad.avif"
    txt = tmp_path / "note.txt"
    jpg.write_text("jpg")
    avif.write_text("avif")
    txt.write_text("note")

    folder_map = {"bad": [jpg, avif], "note": [txt]}
    original_unlink = Path.unlink

    def fake_unlink(self: Path):
        if self.name == "bad.jpg":
            raise OSError("nope")
        return original_unlink(self)

    monkeypatch.setattr(Path, "unlink", fake_unlink)

    deleted = scanner._remove_redundant_originals(folder_map, dry_run=False)

    assert deleted == 0
    assert jpg.exists() is True


def test_scan_multiple_directories_triggers_cleanup(tmp_path: Path):
    scanner = FileScanner()
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    (first / "one.jpg").write_text("jpg")
    (first / "one.avif").write_text("avif")
    (second / "two.jpg").write_text("jpg")
    (second / "two.avif").write_text("avif")

    image_files, _, _ = scanner.scan(tmp_path, dry_run=True, delete_originals=True)

    assert len(image_files) == 2
    assert (first / "one.jpg").exists() is True
    assert (second / "two.jpg").exists() is True


def test_iter_files_returns_sorted_files_only(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()

    first = tmp_path / "b.txt"
    second = nested / "a.txt"
    first.write_text("b")
    second.write_text("a")

    files = list(FileScanner._iter_files(tmp_path))

    assert files == sorted([first, second])
