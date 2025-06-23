from typing import Optional, Union, Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime
import random
from dataclasses import dataclass
import logging

from src.pets.models import Pet
from ..config.game_config import Rarity
from ..features.pets.event_system import EventManager, EventType, GameEvent

logger = logging.getLogger(__name__)


class PetOrigin(Enum):
    OSRS = "osrs"
    POKEMON = "pokemon"
    CUSTOM = "custom"


@dataclass
class PetAbility:
    name: str
    description: str
    effect_type: str
    effect_value: float
    cooldown: int  # in seconds
    last_used: Optional[datetime] = None


class PetStats:
    def __init__(self):
        self.level: int = 1
        self.experience: int = 0
        self.happiness: int = 100
        self.loyalty: int = 0
        self.last_interaction: datetime = datetime.now()
        self.achievements: List[str] = []
        self.skill_levels: Dict[str, int] = {"attack": 1, "defense": 1, "special": 1, "speed": 1}
        self.training_points: int = 0

    def gain_exp(
        self,
        amount: int,
        event_manager: Optional[EventManager] = None,
        pet_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Returns True if leveled up"""
        self.experience += amount
        old_level = self.level
        self.level = 1 + (self.experience // 1000)  # Simple leveling formula
        leveled_up = self.level > old_level

        if leveled_up:
            self.training_points += 1
            if event_manager and pet_data:
                event_manager.emit(
                    GameEvent(
                        type=EventType.PET_LEVELED,
                        user_id=str(pet_data["owner_id"]),
                        timestamp=datetime.utcnow(),
                        data={
                            "pet_id": pet_data["pet_id"],
                            "pet_type": pet_data["origin"].value,
                            "old_level": old_level,
                            "new_level": self.level,
                            "training_points_gained": 1,
                        },
                    )
                )

        return leveled_up

    def train_skill(self, skill: str) -> bool:
        """Train a specific skill using training points"""
        if self.training_points <= 0 or skill not in self.skill_levels:
            return False

        self.skill_levels[skill] += 1
        self.training_points -= 1
        return True

    def calculate_power(self) -> int:
        """Calculate pet's overall power level"""
        base_power = self.level * 10
        skill_power = sum(level * 5 for level in self.skill_levels.values())
        loyalty_bonus = min(self.loyalty * 2, 100)  # Cap at 100
        happiness_multiplier = self.happiness / 100  # 0.0 to 1.0

        return int((base_power + skill_power + loyalty_bonus) * happiness_multiplier)


class PetSystem:
    """Manages the pet system."""

    def __init__(self, bot):
        """Initialize pet system."""
        self.bot = bot
        self.active_pets: Dict[int, Pet] = {}  # owner_id -> Pet

    async def initialize(self):
        """Initialize pet system from database."""
        async with self.bot.db.pool.acquire() as conn:
            # Load all pets
            pets = await conn.fetch("SELECT * FROM osrs_pets")
            for pet_data in pets:
                self.active_pets[pet_data["user_id"]] = Pet(
                    id=pet_data["id"],
                    owner_id=pet_data["user_id"],
                    name=pet_data["name"],
                    pet_type=pet_data["pet_type"],
                    level=pet_data["level"],
                    experience=pet_data["experience"],
                    happiness=pet_data["happiness"],
                    creation_date=pet_data["creation_date"],
                    attributes=pet_data["attributes"],
                )

    async def create_pet(
        self, owner_id: int, name: str, pet_type: str, rarity: str = "common"
    ) -> Optional[Pet]:
        """Create a new pet."""
        try:
            async with self.bot.db.pool.acquire() as conn:
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

                pet = Pet(id=pet_id, owner_id=owner_id, name=name, pet_type=pet_type)
                self.active_pets[owner_id] = pet
                return pet

        except Exception as e:
            logger.error(f"Error creating pet: {e}")
            return None

    async def get_pet(self, owner_id: int) -> Optional[Pet]:
        """Get a player's active pet."""
        return self.active_pets.get(owner_id)

    async def train_pet(self, owner_id: int, activity: str, duration: int) -> Tuple[int, bool]:
        """
        Train a pet and gain experience.
        Returns (xp_gained, leveled_up)
        """
        pet = self.active_pets.get(owner_id)
        if not pet:
            return (0, False)

        # Calculate experience gain
        base_xp = {"walking": 5, "playing": 10, "training": 15}.get(activity, 5)

        xp_gained = base_xp * duration
        leveled_up = pet.add_experience(xp_gained)

        # Update happiness
        happiness_change = random.randint(5, 15)
        pet.happiness = min(100, pet.happiness + happiness_change)

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
                pet.experience,
                pet.level,
                pet.happiness,
                pet.id,
            )

        return (xp_gained, leveled_up)

    async def feed_pet(self, owner_id: int, food_type: str) -> int:
        """
        Feed a pet to increase happiness.
        Returns happiness gained.
        """
        pet = self.active_pets.get(owner_id)
        if not pet:
            return 0

        happiness_gain = {"basic": 10, "premium": 25, "special": 50}.get(food_type, 5)

        old_happiness = pet.happiness
        pet.happiness = min(100, pet.happiness + happiness_gain)
        gained = pet.happiness - old_happiness

        # Update database
        async with self.bot.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE osrs_pets
                SET happiness = $1
                WHERE id = $2
                """,
                pet.happiness,
                pet.id,
            )

        return gained

    async def get_pet_stats(self, owner_id: int) -> Optional[Dict]:
        """Get pet statistics."""
        pet = self.active_pets.get(owner_id)
        if not pet:
            return None

        next_level_xp = pet._experience_for_level(pet.level + 1)
        xp_to_next = next_level_xp - pet.experience

        return {
            "name": pet.name,
            "type": pet.pet_type,
            "level": pet.level,
            "experience": pet.experience,
            "next_level": next_level_xp,
            "xp_to_next": xp_to_next,
            "happiness": pet.happiness,
            "age_days": (datetime.now() - pet.creation_date).days,
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


class PetManager:
    def __init__(self, event_manager: Optional[EventManager] = None):
        self.pets: Dict[str, Pet] = {}
        self.event_manager = event_manager
        self.drop_rates: Dict[Rarity, float] = {
            Rarity.COMMON: 0.4,
            Rarity.UNCOMMON: 0.3,
            Rarity.RARE: 0.15,
            Rarity.EPIC: 0.1,
            Rarity.LEGENDARY: 0.05,
        }

    def register_pet(self, pet: Pet) -> None:
        """Register a new pet in the system"""
        self.pets[str(pet.id)] = pet

        if self.event_manager:
            self.event_manager.emit(
                GameEvent(
                    type=EventType.PET_OBTAINED,
                    user_id=str(pet.owner_id),
                    timestamp=datetime.utcnow(),
                    data={
                        "pet_id": str(pet.id),
                        "pet_type": pet.pet_type,
                        "name": pet.name,
                        "rarity": "common",  # Assuming common rarity
                    },
                )
            )

    def get_pet(self, pet_id: str) -> Optional[Pet]:
        """Retrieve a pet by ID"""
        return self.pets.get(pet_id)

    def roll_for_pet(self, origin: PetOrigin, boost: float = 0.0) -> Optional[Rarity]:
        """Roll for a chance to get a pet of a specific rarity"""
        roll = random.random() - boost  # Apply catch rate boost
        for rarity, rate in self.drop_rates.items():
            if roll < rate:
                return rarity
            roll -= rate
        return None

    def get_pets_by_owner(self, owner_id: str) -> List[Pet]:
        """Get all pets owned by a specific user"""
        return [pet for pet in self.pets.values() if pet.owner_id == int(owner_id)]

    def get_pets_by_origin(self, origin: PetOrigin) -> List[Pet]:
        """Get all pets of a specific origin type"""
        return [pet for pet in self.pets.values() if pet.pet_type == origin.value]

    def get_strongest_pets(self, owner_id: str, limit: int = 5) -> List[Pet]:
        """Get user's strongest pets by power level"""
        user_pets = self.get_pets_by_owner(owner_id)
        return sorted(user_pets, key=lambda p: p.level, reverse=True)[:limit]

    def transfer_pet(self, pet_id: str, new_owner_id: str) -> bool:
        """Transfer pet ownership to another user"""
        pet = self.get_pet(pet_id)
        if not pet:
            return False

        old_owner_id = pet.owner_id
        pet.owner_id = int(new_owner_id)
        pet.level = 1  # Reset level on transfer

        if self.event_manager:
            self.event_manager.emit(
                GameEvent(
                    type=EventType.PET_TRANSFERRED,
                    user_id=str(old_owner_id),
                    timestamp=datetime.utcnow(),
                    data={"pet_id": pet_id, "old_owner": old_owner_id, "new_owner": new_owner_id},
                )
            )

        return True
