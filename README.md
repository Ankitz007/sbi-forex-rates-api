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
      "tt_buy": 82.50,
      "tt_sell": 83.00,
      "bill_buy": 82.25,
      "bill_sell": 83.25,
      "ftc_buy": 82.00,
      "ftc_sell": 83.50,
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

## 🛠️ Local development

Use the repository root on PYTHONPATH so imports resolve the same way as Vercel (PYTHONPATH="."). Two quick ways to run locally:

Run the module directly (uses the app's built-in uvicorn runner):

```bash
PYTHONPATH=. python -m api.main
```

Or run with uvicorn for auto-reload during development:

```bash
PYTHONPATH=. uvicorn api.main:app --reload
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Local URLs:

- API root: <http://localhost:8000/>
- OpenAPI docs: <http://localhost:8000/docs>
