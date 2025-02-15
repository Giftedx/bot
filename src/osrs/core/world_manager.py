"""OSRS world system implementation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import logging

from ..models import Player


logger = logging.getLogger('WorldManager')


@dataclass
class World:
    """Represents an OSRS world."""
    id: int
    name: str
    description: str
    type: str  # regular, pvp, skill, minigame
    region: str  # us, uk, de, au
    members_only: bool = False
    pvp: bool = False
    skill_total: int = 0
    players: Set[int] = field(default_factory=set)  # Set of player IDs
    max_players: int = 2000


class WorldManager:
    """Manages OSRS worlds."""
    
    def __init__(self):
        self.worlds: Dict[int, World] = self._initialize_worlds()
    
    def _initialize_worlds(self) -> Dict[int, World]:
        """Initialize default worlds."""
        worlds = {}
        
        # Free-to-play worlds
        worlds[301] = World(
            id=301,
            name="301",
            description="Free-to-play world",
            type="regular",
            region="us"
        )
        
        worlds[308] = World(
            id=308,
            name="308",
            description="Free-to-play PvP world",
            type="pvp",
            region="us",
            pvp=True
        )
        
        # Members worlds
        worlds[302] = World(
            id=302,
            name="302",
            description="Members world",
            type="regular",
            region="us",
            members_only=True
        )
        
        worlds[325] = World(
            id=325,
            name="325",
            description="High Risk PvP world",
            type="pvp",
            region="uk",
            members_only=True,
            pvp=True
        )
        
        worlds[349] = World(
            id=349,
            name="349",
            description="Skill Total (1500)",
            type="skill",
            region="uk",
            members_only=True,
            skill_total=1500
        )
        
        worlds[361] = World(
            id=361,
            name="361",
            description="High Risk PvP world",
            type="pvp",
            region="au",
            members_only=True,
            pvp=True
        )
        
        return worlds
    
    def get_world(self, world_id: int) -> Optional[World]:
        """Get a world by its ID."""
        return self.worlds.get(world_id)
    
    def get_player_world(self, player: Player) -> Optional[World]:
        """Get the world a player is in."""
        return self.worlds.get(player.current_world)
    
    def join_world(self, player: Player, world_id: int) -> bool:
        """
        Move a player to a different world.
        Returns True if successful.
        """
        # Check if world exists
        world = self.worlds.get(world_id)
        if not world:
            return False
        
        # Check world requirements
        if world.members_only and not self._is_member(player):
            return False
        
        if world.skill_total > 0 and not self._meets_skill_total(player, world.skill_total):
            return False
        
        # Remove from current world
        current_world = self.worlds.get(player.current_world)
        if current_world:
            current_world.players.discard(player.id)
        
        # Check world capacity
        if len(world.players) >= world.max_players:
            return False
        
        # Add to new world
        world.players.add(player.id)
        player.current_world = world_id
        
        return True
    
    def leave_world(self, player: Player) -> None:
        """Remove a player from their current world."""
        world = self.worlds.get(player.current_world)
        if world:
            world.players.discard(player.id)
    
    def are_players_in_same_world(self, player1: Player, player2: Player) -> bool:
        """Check if two players are in the same world."""
        return player1.current_world == player2.current_world
    
    def is_pvp_enabled(self, player: Player) -> bool:
        """Check if a player is in a PvP world."""
        world = self.worlds.get(player.current_world)
        return world is not None and world.pvp
    
    def get_world_players(self, world_id: int) -> Set[int]:
        """Get all players in a world."""
        world = self.worlds.get(world_id)
        return world.players if world else set()
    
    def get_available_worlds(self, player: Player) -> List[World]:
        """Get all worlds available to a player."""
        is_member = self._is_member(player)
        total_level = self._get_total_level(player)
        
        return [
            world for world in self.worlds.values()
            if (not world.members_only or is_member)
            and (world.skill_total == 0 or total_level >= world.skill_total)
        ]
    
    def _is_member(self, player: Player) -> bool:
        """Check if a player is a member."""
        # TODO: Implement membership check
        return True
    
    def _meets_skill_total(self, player: Player, required_total: int) -> bool:
        """Check if a player meets the total level requirement."""
        return self._get_total_level(player) >= required_total
    
    def _get_total_level(self, player: Player) -> int:
        """Calculate a player's total level."""
        return sum(skill.level for skill in player.skills.values())
