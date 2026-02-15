"""Processor for copying files."""

from pathlib import Path

from ..converters.file_copier import FileCopier
from ..utils.path_utils import PathUtils
from ..validators.copy_validator import CopyValidator
from .base_processor import BaseProcessor


class CopyProcessor(BaseProcessor):
    """Processes files by copying them to destination."""

    def __init__(self, copier: FileCopier = None, validator: CopyValidator = None):
        self.validator = validator or CopyValidator()
        self.copier = copier or FileCopier()

    def get_destination_path(self, source_path: Path, dest_root: Path, source_root: Path) -> Path:
        return PathUtils.get_destination_path(source_path, dest_root, source_root)

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        return self.validator.should_skip(source_path, dest_path)

    def execute(self, source_path: Path, dest_path: Path, force: bool) -> bool:
        return self.copier.copy(source_path, dest_path, force=force)
