from src.pets.models import PetType, StatusEffect, PetMove, Pet


def test_pet_type_enum() -> None:
    assert PetType.FIRE.value == "🔥"
    assert PetType.WATER.value == "💧"
    assert PetType.EARTH.value == "🌍"
    assert PetType.AIR.value == "💨"
    assert PetType.LIGHT.value == "✨"
    assert PetType.DARK.value == "🌑"


def test_status_effect_enum() -> None:
    assert StatusEffect.NONE.value == ""
    assert StatusEffect.BURN.value == "🔥"
    assert StatusEffect.FREEZE.value == "❄️"
    assert StatusEffect.POISON.value == "☠️"
    assert StatusEffect.STUN.value == "⚡"
    assert StatusEffect.HEAL.value == "💚"
    assert StatusEffect.SHIELD.value == "🛡️"


def test_pet_move() -> None:
    move = PetMove(
        name="Test Move",
        damage=20,
        element=PetType.FIRE,
        status_effect=StatusEffect.BURN,
        status_duration=2,
        cooldown=1,
        emoji="💥",
    )
    assert move.name == "Test Move"
    assert move.damage == 20
    assert move.element == PetType.FIRE
    assert move.status_effect == StatusEffect.BURN
    assert move.status_duration == 2
    assert move.cooldown == 1
    assert move.emoji == "💥"


def test_pet_init() -> None:
    pet = Pet(name="Test Pet", element=PetType.FIRE)
    assert pet.name == "Test Pet"
    assert pet.element == PetType.FIRE
    assert pet.level == 1
    assert pet.experience == 0
    assert pet.health == 100
    assert pet.max_health == 100
    assert pet.status == StatusEffect.NONE
    assert pet.status_turns == 0
    assert len(pet.moves) == 2


def test_pet_apply_status() -> None:
    pet = Pet(name="Test Pet", element=PetType.FIRE)
    pet.apply_status(StatusEffect.BURN, 3)
    assert pet.status == StatusEffect.BURN
    assert pet.status_turns == 3


def test_pet_update_status() -> None:
    pet = Pet(name="Test Pet", element=PetType.FIRE)
    pet.apply_status(StatusEffect.BURN, 3)
    pet.update_status()
    assert pet.status_turns == 2
    pet.update_status()
    pet.update_status()
    assert pet.status == StatusEffect.NONE
    assert pet.status_turns == 0


def test_pet_add_experience_no_level_up() -> None:
    pet = Pet(name="Test Pet", element=PetType.FIRE)
    leveled_up = pet.add_experience(50)
    assert not leveled_up
    assert pet.experience == 50
    assert pet.level == 1


def test_pet_add_experience_level_up() -> None:
    pet = Pet(name="Test Pet", element=PetType.FIRE)
    leveled_up = pet.add_experience(100)
    assert leveled_up
    assert pet.experience == 0
    assert pet.level == 2


def test_pet_level_up() -> None:
    pet = Pet(name="Test Pet", element=PetType.FIRE, max_health=100, health=80)
    pet.level_up()
    assert pet.level == 2
    assert pet.experience == 0
    assert pet.max_health == 110  # 10% increase
    assert pet.health == 90  # Heal by the HP increase


def test_pet_heal() -> None:
    pet = Pet(name="Test Pet", element=PetType.FIRE, health=50, max_health=100)
    healed_amount = pet.heal(30)
    assert healed_amount == 80
    assert pet.health == 80
    healed_amount = pet.heal(50)
    assert healed_amount == 100
    assert pet.health == 100


def test_pet_take_damage() -> None:
    pet = Pet(name="Test Pet", element=PetType.FIRE, health=80)
    damage_taken = pet.take_damage(30)
    assert damage_taken == 80
    assert pet.health == 50
    damage_taken = pet.take_damage(100)
    assert damage_taken == 50
    assert pet.health == 0


def test_pet_is_defeated() -> None:
    pet = Pet(name="Test Pet", element=PetType.FIRE, health=0)
    assert pet.is_defeated()
    pet.health = 10
    assert not pet.is_defeated()