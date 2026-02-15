"""Processor for converting images to AVIF."""
from pathlib import Path
from ..converters.image_converter import ImageConverter
from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils
from ..validators.image_validator import ImageValidator
from .base_processor import BaseProcessor

class ImageProcessor(BaseProcessor):
    """Processes images by converting them to AVIF."""

    def __init__(self, converter: ImageConverter=None, validator: ImageValidator=None):
        raise NotImplementedError()

    def get_destination_path(self, source_path: Path, dest_root: Path, source_root: Path) -> Path:
        raise NotImplementedError()

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        raise NotImplementedError()

    def execute(self, source_path: Path, dest_path: Path, force: bool) -> bool:
        raise NotImplementedError()
