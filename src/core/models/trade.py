from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class TradeStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class TradeOffer:
    id: int
    sender_id: int
    receiver_id: int
    item_name: str
    item_quantity: int
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: TradeStatus = TradeStatus.PENDING

    def __post_init__(self) -> None:
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(minutes=30)