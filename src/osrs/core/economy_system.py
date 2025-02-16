"""OSRS economy system implementation."""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import random

from ..models.user import User
from ..models.item import Item

logger = logging.getLogger(__name__)

class EconomySystem:
    """Manages the game economy and trading."""
    
    def __init__(self, bot):
        """Initialize economy system."""
        self.bot = bot
        self.active_trades: Dict[int, Dict] = {}  # trade_id -> trade_data
        self.trade_counter = 0

    async def initialize(self):
        """Initialize economy system."""
        # Load active trades from database
        async with self.bot.db.pool.acquire() as conn:
            active_trades = await conn.fetch(
                """
                SELECT * FROM osrs_ge_orders
                WHERE status = 'active'
                """
            )
            for trade in active_trades:
                self.active_trades[trade['id']] = dict(trade)

    async def create_trade(
        self,
        seller_id: int,
        buyer_id: int,
        items: List[Tuple[str, int]]  # List of (item_id, quantity)
    ) -> Optional[int]:
        """Create a new trade."""
        try:
            # Generate trade ID
            self.trade_counter += 1
            trade_id = self.trade_counter

            # Verify items are in seller's inventory
            seller = self.bot.get_player(seller_id)
            if not seller:
                return None

            for item_id, quantity in items:
                if not seller.bank.has(item_id, quantity):
                    return None

            # Initialize trade data
            trade_data = {
                'id': trade_id,
                'seller_id': seller_id,
                'buyer_id': buyer_id,
                'items': items,
                'status': 'pending',
                'created_at': datetime.utcnow()
            }

            # Save to database
            async with self.bot.db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO osrs_ge_orders (
                        id, user_id, item_id, quantity,
                        price_each, type, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    trade_id, seller_id, items[0][0], items[0][1],
                    0, 'trade', 'pending'
                )

            self.active_trades[trade_id] = trade_data
            return trade_id

        except Exception as e:
            logger.error(f"Error creating trade: {e}")
            return None

    async def accept_trade(self, trade_id: int) -> bool:
        """Accept a trade."""
        trade = self.active_trades.get(trade_id)
        if not trade or trade['status'] != 'pending':
            return False

        try:
            seller = self.bot.get_player(trade['seller_id'])
            buyer = self.bot.get_player(trade['buyer_id'])
            if not seller or not buyer:
                return False

            # Transfer items
            async with self.bot.db.pool.acquire() as conn:
                async with conn.transaction():
                    for item_id, quantity in trade['items']:
                        # Remove from seller
                        if not seller.bank.remove(item_id, quantity):
                            return False
                        
                        # Add to buyer
                        buyer.bank.add(item_id, quantity)

                    # Update trade status
                    await conn.execute(
                        """
                        UPDATE osrs_ge_orders
                        SET status = 'completed',
                            completed_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        """,
                        trade_id
                    )

                    # Record transaction
                    await conn.execute(
                        """
                        INSERT INTO osrs_ge_history (
                            item_id, quantity, price,
                            buyer_id, seller_id
                        ) VALUES ($1, $2, $3, $4, $5)
                        """,
                        trade['items'][0][0],
                        trade['items'][0][1],
                        0,  # No price for direct trades
                        buyer.id,
                        seller.id
                    )

            trade['status'] = 'completed'
            trade['completed_at'] = datetime.utcnow()
            return True

        except Exception as e:
            logger.error(f"Error accepting trade: {e}")
            return False

    async def cancel_trade(self, trade_id: int) -> bool:
        """Cancel a trade."""
        trade = self.active_trades.get(trade_id)
        if not trade or trade['status'] != 'pending':
            return False

        try:
            async with self.bot.db.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE osrs_ge_orders
                    SET status = 'cancelled'
                    WHERE id = $1
                    """,
                    trade_id
                )

            trade['status'] = 'cancelled'
            return True

        except Exception as e:
            logger.error(f"Error cancelling trade: {e}")
            return False

    async def create_buy_offer(
        self,
        buyer_id: int,
        item_id: str,
        quantity: int,
        price_per_item: int
    ) -> Optional[int]:
        """Create a buy offer on the Grand Exchange."""
        try:
            # Verify buyer has enough gold
            buyer = self.bot.get_player(buyer_id)
            if not buyer:
                return None

            total_cost = quantity * price_per_item
            if buyer.GP < total_cost:
                return None

            # Create offer
            async with self.bot.db.pool.acquire() as conn:
                offer_id = await conn.fetchval(
                    """
                    INSERT INTO osrs_ge_orders (
                        user_id, item_id, quantity,
                        price_each, type, status
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    buyer_id, item_id, quantity,
                    price_per_item, 'buy', 'active'
                )

                # Reserve gold
                buyer.GP -= total_cost
                await self.bot.db.update_player(buyer)

                return offer_id

        except Exception as e:
            logger.error(f"Error creating buy offer: {e}")
            return None

    async def create_sell_offer(
        self,
        seller_id: int,
        item_id: str,
        quantity: int,
        price_per_item: int
    ) -> Optional[int]:
        """Create a sell offer on the Grand Exchange."""
        try:
            # Verify seller has items
            seller = self.bot.get_player(seller_id)
            if not seller or not seller.bank.has(item_id, quantity):
                return None

            # Create offer
            async with self.bot.db.pool.acquire() as conn:
                offer_id = await conn.fetchval(
                    """
                    INSERT INTO osrs_ge_orders (
                        user_id, item_id, quantity,
                        price_each, type, status
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    seller_id, item_id, quantity,
                    price_per_item, 'sell', 'active'
                )

                # Reserve items
                seller.bank.remove(item_id, quantity)
                await self.bot.db.update_player(seller)

                return offer_id

        except Exception as e:
            logger.error(f"Error creating sell offer: {e}")
            return None

    async def process_offers(self):
        """Process active Grand Exchange offers."""
        try:
            async with self.bot.db.pool.acquire() as conn:
                # Get active offers
                buy_offers = await conn.fetch(
                    """
                    SELECT * FROM osrs_ge_orders
                    WHERE type = 'buy' AND status = 'active'
                    ORDER BY price_each DESC, created_at ASC
                    """
                )

                sell_offers = await conn.fetch(
                    """
                    SELECT * FROM osrs_ge_orders
                    WHERE type = 'sell' AND status = 'active'
                    ORDER BY price_each ASC, created_at ASC
                    """
                )

                # Match offers
                for buy_offer in buy_offers:
                    for sell_offer in sell_offers:
                        if (sell_offer['item_id'] == buy_offer['item_id'] and
                            sell_offer['price_each'] <= buy_offer['price_each']):
                            
                            # Calculate trade quantity
                            quantity = min(
                                buy_offer['quantity'] - buy_offer['quantity_filled'],
                                sell_offer['quantity'] - sell_offer['quantity_filled']
                            )

                            if quantity > 0:
                                # Execute trade
                                price = sell_offer['price_each']
                                total_price = quantity * price

                                # Update offers
                                await conn.execute(
                                    """
                                    UPDATE osrs_ge_orders
                                    SET quantity_filled = quantity_filled + $1,
                                        status = CASE 
                                            WHEN quantity_filled + $1 >= quantity 
                                            THEN 'completed' 
                                            ELSE status 
                                        END
                                    WHERE id = $2
                                    """,
                                    quantity, buy_offer['id']
                                )

                                await conn.execute(
                                    """
                                    UPDATE osrs_ge_orders
                                    SET quantity_filled = quantity_filled + $1,
                                        status = CASE 
                                            WHEN quantity_filled + $1 >= quantity 
                                            THEN 'completed' 
                                            ELSE status 
                                        END
                                    WHERE id = $2
                                    """,
                                    quantity, sell_offer['id']
                                )

                                # Record transaction
                                await conn.execute(
                                    """
                                    INSERT INTO osrs_ge_history (
                                        item_id, quantity, price,
                                        buyer_id, seller_id
                                    ) VALUES ($1, $2, $3, $4, $5)
                                    """,
                                    buy_offer['item_id'],
                                    quantity,
                                    price,
                                    buy_offer['user_id'],
                                    sell_offer['user_id']
                                )

                                # Transfer items and gold
                                buyer = self.bot.get_player(buy_offer['user_id'])
                                seller = self.bot.get_player(sell_offer['user_id'])

                                if buyer and seller:
                                    buyer.bank.add(buy_offer['item_id'], quantity)
                                    seller.GP += total_price

                                    await self.bot.db.update_player(buyer)
                                    await self.bot.db.update_player(seller)

        except Exception as e:
            logger.error(f"Error processing offers: {e}")

    async def get_price_history(
        self,
        item_id: str,
        days: int = 30
    ) -> List[Dict]:
        """Get price history for an item."""
        async with self.bot.db.pool.acquire() as conn:
            history = await conn.fetch(
                """
                SELECT 
                    DATE_TRUNC('day', timestamp) as date,
                    AVG(price) as avg_price,
                    SUM(quantity) as volume
                FROM osrs_ge_history
                WHERE item_id = $1
                  AND timestamp > CURRENT_TIMESTAMP - INTERVAL '$2 days'
                GROUP BY DATE_TRUNC('day', timestamp)
                ORDER BY date DESC
                """,
                item_id, days
            )
            return [dict(record) for record in history]

    async def get_player_trades(
        self,
        player_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """Get player's recent trades."""
        async with self.bot.db.pool.acquire() as conn:
            trades = await conn.fetch(
                """
                SELECT *
                FROM osrs_ge_history
                WHERE buyer_id = $1 OR seller_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                player_id, limit
            )
            return [dict(trade) for trade in trades]

    async def get_active_offers(
        self,
        player_id: int
    ) -> Dict[str, List[Dict]]:
        """Get player's active offers."""
        async with self.bot.db.pool.acquire() as conn:
            buy_offers = await conn.fetch(
                """
                SELECT *
                FROM osrs_ge_orders
                WHERE user_id = $1 AND type = 'buy' AND status = 'active'
                ORDER BY created_at DESC
                """,
                player_id
            )

            sell_offers = await conn.fetch(
                """
                SELECT *
                FROM osrs_ge_orders
                WHERE user_id = $1 AND type = 'sell' AND status = 'active'
                ORDER BY created_at DESC
                """,
                player_id
            )

            return {
                'buy': [dict(offer) for offer in buy_offers],
                'sell': [dict(offer) for offer in sell_offers]
            }

    async def cancel_offer(self, offer_id: int) -> bool:
        """Cancel a Grand Exchange offer."""
        try:
            async with self.bot.db.pool.acquire() as conn:
                offer = await conn.fetchrow(
                    "SELECT * FROM osrs_ge_orders WHERE id = $1",
                    offer_id
                )

                if not offer or offer['status'] != 'active':
                    return False

                # Return items/gold
                player = self.bot.get_player(offer['user_id'])
                if player:
                    if offer['type'] == 'buy':
                        remaining_quantity = offer['quantity'] - offer['quantity_filled']
                        refund = remaining_quantity * offer['price_each']
                        player.GP += refund
                    else:  # sell
                        remaining_quantity = offer['quantity'] - offer['quantity_filled']
                        player.bank.add(offer['item_id'], remaining_quantity)

                    await self.bot.db.update_player(player)

                # Update offer status
                await conn.execute(
                    """
                    UPDATE osrs_ge_orders
                    SET status = 'cancelled'
                    WHERE id = $1
                    """,
                    offer_id
                )

                return True

        except Exception as e:
            logger.error(f"Error cancelling offer: {e}")
            return False 