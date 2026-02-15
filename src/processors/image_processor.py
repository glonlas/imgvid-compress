"""Processor for converting images to AVIF."""

from pathlib import Path

from ..converters.image_converter import ImageConverter
from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils
from ..validators.image_validator import ImageValidator
from .base_processor import BaseProcessor


class ImageProcessor(BaseProcessor):
    """Processes images by converting them to AVIF."""

    def __init__(self, converter: ImageConverter = None, validator: ImageValidator = None):
        self.validator = validator or ImageValidator()
        self.converter = converter or ImageConverter()
        self.logger = LoggerConfig.get_logger(__name__)

    def get_destination_path(self, source_path: Path, dest_root: Path, source_root: Path) -> Path:
        return PathUtils.get_destination_path(
            source_path, dest_root, source_root, new_extension=".avif"
        )

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        return self.validator.should_skip(source_path, dest_path)

    def execute(self, source_path: Path, dest_path: Path, force: bool) -> bool:
        # Validate source before conversion
        if not self.validator.is_valid_image(source_path):
            self.logger.error(f"[red]Invalid source image[/red] {source_path.name}, skipping")
            return False
        return self.converter.convert(source_path, dest_path, force=force)
