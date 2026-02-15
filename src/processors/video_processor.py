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

    def __init__(self, converter: VideoConverter, copier: FileCopier, video_validator: VideoValidator=None, copy_validator: CopyValidator=None):
        pass

    def _is_target_codec(self, source_path: Path) -> bool:
        pass

    def get_destination_path(self, source_path: Path, dest_root: Path, source_root: Path) -> Path:
        pass

    def should_skip(self, source_path: Path, dest_path: Path) -> bool:
        pass

    def execute(self, source_path: Path, dest_path: Path, force: bool) -> bool:
        pass
