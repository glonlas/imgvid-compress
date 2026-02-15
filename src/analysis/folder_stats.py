"""Folder stats data container."""

from dataclasses import dataclass

from ..utils.size_formatter import SizeFormatter


@dataclass
class FolderStats:
    """Statistics about a folder."""

    size_bytes: int
    file_count: int

    @property
    def formatted_size(self) -> str:
        return SizeFormatter.format_size(self.size_bytes)
