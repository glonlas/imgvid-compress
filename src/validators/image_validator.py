"""Image validator for checking file integrity and resume logic."""

from pathlib import Path

from PIL import Image

from ..core.logger_config import LoggerConfig
from .base_validator import BaseValidator


class ImageValidator(BaseValidator):
    """Validates image files and checks whether conversion should be skipped."""

    def __init__(self):
        self.logger = LoggerConfig.get_logger(__name__)

    def is_valid_image(self, file_path: Path) -> bool:
        """
        Check if a file is a valid image that can be opened.

        Args:
            file_path: Path to the image file

        Returns:
            True if valid image, False otherwise
        """
        if not file_path.exists():
            return False

        if file_path.stat().st_size == 0:
            self.logger.warning(f"[yellow]Empty file:[/yellow] {file_path.name}")
            return False

        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception as exc:
            self.logger.debug(f"Invalid image {file_path.name}: {str(exc)}")
            return False

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        """
        Determine if image conversion should be skipped.

        Args:
            source_path: Source image file path
            dest_path: Destination AVIF file path

        Returns:
            True if conversion should be skipped, False otherwise
        """
        # Use base check first (exists, size > 0, mtime)
        if not BaseValidator._should_skip_base(source_path, dest_path):
            return False

        # Additional check: validate the destination image is readable
        if not self.is_valid_image(dest_path):
            self.logger.debug(f"Destination file is invalid, will reconvert: {dest_path.name}")
            return False

        xmp_path = dest_path.with_suffix(".xmp")
        if not BaseValidator._should_skip_base(source_path, xmp_path):
            self.logger.debug(f"XMP sidecar missing or stale, will reconvert: {xmp_path.name}")
            return False

        return True
