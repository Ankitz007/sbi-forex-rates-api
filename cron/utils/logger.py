"""
Logging utilities for the cron package.
"""

import logging
from typing import Optional


class LoggerFactory:
    """Factory class for creating configured loggers."""

    _configured: bool = False

    @classmethod
    def setup_logging(
        cls, level: str = "INFO", format_string: Optional[str] = None
    ) -> None:
        """Configure basic logging for the application."""
        if cls._configured:
            return

        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        logging.basicConfig(
            format=format_string,
            level=getattr(logging, level.upper(), logging.INFO),
            force=True,
        )
        cls._configured = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger with the specified name."""
        if not cls._configured:
            cls.setup_logging()
        return logging.getLogger(name)
