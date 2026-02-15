# Options and Usage

## Core Commands

| Command | Description |
|---|---|
| `make install` | Install runtime environment (`uv`, `.venv`, app deps, FFmpeg check/install) |
| `make install-dev` | Install development dependencies |
| `make convert FOLDER=...` | Run conversion pipeline |
| `make dry-run FOLDER=...` | Preview without writing converted outputs |
| `make test` | Run unit tests with coverage gate |
| `make quality` | Run lint + complexity + tests |
| `make help` | Print command and option help |

## Conversion Variables

| Variable | Default | Description |
|---|---|---|
| `FOLDER` | required | Source folder path (supports `~`) |
| `MODE` | `all` | `all`, `images`, or `videos` |
| `QUALITY` | `85` | Image quality (`0..100`) |
| `VIDEO_CODEC` | `h265` | `h265` or `av1` |
| `VIDEO_CRF` | `28` | CRF quality (`h265: 0..51`, `av1: 0..63`) |
| `VIDEO_PRESET` | `medium` | Preset (`ultrafast` ... `veryslow`) |
| `FORCE` | off | `1` to reconvert existing outputs |
| `KEEP_ORIGINALS` | off | `1` to keep originals even when AVIF exists |
| `VERBOSE` | off | `1` for debug-level logs |

## Common Usage

```bash
# Basic conversion
make convert FOLDER=/path/to/media

# Preview only
make dry-run FOLDER=/path/to/media

# Only images
make convert FOLDER=/path/to/media MODE=images

# Only videos
make convert FOLDER=/path/to/media MODE=videos

# AV1 with custom quality and preset
make convert FOLDER=/path/to/media VIDEO_CODEC=av1 VIDEO_CRF=35 VIDEO_PRESET=slow

# Force reconversion of everything
make convert FOLDER=/path/to/media FORCE=1
```

## Direct Python CLI

```bash
uv run python -m src.main /path/to/media
uv run python -m src.main /path/to/media --help
```

## Safety and Resume Notes

- Re-running conversion is safe: validators skip already-valid outputs.
- Output is written to `<source>_compressed`, leaving source tree untouched.
- Use `--dry-run`/`make dry-run` before first large run.
