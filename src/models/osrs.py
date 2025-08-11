"""OSRS data models."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base


class OSRSPlayer(Base):
    """OSRS player model."""

    username = Column(String(64), unique=True, nullable=False)
    combat_level = Column(Integer)
    total_level = Column(Integer)
    total_xp = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    stats = Column(JSON)  # Stores all skill levels and XP

    # Relationships
    items = relationship("OSRSItem", secondary="player_items")
    achievements = relationship("OSRSAchievement", back_populates="player")


class OSRSItem(Base):
    """OSRS item model."""

    item_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String(512))
    current_price = Column(Integer)
    high_alch_value = Column(Integer)
    is_members = Column(Integer, default=0)
    examine_text = Column(String(256))

    # Price history stored in separate table for efficiency
    price_history = relationship("OSRSItemPrice", back_populates="item")


class OSRSItemPrice(Base):
    """Historical price data for items."""

    item_id = Column(Integer, ForeignKey("osrsitem.item_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    price = Column(Integer, nullable=False)
    volume = Column(Integer)

    # Relationship
    item = relationship("OSRSItem", back_populates="price_history")


class OSRSAchievement(Base):
    """Player achievements and milestones."""

    player_id = Column(Integer, ForeignKey("osrsplayer.id"), nullable=False)
    achievement_type = Column(String(32), nullable=False)  # quest, diary, combat, etc
    name = Column(String(128), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)  # Additional achievement data

    # Relationship
    player = relationship("OSRSPlayer", back_populates="achievements")


# Association table for player items
player_items = Base.metadata.tables.get("player_items") or Table(
    "player_items",
    Base.metadata,
    Column("player_id", Integer, ForeignKey("osrsplayer.id"), primary_key=True),
    Column("item_id", Integer, ForeignKey("osrsitem.item_id"), primary_key=True),
    Column("quantity", Integer, default=1),
    Column("obtained_at", DateTime, default=datetime.utcnow),
)
