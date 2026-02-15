"""Processor for compressing videos or copying when already compressed."""

from pathlib import Path

from ..converters.file_copier import FileCopier
from ..converters.video_converter import VideoConverter
from ..utils.path_utils import PathUtils
from ..validators.copy_validator import CopyValidator
from ..validators.video_validator import VideoValidator
from .base_processor import BaseProcessor


class VideoProcessor(BaseProcessor):
    """Processes videos by compressing or copying when already in target codec."""

    def __init__(
        self,
        converter: VideoConverter,
        copier: FileCopier,
        video_validator: VideoValidator = None,
        copy_validator: CopyValidator = None,
    ):
        self.converter = converter
        self.copier = copier
        self.video_validator = video_validator or VideoValidator()
        self.copy_validator = copy_validator or CopyValidator()
        # Cache for is_target_codec results to avoid duplicate ffprobe calls
        self._target_codec_cache: dict = {}

    def _is_target_codec(self, source_path: Path) -> bool:
        """Check if file is already in target codec, with caching."""
        path_str = str(source_path)
        if path_str not in self._target_codec_cache:
            self._target_codec_cache[path_str] = self.converter.is_target_codec(source_path)
        return self._target_codec_cache[path_str]

    def get_destination_path(self, source_path: Path, dest_root: Path, source_root: Path) -> Path:
        if self._is_target_codec(source_path):
            return PathUtils.get_destination_path(source_path, dest_root, source_root)
        return PathUtils.get_destination_path(
            source_path, dest_root, source_root, new_extension=".mp4"
        )

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        if self._is_target_codec(source_path):
            return self.copy_validator.should_skip(source_path, dest_path)
        return self.video_validator.should_skip(source_path, dest_path)

    def execute(self, source_path: Path, dest_path: Path, force: bool) -> bool:
        if self._is_target_codec(source_path):
            return self.copier.copy(source_path, dest_path, force=force)
        return self.converter.convert(source_path, dest_path, force=force)
