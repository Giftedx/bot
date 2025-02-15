from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)  # Discord user ID
    pets = relationship("Pet", back_populates="owner")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

class Pet(Base):
    __tablename__ = 'pets'
    
    id = Column(String, primary_key=True)  # UUID
    owner_id = Column(String, ForeignKey('users.id'))
    owner = relationship("User", back_populates="pets")
    
    # Base pet attributes
    name = Column(String, nullable=False)
    pet_type = Column(String, nullable=False)  # 'osrs' or 'pokemon'
    creation_date = Column(DateTime, default=datetime.utcnow)
    experience = Column(Integer, default=0)
    level = Column(Integer, default=1)
    happiness = Column(Integer, default=100)
    rarity = Column(String, default="common")
    
    # Type-specific attributes stored as JSON
    attributes = Column(JSON)

class CrossSystemBoost(Base):
    __tablename__ = 'cross_system_boosts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    source_type = Column(String, nullable=False)  # Which pet type provides the boost
    target_type = Column(String, nullable=False)  # Which pet type receives the boost
    boost_value = Column(Float, default=0.0)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration for temporary boosts

class PetAchievement(Base):
    __tablename__ = 'pet_achievements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    description = Column(String)
    achieved_at = Column(DateTime, default=datetime.utcnow)
    requirements = Column(JSON)  # Store achievement requirements
    rewards = Column(JSON)  # Store achievement rewards

def init_db(database_url: str):
    """Initialize the database with all tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine 