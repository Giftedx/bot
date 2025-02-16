"""OSRS database package."""
from .models import Database
from .osrs_database import OSRSDatabase

# Create global database instance
db = Database()

__all__ = ['db', 'Database', 'OSRSDatabase']
