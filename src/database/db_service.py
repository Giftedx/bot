"""Database service for OSRS bot."""

import asyncpg
import json
import logging
from typing import Dict, Optional, Any

from ..osrs.models import Player, SkillType, QuestStatus


logger = logging.getLogger("DatabaseService")


class DatabaseService:
    """Service for handling database operations."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize_tables(self) -> None:
        """Initialize database tables."""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)

            async with self.pool.acquire() as conn:
                # Create players table
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS players (
                        id BIGINT PRIMARY KEY,
                        name TEXT NOT NULL,
                        skills JSONB NOT NULL DEFAULT '{}',
                        inventory JSONB NOT NULL DEFAULT '[]',
                        equipment JSONB NOT NULL DEFAULT '{}',
                        bank JSONB NOT NULL DEFAULT '{}',
                        quests JSONB NOT NULL DEFAULT '{}',
                        quest_points INTEGER NOT NULL DEFAULT 0,
                        gold INTEGER NOT NULL DEFAULT 0,
                        current_world INTEGER NOT NULL DEFAULT 301,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create items table
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS items (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        category TEXT NOT NULL,
                        tradeable BOOLEAN NOT NULL DEFAULT true,
                        stackable BOOLEAN NOT NULL DEFAULT false,
                        equipable BOOLEAN NOT NULL DEFAULT false,
                        high_alch_value INTEGER NOT NULL DEFAULT 0,
                        low_alch_value INTEGER NOT NULL DEFAULT 0,
                        ge_price INTEGER
                    )
                """
                )

                # Create trades table
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trades (
                        id SERIAL PRIMARY KEY,
                        offerer_id BIGINT NOT NULL REFERENCES players(id),
                        receiver_id BIGINT NOT NULL REFERENCES players(id),
                        item_id TEXT NOT NULL REFERENCES items(id),
                        amount INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP WITH TIME ZONE,
                        CONSTRAINT different_players CHECK (offerer_id != receiver_id)
                    )
                """
                )

                logger.info("Database tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def load_player(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Load player data from database."""
        if not self.pool:
            return None

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM players WHERE id = $1", user_id)

                if not row:
                    return None

                # Convert row to dict and parse JSON fields
                player_data = dict(row)
                player_data["skills"] = json.loads(player_data["skills"])
                player_data["inventory"] = json.loads(player_data["inventory"])
                player_data["equipment"] = json.loads(player_data["equipment"])
                player_data["bank"] = json.loads(player_data["bank"])
                player_data["quests"] = json.loads(player_data["quests"])

                return player_data
        except Exception as e:
            logger.error(f"Failed to load player {user_id}: {e}")
            return None

    async def save_player(self, player: Player) -> bool:
        """Save player data to database."""
        if not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                # Convert skills to JSON-compatible format
                skills_data = {
                    skill.value: {
                        "level": player.skills[skill].level,
                        "xp": player.skills[skill].xp,
                    }
                    for skill in player.skills
                }

                # Convert inventory to JSON-compatible format
                inventory_data = [
                    {"item_id": item.item.id, "quantity": item.quantity}
                    for item in player.inventory
                ]

                # Convert equipment to JSON-compatible format
                equipment_data = {
                    slot: getattr(player.equipment, slot).id
                    for slot in player.equipment.__dict__
                    if getattr(player.equipment, slot) is not None
                }

                # Convert bank to JSON-compatible format
                bank_data = player.bank.items

                # Convert quests to JSON-compatible format
                quests_data = {quest_id: status.value for quest_id, status in player.quests.items()}

                await conn.execute(
                    """
                    INSERT INTO players (
                        id, name, skills, inventory, equipment, bank,
                        quests, quest_points, gold, current_world
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        skills = EXCLUDED.skills,
                        inventory = EXCLUDED.inventory,
                        equipment = EXCLUDED.equipment,
                        bank = EXCLUDED.bank,
                        quests = EXCLUDED.quests,
                        quest_points = EXCLUDED.quest_points,
                        gold = EXCLUDED.gold,
                        current_world = EXCLUDED.current_world,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    player.id,
                    player.name,
                    json.dumps(skills_data),
                    json.dumps(inventory_data),
                    json.dumps(equipment_data),
                    json.dumps(bank_data),
                    json.dumps(quests_data),
                    player.quest_points,
                    player.gold,
                    player.current_world,
                )

                return True
        except Exception as e:
            logger.error(f"Failed to save player {player.id}: {e}")
            return False

    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
