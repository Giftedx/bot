from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GEOffer:
    """Represents a Grand Exchange offer."""

    offer_id: int
    player_id: int
    is_buy_offer: bool
    item_id: int
    quantity: int
    price: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_completed: bool = False


class GrandExchangeManager:
    """Manages Grand Exchange offers."""

    def __init__(self):
        self._offers: Dict[int, GEOffer] = {}
        self._next_offer_id = 1

    def place_buy_offer(self, player_id: int, item_id: int, quantity: int, price: int) -> int:
        """Places a buy offer on the Grand Exchange."""
        offer_id = self._next_offer_id
        self._next_offer_id += 1

        offer = GEOffer(
            offer_id=offer_id,
            player_id=player_id,
            is_buy_offer=True,
            item_id=item_id,
            quantity=quantity,
            price=price,
        )

        self._offers[offer_id] = offer
        # In a real implementation, we would have a matching engine here.
        return offer_id

    def place_sell_offer(self, player_id: int, item_id: int, quantity: int, price: int) -> int:
        """Places a sell offer on the Grand Exchange."""
        offer_id = self._next_offer_id
        self._next_offer_id += 1

        offer = GEOffer(
            offer_id=offer_id,
            player_id=player_id,
            is_buy_offer=False,
            item_id=item_id,
            quantity=quantity,
            price=price,
        )

        self._offers[offer_id] = offer
        # In a real implementation, we would have a matching engine here.
        return offer_id

    def get_offers_for_player(self, player_id: int) -> List[GEOffer]:
        """Gets all active offers for a specific player."""
        return [
            offer
            for offer in self._offers.values()
            if offer.player_id == player_id and not offer.is_completed
        ]
