"""Pet manager for handling pets and their mechanics."""

import random
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from .game_tick import GameTick, TickPriority
from .movement import Position
from .skill_manager import SkillType

class PetSource(Enum):
    """Sources for obtaining pets."""
    SKILLING = "skilling"
    BOSS = "boss"
    MINIGAME = "minigame"
    QUEST = "quest"
    OTHER = "other"

@dataclass
class PetData:
    """Data for a pet."""
    id: str
    name: str
    source: PetSource
    base_chance: float  # Base chance to obtain
    level_scaling: bool  # Whether chance scales with level
    threshold: Optional[int] = None  # Drop rate threshold (e.g., boss KC)
    requirements: Dict[str, int] = None  # Requirements to obtain
    examine: str = None  # Examine text
    dialogue: List[str] = None  # Pet dialogue options
    
    def __post_init__(self):
        """Initialize default values."""
        if self.requirements is None:
            self.requirements = {}
        if self.dialogue is None:
            self.dialogue = []

@dataclass
class Pet:
    """Represents an obtained pet."""
    data: PetData
    obtained_at: int  # Game tick when obtained
    following: bool = True  # Whether pet is following
    insured: bool = False  # Whether pet is insured
    lost: bool = False  # Whether pet is lost
    position: Optional[Position] = None  # Current position if following

class PetManager:
    """Manages pets and their mechanics."""
    
    # Constants from OSRS
    INSURANCE_COST = 500000  # GP to insure a pet
    RECLAIM_COST = 1000000  # GP to reclaim a lost pet
    FOLLOW_DISTANCE = 3  # Tiles behind player
    UPDATE_INTERVAL = 2  # Ticks between position updates
    
    def __init__(self, game_tick: GameTick):
        """Initialize pet manager.
        
        Args:
            game_tick: GameTick system instance
        """
        self.game_tick = game_tick
        self.pets: Dict[str, PetData] = {}  # All available pets
        self.player_pets: Dict[int, Dict[str, Pet]] = {}  # player_id: {pet_id: pet}
        self.active_pets: Dict[int, str] = {}  # player_id: active_pet_id
        
        # Register pet tick task
        self.game_tick.register_task(
            "pet_update",
            self._pet_tick,
            TickPriority.WORLD
        )
        
        # Initialize pet data
        self._initialize_pets()
        
    def _initialize_pets(self):
        """Initialize all pet data."""
        # Skilling pets
        self.pets["rock_golem"] = PetData(
            id="rock_golem",
            name="Rock Golem",
            source=PetSource.SKILLING,
            base_chance=1/741600,  # At level 1
            level_scaling=True,
            examine="A rocky companion.",
            dialogue=[
                "Ready to mine?",
                "Found any good rocks lately?"
            ]
        )
        
        self.pets["beaver"] = PetData(
            id="beaver",
            name="Beaver",
            source=PetSource.SKILLING,
            base_chance=1/741600,
            level_scaling=True,
            examine="A wood-loving companion.",
            dialogue=[
                "How much wood could a woodchuck chuck?",
                "Nice trees around here!"
            ]
        )
        
        # Boss pets
        self.pets["prince_black_dragon"] = PetData(
            id="prince_black_dragon",
            name="Prince Black Dragon",
            source=PetSource.BOSS,
            base_chance=1/3000,
            level_scaling=False,
            threshold=None,
            examine="The offspring of the King Black Dragon.",
            dialogue=[
                "Rawr!",
                "When do I get to be king?"
            ]
        )
        
        # Add more pets...
        
    async def _pet_tick(self):
        """Process pet updates for current game tick."""
        current_tick = self.game_tick.get_tick_count()
        
        # Update following pets every UPDATE_INTERVAL ticks
        if current_tick % self.UPDATE_INTERVAL == 0:
            await self._update_pet_positions()
            
    async def _update_pet_positions(self):
        """Update positions of following pets."""
        # This would integrate with the movement system
        # to update pet positions based on player movement
        pass
        
    def roll_for_pet(self,
                     player_id: int,
                     pet_id: str,
                     skill_level: Optional[int] = None,
                     kill_count: Optional[int] = None) -> bool:
        """Roll for a chance at obtaining a pet.
        
        Args:
            player_id: Player's ID
            pet_id: Pet to roll for
            skill_level: Optional skill level for skilling pets
            kill_count: Optional kill count for boss pets
            
        Returns:
            True if pet should be obtained
        """
        if pet_id not in self.pets:
            return False
            
        # Check if player already has pet
        if self.has_pet(player_id, pet_id):
            return False
            
        pet = self.pets[pet_id]
        chance = pet.base_chance
        
        # Apply level scaling for skilling pets
        if pet.level_scaling and skill_level is not None:
            chance = self._scale_chance_by_level(chance, skill_level)
            
        # Apply threshold for boss pets
        if pet.threshold and kill_count is not None:
            chance = self._apply_threshold(chance, kill_count, pet.threshold)
            
        return random.random() < chance
        
    def _scale_chance_by_level(self, base_chance: float, level: int) -> float:
        """Scale pet chance based on skill level.
        
        Args:
            base_chance: Base chance at level 1
            level: Current skill level
            
        Returns:
            Scaled chance
        """
        # OSRS formula for scaling pet chances
        if level >= 99:
            return base_chance * 15
        else:
            return base_chance * (level / 99.0) * 15
            
    def _apply_threshold(self,
                        base_chance: float,
                        kill_count: int,
                        threshold: int) -> float:
        """Apply threshold system to pet chance.
        
        Args:
            base_chance: Base drop chance
            kill_count: Current kill count
            threshold: Threshold for improved rates
            
        Returns:
            Modified chance
        """
        if kill_count < threshold:
            return base_chance
            
        # Each threshold reached improves chance
        thresholds_passed = kill_count // threshold
        return base_chance * (1 + thresholds_passed)
        
    def add_pet(self,
                player_id: int,
                pet_id: str,
                auto_insure: bool = False) -> bool:
        """Add a pet to a player's collection.
        
        Args:
            player_id: Player's ID
            pet_id: Pet to add
            auto_insure: Whether to automatically insure
            
        Returns:
            True if pet was added
        """
        if pet_id not in self.pets:
            return False
            
        if player_id not in self.player_pets:
            self.player_pets[player_id] = {}
            
        # Don't add if already owned
        if pet_id in self.player_pets[player_id]:
            return False
            
        # Create pet instance
        pet = Pet(
            data=self.pets[pet_id],
            obtained_at=self.game_tick.get_tick_count(),
            insured=auto_insure
        )
        
        self.player_pets[player_id][pet_id] = pet
        
        # Set as active pet if no other active pet
        if player_id not in self.active_pets:
            self.active_pets[player_id] = pet_id
            
        return True
        
    def has_pet(self, player_id: int, pet_id: str) -> bool:
        """Check if player has a pet.
        
        Args:
            player_id: Player's ID
            pet_id: Pet to check
            
        Returns:
            True if player has pet
        """
        return (
            player_id in self.player_pets and
            pet_id in self.player_pets[player_id] and
            not self.player_pets[player_id][pet_id].lost
        )
        
    def insure_pet(self, player_id: int, pet_id: str) -> bool:
        """Insure a pet.
        
        Args:
            player_id: Player's ID
            pet_id: Pet to insure
            
        Returns:
            True if pet was insured
        """
        if not self.has_pet(player_id, pet_id):
            return False
            
        pet = self.player_pets[player_id][pet_id]
        if pet.insured:
            return False
            
        pet.insured = True
        return True
        
    def lose_pet(self, player_id: int, pet_id: str) -> bool:
        """Mark a pet as lost.
        
        Args:
            player_id: Player's ID
            pet_id: Pet that was lost
            
        Returns:
            True if pet was marked as lost
        """
        if not self.has_pet(player_id, pet_id):
            return False
            
        pet = self.player_pets[player_id][pet_id]
        pet.lost = True
        
        # Remove from active pet if active
        if self.active_pets.get(player_id) == pet_id:
            self.active_pets.pop(player_id)
            
        return True
        
    def reclaim_pet(self, player_id: int, pet_id: str) -> bool:
        """Reclaim a lost pet.
        
        Args:
            player_id: Player's ID
            pet_id: Pet to reclaim
            
        Returns:
            True if pet was reclaimed
        """
        if player_id not in self.player_pets:
            return False
            
        pet = self.player_pets[player_id].get(pet_id)
        if not pet or not pet.lost:
            return False
            
        # Can only reclaim insured pets
        if not pet.insured:
            return False
            
        pet.lost = False
        return True
        
    def set_active_pet(self,
                      player_id: int,
                      pet_id: Optional[str] = None) -> bool:
        """Set or remove active following pet.
        
        Args:
            player_id: Player's ID
            pet_id: Pet to set active, None to remove
            
        Returns:
            True if pet was set/removed
        """
        # Remove active pet
        if pet_id is None:
            self.active_pets.pop(player_id, None)
            return True
            
        # Set new active pet
        if self.has_pet(player_id, pet_id):
            self.active_pets[player_id] = pet_id
            return True
            
        return False
        
    def get_active_pet(self, player_id: int) -> Optional[Pet]:
        """Get player's active pet.
        
        Args:
            player_id: Player's ID
            
        Returns:
            Active pet if any
        """
        pet_id = self.active_pets.get(player_id)
        if pet_id:
            return self.player_pets[player_id].get(pet_id)
        return None
        
    def get_player_pets(self, player_id: int) -> List[Pet]:
        """Get all pets owned by player.
        
        Args:
            player_id: Player's ID
            
        Returns:
            List of owned pets
        """
        if player_id not in self.player_pets:
            return []
            
        return [
            pet for pet in self.player_pets[player_id].values()
            if not pet.lost
        ]
        
    def get_lost_pets(self, player_id: int) -> List[Pet]:
        """Get player's lost pets.
        
        Args:
            player_id: Player's ID
            
        Returns:
            List of lost pets
        """
        if player_id not in self.player_pets:
            return []
            
        return [
            pet for pet in self.player_pets[player_id].values()
            if pet.lost
        ]
        
    def get_pet_count(self, player_id: int) -> int:
        """Get number of pets owned by player.
        
        Args:
            player_id: Player's ID
            
        Returns:
            Number of pets
        """
        return len(self.get_player_pets(player_id))
        
    def get_random_dialogue(self, pet_id: str) -> Optional[str]:
        """Get random dialogue for a pet.
        
        Args:
            pet_id: Pet identifier
            
        Returns:
            Random dialogue line if any
        """
        pet = self.pets.get(pet_id)
        if not pet or not pet.dialogue:
            return None
            
        return random.choice(pet.dialogue) 