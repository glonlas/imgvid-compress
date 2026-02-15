"""Logging configuration using Rich for modern, colored console output."""

import logging

from rich.console import Console
from rich.logging import RichHandler


class LoggerConfig:
    """Configures application logging with Rich handler for beautiful output."""

    _configured = False
    console = Console()

    @classmethod
    def setup(cls, level: int = logging.INFO) -> None:
        """
        Configure the root logger with Rich handler.

        Args:
            level: Logging level (default: logging.INFO)
        """
        if cls._configured:
            return

        # Remove existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Configure Rich handler
        handler = RichHandler(
            console=cls.console,
            show_time=False,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )

        # Set format
        handler.setFormatter(logging.Formatter("%(message)s"))

        # Configure root logger
        root_logger.addHandler(handler)
        root_logger.setLevel(level)

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with the given name.

        Args:
            name: Name for the logger (typically __name__)

        Returns:
            Logger instance
        """
        if not cls._configured:
            cls.setup()

        return logging.getLogger(name)
