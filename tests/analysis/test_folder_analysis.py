from pathlib import Path

from src.analysis.folder_analyzer import FolderAnalyzer
from src.analysis.folder_stats import FolderStats


def test_analyze_skips_unstatable_files(tmp_path: Path, monkeypatch):
    good_file = tmp_path / "good.txt"
    bad_file = tmp_path / "bad.txt"
    good_file.write_text("ok")
    bad_file.write_text("bad")

    expected_size = good_file.stat().st_size
    original_stat = Path.stat
    original_is_file = Path.is_file

    def fake_stat(self: Path, *args, **kwargs):
        if self.name == "bad.txt":
            raise OSError("cannot stat")
        return original_stat(self, *args, **kwargs)

    def fake_is_file(self: Path):
        if self.name == "bad.txt":
            return True
        return original_is_file(self)

    monkeypatch.setattr(Path, "stat", fake_stat)
    monkeypatch.setattr(Path, "is_file", fake_is_file)

    stats = FolderAnalyzer().analyze(tmp_path)

    assert stats.file_count == 1
    assert stats.size_bytes == expected_size


def test_calculate_savings_handles_zero_original():
    saved, percent = FolderAnalyzer.calculate_savings(0, 0)

    assert saved == 0
    assert percent == 0.0


def test_calculate_savings_normal_case():
    saved, percent = FolderAnalyzer.calculate_savings(100, 40)

    assert saved == 60
    assert percent == 60.0


def test_folder_stats_formatted_size():
    stats = FolderStats(size_bytes=1024, file_count=2)

    assert stats.formatted_size == "1.00 KB"
