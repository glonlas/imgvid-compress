"""File scanner for identifying images, videos, and other files in directory trees."""
from pathlib import Path
from typing import Dict, List, Set, Tuple
from ..core.logger_config import LoggerConfig

class FileScanner:
    """Scans directories for images, videos, and other files."""

    def __init__(self):
        raise NotImplementedError()

    @staticmethod
    def _iter_files(source_path: Path):
        raise NotImplementedError()

    def _categorize_file(self, file_path: Path, image_files: List[Path], video_files: List[Path], other_files: List[Path]) -> None:
        raise NotImplementedError()

    def _log_deleted_summary(self, deleted_count: int, dry_run: bool) -> None:
        raise NotImplementedError()

    def scan(self, source_path: Path, dry_run: bool=False, delete_originals: bool=True) -> Tuple[List[Path], List[Path], List[Path]]:
        raise NotImplementedError()

    def _remove_redundant_originals(self, folder_map: Dict[str, List[Path]], dry_run: bool=False) -> int:
        raise NotImplementedError()
