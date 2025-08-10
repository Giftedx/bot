"""Service layer for the pet system."""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .base_models import BasePet, PetOrigin, PetRarity
from .database import PetDatabase
from .battle_system import BattleSystem
from .event_system import EventManager, EventType, GameEvent, AchievementManager


class PetService:
    """Service layer coordinating pet system components."""

    def __init__(self, database: PetDatabase, event_manager: EventManager):
        """Initialize service with required components."""
        self.database = database
        self.event_manager = event_manager
        self.battle_system = BattleSystem()
        self.achievement_manager = AchievementManager(event_manager)

    async def create_pet(
        self, owner_id: str, name: str, origin: PetOrigin, rarity: PetRarity = PetRarity.COMMON
    ) -> BasePet:
        """Create a new pet."""
        # Create pet instance
        pet = BasePet(
            id=str(uuid.uuid4()), owner_id=owner_id, name=name, origin=origin, rarity=rarity
        )

        # Save to database
        await self.database.save_pet(pet)

        # Emit event
        self.event_manager.emit(
            GameEvent(
                type=EventType.PET_CREATED,
                user_id=owner_id,
                timestamp=datetime.utcnow(),
                data={
                    "pet_id": pet.id,
                    "name": name,
                    "origin": origin.value,
                    "rarity": rarity.value,
                },
            )
        )

        return pet

    async def get_pet(self, pet_id: str) -> Optional[BasePet]:
        """Get a pet by ID."""
        return await self.database.get_pet(pet_id)

    async def get_user_pets(self, user_id: str) -> List[BasePet]:
        """Get all pets owned by a user."""
        return await self.database.get_user_pets(user_id)

    async def train_pet(self, pet_id: str, skill: str) -> Dict[str, Any]:
        """Train a specific pet skill."""
        pet = await self.get_pet(pet_id)
        if not pet:
            return {"error": "Pet not found"}

        if not pet.stats.train_skill(skill):
            return {"error": "Not enough training points"}

        # Save changes
        await self.database.save_pet(pet)

        # Emit event
        self.event_manager.emit(
            GameEvent(
                type=EventType.PET_TRAINED,
                user_id=pet.owner_id,
                timestamp=datetime.utcnow(),
                data={"pet_id": pet.id, "skill": skill, "new_level": pet.stats.skill_levels[skill]},
            )
        )

        return {
            "success": True,
            "skill": skill,
            "new_level": pet.stats.skill_levels[skill],
            "training_points_remaining": pet.stats.training_points,
        }

    async def add_experience(self, pet_id: str, amount: int) -> Dict[str, Any]:
        """Add experience to a pet."""
        pet = await self.get_pet(pet_id)
        if not pet:
            return {"error": "Pet not found"}

        old_level = pet.stats.level
        leveled_up = pet.add_experience(amount)

        # Save changes
        await self.database.save_pet(pet)

        # Emit event if leveled up
        if leveled_up:
            self.event_manager.emit(
                GameEvent(
                    type=EventType.PET_LEVELED,
                    user_id=pet.owner_id,
                    timestamp=datetime.utcnow(),
                    data={
                        "pet_id": pet.id,
                        "old_level": old_level,
                        "new_level": pet.stats.level,
                        "total_exp": pet.stats.experience,
                    },
                )
            )

        return {
            "success": True,
            "experience_gained": amount,
            "total_experience": pet.stats.experience,
            "leveled_up": leveled_up,
            "current_level": pet.stats.level,
        }

    async def start_battle(self, pet1_id: str, pet2_id: str) -> Dict[str, Any]:
        """Start a battle between two pets."""
        # Get pets
        pet1 = await self.get_pet(pet1_id)
        pet2 = await self.get_pet(pet2_id)

        if not pet1 or not pet2:
            return {"error": "One or both pets not found"}

        # Create battle
        battle = self.battle_system.create_battle(pet1, pet2)

        # Emit event
        self.event_manager.emit(
            GameEvent(
                type=EventType.PET_BATTLE_STARTED,
                user_id=pet1.owner_id,
                timestamp=datetime.utcnow(),
                data={"battle_id": battle.id, "pet1_id": pet1_id, "pet2_id": pet2_id},
            )
        )

        return {
            "battle_id": battle.id,
            "pet1": {
                "name": pet1.name,
                "stats": battle.pet1.stats.__dict__,
                "moves": [move.__dict__ for move in battle.pet1.moves],
            },
            "pet2": {
                "name": pet2.name,
                "stats": battle.pet2.stats.__dict__,
                "moves": [move.__dict__ for move in battle.pet2.moves],
            },
        }

    async def process_battle_turn(self, battle_id: str, pet_id: str, move: str) -> Dict[str, Any]:
        """Process a turn in a battle."""
        result = self.battle_system.process_turn(battle_id, move)

        if "error" in result:
            return result

        battle = self.battle_system.get_battle(battle_id)

        # Emit move event
        self.event_manager.emit(
            GameEvent(
                type=EventType.PET_BATTLE_MOVE,
                user_id=battle.pet1.pet.owner_id,  # Use first pet's owner for event
                timestamp=datetime.utcnow(),
                data={
                    "battle_id": battle_id,
                    "attacker_id": pet_id,
                    "move": move,
                    "damage": result["damage"],
                    "effects": result.get("effect_message", ""),
                },
            )
        )

        # If battle is over, save to history and emit event
        if result["battle_over"]:
            await self.database.save_battle(
                battle_id,
                battle.pet1.pet.id,
                battle.pet2.pet.id,
                battle.winner.pet.id,
                battle.current_turn,
                battle.battle_log,
            )

            self.event_manager.emit(
                GameEvent(
                    type=EventType.PET_BATTLE_ENDED,
                    user_id=battle.winner.pet.owner_id,
                    timestamp=datetime.utcnow(),
                    data={
                        "battle_id": battle_id,
                        "winner_id": battle.winner.pet.id,
                        "turns": battle.current_turn,
                        "win_streak": await self._get_win_streak(battle.winner.pet.id),
                    },
                )
            )

            # Clean up battle
            self.battle_system.end_battle(battle_id)

        return result

    async def _get_win_streak(self, pet_id: str) -> int:
        """Calculate current win streak for a pet."""
        history = await self.database.get_battle_history(pet_id, limit=10)
        streak = 0

        for battle in history:
            if battle["winner_id"] == pet_id:
                streak += 1
            else:
                break

        return streak

    async def get_battle_history(
        self, pet_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get battle history for a pet or all battles."""
        return await self.database.get_battle_history(pet_id, limit)

    async def get_achievements(self, user_id: str) -> Dict[str, Any]:
        """Get achievement information for a user."""
        return {
            "completed": self.achievement_manager.get_user_achievements(user_id),
            "available": self.achievement_manager.get_available_achievements(user_id),
        }

    async def delete_pet(self, pet_id: str) -> bool:
        """Delete a pet."""
        return await self.database.delete_pet(pet_id)
