"""Pet service managing pet data and operations.

This service handles all pet-related functionality including:
- Pet creation and customization
- Stats and inventory management 
- Experience and leveling
- Battle participation tracking
"""

from typing import Dict, List, Optional
import logging
from src.pets.models import Pet, PetType, PetMove, StatusEffect

logger = logging.getLogger(__name__)


class PetServiceError(Exception):
    """Base class for pet service errors."""


class PetNotFoundError(PetServiceError):
    """Raised when a pet cannot be found."""


class MaxPetsExceededError(PetServiceError):
    """Raised when trying to add pets beyond the limit."""


class PetService:
    """Core service for pet management."""

    def __init__(self) -> None:
        """Initialize the pet service."""
        self._pets: Dict[int, List[Pet]] = {}  # user_id -> pets
        self._active_pets: Dict[int, int] = {}  # user_id -> active_pet_index
        self._max_pets = 3

    async def create_pet(
        self,
        owner_id: int,
        name: str,
        element: PetType
    ) -> Pet:
        """Create a new pet for a user.

        Args:
            owner_id: Discord ID of pet owner
            name: Name for the new pet
            element: Pet's element type

        Returns:
            The newly created pet
        Raises:
            MaxPetsExceededError: If user has max number of pets
        """
        # Check pet limit
        if len(self._pets.get(owner_id, [])) >= self._max_pets:
            raise MaxPetsExceededError(
                f"Cannot have more than {self._max_pets} pets"
            )

        # Generate starter moves based on element
        moves = self._generate_starter_moves(element)

        # Create pet
        pet = Pet(
            name=name,
            element=element,
            moves=moves
        )

        # Add to storage
        if owner_id not in self._pets:
            self._pets[owner_id] = []
        self._pets[owner_id].append(pet)

        # Set as active if first pet
        if len(self._pets[owner_id]) == 1:
            self._active_pets[owner_id] = 0

        return pet

    def _generate_starter_moves(self, element: PetType) -> List[PetMove]:
        """Generate starter moves for a pet based on its element."""
        moves = []

        # Basic attack
        moves.append(PetMove(
            name="Tackle",
            damage=10,
            element=element,
            cooldown=0,
            emoji="💥"
        ))

        # Element-specific move
        if element == PetType.FIRE:
            moves.append(PetMove(
                name="Ember",
                damage=15,
                element=element,
                cooldown=2,
                emoji="🔥",
                status_effect=StatusEffect.BURN,
                status_chance=20
            ))
        elif element == PetType.WATER:
            moves.append(PetMove(
                name="Water Gun",
                damage=15,
                element=element,
                cooldown=2,
                emoji="💧"
            ))
        elif element == PetType.EARTH:
            moves.append(PetMove(
                name="Rock Throw",
                damage=20,
                element=element,
                cooldown=3,
                emoji="🪨"
            ))
        elif element == PetType.AIR:
            moves.append(PetMove(
                name="Gust",
                damage=12,
                element=element,
                cooldown=1,
                emoji="💨"
            ))
        elif element == PetType.LIGHT:
            moves.append(PetMove(
                name="Flash",
                damage=15,
                element=element,
                cooldown=2,
                emoji="✨",
                status_effect=StatusEffect.PARALYZE,
                status_chance=15
            ))
        elif element == PetType.DARK:
            moves.append(PetMove(
                name="Shadow Strike",
                damage=18,
                element=element,
                cooldown=2,
                emoji="🌑",
                status_effect=StatusEffect.SLEEP,
                status_chance=10
            ))

        return moves

    async def get_pet(
        self,
        owner_id: int,
        index: Optional[int] = None
    ) -> Pet:
        """Get a user's pet by index.

        Args:
            owner_id: Discord ID of pet owner
            index: Pet index to get, None for active pet

        Returns:
            The requested pet
        Raises:
            PetNotFoundError: If pet doesn't exist
        """
        if owner_id not in self._pets:
            raise PetNotFoundError("User has no pets")

        if index is None:
            if owner_id not in self._active_pets:
                raise PetNotFoundError("No active pet set")
            index = self._active_pets[owner_id]

        try:
            return self._pets[owner_id][index]
        except IndexError:
            raise PetNotFoundError(f"No pet at index {index}")

    async def set_active_pet(
        self,
        owner_id: int,
        index: int
    ) -> Pet:
        """Set a user's active pet.

        Args:
            owner_id: Discord ID of pet owner
            index: Index of pet to set active

        Returns:
            The newly active pet
        Raises:
            PetNotFoundError: If pet doesn't exist
        """
        if owner_id not in self._pets:
            raise PetNotFoundError("User has no pets")

        try:
            pet = self._pets[owner_id][index]
            self._active_pets[owner_id] = index
            return pet
        except IndexError:
            raise PetNotFoundError(f"No pet at index {index}")

    async def award_experience(
        self,
        owner_id: int,
        pet_index: Optional[int],
        amount: int,
        source: str
    ) -> Optional[int]:
        """Award experience to a pet.

        Args:
            owner_id: Discord ID of pet owner
            pet_index: Index of pet to award XP, None for active
            amount: Amount of XP to award
            source: What triggered the XP gain

        Returns:
            New level if pet leveled up, None otherwise
        Raises:
            PetNotFoundError: If pet doesn't exist
        """
        pet = await self.get_pet(owner_id, pet_index)

        logger.info(
            "Awarding %s XP to %s (owner: %s) from %s",
            amount, pet.name, owner_id, source
        )

        if pet.add_experience(amount):
            logger.info(f"{pet.name} leveled up to {pet.level}!")
            return pet.level

        return None

    async def get_user_pets(self, owner_id: int) -> List[Pet]:
        """Get all pets owned by a user.

        Args:
            owner_id: Discord ID of pet owner

        Returns:
            List of user's pets
        """
        return self._pets.get(owner_id, [])