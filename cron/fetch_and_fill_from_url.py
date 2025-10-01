import sys
from typing import Optional

import requests
from config.settings import pdf_config

from utils.file_handler import FileHandler
from utils.forex_parser import import_forex_rates_from_pdf
from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class ForexPDFDownloader:
    """Handles downloading and processing of SBI forex rates PDFs."""

    def __init__(self, timeout: Optional[int] = None):
        """Initialize the downloader with configuration.

        Args:
            timeout: Request timeout in seconds (uses config default if None)
        """
        self.timeout = timeout or pdf_config.request_timeout
        self.file_handler = FileHandler()

    def download_pdf(self, url: str) -> Optional[bytes]:
        """Download PDF from the given URL.

        Args:
            url: The URL to download from

        Returns:
            PDF content as bytes if successful, None otherwise
        """
        try:
            logger.info("Downloading PDF from: %s", url)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Check if content is actually a PDF
            content_type = response.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not response.content.startswith(b"%PDF"):
                logger.warning("Downloaded content doesn't appear to be a PDF")
                return None

            logger.info("Successfully downloaded PDF (%d bytes)", len(response.content))
            return response.content

        except requests.exceptions.RequestException as e:
            logger.error("Failed to download PDF from %s: %s", url, e)
            return None

    def fetch_forex_pdf(self) -> Optional[bytes]:
        """Fetch forex rates PDF, trying primary URL first, then fallback.

        Returns:
            PDF content as bytes if successful, None otherwise
        """
        # Try primary URL first
        pdf_content = self.download_pdf(pdf_config.primary_url)
        if pdf_content:
            return pdf_content

        logger.warning("Primary URL failed, trying fallback URL")

        # Try fallback URL
        pdf_content = self.download_pdf(pdf_config.fallback_url)
        if pdf_content:
            return pdf_content

        logger.error("Both primary and fallback URLs failed")
        return None

    def process_forex_pdf(self) -> int:
        """Download and process the forex rates PDF.

        Returns:
            Exit code: 0 for success, non-zero for failure
        """
        logger.info("Starting fetch and fill from URL process")

        # Fetch the PDF
        pdf_content = self.fetch_forex_pdf()
        if not pdf_content:
            logger.error("Failed to fetch PDF from any URL")
            return 1

        # Save PDF to a temporary file
        pdf_path = self.file_handler.save_to_temp_file(pdf_content, suffix=".pdf")
        if not pdf_path:
            logger.error("Failed to save PDF file")
            return 1

        try:
            # Process the PDF using the existing parser with multiple databases
            logger.info("Processing PDF: %s", pdf_path)
            exit_code = import_forex_rates_from_pdf(
                pdf_path, max_pages=pdf_config.max_pages, use_multiple_dbs=True
            )

            if exit_code == 0:
                logger.info("Successfully processed forex rates PDF")
                return 0
            else:
                logger.error("Failed to process PDF (exit code: %d)", exit_code)
                return exit_code

        finally:
            # Clean up temporary file
            self.file_handler.cleanup_temp_file(pdf_path)


def main():
    """Main function to fetch and process SBI forex rates PDF."""
    LoggerFactory.setup_logging()

    downloader = ForexPDFDownloader()
    return downloader.process_forex_pdf()


if __name__ == "__main__":
    sys.exit(main())
