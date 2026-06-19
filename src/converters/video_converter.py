"""Video converter for compressing videos using FFmpeg."""

import json
import os
import shutil
import subprocess
from pathlib import Path

from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils
from ..utils.size_formatter import SizeFormatter


class VideoConverter:
    """Handles video compression using FFmpeg with H.265/HEVC or AV1 codec."""

    def __init__(self, crf: int = 28, preset: str = "medium", codec: str = "h265"):
        """
        Initialize the video converter.

        Args:
            crf: Constant Rate Factor (0-51 for h265, 0-63 for av1, lower = better quality, default: 28)
                 h265: 18-28 is typically acceptable, 23 is default for x265
                 av1: 30-40 is typically acceptable, 30 is default for av1
            preset: Encoding speed preset (ultrafast, superfast, veryfast, faster,
                   fast, medium, slow, slower, veryslow). Default: medium
            codec: Video codec to use: 'h265' (HEVC) or 'av1'. Default: h265
        """
        self.crf = crf
        self.preset = preset
        self.codec = codec.lower()
        self.logger = LoggerConfig.get_logger(__name__)

        # Validate codec choice
        if self.codec not in ["h265", "av1"]:
            self.logger.warning(f"[yellow]Unknown codec '{codec}', using h265[/yellow]")
            self.codec = "h265"

        # Check if FFmpeg is available
        if not self._check_ffmpeg():
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg:\n"
                "  macOS: brew install ffmpeg\n"
                "  Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  Windows: Download from https://ffmpeg.org/download.html"
            )

    def _check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is installed and available.

        Returns:
            True if FFmpeg is available, False otherwise
        """
        return shutil.which("ffmpeg") is not None

    def _get_video_info(self, video_path: Path) -> dict:
        """
        Get video information using ffprobe.

        Args:
            video_path: Path to the video file

        Returns:
            Dictionary with video information
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    "-show_streams",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            return {}
        except Exception as e:
            self.logger.debug(f"Could not get video info for {video_path.name}: {str(e)}")
            return {}

    def _get_current_codec(self, video_path: Path) -> str:
        """
        Get the current video codec.

        Args:
            video_path: Path to the video file

        Returns:
            Codec name (e.g., 'hevc', 'av1', 'h264') or empty string if unknown
        """
        info = self._get_video_info(video_path)

        if "streams" in info:
            for stream in info["streams"]:
                if stream.get("codec_type") == "video":
                    return stream.get("codec_name", "").lower()

        return ""

    def is_target_codec(self, video_path: Path) -> bool:
        """
        Check if video is already encoded with the target codec.

        Args:
            video_path: Path to the video file

        Returns:
            True if already in target codec, False otherwise
        """
        current_codec = self._get_current_codec(video_path)

        if self.codec == "h265":
            return current_codec in ["hevc", "h265"]
        if self.codec == "av1":
            return current_codec == "av1"

        return False

    def _build_h265_command(self, source_path: Path, dest_path: Path) -> list[str]:
        """Build FFmpeg command for H.265/HEVC encoding."""
        return [
            "ffmpeg",
            "-i",
            str(source_path),
            "-map",
            "0",  # Keep all streams (video/audio/subtitles/data)
            "-map_metadata",
            "0",  # Preserve container metadata
            "-map_chapters",
            "0",  # Preserve chapter markers
            "-c:v",
            "libx265",  # Video codec: H.265/HEVC
            "-crf",
            str(self.crf),  # Quality (lower = better)
            "-preset",
            self.preset,  # Encoding speed/efficiency
            "-profile:v",
            "main",  # Main profile (8-bit, compatible with Quick Look)
            "-pix_fmt",
            "yuv420p",  # 8-bit 4:2:0 (most compatible)
            "-tag:v",
            "hvc1",  # Use hvc1 tag (Apple/macOS prefers this over hev1)
            "-c:a",
            "copy",  # Preserve original audio bitstream
            "-c:s",
            "copy",  # Preserve subtitles
            "-c:d",
            "copy",  # Preserve data streams
            "-c:t",
            "copy",  # Preserve attachments/thumbnails when supported
            "-movflags",
            "+faststart",  # Enable streaming & Quick Look
            "-y",  # Overwrite output
            str(dest_path),
        ]

    def _build_av1_command(self, source_path: Path, dest_path: Path) -> list[str]:
        """Build FFmpeg command for AV1 encoding (SVT-AV1 first)."""
        return [
            "ffmpeg",
            "-i",
            str(source_path),
            "-map",
            "0",  # Keep all streams (video/audio/subtitles/data)
            "-map_metadata",
            "0",  # Preserve container metadata
            "-map_chapters",
            "0",  # Preserve chapter markers
            "-c:v",
            "libsvtav1",  # Video codec: AV1 (SVT-AV1 is faster)
            "-crf",
            str(self.crf),  # Quality (lower = better)
            "-preset",
            str(self._map_av1_preset(self.preset)),  # AV1 presets are 0-13
            "-c:a",
            "copy",  # Preserve original audio bitstream
            "-c:s",
            "copy",  # Preserve subtitles
            "-c:d",
            "copy",  # Preserve data streams
            "-c:t",
            "copy",  # Preserve attachments/thumbnails when supported
            "-movflags",
            "+faststart",  # Enable streaming
            "-y",  # Overwrite output
            str(dest_path),
        ]

    def _build_ffmpeg_command(self, source_path: Path, dest_path: Path) -> list[str]:
        """Build FFmpeg command based on selected codec."""
        if self.codec == "h265":
            return self._build_h265_command(source_path, dest_path)
        return self._build_av1_command(source_path, dest_path)

    def _cleanup_partial_output(self, dest_path: Path) -> None:
        """Remove partial output file if present."""
        if not dest_path.exists():
            return
        try:
            dest_path.unlink()
        except OSError as exc:
            self.logger.warning(
                f"[yellow]Could not remove partial output {dest_path.name}:[/yellow] {str(exc)}"
            )

    def _run_ffmpeg(self, cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
        """Execute FFmpeg command."""
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def _run_with_av1_fallback(self, cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
        """
        Run FFmpeg command and fall back from SVT-AV1 to libaom-av1 on timeout.
        """
        try:
            return self._run_ffmpeg(cmd, timeout)
        except subprocess.TimeoutExpired:
            if self.codec != "av1" or "libsvtav1" not in cmd:
                raise

            self.logger.info("[yellow]SVT-AV1 failed, trying libaom-av1...[/yellow]")
            cmd[cmd.index("libsvtav1")] = "libaom-av1"
            preset_idx = cmd.index("-preset") + 1
            cmd[preset_idx] = self.preset
            return self._run_ffmpeg(cmd, timeout)

    def _is_valid_output(self, dest_path: Path) -> bool:
        """Check that output exists and has non-zero size."""
        return dest_path.exists() and dest_path.stat().st_size > 0

    def _log_conversion_summary(self, source_path: Path, dest_path: Path) -> None:
        """Log conversion size summary."""
        source_size = source_path.stat().st_size
        dest_size = dest_path.stat().st_size
        reduction = ((source_size - dest_size) / source_size) * 100 if source_size > 0 else 0
        self.logger.info(
            f"[green]✓ Converted:[/green] {source_path.name} "
            f"({SizeFormatter.format_size(source_size)} → {SizeFormatter.format_size(dest_size)}, "
            f"{reduction:+.1f}%)"
        )

    @staticmethod
    def _preserve_timestamps(source_path: Path, dest_path: Path) -> None:
        source_stat = source_path.stat()
        os.utime(dest_path, (source_stat.st_atime, source_stat.st_mtime))

    def convert(self, source_path: Path, dest_path: Path, force: bool = False) -> bool:
        """
        Convert a video to H.265/HEVC or AV1 format.

        Note: Skip logic is handled by VideoProcessor. This method only converts.

        Args:
            source_path: Path to source video file
            dest_path: Path to destination video file
            force: Unused, kept for API compatibility

        Returns:
            True if conversion succeeded, False otherwise
        """
        try:
            # Validate source file
            if not source_path.exists():
                self.logger.error(f"[red]Source video not found:[/red] {source_path}")
                return False

            # Create destination directory if it doesn't exist
            PathUtils.ensure_parent_dir(dest_path)

            codec_display = "H.265/HEVC" if self.codec == "h265" else "AV1"
            self.logger.info(
                f"[cyan]Converting video to {codec_display}:[/cyan] {source_path.name}"
            )

            # Warn if using AV1 (slow encoding)
            if self.codec == "av1":
                self.logger.info(
                    "[yellow]Note: AV1 encoding is slow, this may take a while...[/yellow]"
                )

            # Increase timeout for AV1 (much slower encoding)
            timeout = 7200 if self.codec == "av1" else 3600  # 2 hours for AV1, 1 hour for H.265
            cmd = self._build_ffmpeg_command(source_path, dest_path)
            result = self._run_with_av1_fallback(cmd, timeout)

            if result.returncode != 0:
                self.logger.error(
                    f"[red]Failed to convert {source_path.name}:[/red] "
                    f"FFmpeg error: {result.stderr[:200]}"
                )
                self._cleanup_partial_output(dest_path)
                return False

            # Verify output file was created and is valid
            if not self._is_valid_output(dest_path):
                self.logger.error(f"[red]Output file is invalid:[/red] {dest_path.name}")
                self._cleanup_partial_output(dest_path)
                return False

            self._preserve_timestamps(source_path, dest_path)
            self._log_conversion_summary(source_path, dest_path)
            return True

        except subprocess.TimeoutExpired:
            timeout_msg = "2 hours" if self.codec == "av1" else "1 hour"
            self.logger.error(f"[red]Conversion timeout ({timeout_msg}):[/red] {source_path.name}")
            self._cleanup_partial_output(dest_path)
            return False
        except Exception as e:
            self.logger.error(f"[red]Error converting {source_path.name}:[/red] {str(e)}")
            self._cleanup_partial_output(dest_path)
            return False

    def _map_av1_preset(self, preset: str) -> int:
        """
        Map x265-style preset names to SVT-AV1 preset numbers (0-13).
        Lower numbers = slower but better compression.

        Args:
            preset: x265-style preset name

        Returns:
            SVT-AV1 preset number
        """
        preset_map = {
            "veryslow": 3,
            "slower": 4,
            "slow": 5,
            "medium": 6,
            "fast": 7,
            "faster": 8,
            "veryfast": 9,
            "superfast": 10,
            "ultrafast": 12,
        }
        return preset_map.get(preset.lower(), 6)  # Default to 6 (medium)
