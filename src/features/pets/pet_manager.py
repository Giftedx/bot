from typing import Dict, List, Optional, Union, Any
import uuid
from datetime import datetime

from ...shared.base_pet import BasePet
from ..osrs.osrs_pet import OSRSPet
from ..pokemon.pokemon_pet import PokemonPet


class PetManager:
    def __init__(self):
        self.pets: Dict[str, BasePet] = {}
        self.user_pets: Dict[str, List[str]] = {}  # user_id -> list of pet_ids

    def add_pet(self, owner_id: str, pet_type: str, **pet_kwargs) -> BasePet:
        """Add a new pet of specified type to the system"""
        pet_id = str(uuid.uuid4())

        if pet_type.lower() == "osrs":
            pet = OSRSPet(pet_id, owner_id, **pet_kwargs)
        elif pet_type.lower() == "pokemon":
            pet = PokemonPet(pet_id, owner_id, **pet_kwargs)
        else:
            raise ValueError(f"Unknown pet type: {pet_type}")

        self.pets[pet_id] = pet
        if owner_id not in self.user_pets:
            self.user_pets[owner_id] = []
        self.user_pets[owner_id].append(pet_id)
        return pet

    def get_pet(self, pet_id: str) -> Optional[BasePet]:
        """Retrieve a pet by its ID"""
        return self.pets.get(pet_id)

    def get_user_pets(self, user_id: str) -> List[BasePet]:
        """Get all pets owned by a user"""
        pet_ids = self.user_pets.get(user_id, [])
        return [self.pets[pid] for pid in pet_ids if pid in self.pets]

    def get_rare_pets(self, rarity: str = "rare") -> List[BasePet]:
        """Get all pets of specified rarity"""
        return [pet for pet in self.pets.values() if pet.rarity == rarity]

    def transfer_pet(self, pet_id: str, new_owner_id: str) -> bool:
        """Transfer pet ownership to another user"""
        pet = self.get_pet(pet_id)
        if not pet:
            return False

        old_owner_id = pet.owner_id
        if old_owner_id in self.user_pets:
            self.user_pets[old_owner_id].remove(pet_id)

        pet.owner_id = new_owner_id
        if new_owner_id not in self.user_pets:
            self.user_pets[new_owner_id] = []
        self.user_pets[new_owner_id].append(pet_id)
        return True

    def level_up_all_pets(self, user_id: str, exp_amount: int) -> None:
        """Give experience to all pets owned by a user"""
        for pet in self.get_user_pets(user_id):
            pet.gain_experience(exp_amount)

    def get_pet_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about a user's pets"""
        pets = self.get_user_pets(user_id)
        return {
            "total_pets": len(pets),
            "average_level": sum(p.level for p in pets) / len(pets) if pets else 0,
            "highest_level": max((p.level for p in pets), default=0),
            "pet_types": {
                "osrs": sum(1 for p in pets if isinstance(p, OSRSPet)),
                "pokemon": sum(1 for p in pets if isinstance(p, PokemonPet)),
            },
        }

    def save_pets_data(self) -> Dict[str, Any]:
        """Convert all pet data to dictionary format for storage"""
        return {
            "pets": {pid: pet.to_dict() for pid, pet in self.pets.items()},
            "user_pets": self.user_pets,
        }

    @classmethod
    def load_pets_data(cls, data: Dict[str, Any]) -> "PetManager":
        """Create PetManager instance from stored data"""
        manager = cls()
        for pid, pet_data in data["pets"].items():
            pet_type = pet_data["type"]
            if pet_type == "OSRSPet":
                pet = OSRSPet.from_dict(pet_data)
            elif pet_type == "PokemonPet":
                pet = PokemonPet.from_dict(pet_data)
            manager.pets[pid] = pet
        manager.user_pets = data["user_pets"]
        return manager
