#!/usr/bin/env python3
"""Fetch SBI forex rates PDF from URL and process it.

This script downloads the latest SBI forex rates PDF from the SBI website,
renames it to the correct date format, and processes it using the
import_forex_rates_from_pdf function.
"""
import logging
import os
import sys
import tempfile
from parser import import_forex_rates_from_pdf
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# SBI forex rates URLs (primary and fallback)
PRIMARY_URL = "https://www.sbi.co.in/documents/16012/1400784/FOREX_CARD_RATES.pdf"
FALLBACK_URL = "https://bank.sbi/documents/16012/1400784/FOREX_CARD_RATES.pdf"


def setup_logging() -> None:
    """Configure basic logging."""
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


def download_pdf(url: str, timeout: int = 30) -> Optional[bytes]:
    """Download PDF from the given URL.

    Args:
        url: The URL to download from
        timeout: Request timeout in seconds

    Returns:
        PDF content as bytes if successful, None otherwise
    """
    try:
        logger.info("Downloading PDF from: %s", url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
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


def fetch_forex_pdf() -> Optional[bytes]:
    """Fetch forex rates PDF, trying primary URL first, then fallback.

    Returns:
        PDF content as bytes if successful, None otherwise
    """
    # Try primary URL first
    pdf_content = download_pdf(PRIMARY_URL)
    if pdf_content:
        return pdf_content

    logger.warning("Primary URL failed, trying fallback URL")

    # Try fallback URL
    pdf_content = download_pdf(FALLBACK_URL)
    if pdf_content:
        return pdf_content

    logger.error("Both primary and fallback URLs failed")
    return None


def save_pdf_to_temp(pdf_content: bytes) -> Optional[str]:
    """Save PDF bytes to a temporary file and return path.

    This does not encode any date in the filename — the PDF's internal
    date will be used by the parser as the source of truth.
    """
    try:
        fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        with open(pdf_path, "wb") as f:
            f.write(pdf_content)
        logger.info("Saved PDF to temporary path: %s", pdf_path)
        return pdf_path
    except Exception as e:
        logger.error("Failed to save PDF to temporary file: %s", e)
        return None


def main():
    """Main function to fetch and process SBI forex rates PDF."""
    setup_logging()

    logger.info("Starting fetch and fill from URL process")

    # Fetch the PDF
    pdf_content = fetch_forex_pdf()
    if not pdf_content:
        logger.error("Failed to fetch PDF from any URL")
        return 1

    # Save PDF to a temporary file (no filename-based date)
    pdf_path = save_pdf_to_temp(pdf_content)
    if not pdf_path:
        logger.error("Failed to save PDF file")
        return 1

    try:
        # Process the PDF using the existing parser
        logger.info("Processing PDF: %s", pdf_path)
        exit_code = import_forex_rates_from_pdf(pdf_path, max_pages=2)

        if exit_code == 0:
            logger.info("Successfully processed forex rates PDF")
            return 0
        else:
            logger.error("Failed to process PDF (exit code: %d)", exit_code)
            return exit_code

    finally:
        # Clean up temporary file
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                # Also remove the temporary directory
                temp_dir = os.path.dirname(pdf_path)
                os.rmdir(temp_dir)
                logger.debug("Cleaned up temporary files")
        except Exception as e:
            logger.warning("Failed to clean up temporary files: %s", e)


if __name__ == "__main__":
    sys.exit(main())
