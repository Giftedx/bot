from typing import Dict, Any, List
from ....shared.base_pet import BasePet

class PokemonPet(BasePet):
    def __init__(self, pet_id: str, owner_id: str, name: str, species: str):
        super().__init__(pet_id, owner_id, name)
        self.species = species
        self.type = []  # e.g., ["Fire", "Flying"]
        self.moves: List[str] = []
        self.evolution_stage = 1
        self.can_evolve = False
        self.stats = {
            "hp": 1,
            "attack": 1,
            "defense": 1,
            "sp_attack": 1,
            "sp_defense": 1,
            "speed": 1
        }

    def special_ability(self) -> str:
        """Pokemon pets can help in battles and contests"""
        return f"Can participate in Pokemon battles and contests with {len(self.moves)} moves"

    def learn_move(self, move: str) -> bool:
        """Learn a new move, maximum 4 moves"""
        if len(self.moves) < 4:
            self.moves.append(move)
            self.gain_experience(25)
            return True
        return False

    def check_evolution(self) -> bool:
        """Check if Pokemon can evolve based on level"""
        if self.can_evolve and self.level >= (self.evolution_stage * 20):
            return True
        return False

    def evolve(self, new_species: str) -> None:
        """Evolve the Pokemon to a new form"""
        self.species = new_species
        self.evolution_stage += 1
        self.gain_experience(100)
        # Boost stats
        for stat in self.stats:
            self.stats[stat] += 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert Pokemon pet data to dictionary, including base pet data"""
        base_data = super().to_dict()
        pokemon_data = {
            "species": self.species,
            "type": self.type,
            "moves": self.moves,
            "evolution_stage": self.evolution_stage,
            "can_evolve": self.can_evolve,
            "stats": self.stats
        }
        return {**base_data, **pokemon_data}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PokemonPet':
        """Create Pokemon pet instance from dictionary data"""
        pet = super().from_dict(cls, data)
        pet.species = data["species"]
        pet.type = data["type"]
        pet.moves = data["moves"]
        pet.evolution_stage = data["evolution_stage"]
        pet.can_evolve = data["can_evolve"]
        pet.stats = data["stats"]
        return pet 