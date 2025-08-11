from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TradeStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class TradeOffer:
    trade_id: int
    sender_id: int
    receiver_id: int
    item_name: str
    quantity: int
    status: TradeStatus = TradeStatus.PENDING
    notes: Optional[str] = None