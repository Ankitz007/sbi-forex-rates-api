"""
Flask application for SBI FX Rates API.

This API provides endpoints to fetch forex rates from the database.
"""

import logging

import psycopg
from flask import Flask, jsonify, request

from api.core import db_manager, settings
from api.schemas import DateAvailabilityResponse, StandardResponse
from api.services import ForexRateService
from api.utils import DateValidator

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Ensure indexes exist (idempotent). This runs on import/startup.
try:
    db_manager.ensure_indexes()
except Exception:
    # Don't fail import if index creation encounters issues in restricted environments
    logger = logging.getLogger(__name__)
    logger.warning(
        "Could not ensure DB indexes on startup. Proceeding without blocking startup."
    )


@app.route("/")
def get_forex_rates():
    """
    Fetch forex rates for a specific date.

    Query Parameters:
        date: Date in DD-MM-YYYY format

    Returns:
        JSON response with forex rates for the specified date

    Raises:
        400: If date format is invalid
        500: If database error occurs
    """
    try:
        # Get date parameter
        date = request.args.get("date")
        if not date:
            return jsonify({"error": "date parameter is required"}), 400

        # Validate date format
        validated_date = DateValidator.validate_date_format(date)

        try:
            forex_rates = ForexRateService.get_rates_by_date(validated_date)

            if not forex_rates:
                response = StandardResponse(
                    success=True,
                    data=[],
                    message=f"No forex rates found for {date}",
                )
                return jsonify(response.to_dict())

            result = [
                ForexRateService.convert_to_response(rate, date) for rate in forex_rates
            ]

            response = StandardResponse(success=True, data=result)
            return jsonify(response.to_dict())

        except psycopg.Error as e:
            logger.error(f"Database error: {e}")
            return jsonify({"error": "Database error occurred"}), 500

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/check-dates")
def check_dates_availability():
    """
    Check which dates in the inclusive range [from_date, to_date] have forex rate data available.

    Query Parameters:
        from: Start date in DD-MM-YYYY format
        to: End date in DD-MM-YYYY format

    Returns:
        JSON response with available dates within the specified range

    Raises:
        400: If input is invalid
        500: If database error occurs
    """
    try:
        # Get query parameters
        from_date = request.args.get("from")
        to_date = request.args.get("to")

        if not from_date:
            return jsonify({"error": "from parameter is required"}), 400
        if not to_date:
            return jsonify({"error": "to parameter is required"}), 400

        # Validate date formats
        start_dt = DateValidator.validate_date_format(from_date)
        end_dt = DateValidator.validate_date_format(to_date)

        if end_dt.date() < start_dt.date():
            return (
                jsonify({"error": "`to` date must be the same or after `from` date"}),
                400,
            )

        try:
            available_dates = ForexRateService.check_dates_availability(
                start_dt, end_dt
            )

            # Calculate total days in range for message
            total_days = (end_dt.date() - start_dt.date()).days + 1

            response = DateAvailabilityResponse(
                success=True,
                data=available_dates,
                message=f"Found data for {len(available_dates)} out of {total_days} dates",
            )

            return jsonify(response.to_dict())

        except psycopg.Error as e:
            logger.error(f"Database error: {e}")
            return jsonify({"error": "Database error occurred"}), 500

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Vercel serverless function handler
def handler(request):
    """Serverless function handler for Vercel."""
    with app.test_request_context(
        request.url, method=request.method, data=request.get_data()
    ):
        return app.full_dispatch_request()


# Used during development
# if __name__ == "__main__":
#     app.run(host=settings.HOST, port=settings.PORT, debug=True)
