import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

from .models import (
    OSRSPet,
    OSRSPetSource,
    OSRSPetRarity,
    OSRSPetAbility,
    OSRSPetVariant,
    OSRSLocation,
    OSRSCombatStats,
    OSRSSkill,
)

logger = logging.getLogger(__name__)


class OSRSDataLoader:
    DATA_DIR = Path("data/osrs")

    def __init__(self):
        self.pets_file = self.DATA_DIR / "pets.json"
        self._pets_cache: Optional[List[OSRSPet]] = None

    def _load_combat_stats(self, stats_dict: Dict) -> OSRSCombatStats:
        """Convert dictionary to OSRSCombatStats object"""
        return OSRSCombatStats(
            attack_level=stats_dict["attack_level"],
            strength_level=stats_dict["strength_level"],
            defence_level=stats_dict["defence_level"],
            hitpoints_level=stats_dict["hitpoints_level"],
            ranged_level=stats_dict["ranged_level"],
            magic_level=stats_dict["magic_level"],
            prayer_level=stats_dict["prayer_level"],
            combat_level=stats_dict["combat_level"],
            attack_bonus=stats_dict["attack_bonus"],
            defence_bonus=stats_dict["defence_bonus"],
            other_bonuses=stats_dict["other_bonuses"],
        )

    def _load_abilities(self, abilities_data: List[Dict]) -> List[OSRSPetAbility]:
        """Convert list of dictionaries to OSRSPetAbility objects"""
        return [
            OSRSPetAbility(
                name=ability["name"],
                description=ability["description"],
                effect_type=ability["effect_type"],
                effect_value=ability["effect_value"],
                passive=ability.get("passive", False),
                cooldown=ability.get("cooldown", 0),
                requirements=ability.get("requirements"),
            )
            for ability in abilities_data
        ]

    def _load_variants(self, variants_data: List[Dict]) -> List[OSRSPetVariant]:
        """Convert list of dictionaries to OSRSPetVariant objects"""
        return [
            OSRSPetVariant(
                name=variant["name"],
                examine_text=variant["examine_text"],
                metamorphic=variant.get("metamorphic", False),
                requirements=variant.get("requirements"),
            )
            for variant in variants_data
        ]

    def _load_locations(self, locations_data: List[Dict]) -> List[OSRSLocation]:
        """Convert list of dictionaries to OSRSLocation objects"""
        return [
            OSRSLocation(
                name=location["name"],
                region=location["region"],
                coordinates=tuple(location["coordinates"]) if location.get("coordinates") else None,
                wilderness_level=location.get("wilderness_level", 0),
                requirements=location.get("requirements"),
                description=location.get("description", ""),
            )
            for location in locations_data
        ]

    def _load_requirements(self, requirements_data: Dict) -> Dict[OSRSSkill, int]:
        """Convert dictionary of skill requirements to proper format"""
        return (
            {OSRSSkill[skill_name]: level for skill_name, level in requirements_data.items()}
            if requirements_data
            else {}
        )

    def load_pets(self, force_reload: bool = False) -> List[OSRSPet]:
        """Load pet data from JSON file"""
        if self._pets_cache is not None and not force_reload:
            return self._pets_cache

        if not self.pets_file.exists():
            logger.warning(f"Pets file not found at {self.pets_file}")
            return []

        try:
            with open(self.pets_file, "r") as f:
                pets_data = json.load(f)

            pets = []
            for pet_data in pets_data:
                try:
                    pet = OSRSPet(
                        id=pet_data["id"],
                        name=pet_data["name"],
                        release_date=datetime.fromisoformat(pet_data["release_date"]),
                        source=OSRSPetSource(pet_data["source"]),
                        rarity=OSRSPetRarity(pet_data["rarity"]),
                        base_stats=self._load_combat_stats(pet_data["base_stats"]),
                        abilities=self._load_abilities(pet_data["abilities"]),
                        variants=self._load_variants(pet_data["variants"]),
                        obtainable_from=pet_data["obtainable_from"],
                        drop_rate=pet_data.get("drop_rate"),
                        requirements=self._load_requirements(pet_data.get("requirements", {})),
                        quest_requirements=pet_data.get("quest_requirements", []),
                        item_requirements=pet_data.get("item_requirements", []),
                        locations=self._load_locations(pet_data.get("locations", [])),
                        examine_text=pet_data.get("examine_text", ""),
                        trivia=pet_data.get("trivia", []),
                        wiki_url=pet_data.get("wiki_url", ""),
                    )
                    pets.append(pet)
                except Exception as e:
                    logger.error(f"Failed to load pet {pet_data.get('name', 'UNKNOWN')}: {e}")
                    continue

            self._pets_cache = pets
            logger.info(f"Loaded {len(pets)} pets from {self.pets_file}")
            return pets

        except Exception as e:
            logger.error(f"Failed to load pets file: {e}")
            return []

    def get_pet_by_name(self, name: str) -> Optional[OSRSPet]:
        """Get a pet by its name"""
        pets = self.load_pets()
        name_lower = name.lower()
        for pet in pets:
            if pet.name.lower() == name_lower:
                return pet
        return None

    def get_pets_by_source(self, source: OSRSPetSource) -> List[OSRSPet]:
        """Get all pets from a specific source"""
        pets = self.load_pets()
        return [pet for pet in pets if pet.source == source]

    def get_pets_by_rarity(self, rarity: OSRSPetRarity) -> List[OSRSPet]:
        """Get all pets of a specific rarity"""
        pets = self.load_pets()
        return [pet for pet in pets if pet.rarity == rarity]

    def get_pets_by_skill_requirement(self, skill: OSRSSkill, min_level: int) -> List[OSRSPet]:
        """Get all pets that require a specific skill level"""
        pets = self.load_pets()
        return [
            pet
            for pet in pets
            if pet.requirements
            and skill in pet.requirements
            and pet.requirements[skill] >= min_level
        ]

    def get_pets_by_quest_requirement(self, quest_name: str) -> List[OSRSPet]:
        """Get all pets that require a specific quest"""
        pets = self.load_pets()
        quest_name_lower = quest_name.lower()
        return [
            pet
            for pet in pets
            if pet.quest_requirements
            and any(quest.lower() == quest_name_lower for quest in pet.quest_requirements)
        ]

    def get_metamorphic_pets(self) -> List[OSRSPet]:
        """Get all pets that have metamorphic variants"""
        pets = self.load_pets()
        return [
            pet
            for pet in pets
            if pet.variants and any(variant.metamorphic for variant in pet.variants)
        ]
