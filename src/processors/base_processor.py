"""Base processor for handling conversion/copy operations."""
from collections.abc import Iterable
from pathlib import Path
from typing import Dict

class BaseProcessor:
    """Base class for processing files with shared skip/dry-run logic."""

    def process_files(self, files: Iterable[Path], dest_root: Path, source_root: Path, tracker, dry_run: bool, force: bool) -> Dict[str, int]:
        raise NotImplementedError()

    def get_destination_path(self, source_path: Path, dest_root: Path, source_root: Path) -> Path:
        raise NotImplementedError()

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        raise NotImplementedError()

    def execute(self, source_path: Path, dest_path: Path, force: bool) -> bool:
        raise NotImplementedError()
