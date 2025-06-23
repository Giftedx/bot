from typing import Dict, List, Optional
import json
import random
from pathlib import Path
from dataclasses import dataclass

from .combat_calculator import CombatStats, EquipmentBonus
from .combat_manager import CombatEntity


@dataclass
class MonsterDefinition:
    id: int
    name: str
    combat_level: int
    hitpoints: int
    attack_level: int
    strength_level: int
    defence_level: int
    magic_level: int
    ranged_level: int
    attack_bonus: int
    strength_bonus: int
    attack_speed: float
    aggressive: bool
    attack_style: str
    weakness: str
    drops: Dict[str, float]  # item_id: drop_rate
    examine: str
    slayer_level: int = 1
    slayer_xp: float = 0.0
    respawn_time: int = 30


class MonsterManager:
    def __init__(self, data_path: str = "data/monsters"):
        self.data_path = Path(data_path)
        self.monsters: Dict[int, MonsterDefinition] = {}
        self.spawned_monsters: Dict[int, CombatEntity] = {}
        self._next_spawn_id = 1

    async def load_monsters(self):
        """Load monster definitions from JSON files."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Monster data directory not found: {self.data_path}")

        for file in self.data_path.glob("*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    for monster_data in data:
                        monster = MonsterDefinition(**monster_data)
                        self.monsters[monster.id] = monster
            except Exception as e:
                print(f"Error loading monster file {file}: {e}")

    def create_monster_entity(self, monster_def: MonsterDefinition) -> CombatEntity:
        """Create a combat entity from a monster definition."""
        stats = CombatStats(
            attack=monster_def.attack_level,
            strength=monster_def.strength_level,
            defence=monster_def.defence_level,
            ranged=monster_def.ranged_level,
            magic=monster_def.magic_level,
            prayer=1,
            hitpoints=monster_def.hitpoints,
        )

        equipment = EquipmentBonus(
            attack_slash=monster_def.attack_bonus, melee_strength=monster_def.strength_bonus
        )

        spawn_id = self._next_spawn_id
        self._next_spawn_id += 1

        return CombatEntity(
            id=spawn_id,
            name=monster_def.name,
            stats=stats,
            equipment=equipment,
            current_hp=monster_def.hitpoints,
            max_hp=monster_def.hitpoints,
            combat_level=monster_def.combat_level,
        )

    def spawn_monster(self, monster_id: int) -> Optional[CombatEntity]:
        """Spawn a new instance of a monster."""
        monster_def = self.monsters.get(monster_id)
        if not monster_def:
            return None

        monster = self.create_monster_entity(monster_def)
        self.spawned_monsters[monster.id] = monster
        return monster

    def despawn_monster(self, spawn_id: int):
        """Remove a spawned monster instance."""
        if spawn_id in self.spawned_monsters:
            del self.spawned_monsters[spawn_id]

    def get_monster_by_name(self, name: str) -> Optional[MonsterDefinition]:
        """Find a monster definition by name (case-insensitive)."""
        name = name.lower()
        for monster in self.monsters.values():
            if monster.name.lower() == name:
                return monster
        return None

    def get_monsters_in_combat_level_range(
        self, min_level: int, max_level: int
    ) -> List[MonsterDefinition]:
        """Get all monsters within a combat level range."""
        return [
            monster
            for monster in self.monsters.values()
            if min_level <= monster.combat_level <= max_level
        ]

    def get_slayer_monsters(self, slayer_level: int) -> List[MonsterDefinition]:
        """Get all monsters that can be assigned at given slayer level."""
        return [
            monster for monster in self.monsters.values() if monster.slayer_level <= slayer_level
        ]

    def roll_drops(self, monster_def: MonsterDefinition) -> List[str]:
        """Roll for monster drops based on drop rates."""
        drops = []
        for item_id, drop_rate in monster_def.drops.items():
            if random.random() < drop_rate:
                drops.append(item_id)
        return drops
