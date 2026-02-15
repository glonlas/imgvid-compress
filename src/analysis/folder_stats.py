"""Folder stats data container."""
from dataclasses import dataclass
from ..utils.size_formatter import SizeFormatter

@dataclass
class FolderStats:
    """Statistics about a folder."""

    @property
    def formatted_size(self) -> str:
        raise NotImplementedError()
