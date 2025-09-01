"""
Date parsing and validation utilities.
"""

import datetime
import re
from typing import Optional

from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class DateParser:
    """Utility class for parsing and validating dates from various sources."""

    @staticmethod
    def parse_pdf_date(line: str) -> Optional[datetime.date]:
        """
        Find a PDF-style date (DD-MM-YYYY) inside a line of text and return a date.

        Args:
            line: Text line containing the date

        Returns:
            datetime.date if found and parsed, otherwise None
        """
        if not line:
            return None

        # Extract day, month, year using regex groups
        match = re.search(r"(\d{2})[-/](\d{2})[-/](\d{4})", line)
        if not match:
            return None

        try:
            day, month, year = map(int, match.groups())
            return datetime.date(year, month, day)
        except ValueError:
            # Handle invalid dates (e.g., 32-13-2023)
            logger.debug("Failed to parse PDF date on line: %s", line)
            return None

    @staticmethod
    def validate_date_format(
        date_str: str, format_str: str = "%Y-%m-%d"
    ) -> Optional[datetime.date]:
        """
        Validate a date string against a specific format.

        Args:
            date_str: Date string to validate
            format_str: Expected format (default: YYYY-MM-DD)

        Returns:
            datetime.date if valid, None otherwise
        """
        try:
            return datetime.datetime.strptime(date_str, format_str).date()
        except ValueError:
            logger.debug(
                "Failed to parse date '%s' with format '%s'", date_str, format_str
            )
            return None
