"""
Configuration settings for the API.
"""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


class Settings:
    """Application settings."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://myuser:mypassword@localhost:5432/mydb"
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API
    API_TITLE: str = "SBI FX Rates API"
    API_DESCRIPTION: str = "API to fetch forex rates from SBI for specific dates"
    API_VERSION: str = "1.0.0"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


# Create settings instance
settings = Settings()
