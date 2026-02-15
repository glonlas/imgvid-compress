# AGENTS.md

This file provides guidance to AI coding agents working with this repository.

## Project Overview

Image & Video Converter CLI that converts images to AVIF and videos to H.265/HEVC or AV1 format, preserving folder structure. Supports automatic resume if interrupted.

## Commands

```bash
make install                        # Install dependencies
make convert FOLDER=/path/to/media  # Convert images and videos
make dry-run FOLDER=/path/to/media  # Preview without changes
make clean                          # Remove venv and caches
```

See [docs/options.md](docs/options.md) for all options.

## Architecture

The codebase follows a processor-based architecture with clear separation of concerns:

```
src/
├── main.py                    # CLI entry point, argument parsing
├── orchestrator/
│   └── converter_orchestrator.py  # Main coordinator - runs 3-phase processing
├── processors/                # Template pattern for file processing
│   ├── base_processor.py      # Abstract base with process_files() loop
│   ├── copy_processor.py      # Handles non-convertible files
│   ├── image_processor.py     # Image → AVIF conversion
│   └── video_processor.py     # Video → H.265/AV1 compression
├── converters/                # Actual conversion logic
│   ├── image_converter.py     # Pillow-based AVIF conversion
│   ├── video_converter.py     # FFmpeg-based video compression
│   └── file_copier.py         # File copy with verification
├── validators/                # Skip logic for resume support
│   ├── base_validator.py      # Shared skip logic base class
│   ├── image_validator.py     # Validates AVIF output exists/valid
│   ├── video_validator.py     # Checks if video needs re-encoding
│   └── copy_validator.py      # Checks if copy is needed
├── scan/
│   └── file_scanner.py        # Discovers files, categorizes by type
├── analysis/
│   ├── folder_analyzer.py     # Calculates folder sizes
│   └── folder_stats.py        # Stats data structures
├── core/
│   ├── logger_config.py       # Rich-based logging setup
│   └── progress_tracker.py    # Progress bar management
└── utils/
    ├── path_utils.py          # Path manipulation helpers
    └── size_formatter.py      # Human-readable size formatting
```

### Processing Flow

1. `ConverterOrchestrator.process()` is the main entry point
2. `FileScanner.scan()` categorizes files into images, videos, and other
3. Three-phase processing (in order for speed optimization):
   - Phase 1: Copy non-processable files (fast)
   - Phase 2: Convert images to AVIF (medium)
   - Phase 3: Compress videos (slowest)
4. Each phase uses a Processor that inherits from `BaseProcessor`
5. Processors use Validators to determine skip logic for resume support
6. Processors delegate actual work to Converters

### Key Design Patterns

- **Template Method**: `BaseProcessor.process_files()` implements the iteration loop; subclasses implement `get_destination_path()`, `should_skip()`, and `execute()`
- **Dependency Injection**: Processors receive Converters/Validators via constructor
- **Resume Support**: Validators check if output exists and is valid before processing

## Code Standards

- Python 3.9+ compatibility
- Type hints encouraged
- One class per file
- Validators are stateless (use `@staticmethod` where possible)
- Converters only convert; skip logic belongs in Processors
- Use `PathUtils` for path operations
- Use `SizeFormatter` for human-readable sizes

## Dependencies

- Python 3.9+, UV package manager
- Pillow with pillow-avif-plugin and pillow-heif for image conversion
- FFmpeg (optional) for video compression
- Rich for CLI output and progress bars
