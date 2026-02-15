"""Base processor for handling conversion/copy operations."""

from collections.abc import Iterable
from pathlib import Path
from typing import Dict


class BaseProcessor:
    """Base class for processing files with shared skip/dry-run logic."""

    def process_files(
        self,
        files: Iterable[Path],
        dest_root: Path,
        source_root: Path,
        tracker,
        dry_run: bool,
        force: bool,
    ) -> Dict[str, int]:
        stats = {"converted": 0, "skipped": 0, "failed": 0}

        for file_path in files:
            dest_path = self.get_destination_path(file_path, dest_root, source_root)

            if not force and self.should_skip(file_path, dest_path):
                stats["skipped"] += 1
                tracker.update(success=True)
                continue

            if dry_run:
                stats["converted"] += 1
                tracker.update(success=True)
                continue

            success = self.execute(file_path, dest_path, force=force)
            if success:
                stats["converted"] += 1
            else:
                stats["failed"] += 1
            tracker.update(success=success)

        return stats

    def get_destination_path(self, source_path: Path, dest_root: Path, source_root: Path) -> Path:
        raise NotImplementedError

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        raise NotImplementedError

    def execute(self, source_path: Path, dest_path: Path, force: bool) -> bool:
        raise NotImplementedError
