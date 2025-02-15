"""Tests for the battle system functionality."""functionality."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import discord
from discord.ext import commandsd
from src.core.battle_manager import BattleManager, BattleTypeimport pytest
from cogs.battle_system import BattleCommands
from src.core.battle_manager import BattleManager, BattleState, BattleType
from src.osrs.battle_system import OSRSBattleSystem
from src.pets.battle_system import PetBattleSystemState, BattleType
from src.pokemon.battle_system import PokemonBattleSystemfrom src.osrs.battle_system import OSRSBattleSystem
from src.pets.battle_system import PetBattleSystem
n.battle_system import PokemonBattleSystem
@pytest.fixture
def bot():
    """Create a mock bot instance."""@pytest.fixture
    bot = AsyncMock(spec=commands.Bot)def bot():
    bot.db = AsyncMock() mock bot instance."""
    return botpec=commands.Bot)
 AsyncMock()
@pytest.fixture
def battle_commands(bot):
    """Create a BattleCommands instance."""
    return BattleCommands(bot)st.fixture
def battle_commands(bot):
@pytest.fixture    """Create a BattleCommands instance."""
def ctx():s(bot)
    """Create a mock command context."""
    ctx = AsyncMock(spec=commands.Context)
    ctx.author = Mock(spec=discord.Member)
    ctx.author.id = 123
    ctx.author.name = "TestUser"
    ctx.author.mention = "@TestUser"
    return ctxember)

@pytest.fixturetUser"
def opponent():
    """Create a mock opponent."""n ctx
    opponent = Mock(spec=discord.Member)
    opponent.id = 456
    opponent.bot = False
    opponent.name = "Opponent"
    opponent.mention = "@Opponent"
    return opponent
    opponent.id = 456
@pytest.fixture
def battle_manager():
    return BattleManager()ent.mention = "@Opponent"

@pytest.fixture
def battle_systems():
    return {xture
        BattleType.OSRS: OSRSBattleSystem(),attle_manager():
        BattleType.POKEMON: PokemonBattleSystem(),
        BattleType.PET: PetBattleSystem(),
    }

class TestBattleSystems:
    """Test battle system implementations."""
        BattleType.OSRS: OSRSBattleSystem(),
    @pytest.mark.parametrize("battle_type", list(BattleType))okemonBattleSystem(),
    def test_battle_creation(self, battle_manager, battle_type):eSystem(),
        """Test battle creation for each type."""
        battle = battle_manager.create_battle(
            battle_type=battle_type,
            challenger_id=1,ystems:
            opponent_id=2,tions."""
            initial_data={"test": "data"},
        )
ger, battle_type):
        assert battle.battle_type == battle_type
        assert battle.challenger_id == 1e_manager.create_battle(
        assert battle.opponent_id == 2
        assert not battle.is_finishednger_id=1,
        assert battle.battle_data == {"test": "data"}ponent_id=2,
nitial_data={"test": "data"},
    @pytest.mark.parametrize(
        "battle_type,system_class",
        [battle_type
            (BattleType.OSRS, OSRSBattleSystem),1
            (BattleType.POKEMON, PokemonBattleSystem), 2
            (BattleType.PET, PetBattleSystem),
        ],
    )
    def test_battle_system_initialization(etrize(
        self, battle_systems, battle_type, system_class
    ):
        """Test battle system class initialization."""attleType.OSRS, OSRSBattleSystem),
        system = battle_systems[battle_type]BattleType.POKEMON, PokemonBattleSystem),
        assert isinstance(system, system_class)tBattleSystem),

    @pytest.mark.parametrize(
        "battle_type,move_data",on(
        [_type, system_class
            (
                BattleType.OSRS,s initialization."""
                {ype]
                    "move": "slash",ss)
                    "attacker_stats": {
                        "skills": {"attack": 60, "strength": 55},
                        "equipment_bonus": 10,a",
                        "combat_style": "accurate",
                    },
                    "defender_stats": {"skills": {"defence": 50}, "hitpoints": 50},
                },
            ),
            (  "attacker_stats": {
                BattleType.POKEMON,          "skills": {"attack": 60, "strength": 55},
                {              "equipment_bonus": 10,
                    "move": "tackle",                   "combat_style": "accurate",
                    "attacker_stats": {
                        "level": 20,50}, "hitpoints": 50},
                        "stats": {"attack": 45},
                        "moves": {"tackle": {"power": 40, "type": "normal", "pp": 35}},
                        "types": ["normal"],
                    },       BattleType.POKEMON,
                    "defender_stats": {"stats": {"defense": 40}, "types": ["normal"]},                {
                },
            ),ker_stats": {
            (
                BattleType.PET,                        "stats": {"attack": 45},
                {"moves": {"tackle": {"power": 40, "type": "normal", "pp": 35}},
                    "move": "scratch",
                    "attacker_stats": {
                        "level": 10,fender_stats": {"stats": {"defense": 40}, "types": ["normal"]},
                        "stats": {"attack": 30},
                        "moves": {
                            "scratch": {
                                "power": 25,.PET,
                                "energy_cost": 10,
                                "element": "normal",
                            }{
                        }, 10,
                        "current_energy": 50,
                        "loyalty": 50,": {
                    },
                    "defender_stats": {"stats": {"defense": 25}, "element": "normal"},          "power": 25,
                },st": 10,
            ),ent": "normal",
        ],          }
    )
    def test_damage_calculation(self, battle_systems, battle_type, move_data):": 50,
        """Test damage calculation for each battle system."""": 50,
        system = battle_systems[battle_type]
        damage, message = system.calculate_damage(,
            move_data["move"], move_data["attacker_stats"], move_data["defender_stats"]
        )

        assert isinstance(damage, int)
        assert damage >= 0est_damage_calculation(self, battle_systems, battle_type, move_data):
        assert isinstance(message, str)        """Test damage calculation for each battle system."""

    @pytest.mark.asyncio        damage, message = system.calculate_damage(
    async def test_battle_flow(self, battle_manager, battle_systems):move"], move_data["attacker_stats"], move_data["defender_stats"]
        """Test complete battle flow."""
        # Create battle
        battle = battle_manager.create_battle(
            battle_type=BattleType.POKEMON,
            challenger_id=1,        assert isinstance(message, str)
            opponent_id=2,
            initial_data={
                "challenger_pokemon": {, battle_manager, battle_systems):
                    "name": "Pikachu",
                    "level": 20,        # Create battle
                    "stats": {"hp": 50, "attack": 45, "defense": 40},
                    "moves": {
                        "thunderbolt": {"power": 90, "type": "electric", "pp": 15}
                    },
                    "types": ["electric"],            initial_data={
                    "current_hp": 50,_pokemon": {
                },
                "opponent_pokemon": {    "level": 20,
                    "name": "Squirtle",
                    "level": 20,   "moves": {
                    "stats": {"hp": 44, "attack": 40, "defense": 45},               "thunderbolt": {"power": 90, "type": "electric", "pp": 15}
                    "moves": {"water_gun": {"power": 40, "type": "water", "pp": 25}},                    },
                    "types": ["water"],s": ["electric"],
                    "current_hp": 44,current_hp": 50,
                },
            },
        )           "name": "Squirtle",

        system = battle_systems[BattleType.POKEMON]ack": 40, "defense": 45},
{"power": 40, "type": "water", "pp": 25}},
        # Process turns                    "types": ["water"],
        result = system.process_turn(battle, "thunderbolt")rent_hp": 44,
        assert result["damage"] > 0  # Super effective
        assert "super effective" in result["message"].lower()
        assert not battle.is_finished

        battle.current_turn = battle.opponent_idystem = battle_systems[BattleType.POKEMON]
        result = system.process_turn(battle, "water_gun")
        assert result["damage"] > 0
        assert "not very effective" in result["message"].lower()nderbolt")

    def test_status_effects(self, battle_systems):        assert "super effective" in result["message"].lower()








































































































































    ctx.send.assert_called_once()    )        "test_battle", 456    battle_commands.battle_manager.end_battle.assert_called_once_with(    # Verify battle was ended        await battle_commands.battle_forfeit(ctx)        )        mention="@Opponent"    battle_commands.bot.get_user.return_value = Mock(    # Mock winner user        )        Mock(xp=25, coins=10)    # Loser reward        Mock(xp=100, coins=50),  # Winner reward    battle_commands.battle_manager.end_battle.return_value = (    # Mock reward calculation        battle_commands.battle_manager.get_player_battle.return_value = mock_battle    mock_battle.opponent_id = 456    mock_battle.challenger_id = 123    mock_battle.battle_id = "test_battle"    mock_battle = Mock()    # Mock battle state    """Test battle forfeit functionality."""async def test_battle_forfeit(battle_commands, ctx):@pytest.mark.asyncio        ctx.send.assert_called_once()    # Verify status was displayed        await battle_commands.battle_status(ctx)        ))        name="TestUser" if id == 123 else "Opponent"    battle_commands.bot.get_user = Mock(side_effect=lambda id: Mock(    # Mock bot user fetching        battle_commands.battle_manager.get_player_battle.return_value = mock_battle    }        }            "status_effects": []            "max_energy": 100,            "current_energy": 60,            "max_hp": 100,            "current_hp": 75,        "opponent_stats": {        },            "status_effects": ["poisoned"]            "max_energy": 100,            "current_energy": 80,            "max_hp": 100,            "current_hp": 90,        "challenger_stats": {    mock_battle.battle_data = {    mock_battle.current_turn = 123    mock_battle.opponent_id = 456    mock_battle.challenger_id = 123    mock_battle.battle_type = BattleType.OSRS    mock_battle = Mock()    # Mock battle state    """Test battle status display."""async def test_battle_status(battle_commands, ctx):@pytest.mark.asyncio    ctx.send.assert_called_once()    mock_system.process_turn.assert_called_once()    # Verify move was processed        await battle_commands.battle_move(ctx, move="slash")        battle_commands.battle_systems[BattleType.OSRS] = mock_system    }        "defender_hp": 90        "damage": 10,        "message": "Hit for 10 damage!",    mock_system.process_turn.return_value = {    mock_system.is_valid_move.return_value = True    mock_system = Mock()    # Mock battle system        battle_commands.battle_manager.get_player_battle.return_value = mock_battle    mock_battle.battle_id = "test_battle"    mock_battle.battle_type = BattleType.OSRS    mock_battle = Mock()    # Mock battle state    """Test battle move processing."""async def test_battle_move_processing(battle_commands, ctx):@pytest.mark.asyncio    ctx.send.assert_called_with("You're already in a battle!")    await battle_commands.battle_osrs(ctx, opponent)    battle_commands.battle_manager.get_player_battle = Mock(return_value=True)    opponent.bot = False    # Test player already in battle        ctx.send.assert_called_with("You can't battle with a bot!")    await battle_commands.battle_osrs(ctx, opponent)    opponent.bot = True    # Test battling with a bot    """Test battle start validation checks."""async def test_battle_start_validation(battle_commands, ctx, opponent):@pytest.mark.asyncio        assert winner_reward.coins > loser_reward.coins        assert winner_reward.xp > loser_reward.xp        winner_reward, loser_reward = battle_manager.end_battle(battle.battle_id, 1)        )            battle_type=BattleType.OSRS, challenger_id=1, opponent_id=2, initial_data={}        battle = battle_manager.create_battle(        """Test battle reward calculation."""    async def test_battle_rewards(self, battle_manager):    @pytest.mark.asyncio        assert "poison" in messages.lower()        assert pet_stats["current_hp"] < 100        messages = pet_system._apply_dot_effects(pet_stats, {})        }            "status_effects": {"poison": {"dot": 8, "turns": 3}},            "current_hp": 100,        pet_stats = {        # Test Pet poison        )            == 50            pokemon_system._apply_stat_stages(pokemon_stats["stats"]["attack"], 0) * 0.5        assert (        pokemon_stats = {"stats": {"attack": 100}, "status": "burn"}        # Test Pokemon burn        pet_system = battle_systems[BattleType.PET]        pokemon_system = battle_systems[BattleType.POKEMON]        """Test status effect application and processing."""        assert not battle.is_finished

        battle.current_turn = battle.opponent_id
        result = system.process_turn(battle, "water_gun")
        assert result["damage"] > 0
        assert "not very effective" in result["message"].lower()

    def test_status_effects(self, battle_systems):
        """Test status effect application and processing."""
        pokemon_system = battle_systems[BattleType.POKEMON]
        pet_system = battle_systems[BattleType.PET]

        # Test Pokemon burn
        pokemon_stats = {"stats": {"attack": 100}, "status": "burn"}
        assert (
            pokemon_system._apply_stat_stages(pokemon_stats["stats"]["attack"], 0) * 0.5
            == 50
        )

        # Test Pet poison
        pet_stats = {
            "current_hp": 100,
            "status_effects": {"poison": {"dot": 8, "turns": 3}},
        }
        messages = pet_system._apply_dot_effects(pet_stats, {})
        assert pet_stats["current_hp"] < 100
        assert "poison" in messages.lower()

    @pytest.mark.asyncio
    async def test_battle_rewards(self, battle_manager):
        """Test battle reward calculation."""
        battle = battle_manager.create_battle(
            battle_type=BattleType.OSRS, challenger_id=1, opponent_id=2, initial_data={}
        )

        winner_reward, loser_reward = battle_manager.end_battle(battle.battle_id, 1)
        assert winner_reward.xp > loser_reward.xp
        assert winner_reward.coins > loser_reward.coins


@pytest.mark.asyncio
async def test_battle_start_validation(battle_commands, ctx, opponent):
    """Test battle start validation checks."""
    # Test battling with a bot
    opponent.bot = True
    await battle_commands.battle_osrs(ctx, opponent)
    ctx.send.assert_called_with("You can't battle with a bot!")

    # Test player already in battle
    opponent.bot = False
    battle_commands.battle_manager.get_player_battle = Mock(return_value=True)
    await battle_commands.battle_osrs(ctx, opponent)
    ctx.send.assert_called_with("You're already in a battle!")


@pytest.mark.asyncio
async def test_battle_move_processing(battle_commands, ctx):
    """Test battle move processing."""
    # Mock battle state
    mock_battle = Mock()
    mock_battle.battle_type = BattleType.OSRS
    mock_battle.battle_id = "test_battle"
    battle_commands.battle_manager.get_player_battle.return_value = mock_battle

    # Mock battle system
    mock_system = Mock()
    mock_system.is_valid_move.return_value = True
    mock_system.process_turn.return_value = {
        "message": "Hit for 10 damage!",
        "damage": 10,
        "defender_hp": 90,
    }
    battle_commands.battle_systems[BattleType.OSRS] = mock_system

    await battle_commands.battle_move(ctx, move="slash")

    # Verify move was processed
    mock_system.process_turn.assert_called_once()
    ctx.send.assert_called_once()


@pytest.mark.asyncio
async def test_battle_status(battle_commands, ctx):
    """Test battle status display."""
    # Mock battle state
    mock_battle = Mock()
    mock_battle.battle_type = BattleType.OSRS
    mock_battle.challenger_id = 123
    mock_battle.opponent_id = 456
    mock_battle.current_turn = 123
    mock_battle.battle_data = {
        "challenger_stats": {
            "current_hp": 90,
            "max_hp": 100,
            "current_energy": 80,
            "max_energy": 100,
            "status_effects": ["poisoned"],
        },
        "opponent_stats": {
            "current_hp": 75,
            "max_hp": 100,
            "current_energy": 60,
            "max_energy": 100,
            "status_effects": [],
        },
    }
    battle_commands.battle_manager.get_player_battle.return_value = mock_battle

    # Mock bot user fetching
    battle_commands.bot.get_user = Mock(
        side_effect=lambda id: Mock(name="TestUser" if id == 123 else "Opponent")
    )

    await battle_commands.battle_status(ctx)

    # Verify status was displayed
    ctx.send.assert_called_once()


@pytest.mark.asyncio
async def test_battle_forfeit(battle_commands, ctx):
    """Test battle forfeit functionality."""
    # Mock battle state
    mock_battle = Mock()
    mock_battle.battle_id = "test_battle"
    mock_battle.challenger_id = 123
    mock_battle.opponent_id = 456
    battle_commands.battle_manager.get_player_battle.return_value = mock_battle

    # Mock reward calculation
    battle_commands.battle_manager.end_battle.return_value = (
        Mock(xp=100, coins=50),  # Winner reward
        Mock(xp=25, coins=10),  # Loser reward
    )

    # Mock winner user
    battle_commands.bot.get_user.return_value = Mock(mention="@Opponent")

    await battle_commands.battle_forfeit(ctx)

    # Verify battle was ended
    battle_commands.battle_manager.end_battle.assert_called_once_with(
        "test_battle", 456
    )
    ctx.send.assert_called_once()
