"""
FastAPI application for SBI FX Rates API.

This API provides endpoints to fetch forex rates from the database.
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from api.config import settings
from api.database import SessionLocal
from api.schemas import StandardResponse
from api.services import ForexRateService
from api.utils import DateValidator

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)


@app.get("/", response_model=StandardResponse)
async def get_forex_rates(
    date: str = Query(..., description="Date in DD-MM-YYYY format"),
    ticker: Optional[str] = Query(None, description="Currency ticker (e.g., USD, EUR)"),
):
    """
    Fetch forex rates for a specific date.

    Args:
        date: Date in DD-MM-YYYY format
        ticker: Optional currency ticker to filter results

    Returns:
        List of forex rates for the specified date

    Raises:
        HTTPException: If date format is invalid or no data found
    """
    try:
        # Validate date format
        validated_date = DateValidator.validate_date_format(date)

        # Get database session
        db = SessionLocal()

        try:
            forex_rates = ForexRateService.get_rates_by_date(db, validated_date, ticker)

            if not forex_rates:
                ticker_msg = f" for {ticker}" if ticker else ""
                return StandardResponse(
                    success=True,
                    data=[],
                    message=f"No forex rates found{ticker_msg} for {date}",
                )

            result = [
                ForexRateService.convert_to_response(rate, date) for rate in forex_rates
            ]

            # If a ticker was requested, return a single object in `data`, else return the list
            if ticker:
                return StandardResponse(success=True, data=result[0])

            return StandardResponse(success=True, data=result)

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")

        finally:
            db.close()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Used during development
# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host=settings.HOST, port=settings.PORT)
