"""
Utility functions for the API.
"""

from datetime import datetime


class DateValidator:
    """Utility class for date validation."""

    @staticmethod
    def validate_date_format(date_str: str) -> datetime:
        """
        Validate date string in DD-MM-YYYY format.

        Args:
            date_str: Date string to validate

        Returns:
            datetime object if valid

        Raises:
            ValueError: If date format is invalid
        """
        try:
            return datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            raise ValueError("Date must be in DD-MM-YYYY format")
