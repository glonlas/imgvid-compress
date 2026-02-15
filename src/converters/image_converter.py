"""Image converter for converting images to AVIF format."""
from pathlib import Path
import pillow_heif
from PIL import Image
from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils

class ImageConverter:
    """Converts images to AVIF format with quality control."""

    def __init__(self, quality: int=85):
        raise NotImplementedError()

    def convert(self, source_path: Path, dest_path: Path, force: bool=False) -> bool:
        raise NotImplementedError()
