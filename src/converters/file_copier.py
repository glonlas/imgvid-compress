"""File copier for copying non-image files to destination."""

import shutil
from pathlib import Path

from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils


class FileCopier:
    """Copies files while preserving folder structure."""

    def __init__(self):
        """Initialize the file copier."""
        self.logger = LoggerConfig.get_logger(__name__)

    def copy(self, source_path: Path, dest_path: Path, force: bool = False) -> bool:
        """
        Copy a file to destination, preserving folder structure.

        Note: Skip logic is handled by CopyProcessor. This method only copies.

        Args:
            source_path: Path to the source file
            dest_path: Path where the file should be copied
            force: Unused, kept for API compatibility

        Returns:
            True if copy was successful, False otherwise
        """
        try:
            # Check if source file exists
            if not source_path.exists():
                self.logger.error(f"[red]Source file not found[/red] {source_path.name}")
                return False

            # Ensure destination directory exists
            PathUtils.ensure_parent_dir(dest_path)

            # Copy file with metadata
            shutil.copy2(source_path, dest_path)

            # Verify the copy
            if dest_path.stat().st_size != source_path.stat().st_size:
                self.logger.error(f"[red]Copy size mismatch[/red] {dest_path.name}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"[red]Failed to copy[/red] {source_path.name}: {str(e)}")
            return False
