# Key APIs

This document lists the core programmatic entry points and responsibilities.

## CLI and orchestration

- `src/main.py`
  - `parse_arguments()`
  - `validate_quality(quality: int) -> int`
  - `validate_video_crf(crf: int, codec: str) -> int`
  - `main()`

- `src/orchestrator/converter_orchestrator.py`
  - `ConverterOrchestrator.__init__(...)`
  - `ConverterOrchestrator.process(source_folder: str)`
  - `ConverterOrchestrator.validate_source(source_path: Path) -> bool`
  - `ConverterOrchestrator.get_destination_path(source_path: Path) -> Path`
  - `ConverterOrchestrator.display_header(...)`
  - `ConverterOrchestrator.display_scan_results(...)`
  - `ConverterOrchestrator.display_results(...)`

## Scanning and analysis

- `src/scan/file_scanner.py`
  - `FileScanner.scan(source_path: Path, dry_run=False, delete_originals=True) -> tuple[list[Path], list[Path], list[Path]]`

- `src/analysis/folder_analyzer.py`
  - `FolderAnalyzer.analyze(path: Path) -> FolderStats`
  - `FolderAnalyzer.calculate_savings(original_size: int, new_size: int) -> tuple[int, float]`

- `src/analysis/folder_stats.py`
  - `FolderStats` dataclass
  - `FolderStats.formatted_size` property

## Processing layer

- `src/processors/base_processor.py`
  - `BaseProcessor.process_files(files, dest_root, source_root, tracker, dry_run, force) -> dict[str, int]`

- `src/processors/copy_processor.py`
  - `CopyProcessor.get_destination_path(...)`
  - `CopyProcessor.should_skip(...)`
  - `CopyProcessor.execute(...)`

- `src/processors/image_processor.py`
  - `ImageProcessor.get_destination_path(...)`
  - `ImageProcessor.should_skip(...)`
  - `ImageProcessor.execute(...)`

- `src/processors/video_processor.py`
  - `VideoProcessor.get_destination_path(...)`
  - `VideoProcessor.should_skip(...)`
  - `VideoProcessor.execute(...)`

## Conversion layer

- `src/converters/file_copier.py`
  - `FileCopier.copy(source_path: Path, dest_path: Path, force=False) -> bool`

- `src/converters/image_converter.py`
  - `ImageConverter.convert(source_path: Path, dest_path: Path, force=False) -> bool`

- `src/converters/video_converter.py`
  - `VideoConverter.is_target_codec(video_path: Path) -> bool`
  - `VideoConverter.convert(source_path: Path, dest_path: Path, force=False) -> bool`

## Validation layer

- `src/validators/base_validator.py`
  - `BaseValidator._should_skip_base(...) -> bool`
  - `BaseValidator.should_skip(...) -> bool`

- `src/validators/copy_validator.py`
  - `CopyValidator.should_skip(source_path: Path, dest_path: Path) -> bool`

- `src/validators/image_validator.py`
  - `ImageValidator.is_valid_image(image_path: Path) -> bool`
  - `ImageValidator.should_skip(source_path: Path, dest_path: Path) -> bool`

- `src/validators/video_validator.py`
  - `VideoValidator.should_skip(source_path: Path, dest_path: Path) -> bool`

## Core and utilities

- `src/core/logger_config.py`
  - `LoggerConfig.setup(level=...)`
  - `LoggerConfig.get_logger(name: str)`

- `src/core/progress_tracker.py`
  - `ProgressTracker.start()`
  - `ProgressTracker.update(...)`
  - `ProgressTracker.stop()`

- `src/utils/path_utils.py`
  - `PathUtils.get_destination_path(...) -> Path`
  - `PathUtils.ensure_parent_dir(path: Path) -> None`

- `src/utils/size_formatter.py`
  - `SizeFormatter.format_size(size_bytes: int) -> str`
