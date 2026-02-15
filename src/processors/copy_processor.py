"""Processor for copying files."""
from pathlib import Path
from ..converters.file_copier import FileCopier
from ..utils.path_utils import PathUtils
from ..validators.copy_validator import CopyValidator
from .base_processor import BaseProcessor

class CopyProcessor(BaseProcessor):
    """Processes files by copying them to destination."""

    def __init__(self, copier: FileCopier=None, validator: CopyValidator=None):
        raise NotImplementedError()

    def get_destination_path(self, source_path: Path, dest_root: Path, source_root: Path) -> Path:
        raise NotImplementedError()

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        raise NotImplementedError()

    def execute(self, source_path: Path, dest_path: Path, force: bool) -> bool:
        raise NotImplementedError()
