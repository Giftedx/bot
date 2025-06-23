"""Database connection and session management."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .base import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str):
        """Initialize database connection.

        Args:
            database_url: Database connection URL
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def get_session(self) -> Generator[Session, None, None]:
        """Get database session.

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def cleanup(self) -> None:
        """Cleanup database connections."""
        try:
            self.engine.dispose()
            logger.info("Database connections cleaned up")
        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up database connections: {e}")
            raise
