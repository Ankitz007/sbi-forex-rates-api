# SBI Forex Rates API

A Python API to fetch foreign exchange rates from the State Bank of India (SBI).

## 🚀 Live API

The API is deployed and available at: <https://sbi-forex-rates-api.vercel.app/>

## 📋 API Endpoints

### 1. Get Forex Rates for a Date

- Endpoint: `GET /`
- Description: Fetch all forex rates for a specific date.
- Query parameters:
  - `date` (required) — Date in DD-MM-YYYY format

Example:

```bash
curl "https://sbi-forex-rates-api.vercel.app/?date=25-04-2025"
```

### 2. Check Date Availability (range)

- Endpoint: `GET /check-dates`
- Description: Return which dates within an inclusive date range have data in the DB.
- Query parameters:
  - `from` (required) — start date in DD-MM-YYYY format
  - `to` (required) — end date in DD-MM-YYYY format

Example (check 1–5 Jan 2025):

```bash
curl "https://sbi-forex-rates-api.vercel.app/check-dates?from=01-01-2025&to=05-01-2025"
```

Notes:

- The API returns dates in DD-MM-YYYY format.
- The service enforces a safety cap on the range (2 years by default). Ask if you want this changed.

## 📊 Response Format

All endpoints return a standardized JSON envelope:

```json
{
  "success": true,
  "data": [...],
  "message": "Optional descriptive message"
}
```

### Sample Forex Rates Response

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "currency": "United States Dollar",
      "ticker": "USD",
      "tt_buy": 82.5,
      "tt_sell": 83.0,
      "bill_buy": 82.25,
      "bill_sell": 83.25,
      "ftc_buy": 82.0,
      "ftc_sell": 83.5,
      "cn_buy": 81.75,
      "cn_sell": 83.75,
      "date": "25-04-2025",
      "category": "below_10"
    }
  ]
}
```

### Sample Date Availability Response

```json
{
  "success": true,
  "data": ["01-01-2025", "03-01-2025"],
  "message": "Found data for 2 out of 5 dates"
}
```

## ⏰ Cron jobs

This repository includes small command-line scripts under the `cron/` folder that are useful for scheduled processing of SBI forex PDFs and bulk ingestion of already-downloaded PDFs.

What is included

- `cron/fetch_and_fill_from_url.py` — Downloads the latest SBI forex rates PDF (tries a primary and fallback URL), saves a temporary file, and processes it into the database.
- `cron/ingest_all.py` — Walks the `pdf_files/` directory and processes all PDF files in parallel (configurable worker count).
- `cron/check_db_sync.py` — Checks if all three databases (primary, fallback, backup) are synchronized by comparing record counts, date ranges, and sample data integrity.
- `cron/requirements.txt` — Extra Python dependencies used by the cron scripts (PDF parsing, DB drivers, requests).

Key configuration

- The cron scripts load environment variables via `python-dotenv`. You can configure database URLs and other settings using a `.env` file or environment variables:
  - `DATABASE_URL` (primary DB connection)
  - `FALLBACK_DATABASE_URL` (optional)
  - `BACKUP_DATABASE_URL` (optional)
  - Other runtime config values are defined in `cron/config/settings.py` (for example, `pdf_files_dir` and `num_workers`).

Manual run (one-shot)

From the project root (recommended to keep imports working):

```bash
# ensure your virtualenv or python env is active and dependencies are installed
pip install -r cron/requirements.txt

# fetch latest PDF and process
PYTHONPATH=. python cron/fetch_and_fill_from_url.py

# process all PDFs under the pdf_files directory
PYTHONPATH=. python cron/ingest_all.py

# check database synchronization status
PYTHONPATH=. python cron/check_db_sync.py
```

Notes & troubleshooting

- The cron scripts expect the repository root on `PYTHONPATH` so internal imports resolve the same way they do when running the API. That's why the examples use `PYTHONPATH=.` and `cd` into the repo first.
- If you use a virtual environment, activate it in the crontab command or point to its `python` binary explicitly.
- If PDF downloads fail, check logs from `cron_fetch.log` and ensure the URLs in `cron/config/settings.py` are reachable.
- Adjust `pdf_files/` directory location or `processing_config.pdf_files_dir` in `cron/config/settings.py` if you store PDFs elsewhere.

## 🛠️ Local development

Use the repository root on PYTHONPATH so imports resolve the same way as Vercel (PYTHONPATH="."). Run locally with:

```bash
PYTHONPATH=. python -m api.main
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Local URLs:

- API root: <http://localhost:8080/>
- OpenAPI docs: <http://localhost:8080/docs>
