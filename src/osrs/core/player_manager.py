"""Player manager for handling player state and actions."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

from .game_tick import GameTick, TickPriority
from .movement import Position, MovementSystem
from .skill_manager import SkillType


class PlayerState(Enum):
    """Player states."""

    IDLE = "idle"
    MOVING = "moving"
    GATHERING = "gathering"
    COMBAT = "combat"
    BANKING = "banking"


@dataclass
class Equipment:
    """Player equipment."""

    head: Optional[int] = None
    cape: Optional[int] = None
    neck: Optional[int] = None
    weapon: Optional[int] = None
    body: Optional[int] = None
    shield: Optional[int] = None
    legs: Optional[int] = None
    hands: Optional[int] = None
    feet: Optional[int] = None
    ring: Optional[int] = None
    ammo: Optional[int] = None


@dataclass
class Player:
    """Represents a player in the game."""

    id: int
    username: str
    position: Position
    state: PlayerState = PlayerState.IDLE
    equipment: Equipment = Equipment()
    skills: Dict[SkillType, int] = None  # skill: level
    experience: Dict[SkillType, float] = None  # skill: xp
    inventory: Dict[int, int] = None  # item_id: quantity
    bank: Dict[int, int] = None  # item_id: quantity
    is_member: bool = False
    run_energy: float = 100.0
    weight: float = 0.0

    def __post_init__(self):
        """Initialize default values."""
        if self.skills is None:
            self.skills = {skill: 1 for skill in SkillType}
            self.skills[SkillType.HITPOINTS] = 10

        if self.experience is None:
            self.experience = {skill: 0.0 for skill in SkillType}
            self.experience[SkillType.HITPOINTS] = 1154  # Level 10

        if self.inventory is None:
            self.inventory = {}

        if self.bank is None:
            self.bank = {}


class PlayerManager:
    """Manages player state and actions."""

    def __init__(self, game_tick: GameTick, movement_system: MovementSystem, database_manager):
        """Initialize player manager.

        Args:
            game_tick: GameTick system instance
            movement_system: MovementSystem instance
            database_manager: Database manager instance
        """
        self.game_tick = game_tick
        self.movement = movement_system
        self.db = database_manager
        self.players: Dict[int, Player] = {}

        # Register player tick task
        self.game_tick.register_task("player_update", self._player_tick, TickPriority.WORLD)

    async def _player_tick(self):
        """Process player updates for current game tick."""
        for player in self.players.values():
            # Update run energy
            if player.state == PlayerState.MOVING:
                if self.movement.running:
                    player.run_energy = self.movement.update_energy(
                        player.run_energy, player.skills[SkillType.AGILITY], True
                    )
                else:
                    player.run_energy = self.movement.update_energy(
                        player.run_energy, player.skills[SkillType.AGILITY], False
                    )

            # Save player state periodically
            await self._save_player(player)

    async def create_player(self, username: str) -> Player:
        """Create a new player.

        Args:
            username: Player's username

        Returns:
            Created player

        Raises:
            ValueError: If username is taken
        """
        # Check if username exists
        if any(p.username == username for p in self.players.values()):
            raise ValueError("Username already exists")

        # Create in database
        player_id = await self.db.create_player(username)

        # Create player object
        player = Player(
            id=player_id, username=username, position=Position(3222, 3218)  # Lumbridge spawn
        )

        self.players[player_id] = player
        await self._save_player(player)

        return player

    async def load_player(self, player_id: int) -> Optional[Player]:
        """Load a player from database.

        Args:
            player_id: Player's ID

        Returns:
            Loaded player if found
        """
        data = await self.db.get_player(player_id)
        if not data:
            return None

        # Load skills and experience
        stats = await self.db.get_player_stats(player_id)
        skills = {}
        experience = {}
        for stat in stats:
            skill = SkillType(stat["skill"])
            skills[skill] = stat["level"]
            experience[skill] = stat["experience"]

        # Load equipment
        equipment_data = await self.db.get_player_equipment(player_id)
        equipment = Equipment()
        for item in equipment_data:
            setattr(equipment, item["slot"], item["item_id"])

        # Load inventory and bank
        inventory = {
            item["item_id"]: item["quantity"]
            for item in await self.db.get_player_inventory(player_id)
        }

        bank = {
            item["item_id"]: item["quantity"] for item in await self.db.get_player_bank(player_id)
        }

        # Load location
        location = await self.db.get_player_location(player_id)
        position = (
            Position(location["x"], location["y"], location["plane"])
            if location
            else Position(3222, 3218)
        )

        # Create player object
        player = Player(
            id=player_id,
            username=data["username"],
            position=position,
            equipment=equipment,
            skills=skills,
            experience=experience,
            inventory=inventory,
            bank=bank,
            is_member=data["is_member"],
        )

        self.players[player_id] = player
        return player

    async def _save_player(self, player: Player):
        """Save player state to database.

        Args:
            player: Player to save
        """
        # Update basic info
        await self.db.update_player(player.id, is_member=player.is_member)

        # Update stats
        for skill, level in player.skills.items():
            await self.db.update_player_stats(
                player.id, skill.value, level, player.experience[skill]
            )

        # Update equipment
        for slot, item_id in vars(player.equipment).items():
            if item_id is not None:
                await self.db.update_player_equipment(player.id, slot, item_id)

        # Update inventory
        await self.db.update_player_inventory(player.id, player.inventory)

        # Update bank
        await self.db.update_player_bank(player.id, player.bank)

        # Update location
        await self.db.update_player_location(
            player.id, player.position.x, player.position.y, player.position.plane
        )

    def get_player(self, player_id: int) -> Optional[Player]:
        """Get player by ID.

        Args:
            player_id: Player's ID

        Returns:
            Player if found
        """
        return self.players.get(player_id)

    def get_player_by_username(self, username: str) -> Optional[Player]:
        """Get player by username.

        Args:
            username: Player's username

        Returns:
            Player if found
        """
        return next((p for p in self.players.values() if p.username == username), None)

    def update_player_state(self, player_id: int, new_state: PlayerState):
        """Update player's state.

        Args:
            player_id: Player's ID
            new_state: New state
        """
        if player := self.get_player(player_id):
            player.state = new_state

    def get_nearby_players(self, position: Position, max_distance: float) -> List[Player]:
        """Get players within range of a position.

        Args:
            position: Center position
            max_distance: Maximum distance to search

        Returns:
            List of players within range
        """
        return [
            player
            for player in self.players.values()
            if player.position.real_distance_to(position) <= max_distance
        ]

    def can_access_content(
        self,
        player_id: int,
        required_skills: Dict[SkillType, int] = None,
        members_only: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """Check if player can access content.

        Args:
            player_id: Player's ID
            required_skills: Required skill levels
            members_only: Whether content is members-only

        Returns:
            Tuple of (can access, reason if cannot)
        """
        player = self.get_player(player_id)
        if not player:
            return (False, "Player not found")

        if members_only and not player.is_member:
            return (False, "Members only content")

        if required_skills:
            for skill, level in required_skills.items():
                if player.skills.get(skill, 1) < level:
                    return (False, f"Requires {skill.value} level {level}")

        return (True, None)

    def add_experience(self, player_id: int, skill: SkillType, amount: float):
        """Add experience to a skill.

        Args:
            player_id: Player's ID
            skill: Skill to add experience to
            amount: Amount of experience
        """
        if player := self.get_player(player_id):
            current_xp = player.experience[skill]
            new_xp = min(200_000_000, current_xp + amount)
            player.experience[skill] = new_xp

            # Update level if needed
            old_level = player.skills[skill]
            new_level = self._get_level_for_xp(new_xp)

            if new_level > old_level:
                player.skills[skill] = new_level

    def _get_level_for_xp(self, xp: float) -> int:
        """Get level for experience amount.

        Args:
            xp: Experience amount

        Returns:
            Corresponding level
        """
        for level in range(99, 0, -1):
            if xp >= self._get_xp_for_level(level):
                return level
        return 1

    def _get_xp_for_level(self, level: int) -> float:
        """Get experience required for level.

        Args:
            level: Target level

        Returns:
            Required experience
        """
        points = math.floor(level - 1 + 300 * 2 ** ((level - 1) / 7))
        return math.floor(points / 4)
