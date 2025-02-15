import pytest
from unittest.mock import Mock
from src.pets.battle import (
    BattleSystem,
    BattleState,
    BattleNotFoundError,
    InvalidMoveError,
)
from src.pets.models import Pet, PetType, PetMove, Battle


@pytest.fixture
def battle_system() -> BattleSystem:
    return BattleSystem()


@pytest.fixture
def mock_pet() -> Mock:
    pet = Mock(spec=Pet)
    pet.max_health = 100
    pet.level = 5
    pet.element = PetType.FIRE
    return pet


@pytest.fixture
def mock_pet_move() -> PetMove:
    move = Mock(spec=PetMove)
    move.damage = 20
    move.name = "Test Move"
    return move


@pytest.mark.asyncio
async def test_start_battle(
    battle_system: BattleSystem, mock_pet: Mock
) -> None:
    pet1: Pet = mock_pet
    pet2: Pet = mock_pet
    battle_state: BattleState = await battle_system.start_battle(
        pet1, pet2
    )
    assert isinstance(battle_state, BattleState)
    assert battle_state.pet1_id == id(pet1)
    assert battle_state.pet2_id == id(pet2)
    assert battle_state.current_turn == 1
    assert battle_state.winner is None


@pytest.mark.asyncio
async def test_start_battle_increments_battle_id(
    battle_system: BattleSystem, mock_pet: Mock
) -> None:
    pet1: Pet = mock_pet
    pet2: Pet = mock_pet
    battle1: BattleState = await battle_system.start_battle(
        pet1, pet2
    )
    battle2: BattleState = await battle_system.start_battle(
        pet1, pet2
    )
    assert battle2.battle_id == battle1.battle_id + 1


@pytest.mark.asyncio
async def test_start_battle_with_different_levels(
    battle_system: BattleSystem, mock_pet: Mock
) -> None:
    pet1: Pet = mock_pet
    pet2: Pet = Mock(spec=Pet)
    pet2.max_health = 100
    pet2.level = 10
    pet2.element = PetType.WATER
    battle_state: BattleState = await battle_system.start_battle(
        pet1, pet2
    )
    assert isinstance(battle_state, BattleState)
    assert battle_state.pet1_id == id(pet1)
    assert battle_state.pet2_id == id(pet2)
    assert battle_state.current_turn == 1
    assert battle_state.winner is None


@pytest.mark.asyncio
async def test_process_turn_valid(
    battle_system: BattleSystem, mock_pet: Mock, mock_pet_move: PetMove
) -> None:
    pet1 = mock_pet
    pet2 = mock_pet
    battle_state: BattleState = await battle_system.start_battle(
        pet1, pet2
    )
    result = await battle_system.process_turn(
        battle_state.battle_id, mock_pet_move, pet1, pet2
    )
    assert result["damage"] > 0
    assert result["move_name"] == "Test Move"
    assert result["attacker"] == id(pet1)
    assert result["defender"] == id(pet2)
    assert not result["battle_over"]
    assert result["winner"] is None
    state = battle_system.get_battle_state(battle_state.battle_id)
    assert state is not None
    if state:
        assert state.current_turn == 2


@pytest.mark.asyncio
async def test_process_turn_ends_battle(
    battle_system: BattleSystem, mock_pet: Mock, mock_pet_move: PetMove
) -> None:
    pet1 = mock_pet
    pet2 = Mock(spec=Pet)
    pet2.max_health = 20  # Make pet2 weak
    pet2.level = 5
    pet2.element = PetType.FIRE
    battle_state: BattleState = await battle_system.start_battle(
        pet1, pet2
    )
    result = await battle_system.process_turn(
        battle_state.battle_id, mock_pet_move, pet1, pet2
    )
    assert result["battle_over"]
    assert result["winner"] == id(pet1)
    assert battle_system.get_battle_state(battle_state.battle_id) is None


@pytest.mark.asyncio
async def test_process_turn_invalid_turn(
    battle_system: BattleSystem, mock_pet: Mock, mock_pet_move: PetMove
) -> None:
    pet1 = mock_pet
    pet2 = mock_pet
    battle_state: BattleState = await battle_system.start_battle(
        pet1, pet2
    )
    with pytest.raises(InvalidMoveError):
        await battle_system.process_turn(
            battle_state.battle_id, mock_pet_move, pet2, pet1
        )


@pytest.mark.asyncio
async def test_process_turn_battle_not_found(
    battle_system: BattleSystem, mock_pet: Mock, mock_pet_move: PetMove
) -> None:
    pet1 = mock_pet
    pet2 = mock_pet
    with pytest.raises(BattleNotFoundError):
        await battle_system.process_turn(
            999, mock_pet_move, pet1, pet2
        )


def test_battle_get_current_pet(battle_system, mock_pet):
    pet1 = mock_pet
    pet2 = Mock(spec=Pet)
    battle = Battle(battle_id=1, pet1=pet1, pet2=pet2)
    assert battle.get_current_pet() == pet1

    battle.current_turn = 2
    assert battle.get_current_pet() == pet2


def test_battle_get_opponent_pet(battle_system, mock_pet):
    pet1 = mock_pet
    pet2 = Mock(spec=Pet)
    battle = Battle(battle_id=1, pet1=pet1, pet2=pet2)
    assert battle.get_opponent_pet() == pet2

    battle.current_turn = 2
    assert battle.get_opponent_pet() == pet1


def test_battle_next_turn(battle_system, mock_pet):
    pet1 = mock_pet
    pet2 = Mock(spec=Pet)
    battle = Battle(battle_id=1, pet1=pet1, pet2=pet2)
    battle.next_turn()
    assert battle.current_turn == 2