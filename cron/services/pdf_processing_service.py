"""
PDF processing service for SBI forex rates.
"""

import datetime
from typing import List, Optional, Tuple

import pdfplumber
from config.settings import pdf_config
from utils.date_parser import DateParser
from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class PDFProcessingService:
    """Service for processing SBI forex rate PDFs."""

    def __init__(self):
        """Initialize the PDF processing service."""
        self.date_parser = DateParser()

    def extract_date_and_tables(
        self, pdf_path: str, max_pages: Optional[int] = None
    ) -> Tuple[
        Optional[datetime.date],
        List[Optional[List[List[Optional[str]]]]],
        List[Optional[str]],
        str,
    ]:
        """Open the PDF once, validate the date, and return up to `max_pages` first tables.

        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to process (uses config default if None)

        Returns:
            Tuple of (pdf_date, tables, page_texts, status)
        """
        max_pages = max_pages or pdf_config.max_pages
        tables: List[Optional[List[List[Optional[str]]]]] = []
        page_texts: List[Optional[str]] = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = min(max_pages, len(pdf.pages))

                first_page = pdf.pages[0]

                # Find date on first page
                date_text = self._find_date_text(first_page)
                pdf_date = (
                    self.date_parser.parse_pdf_date(date_text) if date_text else None
                )

                if pdf_date is None:
                    logger.error(
                        "Could not parse a PDF date from PDF date line: %s", date_text
                    )
                    return None, [], [], "parse_error"

                logger.info("Extracted PDF date: %s", pdf_date)

                # Extract tables and text from each page
                for i in range(page_count):
                    page = pdf.pages[i]

                    # Extract table
                    table = page.extract_table()
                    tables.append(table)

                    # Extract text
                    text = page.extract_text()
                    page_texts.append(text)

                    logger.debug(
                        "Page %d: Extracted table with %d rows",
                        i + 1,
                        len(table) if table else 0,
                    )

                return pdf_date, tables, page_texts, "success"

        except Exception as e:
            logger.error("Error processing PDF %s: %s", pdf_path, e)
            return None, [], [], "error"

    def _find_date_text(self, page) -> Optional[str]:
        """Find the date text line on a PDF page.

        Args:
            page: pdfplumber page object

        Returns:
            Date text line if found, None otherwise
        """
        try:
            for line in page.extract_text_lines():
                text = line.get("text") or ""
                if "Date" in text:
                    logger.debug("Found date line: %s", text)
                    return text
        except Exception as e:
            logger.debug("Error extracting text lines: %s", e)

        return None

    def categorize_table(
        self, raw_table: List[List[Optional[str]]], page_text: Optional[str] = None
    ) -> str:
        """Categorize a table based on its content or associated page text.

        Args:
            raw_table: The extracted table data
            page_text: Optional page text for additional context

        Returns:
            Category string
        """
        # Define marker strings for different categories
        markers = [
            ("BELOW", "below_10"),
            ("BETWEEN 10", "10_to_20"),
            ("10 TO 20", "10_to_20"),
        ]

        # First, check the page text if available
        if page_text:
            upper_text = page_text.upper()
            for key, cat in markers:
                if key in upper_text:
                    return cat

        # Fallback: inspect the first few table rows for the marker string
        look_rows = raw_table[:3] if raw_table else []
        for row in look_rows:
            if not row:
                continue
            for cell in row:
                if not cell:
                    continue
                text = str(cell).strip().upper()
                for key, cat in markers:
                    if key in text:
                        return cat

        return "UNKNOWN"

    def is_currency_row(self, row: List[Optional[str]]) -> bool:
        """Heuristic to determine whether a table row represents currency data.

        We expect a pair like 'USD/INR' in the second column.

        Args:
            row: Table row to check

        Returns:
            True if the row appears to contain currency data
        """
        if len(row) < 2:
            return False

        second = row[1] or ""
        return "/" in second and len(second.split("/")) == 2

    def validate_and_convert_rate(self, value: Optional[str]) -> Optional[float]:
        """Validate and convert a rate value from string to float.

        Args:
            value: String value to convert

        Returns:
            Float value if valid, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        # Clean the value
        cleaned = value.strip()
        if not cleaned or cleaned.lower() in ["na", "n/a", "-", ""]:
            return None

        try:
            return float(cleaned)
        except ValueError:
            logger.debug("Could not convert rate value to float: %s", value)
            return None
