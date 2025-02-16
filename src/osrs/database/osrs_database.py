"""PostgreSQL database implementation for OSRS."""
from typing import Dict, List, Optional, Union
import asyncpg
from datetime import datetime
import json
import logging
from pathlib import Path

from ..data import (
    get_item_data,
    get_quest_data,
    get_skill_data,
    get_equipment_data,
    get_monster_data,
    get_achievement_data,
    get_item_price
)

logger = logging.getLogger(__name__)


class OSRSDatabase:
    """PostgreSQL database manager for OSRS data."""
    
    def __init__(self, pool: asyncpg.Pool):
        """Initialize with connection pool."""
        self.pool = pool

    async def initialize_tables(self):
        """Initialize database tables."""
        async with self.pool.acquire() as conn:
            # Create tables
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_characters (
                    user_id BIGINT PRIMARY KEY,
                    name TEXT NOT NULL,
                    stats JSONB NOT NULL DEFAULT '{}',
                    inventory JSONB NOT NULL DEFAULT '[]',
                    equipment JSONB NOT NULL DEFAULT '{}',
                    bank JSONB NOT NULL DEFAULT '{}',
                    quest_points INTEGER NOT NULL DEFAULT 0,
                    combat_level INTEGER NOT NULL DEFAULT 3,
                    total_level INTEGER NOT NULL DEFAULT 32,
                    total_xp BIGINT NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    last_login TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_quest_completions (
                    user_id BIGINT NOT NULL,
                    quest_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'not_started',
                    completed_at TIMESTAMP,
                    PRIMARY KEY (user_id, quest_name),
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_achievement_diary_tasks (
                    user_id BIGINT NOT NULL,
                    diary_name TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    completed BOOLEAN NOT NULL DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    PRIMARY KEY (user_id, diary_name, task_name),
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_training_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    skill TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    start_level INTEGER NOT NULL,
                    end_level INTEGER,
                    xp_gained INTEGER,
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_transactions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    item_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price_per_item INTEGER NOT NULL,
                    total_price INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_combat_stats (
                    user_id BIGINT NOT NULL,
                    kills INTEGER NOT NULL DEFAULT 0,
                    deaths INTEGER NOT NULL DEFAULT 0,
                    damage_dealt BIGINT NOT NULL DEFAULT 0,
                    damage_taken BIGINT NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_id),
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_pets (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    name TEXT NOT NULL,
                    pet_type TEXT NOT NULL,
                    creation_date TIMESTAMP NOT NULL DEFAULT NOW(),
                    experience INTEGER NOT NULL DEFAULT 0,
                    level INTEGER NOT NULL DEFAULT 1,
                    happiness INTEGER NOT NULL DEFAULT 100,
                    rarity TEXT NOT NULL DEFAULT 'common',
                    attributes JSONB NOT NULL DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_pet_achievements (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    achieved_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    requirements JSONB NOT NULL DEFAULT '{}',
                    rewards JSONB NOT NULL DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_cross_system_boosts (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    source_type TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    boost_value FLOAT NOT NULL DEFAULT 0.0,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_minigame_scores (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    minigame TEXT NOT NULL,
                    score INTEGER NOT NULL DEFAULT 0,
                    high_score INTEGER NOT NULL DEFAULT 0,
                    last_played TIMESTAMP NOT NULL DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE,
                    UNIQUE (user_id, minigame)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_collection_log (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    category TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    obtained_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    count INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE,
                    UNIQUE (user_id, category, item_id)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_player_titles (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    title TEXT NOT NULL,
                    unlocked_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    active BOOLEAN NOT NULL DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE,
                    UNIQUE (user_id, title)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_player_relationships (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    related_user_id BIGINT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (related_user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE,
                    UNIQUE (user_id, related_user_id, relationship_type)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osrs_player_statistics (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    statistic_type TEXT NOT NULL,
                    value BIGINT NOT NULL DEFAULT 0,
                    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES osrs_characters(user_id)
                        ON DELETE CASCADE,
                    UNIQUE (user_id, statistic_type)
                )
            """)

    async def get_character(self, user_id: int) -> Optional[Dict]:
        """Get a character's data."""
        async with self.pool.acquire() as conn:
            char_data = await conn.fetchrow(
                "SELECT * FROM osrs_characters WHERE user_id = $1",
                user_id
            )
            
            if not char_data:
                return None
                
            # Get quest completions
            quests = await conn.fetch(
                "SELECT quest_name, status, completed_at FROM osrs_quest_completions WHERE user_id = $1",
                user_id
            )
            
            # Get achievement diary progress
            achievements = await conn.fetch(
                """SELECT diary_name, task_name, difficulty, completed, completed_at 
                   FROM osrs_achievement_diary_tasks WHERE user_id = $1""",
                user_id
            )
            
            # Get combat stats
            combat_stats = await conn.fetchrow(
                "SELECT * FROM osrs_combat_stats WHERE user_id = $1",
                user_id
            )
            
            return {
                **dict(char_data),
                'quests': [dict(q) for q in quests],
                'achievements': [dict(a) for a in achievements],
                'combat_stats': dict(combat_stats) if combat_stats else None
            }

    async def create_character(self, user_id: int, name: str) -> bool:
        """Create a new character with default stats."""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Create character
                    await conn.execute(
                        """INSERT INTO osrs_characters (user_id, name, stats)
                           VALUES ($1, $2, $3)""",
                        user_id, name, json.dumps({
                            'attack': {'level': 1, 'xp': 0},
                            'strength': {'level': 1, 'xp': 0},
                            'defence': {'level': 1, 'xp': 0},
                            'hitpoints': {'level': 10, 'xp': 1154},
                            'prayer': {'level': 1, 'xp': 0},
                            'magic': {'level': 1, 'xp': 0},
                            'ranged': {'level': 1, 'xp': 0},
                            'mining': {'level': 1, 'xp': 0},
                            'smithing': {'level': 1, 'xp': 0},
                            'fishing': {'level': 1, 'xp': 0},
                            'cooking': {'level': 1, 'xp': 0},
                            'woodcutting': {'level': 1, 'xp': 0},
                            'firemaking': {'level': 1, 'xp': 0},
                            'crafting': {'level': 1, 'xp': 0},
                            'fletching': {'level': 1, 'xp': 0},
                            'agility': {'level': 1, 'xp': 0},
                            'herblore': {'level': 1, 'xp': 0},
                            'thieving': {'level': 1, 'xp': 0},
                            'runecraft': {'level': 1, 'xp': 0},
                            'slayer': {'level': 1, 'xp': 0},
                            'farming': {'level': 1, 'xp': 0},
                            'construction': {'level': 1, 'xp': 0},
                            'hunter': {'level': 1, 'xp': 0}
                        })
                    )
                    
                    # Initialize combat stats
                    await conn.execute(
                        "INSERT INTO osrs_combat_stats (user_id) VALUES ($1)",
                        user_id
                    )
                    
                    return True
        except asyncpg.UniqueViolationError:
            return False
        except Exception as e:
            logger.error(f"Error creating character: {e}")
            return False

    async def update_stats(self, user_id: int, stats: Dict) -> bool:
        """Update a character's stats."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE osrs_characters 
                       SET stats = $1, 
                           total_level = $2,
                           total_xp = $3,
                           combat_level = $4,
                           last_login = NOW()
                       WHERE user_id = $5""",
                    json.dumps(stats),
                    sum(s['level'] for s in stats.values()),
                    sum(s['xp'] for s in stats.values()),
                    self._calculate_combat_level(stats),
                    user_id
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
        """Record a training session."""
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
        """Complete a training session."""
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
        """Record an item transaction."""
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
        """Update a character's inventory."""
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
        """Update a character's equipment."""
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
        """Update a character's bank."""
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
        """Get a character's quest progress."""
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
        """Update a quest's status."""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """INSERT INTO osrs_quest_completions 
                           (user_id, quest_name, status, completed_at)
                           VALUES ($1, $2, $3, $4)
                           ON CONFLICT (user_id, quest_name)
                           DO UPDATE SET status = $3, completed_at = $4""",
                        user_id, quest_name, status, completed_at
                    )
                    
                    if status == 'completed':
                        # Update quest points
                        quest_data = get_quest_data(quest_name)
                        if quest_data:
                            await conn.execute(
                                """UPDATE osrs_characters 
                                   SET quest_points = quest_points + $1
                                   WHERE user_id = $2""",
                                quest_data['rewards']['quest_points'],
                                user_id
                            )
                    
                    return True
        except Exception as e:
            logger.error(f"Error updating quest status: {e}")
            return False

    async def get_achievement_diary_progress(self, user_id: int) -> List[Dict]:
        """Get a character's achievement diary progress."""
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
        """Mark an achievement diary task as completed."""
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
        """Get top players by total XP or specific skill."""
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
        """Get recent achievements (quests and diary tasks)."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """SELECT 'quest' as type, quest_name as name, completed_at
                   FROM osrs_quest_completions
                   WHERE user_id = $1 AND completed_at IS NOT NULL
                   UNION ALL
                   SELECT 'diary' as type, 
                          diary_name || ' - ' || task_name as name,
                          completed_at
                   FROM osrs_achievement_diary_tasks
                   WHERE user_id = $1 AND completed_at IS NOT NULL
                   ORDER BY completed_at DESC
                   LIMIT $2""",
                user_id, limit
            )

    async def get_recent_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent item transactions."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """SELECT *
                   FROM osrs_transactions
                   WHERE user_id = $1
                   ORDER BY created_at DESC
                   LIMIT $2""",
                user_id, limit
            )

    async def record_combat_stats(
        self,
        user_id: int,
        kills: int = 0,
        deaths: int = 0,
        damage_dealt: int = 0,
        damage_taken: int = 0
    ) -> bool:
        """Update combat statistics."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_combat_stats 
                       (user_id, kills, deaths, damage_dealt, damage_taken)
                       VALUES ($1, $2, $3, $4, $5)
                       ON CONFLICT (user_id)
                       DO UPDATE SET 
                           kills = osrs_combat_stats.kills + $2,
                           deaths = osrs_combat_stats.deaths + $3,
                           damage_dealt = osrs_combat_stats.damage_dealt + $4,
                           damage_taken = osrs_combat_stats.damage_taken + $5""",
                    user_id, kills, deaths, damage_dealt, damage_taken
                )
                return True
        except Exception as e:
            logger.error(f"Error updating combat stats: {e}")
            return False

    def _calculate_combat_level(self, stats: Dict) -> int:
        """Calculate combat level from stats."""
        base = 0.25 * (
            stats['defence']['level'] + 
            stats['hitpoints']['level'] +
            stats['prayer']['level'] // 2
        )
        
        melee = 0.325 * (
            stats['attack']['level'] + 
            stats['strength']['level']
        )
        
        ranged = 0.325 * (
            (stats['ranged']['level'] * 3) // 2
        )
        
        magic = 0.325 * (
            (stats['magic']['level'] * 3) // 2
        )
        
        return int(base + max(melee, ranged, magic))

    async def get_pet(self, user_id: int, pet_id: int) -> Optional[Dict]:
        """Get a pet by ID."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM osrs_pets WHERE user_id = $1 AND id = $2",
                user_id, pet_id
            )

    async def create_pet(
        self,
        user_id: int,
        name: str,
        pet_type: str,
        rarity: str = "common",
        attributes: Dict = None
    ) -> bool:
        """Create a new pet."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_pets 
                       (user_id, name, pet_type, rarity, attributes)
                       VALUES ($1, $2, $3, $4, $5)""",
                    user_id, name, pet_type, rarity, 
                    json.dumps(attributes or {})
                )
                return True
        except Exception as e:
            logger.error(f"Error creating pet: {e}")
            return False

    async def update_pet_stats(
        self,
        pet_id: int,
        experience: int = None,
        level: int = None,
        happiness: int = None
    ) -> bool:
        """Update pet statistics."""
        try:
            async with self.pool.acquire() as conn:
                updates = []
                values = []
                if experience is not None:
                    updates.append("experience = $" + str(len(values) + 1))
                    values.append(experience)
                if level is not None:
                    updates.append("level = $" + str(len(values) + 1))
                    values.append(level)
                if happiness is not None:
                    updates.append("happiness = $" + str(len(values) + 1))
                    values.append(happiness)
                
                if updates:
                    values.append(pet_id)
                    await conn.execute(
                        f"""UPDATE osrs_pets 
                           SET {', '.join(updates)}
                           WHERE id = ${len(values)}""",
                        *values
                    )
                return True
        except Exception as e:
            logger.error(f"Error updating pet stats: {e}")
            return False

    async def add_cross_system_boost(
        self,
        user_id: int,
        source_type: str,
        target_type: str,
        boost_value: float,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Add a cross-system boost."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_cross_system_boosts
                       (user_id, source_type, target_type, boost_value, expires_at)
                       VALUES ($1, $2, $3, $4, $5)""",
                    user_id, source_type, target_type, boost_value, expires_at
                )
                return True
        except Exception as e:
            logger.error(f"Error adding cross-system boost: {e}")
            return False

    async def update_minigame_score(
        self,
        user_id: int,
        minigame: str,
        score: int
    ) -> bool:
        """Update minigame score."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_minigame_scores 
                       (user_id, minigame, score, high_score, last_played)
                       VALUES ($1, $2, $3, 
                           GREATEST($3, COALESCE(
                               (SELECT high_score 
                                FROM osrs_minigame_scores 
                                WHERE user_id = $1 AND minigame = $2),
                               0
                           )),
                           NOW()
                       )
                       ON CONFLICT (user_id, minigame)
                       DO UPDATE SET 
                           score = $3,
                           high_score = GREATEST($3, osrs_minigame_scores.high_score),
                           last_played = NOW()""",
                    user_id, minigame, score
                )
                return True
        except Exception as e:
            logger.error(f"Error updating minigame score: {e}")
            return False

    async def add_collection_log_entry(
        self,
        user_id: int,
        category: str,
        item_id: str,
        count: int = 1
    ) -> bool:
        """Add or update collection log entry."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_collection_log
                       (user_id, category, item_id, count)
                       VALUES ($1, $2, $3, $4)
                       ON CONFLICT (user_id, category, item_id)
                       DO UPDATE SET count = osrs_collection_log.count + $4""",
                    user_id, category, item_id, count
                )
                return True
        except Exception as e:
            logger.error(f"Error adding collection log entry: {e}")
            return False

    async def update_player_title(
        self,
        user_id: int,
        title: str,
        active: bool = False
    ) -> bool:
        """Add or update player title."""
        try:
            async with self.pool.acquire() as conn:
                # If setting a title as active, deactivate all other titles
                if active:
                    await conn.execute(
                        """UPDATE osrs_player_titles
                           SET active = FALSE
                           WHERE user_id = $1""",
                        user_id
                    )
                
                await conn.execute(
                    """INSERT INTO osrs_player_titles
                       (user_id, title, active)
                       VALUES ($1, $2, $3)
                       ON CONFLICT (user_id, title)
                       DO UPDATE SET active = $3""",
                    user_id, title, active
                )
                return True
        except Exception as e:
            logger.error(f"Error updating player title: {e}")
            return False

    async def add_player_relationship(
        self,
        user_id: int,
        related_user_id: int,
        relationship_type: str
    ) -> bool:
        """Add player relationship."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_player_relationships
                       (user_id, related_user_id, relationship_type)
                       VALUES ($1, $2, $3)
                       ON CONFLICT (user_id, related_user_id, relationship_type)
                       DO NOTHING""",
                    user_id, related_user_id, relationship_type
                )
                return True
        except Exception as e:
            logger.error(f"Error adding player relationship: {e}")
            return False

    async def update_player_statistic(
        self,
        user_id: int,
        statistic_type: str,
        value: int
    ) -> bool:
        """Update player statistic."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO osrs_player_statistics
                       (user_id, statistic_type, value, last_updated)
                       VALUES ($1, $2, $3, NOW())
                       ON CONFLICT (user_id, statistic_type)
                       DO UPDATE SET 
                           value = osrs_player_statistics.value + $3,
                           last_updated = NOW()""",
                    user_id, statistic_type, value
                )
                return True
        except Exception as e:
            logger.error(f"Error updating player statistic: {e}")
            return False 