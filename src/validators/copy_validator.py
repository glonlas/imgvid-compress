"""Copy validator for comparing file size and modification times."""

from pathlib import Path

from .base_validator import BaseValidator


class CopyValidator(BaseValidator):
    """Validates whether a copy operation can be skipped."""

    @staticmethod
    def should_skip(source_path: Path, dest_path: Path) -> bool:
        """
        Determine if file copy should be skipped (file already exists with same size).

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            True if copy should be skipped, False otherwise
        """
        return BaseValidator._should_skip_base(source_path, dest_path, check_size_match=True)
