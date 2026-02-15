"""Base validator with shared skip logic."""

from pathlib import Path


class BaseValidator:
    """Base class for validators with common skip logic."""

    @staticmethod
    def _should_skip_base(
        source_path: Path, dest_path: Path, check_size_match: bool = False
    ) -> bool:
        """
        Common logic for determining if an operation should be skipped.

        Args:
            source_path: Source file path
            dest_path: Destination file path
            check_size_match: If True, also verify sizes match (for copies)

        Returns:
            True if operation should be skipped, False otherwise
        """
        if not dest_path.exists():
            return False

        dest_stat = dest_path.stat()
        if dest_stat.st_size == 0:
            return False

        source_stat = source_path.stat()

        if check_size_match and source_stat.st_size != dest_stat.st_size:
            return False

        return dest_stat.st_mtime >= source_stat.st_mtime

    @staticmethod
    def should_skip(source_path: Path, dest_path: Path) -> bool:
        """
        Determine if operation should be skipped. Override in subclasses.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            True if operation should be skipped, False otherwise
        """
        raise NotImplementedError("Subclasses must implement should_skip()")
