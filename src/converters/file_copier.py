"""File copier for copying non-image files to destination."""
import shutil
from pathlib import Path
from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils

class FileCopier:
    """Copies files while preserving folder structure."""

    def __init__(self):
        raise NotImplementedError()

    def copy(self, source_path: Path, dest_path: Path, force: bool=False) -> bool:
        raise NotImplementedError()
