from typing import Dict, Optional, List
from datetime import datetime

from src.core.models.trade import TradeOffer, TradeStatus

class TradeManager:
    """Manages all active trade sessions."""
    
    def __init__(self):
        self._trades: Dict[int, TradeOffer] = {}
        self._next_trade_id = 1

    def create_trade(self, sender_id: int, receiver_id: int, item_name: str, item_quantity: int) -> TradeOffer:
        """Creates a new trade offer."""
        trade_id = self._next_trade_id
        self._next_trade_id += 1
        
        offer = TradeOffer(
            id=trade_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            item_name=item_name,
            item_quantity=item_quantity
        )
        
        self._trades[trade_id] = offer
        return offer

    def get_trade(self, trade_id: int) -> Optional[TradeOffer]:
        """Gets a trade by its ID."""
        return self._trades.get(trade_id)

    def get_player_trades(self, player_id: int) -> List[TradeOffer]:
        """Gets all trades involving a specific player."""
        return [t for t in self._trades.values() if player_id in (t.sender_id, t.receiver_id)]

    def _update_trade_status(self, trade_id: int, new_status: TradeStatus) -> Optional[TradeOffer]:
        """Internal helper to update a trade's status."""
        trade = self.get_trade(trade_id)
        if trade:
            # Check for expired trades
            if trade.status != TradeStatus.PENDING or (trade.expires_at and datetime.now() > trade.expires_at):
                trade.status = TradeStatus.EXPIRED
                # We can remove it from active trades later with a cleanup task
                return None
            
            trade.status = new_status
            return trade
        return None

    def accept_trade(self, trade_id: int) -> Optional[TradeOffer]:
        """Accepts a trade offer."""
        return self._update_trade_status(trade_id, TradeStatus.COMPLETED)

    def decline_trade(self, trade_id: int) -> Optional[TradeOffer]:
        """Declines a trade offer."""
        return self._update_trade_status(trade_id, TradeStatus.DECLINED)

    def cancel_trade(self, trade_id: int, requester_id: int) -> Optional[TradeOffer]:
        """Cancels a trade offer, only if requested by the sender."""
        trade = self.get_trade(trade_id)
        if trade and trade.sender_id == requester_id:
            return self._update_trade_status(trade_id, TradeStatus.CANCELLED)
        return None 