from __future__ import annotations

import concurrent.futures
import os
from typing import Optional, Tuple

from config.settings import pdf_config, processing_config
from services.database_service import DatabaseService
from utils.file_handler import FileHandler
from utils.forex_parser import import_forex_rates_from_pdf
from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class PDFBatchProcessor:
    """Handles batch processing of PDF files with optimized database initialization."""

    def __init__(self, num_workers: Optional[int] = None):
        """Initialize the batch processor.

        Args:
            num_workers: Number of parallel workers to use (uses config default if None)
        """
        self.num_workers = num_workers or processing_config.num_workers
        self.file_handler = FileHandler()
        self.shared_db_service = None

    def _initialize_database(self) -> bool:
        """Initialize database schema and connections. Called once before processing."""
        logger.info("Initializing database schema...")
        self.shared_db_service = DatabaseService()

        if not self.shared_db_service.connect():
            logger.error("Failed to connect to database")
            return False

        if not self.shared_db_service.test_connection():
            logger.error("Database connection test failed")
            return False

        logger.info("Database initialization completed successfully")
        return True

    def _process_pdf(self, path: str) -> Tuple[str, int]:
        """Worker that runs the parser and returns (path, exit_code).

        Each worker gets its own database service instance but uses the
        pre-initialized schema.
        """
        try:
            # Create a new database service for this worker
            worker_db_service = DatabaseService()
            exit_code = import_forex_rates_from_pdf(
                path, max_pages=pdf_config.max_pages, db_service=worker_db_service
            )
        except Exception:
            logger.exception("Exception while processing %s", path)
            return path, -1
        return path, int(exit_code)

    def process_all_pdfs(self, root_dir: str) -> int:
        """Process all PDFs in the specified directory using parallel workers.

        Args:
            root_dir: Root directory to search for PDF files

        Returns:
            Exit code: 0 for success, 1 for failure
        """
        if not os.path.isdir(root_dir):
            logger.error("PDF root directory %s not found", root_dir)
            return 1

        pdfs = self.file_handler.collect_pdfs(root_dir)
        if not pdfs:
            logger.error("No PDF files found under %s", root_dir)
            return 1

        # Initialize database schema once before starting workers
        if not self._initialize_database():
            logger.error("Failed to initialize database")
            return 1

        logger.info(
            "Found %d PDF files to process (workers=%d)", len(pdfs), self.num_workers
        )

        processed = 0
        failed = 0

        # Process PDFs with parallel workers
        if self.num_workers == 1:
            # Sequential processing for single worker
            for pdf_path in pdfs:
                path, exit_code = self._process_pdf(pdf_path)
                if exit_code == 0:
                    processed += 1
                    logger.info("Successfully processed: %s", path)
                else:
                    failed += 1
                    logger.error(
                        "Failed to process: %s (exit code: %d)", path, exit_code
                    )
        else:
            # Parallel processing for multiple workers
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.num_workers
            ) as executor:
                future_to_path = {
                    executor.submit(self._process_pdf, p): p for p in pdfs
                }
                for fut in concurrent.futures.as_completed(future_to_path):
                    path, exit_code = fut.result()
                    if exit_code == 0:
                        processed += 1
                        logger.info("Successfully processed: %s", path)
                    else:
                        failed += 1
                        logger.error(
                            "Failed to process: %s (exit code: %d)", path, exit_code
                        )

        logger.info("Processing complete. Processed: %d, Failed: %d", processed, failed)
        return 0 if failed == 0 else 1


def main():
    """Main function to process all PDFs in pdf_files directory using parallel workers."""
    LoggerFactory.setup_logging()

    processor = PDFBatchProcessor()
    return processor.process_all_pdfs(processing_config.pdf_files_dir)


if __name__ == "__main__":
    raise SystemExit(main())
