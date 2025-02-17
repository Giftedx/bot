from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql import text
from contextlib import contextmanager
import logging
from datetime import datetime

from shared.utils.service_interface import BaseService
from .models import Base

T = TypeVar('T', bound=DeclarativeMeta)

class DatabaseService(BaseService):
    """Service for managing database operations"""
    
    def __init__(self, 
                 db_config: Dict[str, str],
                 pool_size: int = 5,
                 max_overflow: int = 10,
                 pool_timeout: int = 30):
        super().__init__("database", "1.0.0")
        self.db_config = db_config
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.engine = None
        self.Session = None
        self.logger = logging.getLogger(__name__)
    
    async def _init_dependencies(self) -> None:
        """Initialize database connection"""
        connection_url = (
            f"postgresql://{self.db_config['user']}:{self.db_config['password']}"
            f"@{self.db_config['host']}:{self.db_config['port']}"
            f"/{self.db_config['database']}"
        )
        
        self.engine = create_engine(
            connection_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout
        )
        
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        self.update_metric("pool_size", self.pool_size)
        self.update_metric("max_overflow", self.max_overflow)
    
    async def _start_service(self) -> None:
        """Start the database service"""
        # Test connection
        try:
            with self.Session() as session:
                session.execute(text("SELECT 1"))
            self.logger.info("Database connection established")
        except Exception as e:
            self.record_error("connection", str(e))
            raise
    
    async def _stop_service(self) -> None:
        """Stop the database service"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("Database connections closed")
    
    async def _cleanup_resources(self) -> None:
        """Cleanup database resources"""
        pass
    
    @contextmanager
    def get_session(self) -> Session:
        """Get a database session"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create(self, model: T) -> T:
        """Create a new database record"""
        with self.get_session() as session:
            session.add(model)
            session.flush()
            session.refresh(model)
            return model
    
    def get_by_id(self, model_class: Type[T], id: int) -> Optional[T]:
        """Get a record by ID"""
        with self.get_session() as session:
            return session.query(model_class).get(id)
    
    def get_all(self, model_class: Type[T], 
                filters: Optional[Dict[str, Any]] = None,
                order_by: Optional[str] = None,
                limit: Optional[int] = None,
                offset: Optional[int] = None) -> List[T]:
        """Get all records of a model with optional filtering"""
        with self.get_session() as session:
            query = session.query(model_class)
            
            if filters:
                for key, value in filters.items():
                    query = query.filter(getattr(model_class, key) == value)
            
            if order_by:
                query = query.order_by(order_by)
            
            if limit is not None:
                query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)
                
            return query.all()
    
    def update(self, model: T, data: Dict[str, Any]) -> T:
        """Update a database record"""
        with self.get_session() as session:
            for key, value in data.items():
                setattr(model, key, value)
            session.merge(model)
            session.flush()
            session.refresh(model)
            return model
    
    def delete(self, model: T) -> None:
        """Delete a database record"""
        with self.get_session() as session:
            session.delete(model)
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query"""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return [dict(row) for row in result]
    
    def bulk_create(self, models: List[T]) -> List[T]:
        """Bulk create records"""
        with self.get_session() as session:
            session.bulk_save_objects(models)
            session.flush()
            return models
    
    def bulk_update(self, model_class: Type[T], ids: List[int], data: Dict[str, Any]) -> int:
        """Bulk update records"""
        with self.get_session() as session:
            result = session.query(model_class)\
                .filter(model_class.id.in_(ids))\
                .update(data, synchronize_session=False)
            return result
    
    def bulk_delete(self, model_class: Type[T], ids: List[int]) -> int:
        """Bulk delete records"""
        with self.get_session() as session:
            result = session.query(model_class)\
                .filter(model_class.id.in_(ids))\
                .delete(synchronize_session=False)
            return result 