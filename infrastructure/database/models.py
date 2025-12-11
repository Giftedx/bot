from datetime import datetime
from typing import Dict, List, Optional, Set
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Float, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Association tables
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

class User(Base):
    """User account model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    avatar_url = Column(String)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    roles = relationship('Role', secondary=user_roles, back_populates='users')
    player_state = relationship('PlayerState', back_populates='user', uselist=False)
    discord_profile = relationship('DiscordProfile', back_populates='user', uselist=False)
    api_keys = relationship('APIKey', back_populates='user')

class Role(Base):
    """User role model"""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    permissions = Column(JSON)
    
    # Relationships
    users = relationship('User', secondary=user_roles, back_populates='roles')

class PlayerState(Base):
    """Game state model"""
    __tablename__ = 'player_states'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    last_action = Column(DateTime)
    
    # Game state
    combat_stats = Column(JSON)  # Dictionary of combat stats
    equipment = Column(JSON)  # Dictionary of equipped items
    skills = Column(JSON)  # Dictionary of skill levels
    experience = Column(JSON)  # Dictionary of skill experience
    inventory = Column(JSON)  # Dictionary of inventory items
    bank = Column(JSON)  # Dictionary of banked items
    
    # Location
    location = Column(String, default='Lumbridge')
    previous_location = Column(String)
    
    # Status
    is_busy = Column(Boolean, default=False)
    current_action = Column(String)
    prayer_points = Column(Integer, default=1)
    run_energy = Column(Float, default=100.0)
    hitpoints = Column(Integer, default=10)
    
    # Progress tracking
    quest_progress = Column(JSON)  # Dictionary of quest states
    achievement_progress = Column(JSON)  # Dictionary of achievement progress
    minigame_scores = Column(JSON)  # Dictionary of minigame scores
    
    # Relationships
    user = relationship('User', back_populates='player_state')

class DiscordProfile(Base):
    """Discord integration model"""
    __tablename__ = 'discord_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    discord_id = Column(String, unique=True)
    username = Column(String)
    discriminator = Column(String)
    avatar_url = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    token_expires_at = Column(DateTime)
    
    # Relationships
    user = relationship('User', back_populates='discord_profile')

class APIKey(Base):
    """API key model"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    key = Column(String, unique=True, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', back_populates='api_keys')

class AuditLog(Base):
    """Audit log model"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String, nullable=False)
    details = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)

class SecurityEvent(Base):
    """Security event model"""
    __tablename__ = 'security_events'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now())
    event_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    ip_address = Column(String)
    details = Column(JSON)
    severity = Column(String)  # 'low', 'medium', 'high', 'critical'

class SystemMetric(Base):
    """System metrics model"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now())
    service = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float)
    labels = Column(JSON)  # Additional metric labels/tags 