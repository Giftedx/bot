from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


class PetType(Enum):
    OSRS = "osrs"
    POKEMON = "pokemon"


class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class PetConfig:
    base_catch_rate: float
    max_boost: float
    max_level: int
    exp_per_level: int


@dataclass
class OSRSPetConfig(PetConfig):
    pets: Dict[str, Dict[str, Any]]
    max_combat_level: int
    boss_exp_range: tuple[int, int]


@dataclass
class PokemonPetConfig(PetConfig):
    species: Dict[str, Dict[str, Any]]
    max_moves: int
    move_learn_chance: float
    evolution_level_multiplier: int


class GameConfig:
    def __init__(self):
        self.osrs_config = OSRSPetConfig(
            base_catch_rate=0.1,
            max_boost=0.5,
            max_level=99,
            exp_per_level=100,
            max_combat_level=99,
            boss_exp_range=(20, 50),
            pets={
                "Baby Mole": {
                    "rarity": Rarity.UNCOMMON,
                    "boss_origin": "Giant Mole",
                    "base_combat": 5,
                    "skill_boost": "mining",
                },
                "Prince Black Dragon": {
                    "rarity": Rarity.RARE,
                    "boss_origin": "King Black Dragon",
                    "base_combat": 15,
                    "skill_boost": "combat",
                },
                "Pet Chaos Elemental": {
                    "rarity": Rarity.EPIC,
                    "boss_origin": "Chaos Elemental",
                    "base_combat": 25,
                    "skill_boost": "magic",
                },
            },
        )

        self.pokemon_config = PokemonPetConfig(
            base_catch_rate=0.1,
            max_boost=0.5,
            max_level=100,
            exp_per_level=100,
            max_moves=4,
            move_learn_chance=0.3,
            evolution_level_multiplier=20,
            species={
                "Pikachu": {
                    "rarity": Rarity.UNCOMMON,
                    "types": ["Electric"],
                    "base_stats": {"hp": 35, "attack": 55, "defense": 40},
                    "possible_moves": ["Thunder Shock", "Quick Attack", "Thunderbolt"],
                    "evolution": "Raichu",
                },
                "Charmander": {
                    "rarity": Rarity.UNCOMMON,
                    "types": ["Fire"],
                    "base_stats": {"hp": 39, "attack": 52, "defense": 43},
                    "possible_moves": ["Scratch", "Ember", "Fire Spin"],
                    "evolution": "Charmeleon",
                },
                "Bulbasaur": {
                    "rarity": Rarity.UNCOMMON,
                    "types": ["Grass", "Poison"],
                    "base_stats": {"hp": 45, "attack": 49, "defense": 49},
                    "possible_moves": ["Tackle", "Vine Whip", "Razor Leaf"],
                    "evolution": "Ivysaur",
                },
            },
        )

    def get_pet_config(self, pet_type: PetType) -> PetConfig:
        if pet_type == PetType.OSRS:
            return self.osrs_config
        elif pet_type == PetType.POKEMON:
            return self.pokemon_config
        raise ValueError(f"Unknown pet type: {pet_type}")

    def get_rarity_boost_multiplier(self, rarity: Rarity) -> float:
        """Get catch rate multiplier based on rarity"""
        multipliers = {
            Rarity.COMMON: 1.0,
            Rarity.UNCOMMON: 0.7,
            Rarity.RARE: 0.4,
            Rarity.EPIC: 0.2,
            Rarity.LEGENDARY: 0.1,
        }
        return multipliers.get(rarity, 1.0)

    def calculate_exp_needed(self, current_level: int) -> int:
        """Calculate experience needed for next level"""
        return current_level * self.osrs_config.exp_per_level  # Same for both types


game_config = GameConfig()
