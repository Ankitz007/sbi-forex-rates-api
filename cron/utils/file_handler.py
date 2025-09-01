"""
File handling utilities.
"""

import os
import tempfile
from typing import List, Optional

from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class FileHandler:
    """Utility class for file operations."""

    @staticmethod
    def collect_pdfs(path: str) -> List[str]:
        """
        Recursively collect .pdf file paths under `path`.

        Args:
            path: Root directory to search

        Returns:
            Sorted list of absolute paths to PDF files
        """
        pdfs = []
        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                if filename.lower().endswith(".pdf"):
                    pdfs.append(os.path.join(dirpath, filename))
        return sorted(pdfs)

    @staticmethod
    def save_to_temp_file(content: bytes, suffix: str = ".pdf") -> Optional[str]:
        """
        Save content to a temporary file and return the path.

        Args:
            content: Bytes content to save
            suffix: File suffix/extension

        Returns:
            Path to temporary file if successful, None otherwise
        """
        try:
            fd, temp_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)

            with open(temp_path, "wb") as f:
                f.write(content)

            logger.debug("Saved content to temporary file: %s", temp_path)
            return temp_path

        except Exception as e:
            logger.error("Failed to save content to temporary file: %s", e)
            return None

    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        """
        Clean up a temporary file and its directory if empty.

        Args:
            file_path: Path to the temporary file
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)

                # Try to remove the temporary directory if it's empty
                temp_dir = os.path.dirname(file_path)
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    # Directory not empty or other error, ignore
                    pass

                logger.debug("Cleaned up temporary file: %s", file_path)

        except Exception as e:
            logger.warning("Failed to clean up temporary file %s: %s", file_path, e)
