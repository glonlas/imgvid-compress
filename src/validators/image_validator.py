"""Image validator for checking file integrity and resume logic."""
from pathlib import Path
from PIL import Image
from ..core.logger_config import LoggerConfig
from .base_validator import BaseValidator

class ImageValidator(BaseValidator):
    """Validates image files and checks whether conversion should be skipped."""

    def __init__(self):
        raise NotImplementedError()

    def is_valid_image(self, file_path: Path) -> bool:
        raise NotImplementedError()

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        raise NotImplementedError()
