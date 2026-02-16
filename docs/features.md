# Feature Reference

## Makefile Features

The `Makefile` is the primary interface for install, run, and quality workflows.

### Setup and install

- `make install`
  - Bootstraps `uv` if needed.
  - Creates `.venv` if missing.
  - Installs runtime dependencies.
  - Checks FFmpeg availability and installs when supported.
- `make install-dev`
  - Installs dev dependencies (tests, lint, quality tooling).
- `make clean`
  - Removes virtualenv and cache artifacts.

### Conversion workflow

- `make convert FOLDER=...`
  - Runs full conversion pipeline.
- `make dry-run FOLDER=...`
  - Simulates conversion without writing outputs.
- `make smoke-test`
  - Runs a local conversion against `test_images/`.

### Testing and quality

- `make test` / `make unit-test`
  - Runs pytest with coverage and a 100% threshold.
- `make lint`
  - `ruff check` + formatting check.
- `make lint-fix`
  - Auto-fixes lint issues and formats files.
- `make format`
  - Applies code formatting.
- `make complexity`
  - Prints complexity report and enforces xenon thresholds.
- `make quality`
  - Full gate: lint + complexity + tests.

## `src/main.py` Features

`src/main.py` is the CLI entrypoint and boundary for user input validation.

### CLI arguments

- Required folder path.
- Image quality (`--quality`).
- Video quality (`--video-crf`).
- Video codec (`--video-codec`: `h265` or `av1`).
- Video preset (`--video-preset`).
- Execution flags: `--dry-run`, `--force`, `--verbose`.
- Mode flags: `--images-only` or `--videos-only` (mutually exclusive).
- Cleanup flag: `--keep-originals`.

### Validation and safety

- Clamps image quality into `0..100`.
- Validates CRF by codec:
  - `h265`: `0..51`
  - `av1`: `0..63`
- Rejects conflicting mode flags by parser design.

### Runtime behavior

- Configures logging level from `--verbose`.
- Instantiates `ConverterOrchestrator` with validated options.
- Handles failures predictably:
  - `KeyboardInterrupt` exits with code `130`.
  - Unexpected exceptions exit with code `1`.
