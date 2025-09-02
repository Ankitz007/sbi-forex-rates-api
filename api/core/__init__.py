"""Core functionality for the API."""

from .config import settings
from .database import db_manager, get_db

__all__ = ["settings", "db_manager", "get_db"]
