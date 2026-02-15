"""Copy validator for comparing file size and modification times."""
from pathlib import Path
from .base_validator import BaseValidator

class CopyValidator(BaseValidator):
    """Validates whether a copy operation can be skipped."""

    @staticmethod
    def should_skip(source_path: Path, dest_path: Path) -> bool:
        raise NotImplementedError()
