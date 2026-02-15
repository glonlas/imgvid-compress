"""Folder analyzer for calculating and analyzing folder sizes."""

from pathlib import Path
from typing import Tuple

from .folder_stats import FolderStats


class FolderAnalyzer:
    """Analyzes folder sizes and provides statistics."""

    def analyze(self, folder_path: Path) -> FolderStats:
        """
        Calculate total size and file count of a folder.

        Args:
            folder_path: Path to the folder to analyze

        Returns:
            FolderStats object with size and file count
        """
        total_size = 0
        file_count = 0

        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except OSError:
                    # File may have been deleted during iteration
                    pass

        return FolderStats(size_bytes=total_size, file_count=file_count)

    @staticmethod
    def calculate_savings(original_size: int, new_size: int) -> Tuple[int, float]:
        """
        Calculate size savings.

        Args:
            original_size: Original size in bytes
            new_size: New size in bytes

        Returns:
            Tuple of (saved_bytes, saved_percentage)
        """
        saved_size = original_size - new_size
        saved_percent = (saved_size / original_size * 100) if original_size > 0 else 0.0

        return saved_size, saved_percent
