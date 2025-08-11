import asyncio
import json
from pathlib import Path
import logging
from typing import List

from .fetcher import OSRSDataFetcher
from .models import OSRSPet

logger = logging.getLogger(__name__)


class OSRSDataPopulator:
    DATA_DIR = Path("data/osrs")

    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.pets_file = self.DATA_DIR / "pets.json"
        self.fetcher = OSRSDataFetcher()

    def _save_pets(self, pets: List[OSRSPet]):
        """Save pet data to JSON file"""
        pet_data = []
        for pet in pets:
            # Convert pet object to dictionary, handling datetime serialization
            pet_dict = {
                "id": pet.id,
                "name": pet.name,
                "release_date": pet.release_date.isoformat(),
                "source": pet.source.value,
                "rarity": pet.rarity.value,
                "base_stats": {
                    "attack_level": pet.base_stats.attack_level,
                    "strength_level": pet.base_stats.strength_level,
                    "defence_level": pet.base_stats.defence_level,
                    "hitpoints_level": pet.base_stats.hitpoints_level,
                    "ranged_level": pet.base_stats.ranged_level,
                    "magic_level": pet.base_stats.magic_level,
                    "prayer_level": pet.base_stats.prayer_level,
                    "combat_level": pet.base_stats.combat_level,
                    "attack_bonus": pet.base_stats.attack_bonus,
                    "defence_bonus": pet.base_stats.defence_bonus,
                    "other_bonuses": pet.base_stats.other_bonuses,
                },
                "abilities": [
                    {
                        "name": ability.name,
                        "description": ability.description,
                        "effect_type": ability.effect_type,
                        "effect_value": ability.effect_value,
                        "passive": ability.passive,
                        "cooldown": ability.cooldown,
                        "requirements": ability.requirements,
                    }
                    for ability in pet.abilities
                ],
                "variants": [
                    {
                        "name": variant.name,
                        "examine_text": variant.examine_text,
                        "metamorphic": variant.metamorphic,
                        "requirements": variant.requirements,
                    }
                    for variant in pet.variants
                ],
                "obtainable_from": pet.obtainable_from,
                "drop_rate": pet.drop_rate,
                "requirements": {
                    skill.name: level for skill, level in (pet.requirements or {}).items()
                },
                "quest_requirements": pet.quest_requirements,
                "item_requirements": pet.item_requirements,
                "locations": [
                    {
                        "name": location.name,
                        "region": location.region,
                        "coordinates": location.coordinates,
                        "wilderness_level": location.wilderness_level,
                        "requirements": location.requirements,
                        "description": location.description,
                    }
                    for location in pet.locations
                ],
                "examine_text": pet.examine_text,
                "trivia": pet.trivia,
                "wiki_url": pet.wiki_url,
            }
            pet_data.append(pet_dict)

        with open(self.pets_file, "w") as f:
            json.dump(pet_data, f, indent=2, sort_keys=True, ensure_ascii=False)
        logger.info(f"Saved {len(pet_data)} pets to {self.pets_file}")

    async def populate_pets(self):
        """Fetch and save all OSRS pet data"""
        async with self.fetcher:
            logger.info("Fetching OSRS pet data...")
            pets = await self.fetcher.fetch_all_pets()
            if pets:
                self._save_pets(pets)
                logger.info(f"Successfully populated {len(pets)} pets")
            else:
                logger.error("Failed to fetch pet data")


async def main():
    """Main function to populate the database"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    populator = OSRSDataPopulator()
    await populator.populate_pets()


if __name__ == "__main__":
    asyncio.run(main())
