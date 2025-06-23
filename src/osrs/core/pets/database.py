"""Database integration for the pet system."""
from typing import Dict, List, Optional, Any
import asyncpg
from datetime import datetime

from .base_models import BasePet, PetStats, PetAbility, PetOrigin, PetRarity, StatusEffect


class PetDatabase:
    """Database integration for the pet system."""

    def __init__(self, pool: asyncpg.Pool):
        """Initialize with database connection pool."""
        self.pool = pool

    async def initialize(self) -> None:
        """Initialize database tables."""
        async with self.pool.acquire() as conn:
            # Create pets table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pets (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    rarity TEXT NOT NULL,
                    level INTEGER NOT NULL DEFAULT 1,
                    experience INTEGER NOT NULL DEFAULT 0,
                    happiness INTEGER NOT NULL DEFAULT 100,
                    loyalty INTEGER NOT NULL DEFAULT 0,
                    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_interaction TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    attributes JSONB NOT NULL DEFAULT '{}'::jsonb
                )
            """
            )

            # Create pet_abilities table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pet_abilities (
                    pet_id TEXT NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    effect_type TEXT NOT NULL,
                    effect_value FLOAT NOT NULL,
                    cooldown INTEGER NOT NULL,
                    last_used TIMESTAMP,
                    PRIMARY KEY (pet_id, name)
                )
            """
            )

            # Create pet_achievements table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pet_achievements (
                    pet_id TEXT NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
                    achievement_id TEXT NOT NULL,
                    unlocked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (pet_id, achievement_id)
                )
            """
            )

            # Create battle_history table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS battle_history (
                    id TEXT PRIMARY KEY,
                    pet1_id TEXT NOT NULL REFERENCES pets(id),
                    pet2_id TEXT NOT NULL REFERENCES pets(id),
                    winner_id TEXT NOT NULL REFERENCES pets(id),
                    turns INTEGER NOT NULL,
                    battle_log JSONB NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create breeding_history table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS breeding_history (
                    id TEXT PRIMARY KEY,
                    parent1_id TEXT NOT NULL REFERENCES pets(id),
                    parent2_id TEXT NOT NULL REFERENCES pets(id),
                    offspring_id TEXT REFERENCES pets(id),
                    success BOOLEAN NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
                )
            """
            )

    async def save_pet(self, pet: BasePet) -> None:
        """Save or update a pet in the database."""
        async with self.pool.acquire() as conn:
            # Save pet data
            await conn.execute(
                """
                INSERT INTO pets (
                    id, owner_id, name, origin, rarity, level, experience,
                    happiness, loyalty, creation_date, last_interaction, attributes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (id) DO UPDATE SET
                    level = EXCLUDED.level,
                    experience = EXCLUDED.experience,
                    happiness = EXCLUDED.happiness,
                    loyalty = EXCLUDED.loyalty,
                    last_interaction = EXCLUDED.last_interaction,
                    attributes = EXCLUDED.attributes
            """,
                pet.id,
                pet.owner_id,
                pet.name,
                pet.origin.value,
                pet.rarity.value,
                pet.stats.level,
                pet.stats.experience,
                pet.stats.happiness,
                pet.stats.loyalty,
                pet.creation_date,
                pet.stats.last_interaction,
                pet.attributes,
            )

            # Save abilities
            await conn.execute("DELETE FROM pet_abilities WHERE pet_id = $1", pet.id)
            if pet.abilities:
                await conn.executemany(
                    """
                    INSERT INTO pet_abilities (
                        pet_id, name, description, effect_type,
                        effect_value, cooldown, last_used
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    [
                        (
                            pet.id,
                            ability.name,
                            ability.description,
                            ability.effect_type,
                            ability.effect_value,
                            ability.cooldown,
                            ability.last_used,
                        )
                        for ability in pet.abilities
                    ],
                )

    async def get_pet(self, pet_id: str) -> Optional[BasePet]:
        """Get a pet by ID."""
        async with self.pool.acquire() as conn:
            # Get pet data
            pet_data = await conn.fetchrow(
                """
                SELECT * FROM pets WHERE id = $1
            """,
                pet_id,
            )

            if not pet_data:
                return None

            # Get abilities
            abilities = await conn.fetch(
                """
                SELECT * FROM pet_abilities WHERE pet_id = $1
            """,
                pet_id,
            )

            # Create PetStats
            stats = PetStats(
                level=pet_data["level"],
                experience=pet_data["experience"],
                happiness=pet_data["happiness"],
                loyalty=pet_data["loyalty"],
                last_interaction=pet_data["last_interaction"],
            )

            # Create abilities
            pet_abilities = [
                PetAbility(
                    name=ability["name"],
                    description=ability["description"],
                    effect_type=ability["effect_type"],
                    effect_value=ability["effect_value"],
                    cooldown=ability["cooldown"],
                    last_used=ability["last_used"],
                )
                for ability in abilities
            ]

            # Create and return pet
            return BasePet(
                id=pet_data["id"],
                owner_id=pet_data["owner_id"],
                name=pet_data["name"],
                origin=PetOrigin(pet_data["origin"]),
                rarity=PetRarity(pet_data["rarity"]),
                stats=stats,
                abilities=pet_abilities,
                creation_date=pet_data["creation_date"],
                attributes=pet_data["attributes"],
            )

    async def get_user_pets(self, user_id: str) -> List[BasePet]:
        """Get all pets owned by a user."""
        async with self.pool.acquire() as conn:
            # Get all pet IDs for user
            pet_ids = await conn.fetch(
                """
                SELECT id FROM pets WHERE owner_id = $1
            """,
                user_id,
            )

            # Get each pet
            pets = []
            for record in pet_ids:
                if pet := await self.get_pet(record["id"]):
                    pets.append(pet)

            return pets

    async def delete_pet(self, pet_id: str) -> bool:
        """Delete a pet. Returns True if successful."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM pets WHERE id = $1
            """,
                pet_id,
            )
            return result == "DELETE 1"

    async def save_battle(
        self,
        battle_id: str,
        pet1_id: str,
        pet2_id: str,
        winner_id: str,
        turns: int,
        battle_log: List[Dict[str, Any]],
    ) -> None:
        """Save a battle record."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO battle_history (
                    id, pet1_id, pet2_id, winner_id, turns, battle_log
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                battle_id,
                pet1_id,
                pet2_id,
                winner_id,
                turns,
                battle_log,
            )

    async def save_breeding(
        self,
        breeding_id: str,
        parent1_id: str,
        parent2_id: str,
        success: bool,
        started_at: datetime,
        offspring_id: Optional[str] = None,
        completed_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save a breeding record."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO breeding_history (
                    id, parent1_id, parent2_id, offspring_id,
                    success, started_at, completed_at, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                breeding_id,
                parent1_id,
                parent2_id,
                offspring_id,
                success,
                started_at,
                completed_at,
                metadata or {},
            )

    async def get_pet_achievements(self, pet_id: str) -> List[Dict[str, Any]]:
        """Get all achievements for a pet."""
        async with self.pool.acquire() as conn:
            achievements = await conn.fetch(
                """
                SELECT achievement_id, unlocked_at
                FROM pet_achievements
                WHERE pet_id = $1
                ORDER BY unlocked_at DESC
            """,
                pet_id,
            )

            return [dict(ach) for ach in achievements]

    async def add_pet_achievement(self, pet_id: str, achievement_id: str) -> None:
        """Add an achievement for a pet."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pet_achievements (pet_id, achievement_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """,
                pet_id,
                achievement_id,
            )

    async def get_battle_history(
        self, pet_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get battle history for a pet or all battles."""
        async with self.pool.acquire() as conn:
            if pet_id:
                battles = await conn.fetch(
                    """
                    SELECT *
                    FROM battle_history
                    WHERE pet1_id = $1 OR pet2_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """,
                    pet_id,
                    limit,
                )
            else:
                battles = await conn.fetch(
                    """
                    SELECT *
                    FROM battle_history
                    ORDER BY created_at DESC
                    LIMIT $1
                """,
                    limit,
                )

            return [dict(battle) for battle in battles]

    async def get_breeding_history(
        self, pet_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get breeding history for a pet or all breeding attempts."""
        async with self.pool.acquire() as conn:
            if pet_id:
                breedings = await conn.fetch(
                    """
                    SELECT *
                    FROM breeding_history
                    WHERE parent1_id = $1 OR parent2_id = $1
                    ORDER BY started_at DESC
                    LIMIT $2
                """,
                    pet_id,
                    limit,
                )
            else:
                breedings = await conn.fetch(
                    """
                    SELECT *
                    FROM breeding_history
                    ORDER BY started_at DESC
                    LIMIT $1
                """,
                    limit,
                )

            return [dict(breeding) for breeding in breedings]
