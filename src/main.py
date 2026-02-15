#!/usr/bin/env python3
"""
Main entry point for the Image & Video Converter.
"""

import argparse
import sys

from .core.logger_config import LoggerConfig
from .orchestrator.converter_orchestrator import ConverterOrchestrator


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Convert images to AVIF and videos to H.265/HEVC while preserving folder structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/media
  %(prog)s /path/to/media --quality 95                         # High quality images
  %(prog)s /path/to/media --video-crf 23                       # Better video quality
  %(prog)s /path/to/media --video-codec av1                    # Use AV1 (better compression, slower)
  %(prog)s /path/to/media --video-codec av1 --video-crf 35     # AV1 with default quality
  %(prog)s ~/Pictures/vacation2024 -q 80 --video-crf 28
  %(prog)s /path/to/media --dry-run                            # Preview without converting
  %(prog)s /path/to/media --force                              # Reconvert all files
  %(prog)s /path/to/media -q 95 --video-preset slow -v         # High quality, slow encoding
        """,
    )

    parser.add_argument("folder", type=str, help="Path to the folder containing images")

    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=85,
        metavar="N",
        help="AVIF quality (0-100, default: 85)",
    )

    parser.add_argument(
        "--video-crf",
        type=int,
        default=28,
        metavar="N",
        help="Video CRF quality (0-51, lower = better quality, default: 28)",
    )

    parser.add_argument(
        "--video-preset",
        type=str,
        default="medium",
        choices=[
            "ultrafast",
            "superfast",
            "veryfast",
            "faster",
            "fast",
            "medium",
            "slow",
            "slower",
            "veryslow",
        ],
        help="Video encoding preset (default: medium, slower = better compression)",
    )

    parser.add_argument(
        "--video-codec",
        type=str,
        default="h265",
        choices=["h265", "av1"],
        help="Video codec: h265 (fast, compatible) or av1 (better compression, slower). Default: h265",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force reconversion of all files, even if they already exist",
    )

    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Preview operations without executing them"
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--images-only", action="store_true", help="Only convert images, skip videos"
    )
    mode_group.add_argument(
        "--videos-only", action="store_true", help="Only compress videos, skip images"
    )

    parser.add_argument(
        "--keep-originals",
        action="store_true",
        help="Keep original images even if AVIF versions exist",
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    return parser.parse_args()


def validate_quality(quality: int) -> int:
    """
    Validate and clamp quality value.

    Args:
        quality: Quality value to validate

    Returns:
        Clamped quality value between 0 and 100
    """
    if not 0 <= quality <= 100:
        logger = LoggerConfig.get_logger(__name__)
        logger.warning("⚠️  Quality must be between 0 and 100. Using clamped value.")
        return max(0, min(100, quality))
    return quality


def validate_video_crf(crf: int, codec: str) -> int:
    """
    Validate CRF range for selected codec.

    Args:
        crf: Video CRF value
        codec: Selected video codec

    Returns:
        Same CRF value if valid

    Raises:
        ValueError: If CRF is out of range for the codec
    """
    max_crf = 63 if codec == "av1" else 51
    if not 0 <= crf <= max_crf:
        raise ValueError(f"Video CRF for {codec} must be between 0 and {max_crf}. Got: {crf}")
    return crf


def main():
    """Main entry point for the application."""
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    import logging

    log_level = logging.DEBUG if args.verbose else logging.INFO
    LoggerConfig.setup(level=log_level)

    # Create orchestrator and process
    try:
        # Validate quality and video CRF
        quality = validate_quality(args.quality)
        video_crf = validate_video_crf(args.video_crf, args.video_codec)

        orchestrator = ConverterOrchestrator(
            quality=quality,
            video_crf=video_crf,
            video_preset=args.video_preset,
            video_codec=args.video_codec,
            force=args.force,
            dry_run=args.dry_run,
            images_only=args.images_only,
            videos_only=args.videos_only,
            delete_originals=not args.keep_originals,
        )
        orchestrator.process(args.folder)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger = LoggerConfig.get_logger(__name__)
        logger.error(f"[red]Fatal error:[/red] {str(e)}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
