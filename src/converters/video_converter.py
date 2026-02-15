"""Video converter for compressing videos using FFmpeg."""
import json
import shutil
import subprocess
from pathlib import Path
from ..core.logger_config import LoggerConfig
from ..utils.path_utils import PathUtils
from ..utils.size_formatter import SizeFormatter

class VideoConverter:
    """Handles video compression using FFmpeg with H.265/HEVC or AV1 codec."""

    def __init__(self, crf: int=28, preset: str='medium', codec: str='h265'):
        raise NotImplementedError()

    def _check_ffmpeg(self) -> bool:
        raise NotImplementedError()

    def _get_video_info(self, video_path: Path) -> dict:
        raise NotImplementedError()

    def _get_current_codec(self, video_path: Path) -> str:
        raise NotImplementedError()

    def is_target_codec(self, video_path: Path) -> bool:
        raise NotImplementedError()

    def _build_h265_command(self, source_path: Path, dest_path: Path) -> list[str]:
        raise NotImplementedError()

    def _build_av1_command(self, source_path: Path, dest_path: Path) -> list[str]:
        raise NotImplementedError()

    def _build_ffmpeg_command(self, source_path: Path, dest_path: Path) -> list[str]:
        raise NotImplementedError()

    def _cleanup_partial_output(self, dest_path: Path) -> None:
        raise NotImplementedError()

    def _run_ffmpeg(self, cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
        raise NotImplementedError()

    def _run_with_av1_fallback(self, cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
        raise NotImplementedError()

    def _is_valid_output(self, dest_path: Path) -> bool:
        raise NotImplementedError()

    def _log_conversion_summary(self, source_path: Path, dest_path: Path) -> None:
        raise NotImplementedError()

    def convert(self, source_path: Path, dest_path: Path, force: bool=False) -> bool:
        raise NotImplementedError()

    def _map_av1_preset(self, preset: str) -> int:
        raise NotImplementedError()
