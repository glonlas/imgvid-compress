"""Video validator for determining whether compression should be skipped."""
from pathlib import Path
from .base_validator import BaseValidator

class VideoValidator(BaseValidator):
    """Validates whether a video conversion can be skipped."""

    @staticmethod
    def should_skip(source_path: Path, dest_path: Path) -> bool:
        pass
