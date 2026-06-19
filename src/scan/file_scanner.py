"""File scanner for identifying images, videos, and other files in directory trees."""

from pathlib import Path
from typing import Dict, List, Set, Tuple

from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils


class FileScanner:
    """Scans directories for images, videos, and other files."""

    # Supported image formats for conversion (excludes .avif - already target format)
    IMAGE_EXTENSIONS: Set[str] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".gif",
        ".tiff",
        ".tif",
        ".webp",
        ".heic",
        ".heif",
    }

    # Supported video formats for compression
    VIDEO_EXTENSIONS: Set[str] = {
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".m4v",
        ".wmv",
        ".flv",
        ".webm",
        ".mpeg",
        ".mpg",
        ".3gp",
    }

    def __init__(self):
        """Initialize the file scanner."""
        self.logger = LoggerConfig.get_logger(__name__)

    @staticmethod
    def _iter_files(source_path: Path):
        """Yield files under source_path in stable order."""
        for file_path in sorted(source_path.rglob("*")):
            if file_path.is_file():
                yield file_path

    def _categorize_file(
        self,
        file_path: Path,
        image_files: List[Path],
        video_files: List[Path],
        other_files: List[Path],
    ) -> None:
        """Categorize file by extension."""
        file_ext = file_path.suffix.lower()
        if file_ext in self.IMAGE_EXTENSIONS:
            image_files.append(file_path)
            return
        if file_ext in self.VIDEO_EXTENSIONS:
            video_files.append(file_path)
            return
        other_files.append(file_path)

    def _log_deleted_summary(self, deleted_count: int, dry_run: bool) -> None:
        """Log summary for deleted or would-be-deleted originals."""
        if dry_run:
            self.logger.info(
                f"[yellow]Would delete {deleted_count} original image(s) "
                f"with existing AVIF versions[/yellow]"
            )
            return
        self.logger.info(
            f"[green]Deleted {deleted_count} original image(s) with existing AVIF versions[/green]"
        )

    def scan(
        self, source_path: Path, dry_run: bool = False, delete_originals: bool = True
    ) -> Tuple[List[Path], List[Path], List[Path]]:
        """
        Scan source folder for all files, categorizing them as images, videos, or other files.
        Also removes original images if AVIF versions already exist (single-pass).

        Args:
            source_path: Path to the source directory
            dry_run: If True, only report what would be deleted without actually deleting
            delete_originals: If True, delete originals when AVIF exists

        Returns:
            Tuple of (image_files, video_files, other_files) as lists of Path objects
        """
        source_display = PathUtils.format_display_path(source_path)
        self.logger.info(f"[cyan]Scanning files in:[/cyan] {source_display}")

        image_files: List[Path] = []
        video_files: List[Path] = []
        other_files: List[Path] = []
        deleted_count = 0

        # Group files by their parent directory for redundant original detection.
        # Keying by parent (rather than tracking directory transitions during the
        # walk) keeps detection correct regardless of iteration order: a
        # subdirectory can sort between two sibling files in the sorted walk, which
        # would otherwise split a directory's files across separate groups.
        dir_maps: Dict[Path, Dict[str, List[Path]]] = {}

        for file_path in self._iter_files(source_path):
            # Build per-directory folder map for redundant original detection
            if delete_originals:
                folder_map = dir_maps.setdefault(file_path.parent, {})
                folder_map.setdefault(file_path.stem, []).append(file_path)

            self._categorize_file(file_path, image_files, video_files, other_files)

        # Process each directory's grouped files
        if delete_originals:
            for folder_map in dir_maps.values():
                deleted_count += self._remove_redundant_originals(folder_map, dry_run)

        # Remove deleted files from image_files list
        if deleted_count > 0:
            image_files = [f for f in image_files if f.exists()]
            self._log_deleted_summary(deleted_count, dry_run)

        self.logger.info(
            f"[green]Found:[/green] {len(image_files)} images to convert, "
            f"{len(video_files)} videos to compress, "
            f"{len(other_files)} other files to copy"
        )

        return image_files, video_files, other_files

    def _remove_redundant_originals(
        self, folder_map: Dict[str, List[Path]], dry_run: bool = False
    ) -> int:
        """
        Remove original images that have AVIF versions in the same folder.

        Args:
            folder_map: Dictionary mapping file stems to lists of file paths
            dry_run: If True, only report what would be deleted without actually deleting

        Returns:
            Number of files deleted (or that would be deleted in dry-run mode)
        """
        deleted_count = 0

        for _stem, files in folder_map.items():
            avif_file = next((f for f in files if f.suffix.lower() == ".avif"), None)
            if avif_file is None:
                continue

            for original in files:
                if original.suffix.lower() in self.IMAGE_EXTENSIONS:
                    if dry_run:
                        self.logger.info(
                            f"[yellow]Would delete:[/yellow] {original.name} "
                            f"(AVIF version exists: {avif_file.name})"
                        )
                        deleted_count += 1
                    else:
                        try:
                            original.unlink()
                            deleted_count += 1
                            self.logger.info(
                                f"[red]Deleted:[/red] {original.name} "
                                f"(AVIF version exists: {avif_file.name})"
                            )
                        except OSError as exc:
                            self.logger.error(
                                f"[red]Failed to delete {original.name}:[/red] {str(exc)}"
                            )

        return deleted_count
