.PHONY: help install install-dev setup clean convert dry-run test smoke-test unit-test lint lint-fix format complexity quality

# Default target
help:
	@echo "📦 Image & Video Converter - Available Commands"
	@echo ""
	@echo "1. Getting Started"
	@echo "  make install    - Install everything (UV, venv, dependencies, FFmpeg)"
	@echo "  make convert    - Convert images/videos (requires FOLDER=path/to/folder)"
	@echo ""
	@echo "2. Usage"
	@echo "  make convert    - Convert images/videos (requires FOLDER=path/to/folder)"
	@echo "  make dry-run    - Preview conversion without executing (requires FOLDER=)"
	@echo ""
	@echo "3. For Developer"
	@echo "  make install-dev - Install development dependencies (tests, coverage)"
	@echo "  make clean       - Remove virtual environment and cache files"
	@echo "  make test        - Run unit-test, smoke-test, and lint"
	@echo "  make unit-test   - Run unit tests with coverage (100%)"
	@echo "  make smoke-test  - Run a test conversion on sample folder"
	@echo "  make lint        - Run lint checks"
	@echo ""
	@echo "4. Enhance Code"
	@echo "  make lint-fix    - Auto-fix lint issues and format imports"
	@echo "  make format      - Format code"
	@echo "  make quality     - Run full quality checks (lint + complexity + tests)"
	@echo ""
	@echo "Options:"
	@echo "  FOLDER=path     - Path to folder (required)"
	@echo "  MODE=X          - What to convert: all (default), images, or videos"
	@echo "  QUALITY=N       - Image quality 0-100 (default: 85)"
	@echo "  VIDEO_CRF=N     - Video CRF 0-51 (h265) or 0-63 (av1), lower=better (default: 28)"
	@echo "  VIDEO_PRESET=X  - Video preset: medium, slow, fast, etc. (default: medium)"
	@echo "  VIDEO_CODEC=X   - Video codec: h265 (fast) or av1 (better, slower) (default: h265)"
	@echo "  FORCE=1         - Force reconversion of all files"
	@echo "  VERBOSE=1       - Enable verbose output"
	@echo "  KEEP_ORIGINALS=1 - Keep original images even if AVIF exists (Default is to delete originals)"
	@echo ""
	@echo "Examples:"
	@echo "  make install                                           # First time setup"
	@echo "  make dry-run FOLDER=/path/to/media                     # Perform a Dry run. No file updated"
	@echo "  make convert FOLDER=/path/to/media                     # Convert images & videos (H.265)"
	@echo "  make convert FOLDER=/path/to/media MODE=images         # Only convert images"
	@echo "  make convert FOLDER=/path/to/media MODE=videos         # Only compress videos"
	@echo "  make convert FOLDER=/path/to/media QUALITY=95          # Set image quality to 95% (Default is 85)"
	@echo "  make convert FOLDER=/path/to/media VIDEO_CRF=23        # Set video quality to 23 (Default is 28)"
	@echo "  make convert FOLDER=/path/to/media VIDEO_CODEC=av1     # Use AV1 (better quality, slower encoding)"
	@echo "  make convert FOLDER=/path/to/media FORCE=1 VERBOSE=1"	# Force reconversion of all files and enable verbose output
	
	
	@echo ""

# Smart install - handles UV installation, venv creation, and dependencies
install:
	@echo "🔧 Installing Image & Video Converter..."
	@echo ""
	@# Check if UV is installed
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "📥 UV not found, installing..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo ""; \
		if ! command -v uv >/dev/null 2>&1; then \
			echo "⚠️  UV installed but not in PATH yet."; \
			echo ""; \
			echo "Run one of these commands to add UV to your PATH:"; \
			echo "  export PATH=\"\$$HOME/.cargo/bin:\$$PATH\""; \
			echo "  source \$$HOME/.cargo/env"; \
			echo ""; \
			echo "Then run 'make install' again."; \
			exit 1; \
		fi; \
	fi
	@echo "✅ UV is available"
	@echo ""
	@# Create venv if it doesn't exist
	@if [ ! -d .venv ]; then \
		echo "📦 Creating virtual environment..."; \
		uv venv || exit 1; \
		echo "✅ Virtual environment created"; \
	else \
		echo "✅ Virtual environment exists"; \
	fi
	@echo ""
	@# Install dependencies
	@echo "📦 Installing dependencies..."
	@uv pip install -e . || exit 1
	@echo ""
	@# Check and install FFmpeg
	@echo "🎬 Checking for FFmpeg..."
	@if ! command -v ffmpeg >/dev/null 2>&1; then \
		echo "📥 FFmpeg not found, installing..."; \
		if [ "$$(uname)" = "Darwin" ]; then \
			if command -v brew >/dev/null 2>&1; then \
				brew install ffmpeg || { echo "❌ Failed to install FFmpeg"; exit 1; }; \
			else \
				echo "❌ Homebrew not found. Install it first: https://brew.sh"; \
				exit 1; \
			fi; \
		elif [ -f /etc/debian_version ]; then \
			sudo apt-get update && sudo apt-get install -y ffmpeg || { echo "❌ Failed to install FFmpeg"; exit 1; }; \
		elif [ -f /etc/redhat-release ]; then \
			sudo dnf install -y ffmpeg || sudo yum install -y ffmpeg || { echo "❌ Failed to install FFmpeg"; exit 1; }; \
		else \
			echo "❌ Unsupported OS. Please install FFmpeg manually: https://ffmpeg.org/download.html"; \
			exit 1; \
		fi; \
		echo "✅ FFmpeg installed"; \
	else \
		echo "✅ FFmpeg is available"; \
	fi
	@echo "✅ Installation complete!"
	@echo ""
	@echo "Ready to use. Try:"
	@echo "  make convert FOLDER=/path/to/your/media"
	@echo ""

# Install development dependencies
install-dev:
	@echo "🧪 Installing development dependencies..."
	@uv pip install -e . --group dev || exit 1
	@echo "✅ Development dependencies installed!"

# Alias for backwards compatibility
setup: install

# Convert images and videos
convert:
ifndef FOLDER
	@echo "❌ Error: FOLDER parameter is required"
	@echo "Usage: make convert FOLDER=/path/to/folder"
	@exit 1
endif
	@echo "🎨 Converting images and videos in $(FOLDER)..."
	@EXPANDED_FOLDER=$$(eval echo "$(FOLDER)"); \
	uv run python -m src.main "$$EXPANDED_FOLDER" \
		$(if $(QUALITY),--quality $(QUALITY),) \
		$(if $(VIDEO_CRF),--video-crf $(VIDEO_CRF),) \
		$(if $(VIDEO_PRESET),--video-preset $(VIDEO_PRESET),) \
		$(if $(VIDEO_CODEC),--video-codec $(VIDEO_CODEC),) \
		$(if $(filter images,$(MODE)),--images-only,) \
		$(if $(filter videos,$(MODE)),--videos-only,) \
		$(if $(KEEP_ORIGINALS),--keep-originals,) \
		$(if $(FORCE),--force,) \
		$(if $(VERBOSE),--verbose,)

# Dry run - preview without executing
dry-run:
ifndef FOLDER
	@echo "❌ Error: FOLDER parameter is required"
	@echo "Usage: make dry-run FOLDER=/path/to/folder"
	@exit 1
endif
	@echo "🔍 Previewing conversion for $(FOLDER)..."
	@EXPANDED_FOLDER=$$(eval echo "$(FOLDER)"); \
	uv run python -m src.main "$$EXPANDED_FOLDER" \
		--dry-run \
		$(if $(QUALITY),--quality $(QUALITY),) \
		$(if $(VIDEO_CRF),--video-crf $(VIDEO_CRF),) \
		$(if $(VIDEO_PRESET),--video-preset $(VIDEO_PRESET),) \
		$(if $(VIDEO_CODEC),--video-codec $(VIDEO_CODEC),) \
		$(if $(filter images,$(MODE)),--images-only,) \
		$(if $(filter videos,$(MODE)),--videos-only,) \
		$(if $(KEEP_ORIGINALS),--keep-originals,) \
		$(if $(VERBOSE),--verbose,)

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf .venv
	@rm -rf __pycache__
	@rm -rf src/__pycache__
	@rm -rf *.egg-info
	@rm -rf .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete"

# Test conversion (create sample folder if needed)
smoke-test:
	@echo "🧪 Running test conversion..."
	@if [ ! -d "test_images" ] || [ -z "$$(find test_images -type f 2>/dev/null)" ]; then \
		echo "📁 Preparing sample media in test_images/..."; \
		mkdir -p test_images/subfolder; \
		uv run python -c "from PIL import Image; Image.new('RGB',(8,8),(64,128,192)).save('test_images/subfolder/sample.png')"; \
	fi
	@uv run python -m src.main test_images

# Unit tests with coverage
unit-test:
	@echo "🧪 Running unit tests with coverage..."
	@uv run --group dev pytest --cov=src --cov-report=term-missing --cov-fail-under=100

# Full developer test suite
test: lint unit-test smoke-test

# Lint checks
lint:
	@echo "🔎 Running lint checks..."
	@uv run --group dev ruff check src tests
	@uv run --group dev ruff format --check src tests

# Auto-fix lint issues
lint-fix:
	@echo "🛠️ Auto-fixing lint issues..."
	@uv run --group dev ruff check --fix src tests
	@uv run --group dev ruff format src tests

# Format code
format:
	@echo "🎨 Formatting code..."
	@uv run --group dev ruff format src tests

# Complexity analysis and quality gate
complexity:
	@echo "📊 Evaluating code complexity..."
	@uv run --group dev radon cc src -s -a
	@uv run --group dev xenon --max-absolute C --max-modules B --max-average A src

# Full local quality gate
quality: complexity test
