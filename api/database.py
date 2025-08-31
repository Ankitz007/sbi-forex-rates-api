"""
Database utilities for the API.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.config import settings

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
