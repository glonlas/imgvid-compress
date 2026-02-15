"""Path utility functions to avoid code duplication."""
from pathlib import Path

class PathUtils:
    """Utility class for path operations."""

    @staticmethod
    def get_destination_path(source_path: Path, dest_root: Path, source_root: Path, new_extension: str=None) -> Path:
        raise NotImplementedError()

    @staticmethod
    def ensure_parent_dir(file_path: Path) -> None:
        raise NotImplementedError()
