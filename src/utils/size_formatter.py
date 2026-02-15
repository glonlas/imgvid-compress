"""Size formatter utility for human-readable sizes."""


class SizeFormatter:
    """Formats byte sizes into human-readable strings."""

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Convert bytes to human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string (e.g., "123.45 MB")
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
