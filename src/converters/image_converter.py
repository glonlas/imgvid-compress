"""Image converter for converting images to AVIF format."""

from pathlib import Path

import pillow_heif
from PIL import Image

from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils

# Register HEIF opener to enable HEIC/HEIF format support
pillow_heif.register_heif_opener()


class ImageConverter:
    """Converts images to AVIF format with quality control."""

    def __init__(self, quality: int = 85):
        """
        Initialize the image converter.

        Args:
            quality: AVIF quality setting (0-100, default: 85)
        """
        self.quality = max(0, min(100, quality))  # Clamp between 0-100
        self.logger = LoggerConfig.get_logger(__name__)

    def convert(self, source_path: Path, dest_path: Path, force: bool = False) -> bool:
        """
        Convert an image to AVIF format.

        Note: Skip logic is handled by ImageProcessor. This method only converts.

        Args:
            source_path: Path to the source image
            dest_path: Path where the AVIF image should be saved
            force: Unused, kept for API compatibility

        Returns:
            True if conversion was successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            PathUtils.ensure_parent_dir(dest_path)

            # Open and convert image
            with Image.open(source_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img, mask=img.split()[1])
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Save as AVIF
                img.save(dest_path, "AVIF", quality=self.quality)

            # Validate the converted file exists and has content
            if not dest_path.exists() or dest_path.stat().st_size == 0:
                self.logger.error(f"[red]Conversion produced invalid file[/red] {dest_path.name}")
                if dest_path.exists():
                    dest_path.unlink()
                return False

            return True

        except Exception as e:
            self.logger.error(f"[red]Failed to convert[/red] {source_path.name}: {str(e)}")
            # Clean up partial file if it exists
            if dest_path.exists():
                try:
                    dest_path.unlink()
                except OSError:
                    pass
            return False
