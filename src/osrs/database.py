from typing import Dict, List, Optional, Union
import asyncpg
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class OSRSDatabase:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_character(self, user_id: int) -> Optional[Dict]:
        """Get a character's data"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM osrs_characters WHERE user_id = $1",
                user_id
            )

    async def create_character(self, user_id: int, name: str, stats: Dict) -> bool:
        """Create a new character"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_characters (user_id, name, stats)
                       VALUES ($1, $2, $3)""",
                    user_id, name, json.dumps(stats)
                )
                return True
        except asyncpg.UniqueViolationError:
            return False
        except Exception as e:
            logger.error(f"Error creating character: {e}")
            return False

    async def update_stats(self, user_id: int, stats: Dict) -> bool:
        """Update a character's stats"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE osrs_characters 
                       SET stats = $1, last_trained = NOW()
                       WHERE user_id = $2""",
                    json.dumps(stats), user_id
                )
                return True
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
            return False

    async def record_training_session(
        self, 
        user_id: int, 
        skill: str, 
        start_time: datetime,
        start_level: int,
        end_level: int = None,
        xp_gained: int = None
    ) -> int:
        """Record a training session"""
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(
                    """INSERT INTO osrs_training_sessions 
                       (user_id, skill, start_time, start_level, end_level, xp_gained)
                       VALUES ($1, $2, $3, $4, $5, $6)
                       RETURNING id""",
                    user_id, skill, start_time, start_level, end_level, xp_gained
                )
        except Exception as e:
            logger.error(f"Error recording training session: {e}")
            return None

    async def complete_training_session(
        self, 
        session_id: int,
        end_level: int,
        xp_gained: int
    ) -> bool:
        """Complete a training session"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE osrs_training_sessions 
                       SET end_level = $1, xp_gained = $2, end_time = NOW()
                       WHERE id = $3""",
                    end_level, xp_gained, session_id
                )
                return True
        except Exception as e:
            logger.error(f"Error completing training session: {e}")
            return False

    async def record_transaction(
        self,
        user_id: int,
        item_id: int,
        quantity: int,
        price_per_item: int,
        transaction_type: str
    ) -> int:
        """Record an item transaction"""
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(
                    """INSERT INTO osrs_transactions 
                       (user_id, item_id, quantity, price_per_item, total_price, transaction_type)
                       VALUES ($1, $2, $3, $4, $5, $6)
                       RETURNING id""",
                    user_id, item_id, quantity, price_per_item, 
                    quantity * price_per_item, transaction_type
                )
        except Exception as e:
            logger.error(f"Error recording transaction: {e}")
            return None

    async def update_inventory(self, user_id: int, inventory: List[Dict]) -> bool:
        """Update a character's inventory"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE osrs_characters 
                       SET inventory = $1
                       WHERE user_id = $2""",
                    json.dumps(inventory), user_id
                )
                return True
        except Exception as e:
            logger.error(f"Error updating inventory: {e}")
            return False

    async def update_equipment(self, user_id: int, equipment: Dict) -> bool:
        """Update a character's equipment"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE osrs_characters 
                       SET equipment = $1
                       WHERE user_id = $2""",
                    json.dumps(equipment), user_id
                )
                return True
        except Exception as e:
            logger.error(f"Error updating equipment: {e}")
            return False

    async def update_bank(self, user_id: int, bank: Dict) -> bool:
        """Update a character's bank"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE osrs_characters 
                       SET bank = $1
                       WHERE user_id = $2""",
                    json.dumps(bank), user_id
                )
                return True
        except Exception as e:
            logger.error(f"Error updating bank: {e}")
            return False

    async def get_quest_progress(self, user_id: int) -> List[Dict]:
        """Get a character's quest progress"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM osrs_quest_completions WHERE user_id = $1",
                user_id
            )

    async def update_quest_status(
        self,
        user_id: int,
        quest_name: str,
        status: str,
        completed_at: datetime = None
    ) -> bool:
        """Update a quest's status"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_quest_completions 
                       (user_id, quest_name, status, completed_at)
                       VALUES ($1, $2, $3, $4)
                       ON CONFLICT (user_id, quest_name)
                       DO UPDATE SET status = $3, completed_at = $4""",
                    user_id, quest_name, status, completed_at
                )
                return True
        except Exception as e:
            logger.error(f"Error updating quest status: {e}")
            return False

    async def get_achievement_diary_progress(self, user_id: int) -> List[Dict]:
        """Get a character's achievement diary progress"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM osrs_achievement_diary_tasks WHERE user_id = $1",
                user_id
            )

    async def complete_achievement_task(
        self,
        user_id: int,
        diary_name: str,
        task_name: str,
        difficulty: str
    ) -> bool:
        """Mark an achievement diary task as completed"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_achievement_diary_tasks 
                       (user_id, diary_name, task_name, difficulty, completed, completed_at)
                       VALUES ($1, $2, $3, $4, true, NOW())
                       ON CONFLICT (user_id, diary_name, task_name)
                       DO UPDATE SET completed = true, completed_at = NOW()""",
                    user_id, diary_name, task_name, difficulty
                )
                return True
        except Exception as e:
            logger.error(f"Error completing achievement task: {e}")
            return False

    async def get_top_players(self, skill: str = None, limit: int = 10) -> List[Dict]:
        """Get top players by total XP or specific skill"""
        async with self.pool.acquire() as conn:
            if skill:
                return await conn.fetch(
                    """SELECT user_id, name, stats->$1 as level, total_xp
                       FROM osrs_characters
                       ORDER BY (stats->$1)::int DESC
                       LIMIT $2""",
                    skill, limit
                )
            else:
                return await conn.fetch(
                    """SELECT user_id, name, combat_level, total_xp
                       FROM osrs_characters
                       ORDER BY total_xp DESC
                       LIMIT $1""",
                    limit
                )

    async def get_recent_achievements(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent achievements (quests and diary tasks)"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """SELECT 'quest' as type, quest_name as name, completed_at
                   FROM osrs_quest_completions
                   WHERE user_id = $1 AND status = 'completed'
                   UNION ALL
                   SELECT 'diary' as type, 
                          diary_name || ' - ' || task_name as name,
                          completed_at
                   FROM osrs_achievement_diary_tasks
                   WHERE user_id = $1 AND completed = true
                   ORDER BY completed_at DESC
                   LIMIT $2""",
                user_id, limit
            )

    async def get_recent_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent item transactions"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """SELECT * FROM osrs_transactions
                   WHERE user_id = $1
                   ORDER BY created_at DESC
                   LIMIT $2""",
                user_id, limit
            ) 