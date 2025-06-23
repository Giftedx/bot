from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

class TradeStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class TradeOffer:
    """Represents a trade offer between players."""
    id: int
    sender_id: int
    receiver_id: int
    item_name: str # Using name for simplicity, like in Player.add_item_to_inventory
    item_quantity: int
    status: TradeStatus = TradeStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=5)) 