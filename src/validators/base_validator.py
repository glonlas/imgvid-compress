"""Base validator with shared skip logic."""
from pathlib import Path

class BaseValidator:
    """Base class for validators with common skip logic."""

    @staticmethod
    def _should_skip_base(source_path: Path, dest_path: Path, check_size_match: bool=False) -> bool:
        pass

    @staticmethod
    def should_skip(source_path: Path, dest_path: Path) -> bool:
        pass
