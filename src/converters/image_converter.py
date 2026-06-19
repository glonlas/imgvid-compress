"""Image converter for converting images to AVIF format."""

import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pillow_heif
from PIL import Image

from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils

# Register HEIF opener to enable HEIC/HEIF format support
pillow_heif.register_heif_opener()


class ImageConverter:
    """Converts images to AVIF format with quality control."""

    _EXIF_DATETIME_ORIGINAL = 36867
    _EXIF_DATETIME_DIGITIZED = 36868
    _EXIF_DATETIME_MODIFIED = 306
    _EXIF_SUBSEC_ORIGINAL = 37521
    _EXIF_SUBSEC_DIGITIZED = 37522
    _EXIF_SUBSEC_MODIFIED = 37520
    _EXIF_OFFSET_ORIGINAL = 36881
    _EXIF_OFFSET_DIGITIZED = 36882
    _EXIF_OFFSET_MODIFIED = 36880

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
        xmp_path = self._get_xmp_path(dest_path)
        try:
            source_stat = source_path.stat()
            oldest_timestamp = self._get_oldest_filesystem_timestamp(source_stat)
            capture_datetime = datetime.fromtimestamp(oldest_timestamp, tz=timezone.utc)

            # Ensure destination directory exists
            PathUtils.ensure_parent_dir(dest_path)

            # Open and convert image
            with Image.open(source_path) as img:
                exif_bytes = self._extract_exif_bytes(img)
                extracted_datetime = self._extract_capture_datetime(img)
                if extracted_datetime is not None:
                    capture_datetime = extracted_datetime

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
                save_kwargs = {"quality": self.quality}
                if exif_bytes is not None:
                    save_kwargs["exif"] = exif_bytes
                img.save(dest_path, "AVIF", **save_kwargs)

            # Validate the converted file exists and has content
            if not dest_path.exists() or dest_path.stat().st_size == 0:
                self.logger.error(f"[red]Conversion produced invalid file[/red] {dest_path.name}")
                if dest_path.exists():
                    dest_path.unlink()
                return False

            self._write_xmp_sidecar(xmp_path, capture_datetime)
            self._preserve_timestamps(source_stat, dest_path, mtime=source_stat.st_mtime)
            self._preserve_timestamps(source_stat, xmp_path, mtime=source_stat.st_mtime)

            return True

        except Exception as e:
            self.logger.error(f"[red]Failed to convert[/red] {source_path.name}: {str(e)}")
            # Clean up partial file if it exists
            if dest_path.exists():
                try:
                    dest_path.unlink()
                except OSError:
                    pass
            if xmp_path.exists():
                try:
                    xmp_path.unlink()
                except OSError:
                    pass
            return False

    @staticmethod
    def _get_xmp_path(dest_path: Path) -> Path:
        return dest_path.with_suffix(".xmp")

    @staticmethod
    def _get_oldest_filesystem_timestamp(source_stat: os.stat_result) -> float:
        created_ts = getattr(source_stat, "st_birthtime", None)
        if created_ts is None:
            created_ts = source_stat.st_ctime
        return min(source_stat.st_mtime, created_ts)

    @staticmethod
    def _extract_exif_bytes(image: Image.Image) -> Optional[bytes]:
        info_exif = getattr(image, "info", {}).get("exif")
        if isinstance(info_exif, (bytes, bytearray)):
            return bytes(info_exif)

        if not hasattr(image, "getexif"):
            return None

        exif = image.getexif()
        if not exif or not hasattr(exif, "tobytes"):
            return None

        try:
            return exif.tobytes()
        except Exception:
            return None

    def _extract_capture_datetime(self, image: Image.Image) -> Optional[datetime]:
        if not hasattr(image, "getexif"):
            return None

        exif = image.getexif()
        if not exif:
            return None

        datetime_raw = (
            exif.get(self._EXIF_DATETIME_ORIGINAL)
            or exif.get(self._EXIF_DATETIME_DIGITIZED)
            or exif.get(self._EXIF_DATETIME_MODIFIED)
        )
        if not datetime_raw:
            return None

        subsec_raw = (
            exif.get(self._EXIF_SUBSEC_ORIGINAL)
            or exif.get(self._EXIF_SUBSEC_DIGITIZED)
            or exif.get(self._EXIF_SUBSEC_MODIFIED)
        )
        offset_raw = (
            exif.get(self._EXIF_OFFSET_ORIGINAL)
            or exif.get(self._EXIF_OFFSET_DIGITIZED)
            or exif.get(self._EXIF_OFFSET_MODIFIED)
        )

        parsed = self._parse_exif_datetime(datetime_raw)
        if parsed is None:
            return None

        microseconds = self._extract_microseconds(subsec_raw)
        if microseconds is not None:
            parsed = parsed.replace(microsecond=microseconds)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=self._parse_exif_offset(offset_raw) or timezone.utc)

        return parsed

    @staticmethod
    def _parse_exif_datetime(datetime_raw: object) -> Optional[datetime]:
        text = str(datetime_raw).strip()
        if not text:
            return None

        try:
            return datetime.strptime(text[:19], "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass

        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _extract_microseconds(subsec_raw: object) -> Optional[int]:
        if subsec_raw is None:
            return None

        digits = "".join(ch for ch in str(subsec_raw) if ch.isdigit())
        if not digits:
            return None

        return int((digits + "000000")[:6])

    @staticmethod
    def _parse_exif_offset(offset_raw: object) -> Optional[timezone]:
        if offset_raw is None:
            return None

        match = re.fullmatch(r"([+-])(\d{2}):?(\d{2})", str(offset_raw).strip())
        if not match:
            return None

        sign, hours, minutes = match.groups()
        delta = timedelta(hours=int(hours), minutes=int(minutes))
        if sign == "-":
            delta = -delta

        return timezone(delta)

    def _write_xmp_sidecar(self, xmp_path: Path, capture_datetime: datetime) -> None:
        capture_iso = self._format_datetime_for_xmp(capture_datetime)
        xmp_content = (
            "<?xpacket begin='\ufeff' id='W5M0MpCehiHzreSzNTczkc9d'?>\n"
            "<x:xmpmeta xmlns:x='adobe:ns:meta/' x:xmptk='imgvid-compress'>\n"
            "<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>\n"
            "\n"
            " <rdf:Description rdf:about=''\n"
            "  xmlns:exif='http://ns.adobe.com/exif/1.0/'>\n"
            f"  <exif:DateTimeOriginal>{capture_iso}</exif:DateTimeOriginal>\n"
            " </rdf:Description>\n"
            "\n"
            " <rdf:Description rdf:about=''\n"
            "  xmlns:photoshop='http://ns.adobe.com/photoshop/1.0/'>\n"
            f"  <photoshop:DateCreated>{capture_iso}</photoshop:DateCreated>\n"
            " </rdf:Description>\n"
            "</rdf:RDF>\n"
            "</x:xmpmeta>\n"
            "<?xpacket end='w'?>\n"
        )
        xmp_path.write_text(xmp_content, encoding="utf-8")

    @staticmethod
    def _format_datetime_for_xmp(capture_datetime: datetime) -> str:
        if capture_datetime.tzinfo is None:
            capture_datetime = capture_datetime.replace(tzinfo=timezone.utc)
        return capture_datetime.isoformat(timespec="milliseconds")

    @staticmethod
    def _preserve_timestamps(source_stat: os.stat_result, target_path: Path, mtime: float) -> None:
        os.utime(target_path, (source_stat.st_atime, mtime))
