from pathlib import Path
from src.scan.file_scanner import FileScanner

def _create_sample_files(base: Path) -> None:
    pass

def test_scan_dry_run_keeps_originals(tmp_path: Path):
    pass

def test_scan_deletes_redundant_originals(tmp_path: Path):
    pass

def test_scan_skip_deleting_originals(tmp_path: Path):
    pass

def test_remove_redundant_originals_dry_run(tmp_path: Path):
    pass

def test_remove_redundant_originals_unlink_error(tmp_path: Path, monkeypatch):
    pass

def test_scan_multiple_directories_triggers_cleanup(tmp_path: Path):
    pass

def test_iter_files_returns_sorted_files_only(tmp_path: Path):
    pass
