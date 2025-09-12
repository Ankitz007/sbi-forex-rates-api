# # Below two lines are only for development
# import sys, pathlib

# sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
import argparse
import datetime
from typing import List, Optional, Tuple

import pdfplumber
from services.database_service import DatabaseService

from utils.date_parser import DateParser
from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def extract_date_and_tables(pdf_path: str, max_pages: int = 2) -> Tuple[
    Optional[datetime.date],
    List[Optional[List[List[Optional[str]]]]],
    List[Optional[str]],
    str,
]:
    """Open the PDF once, validate the date, and return up to `max_pages` first tables.

    Returns (pdf_date, [table_page0, table_page1, ...], status)
    """
    tables: List[Optional[List[List[Optional[str]]]]] = []
    page_texts: List[Optional[str]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_count = min(max_pages, len(pdf.pages))

            first_page = pdf.pages[0]

            # find date on first page
            date_text = None
            for line in first_page.extract_text_lines():
                text = line.get("text") or ""
                if "Date" in text:
                    date_text = text
                    logger.debug("Found date line: %s", text)
                    break

            pdf_date = parse_pdf_date(date_text) if date_text else None
            if pdf_date is None:
                logger.error(
                    "Could not parse a PDF date from PDF date line: %s", date_text
                )
                return None, [], [], "parse_error"

            # extract first table from up to page_count pages
            found_any = False
            for i in range(page_count):
                page = pdf.pages[i]
                page_text = page.extract_text() if page.extract_text() else ""
                page_texts.append(page_text)
                page_tables = page.extract_tables()
                if page_tables:
                    tables.append(page_tables[0])
                    found_any = True
                else:
                    tables.append(None)

            if not found_any:
                return pdf_date, tables, page_texts, "no_table"
            return pdf_date, tables, page_texts, "ok"
    except FileNotFoundError:
        logger.error("File not found: %s", pdf_path)
        return None, [], [], "file_not_found"
    except Exception as exc:
        logger.error("Error reading PDF '%s': %s", pdf_path, exc)
        return None, [], [], "error"


def categorize_table(
    raw_table: List[List[Optional[str]]], page_text: Optional[str] = None
) -> str:
    """Detect category string inside the first up to 3 rows of a raw table.

    Returns one of:
      - 'CARD RATES FOR TRANSACTIONS BELOW'
      - 'CARD RATES FOR TRANSACTIONS BETWEEN'
      - 'UNKNOWN'
    """
    if not raw_table:
        return "UNKNOWN"
    markers = [
        ("CARD RATES FOR TRANSACTIONS BELOW", "BELOW_10"),
        ("CARD RATES FOR TRANSACTIONS BETWEEN", "BETWEEN_10_20"),
    ]
    # If page text is provided, check it first for an explicit marker.
    if page_text:
        up = page_text.upper()
        for key, cat in markers:
            if key in up:
                return cat

    # Fallback: inspect the first few table rows for the marker string.
    look_rows = raw_table[:3]
    for row in look_rows:
        if not row:
            continue
        for cell in row:
            if not cell:
                continue
            text = str(cell).strip()
            upper = text.upper()
            for key, cat in markers:
                if key in upper:
                    return cat
    return "UNKNOWN"


def parse_pdf_date(line: str) -> Optional[datetime.date]:
    """Find a PDF-style date (DD-MM-YYYY) inside a line of text and return a date.

    Returns a datetime.date if found and parsed, otherwise None.
    """
    return DateParser.parse_pdf_date(line)


# filename-based date extraction removed: PDF-extracted date is the source of truth


def _is_currency_row(row: List[Optional[str]]) -> bool:
    """Heuristic to determine whether a table row represents currency data.

    We expect a pair like 'USD/INR' in the second column.
    """
    if len(row) < 2:
        return False
    second = row[1] or ""
    return "/" in second


def clean_table(
    raw_table: List[List[Optional[str]]],
) -> Tuple[List[str], List[List[str]]]:
    """Normalize the raw table into headers and cleaned rows.

    Returns a tuple of (headers, cleaned_rows).
    """
    headers = [
        "CURRENCY",
        "TICKER",
        "TT BUY",
        "TT SELL",
        "BILL BUY",
        "BILL SELL",
        "FTC BUY",
        "FTC SELL",
        "CN BUY",
        "CN SELL",
    ]

    data_rows: List[List[str]] = []
    for row in raw_table:
        if not _is_currency_row(row):
            logger.debug("Skipping non-currency row: %s", row)
            continue
        cleaned = [
            (str(cell).replace("\n", " ").strip() if cell else "0") for cell in row
        ]
        # If the second column contains a pair like 'USD/INR', replace it with the ticker 'USD'
        if len(cleaned) >= 2 and cleaned[1] and "/" in cleaned[1]:
            try:
                cleaned[1] = cleaned[1].split("/")[0].strip()
            except Exception:
                # fallback: leave as-is
                pass
        # Ensure row has at least as many columns as headers
        if len(cleaned) < len(headers):
            cleaned += ["0"] * (len(headers) - len(cleaned))
        data_rows.append(cleaned[: len(headers)])

    return headers, data_rows


def table_to_records(
    date: datetime.date, category: str, headers: List[str], rows: List[List[str]]
) -> List[dict]:
    """Convert a table (headers+rows) into a list of dict records ready for DB insert.

    Returns a list of dicts with standard field names. Keeps values as strings for
    downstream conversion/migration.
    """
    field_names = [
        "name",
        "ticker",
        "tt_buy",
        "tt_sell",
        "bill_buy",
        "bill_sell",
        "ftc_buy",
        "ftc_sell",
        "cn_buy",
        "cn_sell",
    ]
    records: List[dict] = []
    for row in rows:
        # normalize row length
        r = list(row) + ["0"] * (len(field_names) - len(row))
        rec = {field_names[i]: r[i] for i in range(len(field_names))}
        rec["date"] = date.isoformat()
        rec["category"] = category
        records.append(rec)
    return records


def process_pdf(path: str, max_pages: int = 2) -> Tuple[Optional[List[dict]], int]:
    """High-level processing: extract tables from PDF and return records.

    The date is read from the PDF itself and used as the source of truth.
    Returns (records_list, exit_code) where exit_code is 0 on success.
    """

    pdf_date, page_tables, page_texts, status = extract_date_and_tables(
        path, max_pages=max_pages
    )
    if status != "ok":
        # map statuses to exit codes
        if status == "file_not_found":
            return [], 4
        if status == "parse_error":
            return [], 5
        if status == "no_table":
            return [], 2
        return [], 1

    all_records: List[dict] = []
    for idx, raw_table in enumerate(page_tables):
        if not raw_table:
            continue
        page_text = page_texts[idx] if page_texts and idx < len(page_texts) else None
        category = categorize_table(raw_table, page_text=page_text)
        headers, rows = clean_table(raw_table)
        if not rows:
            continue
        if pdf_date is None or category == "UNKNOWN":
            logger.error("Cannot process records without a valid PDF date or category")
            return [], 1
        records = table_to_records(pdf_date, category, headers, rows)
        all_records.extend(records)

    if not all_records:
        return [], 3
    return all_records, 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    p = argparse.ArgumentParser(
        description="Parse SBI FX rates PDF and save to database"
    )
    p.add_argument("pdf", help="PDF file to parse")
    p.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    return p.parse_args(argv)


def import_forex_rates_from_pdf(
    path: str,
    max_pages: int,
    db_service: Optional[DatabaseService] = None,
    use_multiple_dbs: bool = True,
) -> int:
    LoggerFactory.setup_logging()

    def _prepare_db_and_insert(
        svc: DatabaseService, records: List[dict], db_name: str = "database"
    ) -> bool:
        """Connect, test and insert; return True on success."""
        if not svc.connect():
            logger.error(f"Failed to connect to {db_name}")
            return False
        if not svc.test_connection():
            logger.error(f"{db_name} connection test failed")
            return False
        if svc.insert_forex_records(records):
            logger.info(f"Successfully inserted {len(records)} records into {db_name}")
            return True
        logger.error(f"Failed to insert records into {db_name}")
        return False

    # Process PDF once
    records, exit_code = process_pdf(path, max_pages=max_pages)
    if exit_code != 0:
        logger.error(f"Failed to process PDF: {path} exit_code: {exit_code}")
        return exit_code
    if not records:
        logger.error(f"No records to process for PDF: {path}")
        return 3

    # Single DB flow (used by ingest_all)
    if not use_multiple_dbs:
        if db_service is None:
            db_service = DatabaseService()
        ok = _prepare_db_and_insert(db_service, records, db_name="primary")
        return 0 if ok else 1

    # Multiple databases flow
    from config.settings import db_config

    db_urls = db_config.get_all_urls()
    if not db_urls:
        logger.error("No database URLs configured")
        return 1

    success_count = 0
    failure_count = 0
    total_dbs = len(db_urls)
    for i, db_url in enumerate(db_urls):
        db_name = ["primary", "backup"][i] if i < 2 else f"db_{i}"
        logger.info(f"Processing {db_name} database...")

        try:
            svc = DatabaseService(database_url=db_url)
            ok = _prepare_db_and_insert(svc, records, db_name=db_name)
            if ok:
                success_count += 1
            else:
                failure_count += 1
                logger.error(f"{db_name} reported failure during insert")
        except Exception as e:
            failure_count += 1
            logger.error(f"Error processing {db_name} database: {e}")
            continue

    logger.info(
        f"Processed {success_count}/{total_dbs} successful, {failure_count} failed"
    )
    # Even a single failure should be treated as an overall error
    if failure_count > 0:
        return 1
    return 0


def main():
    """Main function for command-line usage."""
    import sys

    args = parse_args(sys.argv[1:])
    return import_forex_rates_from_pdf(args.pdf, max_pages=2, use_multiple_dbs=False)


if __name__ == "__main__":
    import sys

    sys.exit(main())
