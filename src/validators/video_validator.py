"""Video validator for determining whether compression should be skipped."""

from pathlib import Path

from .base_validator import BaseValidator


class VideoValidator(BaseValidator):
    """Validates whether a video conversion can be skipped."""

    @staticmethod
    def should_skip(source_path: Path, dest_path: Path) -> bool:
        """
        Determine if video conversion should be skipped based on size and mtime.

        Args:
            source_path: Source video file path
            dest_path: Destination video file path

        Returns:
            True if conversion should be skipped, False otherwise
        """
        return BaseValidator._should_skip_base(source_path, dest_path, check_size_match=False)
