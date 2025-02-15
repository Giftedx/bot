"""OSRS database package."""
from .models import Database

# Create global database instance
db = Database()

__all__ = ['db', 'Database']
