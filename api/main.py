"""
FastAPI application for SBI FX Rates API.

This API provides endpoints to fetch forex rates from the database.
"""

import logging

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from api.core import SessionLocal, settings
from api.schemas import DateAvailabilityResponse, StandardResponse
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
):
    """
    Fetch forex rates for a specific date.

    Args:
        date: Date in DD-MM-YYYY format

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
            forex_rates = ForexRateService.get_rates_by_date(db, validated_date)

            if not forex_rates:
                return StandardResponse(
                    success=True,
                    data=[],
                    message=f"No forex rates found for {date}",
                )

            result = [
                ForexRateService.convert_to_response(rate, date) for rate in forex_rates
            ]

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


@app.get("/check-dates", response_model=DateAvailabilityResponse)
async def check_dates_availability(
    from_date: str = Query(
        ..., alias="from", description="Start date in DD-MM-YYYY format"
    ),
    to_date: str = Query(..., alias="to", description="End date in DD-MM-YYYY format"),
):
    """
    Check which dates in the inclusive range [from_date, to_date] have forex rate data available.

    Args:
        from_date: Start date in DD-MM-YYYY format
        to_date: End date in DD-MM-YYYY format

    Returns:
        List of available dates within the specified range

    Raises:
        HTTPException: If database error occurs or input is invalid
    """
    try:
        # Validate date formats
        start_dt = DateValidator.validate_date_format(from_date)
        end_dt = DateValidator.validate_date_format(to_date)

        if end_dt.date() < start_dt.date():
            raise ValueError("`to` date must be the same or after `from` date")

        # Get database session
        db = SessionLocal()

        try:
            available_dates = ForexRateService.check_dates_availability(
                db, start_dt, end_dt
            )

            # Calculate total days in range for message
            total_days = (end_dt.date() - start_dt.date()).days + 1

            return DateAvailabilityResponse(
                success=True,
                data=available_dates,
                message=f"Found data for {len(available_dates)} out of {total_days} dates",
            )

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
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
