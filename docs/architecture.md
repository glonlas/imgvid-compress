# Architecture

## Overview

The app is a pipeline-based CLI with clear separation between orchestration, scanning, processing, conversion, and validation.

High-level flow:

1. Parse and validate CLI args in `src/main.py`.
2. Build `ConverterOrchestrator`.
3. Scan source files and compute original folder stats.
4. Run three processing phases in order:
   - copy non-convertible files
   - convert images
   - process videos (compress or copy)
5. Compute final stats and print summary.

## Project Structure

```text
src/
├── main.py
├── orchestrator/
│   └── converter_orchestrator.py
├── processors/
│   ├── base_processor.py
│   ├── copy_processor.py
│   ├── image_processor.py
│   └── video_processor.py
├── converters/
│   ├── file_copier.py
│   ├── image_converter.py
│   └── video_converter.py
├── validators/
│   ├── base_validator.py
│   ├── copy_validator.py
│   ├── image_validator.py
│   └── video_validator.py
├── scan/
│   └── file_scanner.py
├── analysis/
│   ├── folder_analyzer.py
│   └── folder_stats.py
├── core/
│   ├── logger_config.py
│   └── progress_tracker.py
└── utils/
    ├── path_utils.py
    └── size_formatter.py
```

## Responsibilities by Layer

| Layer | Responsibility |
|---|---|
| `main.py` | CLI input parsing, validation, and top-level error handling |
| `orchestrator/` | End-to-end workflow control and phase ordering |
| `scan/` | File discovery and type categorization |
| `processors/` | Iteration loop over files, skip decisions, and execution routing |
| `converters/` | Actual media conversion and file copy operations |
| `validators/` | Resume safety checks (whether an output should be skipped) |
| `analysis/` | Folder size metrics and savings calculation |
| `core/` | Logging and progress UI |
| `utils/` | Shared helper logic |

## Key Design Patterns

### Template Method

`BaseProcessor.process_files(...)` implements the common processing loop. Concrete processors define:

- destination path resolution
- skip logic
- execution action

### Dependency Injection

Converters and validators are provided to processors via constructor arguments, enabling isolated tests and replaceable behavior.

### Resume-First Behavior

Validators ensure existing valid outputs are skipped, so reruns are incremental instead of destructive.

## Runtime Behavior Notes

- Video compression is optional at runtime and depends on FFmpeg availability.
- If FFmpeg is unavailable, video compression is disabled and video files are copied.
- The destination is always a sibling directory named `<source>_compressed`.
