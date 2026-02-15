"""Progress tracker for displaying conversion progress."""

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


class ProgressTracker:
    """Manages and displays progress for file conversion operations."""

    def __init__(self, total_files: int, console: Console = None):
        """
        Initialize the progress tracker.

        Args:
            total_files: Total number of files to process
            console: Optional Rich console instance
        """
        self.total_files = total_files
        self.console = console or Console()
        self.progress = None
        self.task_id = None
        self.success_count = 0
        self.failed_count = 0

    def start(self):
        """Start the progress tracking."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
        )

        self.progress.start()
        self.task_id = self.progress.add_task("[cyan]Processing files...", total=self.total_files)

    def update(self, increment: int = 1, success: bool = True):
        """
        Update progress.

        Args:
            increment: Number of files processed
            success: Whether the operation was successful
        """
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, advance=increment)

            if success:
                self.success_count += increment
            else:
                self.failed_count += increment

    def stop(self):
        """Stop the progress tracking."""
        if self.progress:
            self.progress.stop()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
