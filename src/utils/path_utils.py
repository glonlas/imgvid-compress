"""Path utility functions to avoid code duplication."""

from pathlib import Path


class PathUtils:
    """Utility class for path operations."""

    @staticmethod
    def get_destination_path(
        source_path: Path, dest_root: Path, source_root: Path, new_extension: str = None
    ) -> Path:
        """
        Calculate destination path for a file, preserving folder structure.

        Args:
            source_path: Source file path
            dest_root: Destination root directory
            source_root: Source root directory
            new_extension: Optional new file extension (e.g., '.avif')

        Returns:
            Destination file path
        """
        rel_path = source_path.relative_to(source_root)

        if new_extension:
            rel_path = rel_path.with_suffix(new_extension)

        return dest_root / rel_path

    @staticmethod
    def ensure_parent_dir(file_path: Path) -> None:
        """
        Ensure the parent directory of a file exists.

        Args:
            file_path: File path whose parent should be created
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def format_display_path(path: Path) -> str:
        """
        Format path for user-facing logs.

        Converts paths under the user's home directory to `~` form.

        Args:
            path: Path to format

        Returns:
            User-friendly path string
        """
        home = Path.home()
        try:
            rel = path.relative_to(home)
            return "~" if str(rel) == "." else f"~/{rel}"
        except ValueError:
            return str(path)
