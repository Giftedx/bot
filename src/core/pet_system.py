from typing import Optional, Union, Dict, List, Any
from enum import Enum
from datetime import datetime
import random
from dataclasses import dataclass

from ..config.game_config import Rarity
from ..features.pets.event_system import EventManager, EventType, GameEvent

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
        self.skill_levels: Dict[str, int] = {
            "attack": 1,
            "defense": 1,
            "special": 1,
            "speed": 1
        }
        self.training_points: int = 0
        
    def gain_exp(self, amount: int, event_manager: Optional[EventManager] = None, 
                pet_data: Optional[Dict[str, Any]] = None) -> bool:
        """Returns True if leveled up"""
        self.experience += amount
        old_level = self.level
        self.level = 1 + (self.experience // 1000)  # Simple leveling formula
        leveled_up = self.level > old_level
        
        if leveled_up:
            self.training_points += 1
            if event_manager and pet_data:
                event_manager.emit(GameEvent(
                    type=EventType.PET_LEVELED,
                    user_id=str(pet_data["owner_id"]),
                    timestamp=datetime.utcnow(),
                    data={
                        "pet_id": pet_data["pet_id"],
                        "pet_type": pet_data["origin"].value,
                        "old_level": old_level,
                        "new_level": self.level,
                        "training_points_gained": 1
                    }
                ))
        
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

class Pet:
    def __init__(
        self,
        pet_id: str,
        name: str,
        origin: PetOrigin,
        rarity: Rarity,
        owner_id: str,
        base_stats: Dict[str, int],
        abilities: List[PetAbility],
        metadata: Dict = None,
        event_manager: Optional[EventManager] = None
    ):
        self.pet_id = pet_id
        self.name = name
        self.origin = origin
        self.rarity = rarity
        self.owner_id = owner_id
        self.base_stats = base_stats
        self.abilities = abilities
        self.stats = PetStats()
        self.metadata = metadata or {}
        self.obtained_date = datetime.now()
        self.event_manager = event_manager
        self.daily_interaction_count = 0
        self.last_daily_reset = datetime.now()

    def interact(self, interaction_type: str) -> Dict[str, Union[str, int, bool]]:
        """Handle pet interactions and return results"""
        now = datetime.now()
        
        # Reset daily interaction count if it's a new day
        if (now - self.last_daily_reset).days >= 1:
            self.daily_interaction_count = 0
            self.last_daily_reset = now
        
        # Check daily interaction limit
        if self.daily_interaction_count >= 10:
            return {
                "success": False,
                "message": "You've reached the daily interaction limit with this pet!"
            }
            
        self.stats.last_interaction = now
        self.daily_interaction_count += 1
        
        # Basic interaction rewards
        exp_gain = random.randint(10, 30)
        happiness_gain = random.randint(5, 15)
        
        # Apply rarity bonuses
        rarity_multiplier = {
            Rarity.COMMON: 1.0,
            Rarity.UNCOMMON: 1.2,
            Rarity.RARE: 1.5,
            Rarity.EPIC: 2.0,
            Rarity.LEGENDARY: 3.0
        }.get(self.rarity, 1.0)
        
        exp_gain = int(exp_gain * rarity_multiplier)
        
        # Apply loyalty bonus
        loyalty_bonus = min(self.stats.loyalty * 0.05, 0.5)  # Max 50% bonus
        exp_gain = int(exp_gain * (1 + loyalty_bonus))
        
        leveled_up = self.stats.gain_exp(exp_gain, self.event_manager, {
            "pet_id": self.pet_id,
            "owner_id": self.owner_id,
            "origin": self.origin
        })
        
        self.stats.happiness = min(100, self.stats.happiness + happiness_gain)
        self.stats.loyalty += 1

        # Check for ability activation
        activated_abilities = []
        for ability in self.abilities:
            if ability.last_used is None or \
               (now - ability.last_used).seconds >= ability.cooldown:
                if random.random() < 0.1:  # 10% chance to activate
                    ability.last_used = now
                    activated_abilities.append(ability.name)

        return {
            "success": True,
            "exp_gained": exp_gain,
            "happiness_gained": happiness_gain,
            "leveled_up": leveled_up,
            "current_level": self.stats.level,
            "power_level": self.stats.calculate_power(),
            "activated_abilities": activated_abilities,
            "interactions_remaining": 10 - self.daily_interaction_count
        }

    def use_ability(self, ability_name: str) -> Dict[str, Any]:
        """Use a specific pet ability"""
        ability = next((a for a in self.abilities if a.name == ability_name), None)
        if not ability:
            return {
                "success": False,
                "message": f"This pet doesn't have the ability: {ability_name}"
            }
            
        now = datetime.now()
        if ability.last_used and (now - ability.last_used).seconds < ability.cooldown:
            cooldown_remaining = ability.cooldown - (now - ability.last_used).seconds
            return {
                "success": False,
                "message": f"Ability on cooldown for {cooldown_remaining} seconds"
            }
            
        ability.last_used = now
        return {
            "success": True,
            "ability_name": ability.name,
            "effect_type": ability.effect_type,
            "effect_value": ability.effect_value
        }

class PetManager:
    def __init__(self, event_manager: Optional[EventManager] = None):
        self.pets: Dict[str, Pet] = {}
        self.event_manager = event_manager
        self.drop_rates: Dict[Rarity, float] = {
            Rarity.COMMON: 0.4,
            Rarity.UNCOMMON: 0.3,
            Rarity.RARE: 0.15,
            Rarity.EPIC: 0.1,
            Rarity.LEGENDARY: 0.05
        }

    def register_pet(self, pet: Pet) -> None:
        """Register a new pet in the system"""
        self.pets[pet.pet_id] = pet
        
        if self.event_manager:
            self.event_manager.emit(GameEvent(
                type=EventType.PET_OBTAINED,
                user_id=str(pet.owner_id),
                timestamp=datetime.utcnow(),
                data={
                    "pet_id": pet.pet_id,
                    "pet_type": pet.origin.value,
                    "name": pet.name,
                    "rarity": pet.rarity.value
                }
            ))

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
        return [pet for pet in self.pets.values() if pet.owner_id == owner_id]

    def get_pets_by_origin(self, origin: PetOrigin) -> List[Pet]:
        """Get all pets of a specific origin type"""
        return [pet for pet in self.pets.values() if pet.origin == origin]

    def get_strongest_pets(self, owner_id: str, limit: int = 5) -> List[Pet]:
        """Get user's strongest pets by power level"""
        user_pets = self.get_pets_by_owner(owner_id)
        return sorted(user_pets, key=lambda p: p.stats.calculate_power(), reverse=True)[:limit]

    def transfer_pet(self, pet_id: str, new_owner_id: str) -> bool:
        """Transfer pet ownership to another user"""
        pet = self.get_pet(pet_id)
        if not pet:
            return False
            
        old_owner_id = pet.owner_id
        pet.owner_id = new_owner_id
        pet.stats.loyalty = max(0, pet.stats.loyalty - 50)  # Loyalty penalty on transfer
        
        if self.event_manager:
            self.event_manager.emit(GameEvent(
                type=EventType.PET_TRANSFERRED,
                user_id=str(old_owner_id),
                timestamp=datetime.utcnow(),
                data={
                    "pet_id": pet_id,
                    "old_owner": old_owner_id,
                    "new_owner": new_owner_id
                }
            ))
            
        return True 