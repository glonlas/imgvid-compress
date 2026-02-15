"""Main orchestrator for coordinating the image conversion process."""

import sys
from pathlib import Path
from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..analysis.folder_analyzer import FolderAnalyzer
from ..converters.file_copier import FileCopier
from ..converters.image_converter import ImageConverter
from ..converters.video_converter import VideoConverter
from ..core.logger_config import LoggerConfig
from ..core.progress_tracker import ProgressTracker
from ..processors.copy_processor import CopyProcessor
from ..processors.image_processor import ImageProcessor
from ..processors.video_processor import VideoProcessor
from ..scan.file_scanner import FileScanner
from ..utils.size_formatter import SizeFormatter


class ConverterOrchestrator:
    """Orchestrates the entire image conversion process."""

    def __init__(
        self,
        quality: int = 85,
        video_crf: int = 28,
        video_preset: str = "medium",
        video_codec: str = "h265",
        force: bool = False,
        dry_run: bool = False,
        images_only: bool = False,
        videos_only: bool = False,
        delete_originals: bool = True,
    ):
        """
        Initialize the converter orchestrator.

        Args:
            quality: AVIF quality setting (0-100, default: 85)
            video_crf: Video CRF quality (0-51 for h265, 0-63 for av1, default: 28)
            video_preset: Video encoding preset (default: medium)
            video_codec: Video codec: 'h265' (HEVC) or 'av1' (default: h265)
            force: Force conversion even if files exist
            dry_run: Preview operations without executing them
            images_only: Only convert images, skip videos
            videos_only: Only compress videos, skip images
            delete_originals: Delete original images if AVIF exists in same folder
        """
        self.quality = quality
        self.video_crf = video_crf
        self.video_preset = video_preset
        self.video_codec = video_codec
        self.force = force
        self.dry_run = dry_run
        self.images_only = images_only
        self.videos_only = videos_only
        self.delete_originals = delete_originals
        self.console = Console()
        self.logger = LoggerConfig.get_logger(__name__)

        self.scanner = FileScanner()
        self.analyzer = FolderAnalyzer()

        self.copier = FileCopier()
        self.copy_processor = CopyProcessor(copier=self.copier)
        self.image_processor = ImageProcessor(converter=ImageConverter(quality=quality))

        try:
            self.video_converter = VideoConverter(
                crf=video_crf,
                preset=video_preset,
                codec=video_codec,
            )
            self.video_processor = VideoProcessor(
                converter=self.video_converter,
                copier=self.copier,
            )
        except RuntimeError as exc:
            self.logger.warning(f"[yellow]Video compression disabled:[/yellow] {str(exc)}")
            self.video_converter = None
            self.video_processor = None

    def validate_source(self, source_path: Path) -> bool:
        """
        Validate the source folder.

        Args:
            source_path: Path to validate

        Returns:
            True if valid, False otherwise
        """
        if not source_path.exists():
            self.logger.error(f"[red]Error:[/red] Source folder does not exist: {source_path}")
            return False

        if not source_path.is_dir():
            self.logger.error(f"[red]Error:[/red] Path is not a directory: {source_path}")
            return False

        return True

    def get_destination_path(self, source_path: Path) -> Path:
        """
        Get the destination path for converted files.

        Args:
            source_path: Source folder path

        Returns:
            Destination folder path
        """
        dest_folder_name = f"{source_path.name}_compressed"
        return source_path.parent / dest_folder_name

    def handle_existing_destination(self, dest_path: Path) -> bool:
        """
        Handle existing destination folder.

        Args:
            dest_path: Destination folder path

        Returns:
            True if should proceed, False otherwise
        """
        if dest_path.exists():
            if self.force:
                self.logger.info(
                    "[yellow]Destination exists, will overwrite changed files[/yellow]"
                )
            else:
                self.logger.info(
                    "[yellow]Destination exists, will resume and skip existing files[/yellow]"
                )
                self.logger.info("[dim]Use --force to reconvert all files[/dim]")

        return True

    def display_header(self, source_path: Path, dest_path: Path):
        """
        Display conversion header information.

        Args:
            source_path: Source folder path
            dest_path: Destination folder path
        """
        mode_text = "DRY RUN - " if self.dry_run else ""
        force_text = " (Force Mode)" if self.force else " (Resume Mode)"

        if self.images_only:
            processing_mode = "\nMode: Images only"
        elif self.videos_only:
            processing_mode = "\nMode: Videos only"
        else:
            processing_mode = ""

        cleanup_text = "" if self.delete_originals else "\nCleanup: Keep originals"

        video_status = ""
        if not self.images_only:
            if self.video_converter:
                codec_name = "H.265/HEVC" if self.video_codec == "h265" else "AV1"
                video_status = (
                    f"\nVideo: {codec_name}, CRF {self.video_crf}, Preset {self.video_preset}"
                )
            else:
                video_status = "\n[yellow]Video compression: Disabled (FFmpeg not found)[/yellow]"

        self.console.print()
        self.console.print(
            Panel.fit(
                f"[bold cyan]{mode_text}Image & Video Converter[/bold cyan]\n"
                f"Image Quality: {self.quality}{force_text}{processing_mode}{cleanup_text}{video_status}",
                border_style="yellow" if self.dry_run else "cyan",
            )
        )
        self.console.print()
        self.console.print(f"[cyan]📁 Source:[/cyan]      {source_path}")
        self.console.print(f"[cyan]📁 Destination:[/cyan] {dest_path}")
        self.console.print()

    def display_scan_results(
        self, image_count: int, video_count: int, other_count: int, original_stats
    ):
        """
        Display scan results.

        Args:
            image_count: Number of images found
            video_count: Number of videos found
            other_count: Number of other files found
            original_stats: Original folder statistics
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="cyan")
        table.add_column(style="white")

        if self.videos_only:
            table.add_row("Images to copy:", f"{image_count:,} [yellow](not converting)[/yellow]")
        else:
            table.add_row("Images to convert:", f"{image_count:,}")

        if self.images_only:
            table.add_row("Videos to copy:", f"{video_count:,} [yellow](not compressing)[/yellow]")
        elif self.video_converter:
            table.add_row("Videos to compress:", f"{video_count:,}")
        else:
            table.add_row(
                "Videos to compress:", f"{video_count:,} [yellow](will be copied)[/yellow]"
            )

        table.add_row("Other files to copy:", f"{other_count:,}")
        table.add_row("Total files:", f"{image_count + video_count + other_count:,}")
        table.add_row("Original size:", original_stats.formatted_size)

        self.console.print(table)
        self.console.print()

    def display_results(
        self, stats: Dict[str, int], original_size: int, new_size: int, dest_path: Path
    ):
        """
        Display final conversion results.

        Args:
            stats: Processing statistics
            original_size: Original folder size in bytes
            new_size: New folder size in bytes
            dest_path: Destination folder path
        """
        saved_size, saved_percent = self.analyzer.calculate_savings(original_size, new_size)

        self.console.print()
        self.console.print("=" * 70)

        if self.dry_run:
            self.console.print("[bold yellow]🔍 DRY RUN COMPLETE[/bold yellow]")
        else:
            self.console.print("[bold green]✅ CONVERSION COMPLETE[/bold green]")

        self.console.print("=" * 70)
        self.console.print(f"[cyan]📁 Output folder:[/cyan] {dest_path}")
        self.console.print()

        stats_table = Table(show_header=False, box=None, padding=(0, 2))
        stats_table.add_column(style="cyan bold")
        stats_table.add_column(style="white")

        if stats["converted"] > 0:
            stats_table.add_row("Converted:", f"[green]{stats['converted']:,} files[/green]")
        if stats["skipped"] > 0:
            stats_table.add_row(
                "Skipped (already exist):", f"[yellow]{stats['skipped']:,} files[/yellow]"
            )
        if stats["failed"] > 0:
            stats_table.add_row("Failed:", f"[red]{stats['failed']:,} files[/red]")

        self.console.print("[bold]📊 Statistics:[/bold]")
        self.console.print(stats_table)
        self.console.print()

        if not self.dry_run:
            storage_table = Table(show_header=False, box=None, padding=(0, 2))
            storage_table.add_column(style="cyan bold")
            storage_table.add_column(style="white")

            storage_table.add_row("Original size:", SizeFormatter.format_size(original_size))
            storage_table.add_row("Compressed size:", SizeFormatter.format_size(new_size))
            storage_table.add_row(
                "Saved:",
                f"[green]{SizeFormatter.format_size(saved_size)} ({saved_percent:.1f}%)[/green]",
            )

            self.console.print("[bold]💾 Storage:[/bold]")
            self.console.print(storage_table)

        self.console.print("=" * 70)
        self.console.print()

    def _merge_stats(self, base: Dict[str, int], update: Dict[str, int]) -> Dict[str, int]:
        base["converted"] += update.get("converted", 0)
        base["skipped"] += update.get("skipped", 0)
        base["failed"] += update.get("failed", 0)
        return base

    def process(self, source_folder: str):
        """
        Main processing method to convert images in a folder.

        Args:
            source_folder: Path to the source folder
        """
        source_path = Path(source_folder).resolve()

        if not self.validate_source(source_path):
            sys.exit(1)

        dest_path = self.get_destination_path(source_path)

        if not self.handle_existing_destination(dest_path):
            sys.exit(0)

        self.display_header(source_path, dest_path)

        image_files, video_files, other_files = self.scanner.scan(
            source_path,
            dry_run=self.dry_run,
            delete_originals=self.delete_originals,
        )

        total_files = len(image_files) + len(video_files) + len(other_files)

        if total_files == 0:
            self.logger.warning("[yellow]No files found to process[/yellow]")
            sys.exit(0)

        self.logger.info("[cyan]Analyzing original folder...[/cyan]")
        original_stats = self.analyzer.analyze(source_path)

        self.display_scan_results(
            len(image_files), len(video_files), len(other_files), original_stats
        )

        if self.dry_run:
            self.logger.info("[yellow]DRY RUN: No files will be modified[/yellow]\n")

        self.logger.info("[bold green]🚀 Processing files...[/bold green]\n")

        stats = {"converted": 0, "skipped": 0, "failed": 0}

        with ProgressTracker(total_files, console=self.console) as tracker:
            self.logger.info("[cyan]Phase 1/3: Copying non-processable files...[/cyan]")
            stats = self._merge_stats(
                stats,
                self.copy_processor.process_files(
                    other_files, dest_path, source_path, tracker, self.dry_run, self.force
                ),
            )

            if image_files:
                if self.videos_only:
                    self.logger.info("[cyan]Phase 2/3: Copying images (videos-only mode)...[/cyan]")
                    stats = self._merge_stats(
                        stats,
                        self.copy_processor.process_files(
                            image_files, dest_path, source_path, tracker, self.dry_run, self.force
                        ),
                    )
                else:
                    self.logger.info("[cyan]Phase 2/3: Converting images to AVIF...[/cyan]")
                    stats = self._merge_stats(
                        stats,
                        self.image_processor.process_files(
                            image_files, dest_path, source_path, tracker, self.dry_run, self.force
                        ),
                    )

            if video_files:
                if self.images_only:
                    self.logger.info("[cyan]Phase 3/3: Copying videos (images-only mode)...[/cyan]")
                    stats = self._merge_stats(
                        stats,
                        self.copy_processor.process_files(
                            video_files, dest_path, source_path, tracker, self.dry_run, self.force
                        ),
                    )
                elif self.video_processor:
                    self.logger.info("[cyan]Phase 3/3: Compressing videos...[/cyan]")
                    stats = self._merge_stats(
                        stats,
                        self.video_processor.process_files(
                            video_files, dest_path, source_path, tracker, self.dry_run, self.force
                        ),
                    )
                else:
                    self.logger.info(
                        "[cyan]Phase 3/3: Copying videos (FFmpeg not available)...[/cyan]"
                    )
                    stats = self._merge_stats(
                        stats,
                        self.copy_processor.process_files(
                            video_files, dest_path, source_path, tracker, self.dry_run, self.force
                        ),
                    )

        if not self.dry_run:
            self.logger.info("\n[cyan]Analyzing compressed folder...[/cyan]")
            new_stats = self.analyzer.analyze(dest_path)
        else:
            new_stats = original_stats

        final_stats = {
            "total": total_files,
            "converted": stats["converted"],
            "skipped": stats["skipped"],
            "failed": stats["failed"],
        }

        self.display_results(
            final_stats, original_stats.size_bytes, new_stats.size_bytes, dest_path
        )
