"""OSRS pet system manager."""
from typing import Dict, List, Optional
import logging
from datetime import datetime

from .models import Pet, PetType, StatusEffect
from .osrs_pet import OSRSPet

logger = logging.getLogger(__name__)


class PetManager:
    """Manages the pet system."""

    def __init__(self, bot):
        """Initialize pet manager."""
        self.bot = bot
        self.active_pets: Dict[int, Pet] = {}  # owner_id -> Pet
        self.max_pets = 3  # Maximum pets per player

    async def initialize(self):
        """Initialize pet system from database."""
        async with self.bot.db.pool.acquire() as conn:
            # Load all pets
            pets = await conn.fetch("SELECT * FROM osrs_pets")
            for pet_data in pets:
                try:
                    if pet_data["pet_type"] == PetType.OSRS.value:
                        pet = OSRSPet.from_dict(dict(pet_data))
                    else:
                        pet = Pet.from_dict(dict(pet_data))
                    self.active_pets[pet_data["user_id"]] = pet
                except Exception as e:
                    logger.error(f"Error loading pet {pet_data['id']}: {e}")

    async def create_pet(
        self, owner_id: int, name: str, pet_type: str, rarity: str = "common"
    ) -> Optional[Pet]:
        """Create a new pet."""
        try:
            # Check pet limit
            owner_pets = [p for p in self.active_pets.values() if p.owner_id == owner_id]
            if len(owner_pets) >= self.max_pets:
                return None

            async with self.bot.db.pool.acquire() as conn:
                # Create pet record
                pet_id = await conn.fetchval(
                    """
                    INSERT INTO osrs_pets (
                        user_id, name, pet_type, rarity
                    ) VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    owner_id,
                    name,
                    pet_type,
                    rarity,
                )

                # Create appropriate pet type
                if pet_type == PetType.OSRS.value:
                    pet = OSRSPet(id=pet_id, owner_id=owner_id, name=name, pet_type=pet_type)
                else:
                    pet = Pet(id=pet_id, owner_id=owner_id, name=name, pet_type=PetType(pet_type))

                self.active_pets[owner_id] = pet
                return pet

        except Exception as e:
            logger.error(f"Error creating pet: {e}")
            return None

    async def get_pet(self, owner_id: int) -> Optional[Pet]:
        """Get a player's active pet."""
        return self.active_pets.get(owner_id)

    async def train_pet(self, owner_id: int, activity: str, duration: int) -> tuple[int, bool]:
        """Train a pet and gain experience."""
        pet = self.active_pets.get(owner_id)
        if not pet:
            return (0, False)

        # Calculate experience gain
        base_xp = {"walking": 5, "playing": 10, "training": 15}.get(activity, 5)

        xp_gained = base_xp * duration
        leveled_up = pet.add_experience(xp_gained)

        # Update happiness
        happiness_change = pet.heal(duration * 2)  # 2 happiness per duration unit

        # Update database
        async with self.bot.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE osrs_pets
                SET experience = $1,
                    level = $2,
                    happiness = $3
                WHERE id = $4
                """,
                pet.stats.experience,
                pet.stats.level,
                pet.stats.happiness,
                pet.id,
            )

        return (xp_gained, leveled_up)

    async def feed_pet(self, owner_id: int, food_type: str) -> int:
        """Feed a pet to increase happiness."""
        pet = self.active_pets.get(owner_id)
        if not pet:
            return 0

        happiness_gain = {"basic": 10, "premium": 25, "special": 50}.get(food_type, 5)

        gained = pet.heal(happiness_gain)

        # Update database
        async with self.bot.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE osrs_pets
                SET happiness = $1
                WHERE id = $2
                """,
                pet.stats.happiness,
                pet.id,
            )

        return gained

    async def get_pet_stats(self, owner_id: int) -> Optional[Dict]:
        """Get pet statistics."""
        pet = self.active_pets.get(owner_id)
        if not pet:
            return None

        return {
            "name": pet.name,
            "type": pet.pet_type.value,
            "level": pet.stats.level,
            "experience": pet.stats.experience,
            "next_level": (pet.stats.level + 1) * 1000,  # Based on leveling formula
            "xp_to_next": (pet.stats.level + 1) * 1000 - pet.stats.experience,
            "happiness": pet.stats.happiness,
            "loyalty": pet.stats.loyalty,
            "age_days": (datetime.now() - pet.creation_date).days,
            "skill_levels": pet.stats.skill_levels,
            "training_points": pet.stats.training_points,
            "status": pet.status.value if pet.status else "none",
            "attributes": pet.attributes,
        }

    async def update_pet_attributes(self, owner_id: int, attributes: Dict) -> bool:
        """Update pet attributes."""
        pet = self.active_pets.get(owner_id)
        if not pet:
            return False

        pet.attributes.update(attributes)

        # Update database
        async with self.bot.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE osrs_pets
                SET attributes = $1
                WHERE id = $2
                """,
                pet.attributes,
                pet.id,
            )

        return True

    async def delete_pet(self, owner_id: int) -> bool:
        """Delete a pet."""
        if owner_id not in self.active_pets:
            return False

        try:
            async with self.bot.db.pool.acquire() as conn:
                await conn.execute("DELETE FROM osrs_pets WHERE user_id = $1", owner_id)
            del self.active_pets[owner_id]
            return True
        except Exception as e:
            logger.error(f"Error deleting pet: {e}")
            return False

    async def get_all_pets(self, owner_id: int) -> List[Pet]:
        """Get all pets owned by a player."""
        return [pet for pet in self.active_pets.values() if pet.owner_id == owner_id]

    async def apply_status(self, owner_id: int, status: StatusEffect, duration: int = 3) -> bool:
        """Apply a status effect to a pet."""
        pet = self.active_pets.get(owner_id)
        if not pet:
            return False

        pet.apply_status(status, duration)

        # Update database
        async with self.bot.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE osrs_pets
                SET status = $1,
                    status_turns = $2
                WHERE id = $3
                """,
                status.value,
                duration,
                pet.id,
            )

        return True
