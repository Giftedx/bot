"""Base database models and utilities."""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declared_attr

class CustomBase:
    """Custom base class for all models."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomBase':
        """Create model instance from dictionary."""
        return cls(**{
            k: v for k, v in data.items() 
            if k in cls.__table__.columns
        })

Base = declarative_base(cls=CustomBase)

class User(Base):
    """User model for Discord users."""
    
    discord_id = Column(String(32), unique=True, nullable=False)
    username = Column(String(128), nullable=False)
    discriminator = Column(String(4))
    
    def __repr__(self) -> str:
        return f"<User {self.username}#{self.discriminator}>" 