"""Minigame manager for handling minigame mechanics and rewards."""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from .game_tick import GameTick, TickPriority
from .skill_manager import SkillType
from .movement import Position

class MinigameType(Enum):
    """Types of minigames."""
    COMBAT = "combat"  # Castle Wars, Fight Caves, etc.
    SKILLING = "skilling"  # Wintertodt, Tempoross, etc.
    HYBRID = "hybrid"  # Barbarian Assault, Pest Control, etc.
    PUZZLE = "puzzle"  # Barrows, etc.

class MinigameStatus(Enum):
    """Minigame status."""
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class MinigameRequirement:
    """Requirement to participate in a minigame."""
    type: str  # skill, quest, item, combat, etc.
    id: str  # requirement identifier
    value: int  # required value/level
    description: str

@dataclass
class MinigameReward:
    """Reward from a minigame."""
    type: str  # points, xp, item, etc.
    id: str  # reward identifier
    value: int  # reward amount
    chance: float = 1.0  # chance to receive (0-1)

@dataclass
class MinigameInstance:
    """Instance of a running minigame."""
    id: str
    minigame_id: str
    players: Set[int]  # player IDs
    status: MinigameStatus
    start_tick: int
    points: Dict[int, int] = None  # player_id: points
    waves_completed: int = 0
    custom_data: Dict = None  # minigame-specific data
    
    def __post_init__(self):
        """Initialize default values."""
        if self.points is None:
            self.points = {}
        if self.custom_data is None:
            self.custom_data = {}

@dataclass
class Minigame:
    """Represents a minigame."""
    id: str
    name: str
    type: MinigameType
    description: str
    requirements: List[MinigameRequirement]
    rewards: List[MinigameReward]
    min_players: int = 1
    max_players: int = 1
    points_per_round: int = 0
    is_members: bool = False
    location: Position = None

class MinigameManager:
    """Manages minigame mechanics and rewards."""
    
    def __init__(self, game_tick: GameTick):
        """Initialize minigame manager.
        
        Args:
            game_tick: GameTick system instance
        """
        self.game_tick = game_tick
        self.minigames: Dict[str, Minigame] = {}
        self.active_instances: Dict[str, MinigameInstance] = {}
        self.player_instances: Dict[int, str] = {}  # player_id: instance_id
        self.player_points: Dict[int, Dict[str, int]] = {}  # player_id: {minigame_id: total_points}
        
        # Register minigame tick task
        self.game_tick.register_task(
            "minigame_update",
            self._minigame_tick,
            TickPriority.WORLD
        )
        
    async def _minigame_tick(self):
        """Process minigame updates for current game tick."""
        current_tick = self.game_tick.get_tick_count()
        
        # Process active instances
        for instance_id, instance in list(self.active_instances.items()):
            if instance.status == MinigameStatus.IN_PROGRESS:
                await self._process_instance(instance_id, current_tick)
                
    async def _process_instance(self, instance_id: str, current_tick: int):
        """Process a minigame instance.
        
        Args:
            instance_id: Instance identifier
            current_tick: Current game tick
        """
        instance = self.active_instances[instance_id]
        minigame = self.minigames[instance.minigame_id]
        
        # This would handle minigame-specific logic
        # For example:
        if minigame.type == MinigameType.COMBAT:
            await self._process_combat_minigame(instance, current_tick)
        elif minigame.type == MinigameType.SKILLING:
            await self._process_skilling_minigame(instance, current_tick)
        elif minigame.type == MinigameType.HYBRID:
            await self._process_hybrid_minigame(instance, current_tick)
        elif minigame.type == MinigameType.PUZZLE:
            await self._process_puzzle_minigame(instance, current_tick)
            
    async def _process_combat_minigame(self, instance: MinigameInstance, current_tick: int):
        """Process combat minigame mechanics.
        
        Args:
            instance: Minigame instance
            current_tick: Current game tick
        """
        # Handle combat minigame logic
        # For example: Fight Caves wave spawns, Castle Wars mechanics, etc.
        pass
        
    async def _process_skilling_minigame(self, instance: MinigameInstance, current_tick: int):
        """Process skilling minigame mechanics.
        
        Args:
            instance: Minigame instance
            current_tick: Current game tick
        """
        # Handle skilling minigame logic
        # For example: Wintertodt energy, Tempoross intensity, etc.
        pass
        
    async def _process_hybrid_minigame(self, instance: MinigameInstance, current_tick: int):
        """Process hybrid minigame mechanics.
        
        Args:
            instance: Minigame instance
            current_tick: Current game tick
        """
        # Handle hybrid minigame logic
        # For example: Barbarian Assault roles, Pest Control portals, etc.
        pass
        
    async def _process_puzzle_minigame(self, instance: MinigameInstance, current_tick: int):
        """Process puzzle minigame mechanics.
        
        Args:
            instance: Minigame instance
            current_tick: Current game tick
        """
        # Handle puzzle minigame logic
        # For example: Barrows tunnels, puzzle room states, etc.
        pass
        
    def add_minigame(self, minigame: Minigame):
        """Add a minigame to the manager.
        
        Args:
            minigame: Minigame to add
        """
        self.minigames[minigame.id] = minigame
        
    def get_minigame(self, minigame_id: str) -> Optional[Minigame]:
        """Get minigame by ID.
        
        Args:
            minigame_id: Minigame identifier
            
        Returns:
            Minigame if found, None otherwise
        """
        return self.minigames.get(minigame_id)
        
    def can_join_minigame(self,
                         player_id: int,
                         minigame_id: str,
                         player_stats: Dict[SkillType, int],
                         completed_quests: Set[str],
                         inventory: Dict[str, int],
                         is_member: bool) -> Tuple[bool, Optional[str]]:
        """Check if player can join a minigame.
        
        Args:
            player_id: Player's ID
            minigame_id: Minigame to check
            player_stats: Player's skill levels
            completed_quests: Set of completed quest IDs
            inventory: Player's inventory
            is_member: Whether player is a member
            
        Returns:
            Tuple of (can join, reason if cannot)
        """
        minigame = self.get_minigame(minigame_id)
        if not minigame:
            return (False, "Minigame not found")
            
        # Check membership
        if minigame.is_members and not is_member:
            return (False, "Members only minigame")
            
        # Check if already in a minigame
        if player_id in self.player_instances:
            return (False, "Already in a minigame")
            
        # Check requirements
        for req in minigame.requirements:
            if req.type == "skill":
                if player_stats.get(req.id, 1) < req.value:
                    return (False, f"Requires {req.id} level {req.value}")
            elif req.type == "quest":
                if req.id not in completed_quests:
                    return (False, f"Requires quest: {req.id}")
            elif req.type == "item":
                if inventory.get(req.id, 0) < req.value:
                    return (False, "Missing required items")
            elif req.type == "combat":
                combat_level = self._calculate_combat_level(player_stats)
                if combat_level < req.value:
                    return (False, f"Requires combat level {req.value}")
                    
        return (True, None)
        
    def start_minigame(self,
                      minigame_id: str,
                      players: Set[int]) -> Optional[str]:
        """Start a minigame instance.
        
        Args:
            minigame_id: Minigame to start
            players: Set of player IDs
            
        Returns:
            Instance ID if started, None otherwise
        """
        minigame = self.get_minigame(minigame_id)
        if not minigame:
            return None
            
        # Check player count
        if not (minigame.min_players <= len(players) <= minigame.max_players):
            return None
            
        # Create instance
        instance_id = f"{minigame_id}_{self.game_tick.get_tick_count()}"
        instance = MinigameInstance(
            id=instance_id,
            minigame_id=minigame_id,
            players=players,
            status=MinigameStatus.IN_PROGRESS,
            start_tick=self.game_tick.get_tick_count()
        )
        
        # Add instance
        self.active_instances[instance_id] = instance
        
        # Update player instances
        for player_id in players:
            self.player_instances[player_id] = instance_id
            
        return instance_id
        
    def end_minigame(self,
                    instance_id: str,
                    status: MinigameStatus = MinigameStatus.COMPLETED):
        """End a minigame instance.
        
        Args:
            instance_id: Instance to end
            status: Final status
        """
        if instance_id not in self.active_instances:
            return
            
        instance = self.active_instances[instance_id]
        instance.status = status
        
        # Award points and rewards
        if status == MinigameStatus.COMPLETED:
            minigame = self.minigames[instance.minigame_id]
            for player_id in instance.players:
                points = instance.points.get(player_id, 0)
                self._award_points(player_id, minigame.id, points)
                self._award_rewards(player_id, minigame, points)
                
        # Clean up
        for player_id in instance.players:
            self.player_instances.pop(player_id, None)
            
        self.active_instances.pop(instance_id)
        
    def _award_points(self,
                     player_id: int,
                     minigame_id: str,
                     points: int):
        """Award minigame points to a player.
        
        Args:
            player_id: Player's ID
            minigame_id: Minigame identifier
            points: Points to award
        """
        if player_id not in self.player_points:
            self.player_points[player_id] = {}
            
        current = self.player_points[player_id].get(minigame_id, 0)
        self.player_points[player_id][minigame_id] = current + points
        
    def _award_rewards(self,
                      player_id: int,
                      minigame: Minigame,
                      points: int):
        """Award minigame rewards to a player.
        
        Args:
            player_id: Player's ID
            minigame: Minigame completed
            points: Points earned
        """
        for reward in minigame.rewards:
            if random.random() < reward.chance:
                # Scale reward by points if applicable
                value = reward.value
                if reward.type == "points":
                    value = math.floor(value * (points / minigame.points_per_round))
                    
                # Grant reward (would integrate with other systems)
                pass
                
    def get_player_points(self,
                         player_id: int,
                         minigame_id: Optional[str] = None) -> int:
        """Get player's minigame points.
        
        Args:
            player_id: Player's ID
            minigame_id: Optional specific minigame
            
        Returns:
            Total points (or points for specific minigame)
        """
        if player_id not in self.player_points:
            return 0
            
        if minigame_id:
            return self.player_points[player_id].get(minigame_id, 0)
            
        return sum(self.player_points[player_id].values())
        
    def get_player_instance(self, player_id: int) -> Optional[MinigameInstance]:
        """Get player's current minigame instance.
        
        Args:
            player_id: Player's ID
            
        Returns:
            Current instance if in minigame
        """
        instance_id = self.player_instances.get(player_id)
        if instance_id:
            return self.active_instances.get(instance_id)
        return None
        
    def _calculate_combat_level(self, stats: Dict[SkillType, int]) -> int:
        """Calculate combat level from stats.
        
        Args:
            stats: Player's skill levels
            
        Returns:
            Combat level
        """
        base = math.floor(
            (stats.get(SkillType.DEFENCE, 1) +
             stats.get(SkillType.HITPOINTS, 10) +
             math.floor(stats.get(SkillType.PRAYER, 1) / 2)) / 4
        )
        
        melee = math.floor(13/40 * (
            stats.get(SkillType.ATTACK, 1) +
            stats.get(SkillType.STRENGTH, 1)
        ))
        
        ranged = math.floor(13/40 * math.floor(
            3 * stats.get(SkillType.RANGED, 1) / 2
        ))
        
        magic = math.floor(13/40 * math.floor(
            3 * stats.get(SkillType.MAGIC, 1) / 2
        ))
        
        return base + max(melee, ranged, magic) 