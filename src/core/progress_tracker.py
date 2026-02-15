"""Progress tracker for displaying conversion progress."""
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

class ProgressTracker:
    """Manages and displays progress for file conversion operations."""

    def __init__(self, total_files: int, console: Console=None):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def update(self, increment: int=1, success: bool=True):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def __enter__(self):
        raise NotImplementedError()

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError()
