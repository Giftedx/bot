"""Test OSRS world management system."""
import pytest
from datetime import datetime
from typing import Dict, Optional

from src.osrs.core.world_manager import World, WorldManager
from src.osrs.models import Player, SkillType, Skill


@pytest.fixture
def world() -> World:
    """Create a test world."""
    return World(
        id=301,
        name="Test World 301",
        type="normal",
        region="us"
    )


@pytest.fixture
def world_manager() -> WorldManager:
    """Create a test world manager."""
    return WorldManager()


@pytest.fixture
def player() -> Player:
    """Create a test player."""
    skills: Dict[SkillType, Skill] = {
        skill_type: Skill(type=skill_type)
        for skill_type in SkillType
    }
    # Set Hitpoints to 10
    skills[SkillType.HITPOINTS].level = 10
    
    return Player(
        id=1,
        name="TestPlayer",
        skills=skills
    )


@pytest.fixture
def high_level_player() -> Player:
    """Create a high level test player."""
    skills: Dict[SkillType, Skill] = {
        skill_type: Skill(type=skill_type, level=70)
        for skill_type in SkillType
    }
    return Player(
        id=2,
        name="HighLevelPlayer",
        skills=skills
    )


def test_world_creation(world: World) -> None:
    """Test world initialization."""
    assert world.id == 301
    assert world.name == "Test World 301"
    assert world.type == "normal"
    assert world.region == "us"
    assert world.player_count == 0
    assert not world.is_full


def test_world_serialization(world: World) -> None:
    """Test world serialization and deserialization."""
    # Add a player
    world.players.add(1)
    world.last_update = datetime.utcnow()
    
    # Convert to dict
    world_dict = world.to_dict()
    
    # Create new world from dict
    new_world = World.from_dict(world_dict)
    
    assert new_world.id == world.id
    assert new_world.name == world.name
    assert new_world.type == world.type
    assert new_world.region == world.region
    assert new_world.players == world.players
    assert new_world.max_players == world.max_players
    assert new_world.creation_time == world.creation_time
    assert new_world.last_update == world.last_update


def test_world_manager_initialization(world_manager: WorldManager) -> None:
    """Test world manager setup."""
    # Should have default worlds
    assert len(world_manager.worlds) > 0
    
    # Should have main worlds
    assert world_manager.get_world(301) is not None
    assert world_manager.get_world(302) is not None
    
    # Should have PvP world
    pvp_worlds = world_manager.get_available_worlds(type_filter="pvp")
    assert len(pvp_worlds) > 0
    
    # Should have skill total worlds
    skill_worlds = world_manager.get_available_worlds(
        type_filter="skill_total"
    )
    assert len(skill_worlds) > 0


def test_world_joining(
    world_manager: WorldManager,
    player: Player
) -> None:
    """Test player joining worlds."""
    # Join normal world
    assert world_manager.join_world(player, 301)
    
    # Should be in world 301
    current_world = world_manager.get_player_world(player)
    assert current_world is not None
    assert current_world.id == 301
    
    # Join another world
    assert world_manager.join_world(player, 302)
    
    # Should be in world 302 and not 301
    current_world = world_manager.get_player_world(player)
    assert current_world is not None
    assert current_world.id == 302
    
    # Verify player is not in world 301
    world_301: Optional[World] = world_manager.get_world(301)
    assert world_301 is not None, "World 301 should exist"
    assert player.id not in world_301.players


def test_skill_total_requirements(
    world_manager: WorldManager,
    player: Player,
    high_level_player: Player
) -> None:
    """Test skill total world requirements."""
    # Get 1250+ world
    skill_world = next(
        w for w in world_manager.worlds.values()
        if "1250+" in w.name
    )
    
    # Low level player should not be able to join
    assert not world_manager.join_world(player, skill_world.id)
    
    # High level player should be able to join
    assert world_manager.join_world(high_level_player, skill_world.id)


def test_world_action_validation(
    world_manager: WorldManager,
    player: Player
) -> None:
    """Test world action validation."""
    # Join PvP world
    pvp_world = next(
        w for w in world_manager.worlds.values()
        if w.type == "pvp"
    )
    assert world_manager.join_world(player, pvp_world.id)
    
    # Trading should be restricted in PvP worlds
    assert not world_manager.validate_world_action(player, "trade")
    
    # Join normal world
    normal_world = next(
        w for w in world_manager.worlds.values()
        if w.type == "normal"
    )
    assert world_manager.join_world(player, normal_world.id)
    
    # Trading should be allowed in normal worlds
    assert world_manager.validate_world_action(player, "trade")


def test_deadman_restrictions(
    world_manager: WorldManager,
    player: Player
) -> None:
    """Test deadman mode restrictions."""
    # Join deadman world
    deadman_world = next(
        w for w in world_manager.worlds.values()
        if w.type == "deadman"
    )
    assert world_manager.join_world(player, deadman_world.id)
    
    # Get a normal world
    normal_world = next(
        w for w in world_manager.worlds.values()
        if w.type == "normal"
    )
    
    # Should not be able to interact with normal worlds
    assert not world_manager.validate_world_action(
        player,
        "trade",
        normal_world
    )


def test_high_risk_restrictions(
    world_manager: WorldManager,
    player: Player
) -> None:
    """Test high risk world restrictions."""
    # Join high risk world
    high_risk_world = next(
        w for w in world_manager.worlds.values()
        if w.type == "high_risk"
    )
    assert world_manager.join_world(player, high_risk_world.id)
    
    # Protect item prayer should be restricted
    assert not world_manager.validate_world_action(player, "protect_item")
