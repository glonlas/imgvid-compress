"""Folder analyzer for calculating and analyzing folder sizes."""
from pathlib import Path
from typing import Tuple
from .folder_stats import FolderStats

class FolderAnalyzer:
    """Analyzes folder sizes and provides statistics."""

    def analyze(self, folder_path: Path) -> FolderStats:
        raise NotImplementedError()

    @staticmethod
    def calculate_savings(original_size: int, new_size: int) -> Tuple[int, float]:
        raise NotImplementedError()
