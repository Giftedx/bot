from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class SkillType(Enum):
    """OSRS skill types"""
    ATTACK = "attack"
    DEFENCE = "defence"
    STRENGTH = "strength"
    HITPOINTS = "hitpoints"
    RANGED = "ranged"
    PRAYER = "prayer"
    MAGIC = "magic"
    COOKING = "cooking"
    WOODCUTTING = "woodcutting"
    FLETCHING = "fletching"
    FISHING = "fishing"
    FIREMAKING = "firemaking"
    CRAFTING = "crafting"
    SMITHING = "smithing"
    MINING = "mining"
    HERBLORE = "herblore"
    AGILITY = "agility"
    THIEVING = "thieving"
    SLAYER = "slayer"
    FARMING = "farming"
    RUNECRAFT = "runecraft"
    HUNTER = "hunter"
    CONSTRUCTION = "construction"

class CombatStyle(Enum):
    """Combat attack styles"""
    ACCURATE = "accurate"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CONTROLLED = "controlled"
    RAPID = "rapid"
    LONGRANGE = "longrange"

class AttackType(Enum):
    """Types of attacks"""
    STAB = "stab"
    SLASH = "slash"
    CRUSH = "crush"
    MAGIC = "magic"
    RANGED = "ranged"

class QuestStatus(Enum):
    """Quest completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@dataclass
class Position:
    """World position"""
    x: int
    y: int
    z: int = 0
    region_id: Optional[int] = None

@dataclass
class CombatStats:
    """Combat-related stats"""
    attack: int = 1
    strength: int = 1
    defence: int = 1
    ranged: int = 1
    magic: int = 1
    hitpoints: int = 10
    prayer: int = 1
    
    @property
    def combat_level(self) -> int:
        """Calculate combat level"""
        base = 0.25 * (defence + hitpoints + math.floor(prayer/2))
        melee = 0.325 * (attack + strength)
        range_magic = 0.325 * (math.floor(3*ranged/2) if ranged > magic 
                              else math.floor(3*magic/2))
        return math.floor(base + max(melee, range_magic))

@dataclass
class Equipment:
    """Equipped items"""
    head: Optional[str] = None
    cape: Optional[str] = None
    amulet: Optional[str] = None
    weapon: Optional[str] = None
    body: Optional[str] = None
    shield: Optional[str] = None
    legs: Optional[str] = None
    gloves: Optional[str] = None
    boots: Optional[str] = None
    ring: Optional[str] = None
    ammo: Optional[str] = None

@dataclass
class InventoryItem:
    """Item in inventory"""
    item_id: str
    quantity: int
    slot: int

@dataclass
class BankItem:
    """Item in bank"""
    item_id: str
    quantity: int
    tab: int

@dataclass
class Skills:
    """Skill levels and experience"""
    levels: Dict[SkillType, int]
    experience: Dict[SkillType, int]
    
    @staticmethod
    def level_for_xp(xp: int) -> int:
        """Calculate level from experience"""
        for level in range(1, 100):
            if xp < XP_TABLE[level]:
                return level - 1
        return 99

@dataclass
class GameState:
    """Current state of a player's game"""
    user_id: str
    position: Position
    combat_stats: CombatStats
    equipment: Equipment
    inventory: List[InventoryItem]
    bank: List[BankItem]
    skills: Skills
    quest_progress: Dict[str, QuestStatus]
    achievement_progress: Dict[str, bool]
    is_busy: bool = False
    current_action: Optional[str] = None
    last_action: Optional[datetime] = None

@dataclass
class CombatBonuses:
    """Equipment combat bonuses"""
    attack_stab: int = 0
    attack_slash: int = 0
    attack_crush: int = 0
    attack_magic: int = 0
    attack_ranged: int = 0
    defence_stab: int = 0
    defence_slash: int = 0
    defence_crush: int = 0
    defence_magic: int = 0
    defence_ranged: int = 0
    melee_strength: int = 0
    ranged_strength: int = 0
    magic_damage: float = 0
    prayer: int = 0

@dataclass
class ActionResult:
    """Result of a game action"""
    success: bool
    message: str
    experience_gained: Dict[SkillType, int] = None
    items_gained: List[InventoryItem] = None
    items_lost: List[InventoryItem] = None
    state_updates: Dict[str, Any] = None

# Experience table
XP_TABLE = {
    1: 0,
    2: 83,
    3: 174,
    # ... (complete XP table)
    98: 11_805_606,
    99: 13_034_431
}

# Prayer bonuses
PRAYER_BONUSES = {
    "thick_skin": 0.05,
    "rock_skin": 0.10,
    "steel_skin": 0.15,
    "clarity_of_thought": 0.05,
    "improved_reflexes": 0.10,
    "incredible_reflexes": 0.15,
    "burst_of_strength": 0.05,
    "superhuman_strength": 0.10,
    "ultimate_strength": 0.15,
    "mystic_will": 0.05,
    "mystic_lore": 0.10,
    "mystic_might": 0.15,
    "sharp_eye": 0.05,
    "hawk_eye": 0.10,
    "eagle_eye": 0.15,
    "protect_item": 0,
    "protect_from_magic": 1,
    "protect_from_missiles": 1,
    "protect_from_melee": 1,
    "retribution": 0,
    "redemption": 0,
    "smite": 0
}

# Combat formulas
def calculate_max_hit(
    strength_level: int,
    equipment_bonus: int,
    prayer_bonus: float = 1.0,
    other_bonus: float = 1.0
) -> int:
    """Calculate maximum melee hit"""
    effective_level = math.floor(strength_level * prayer_bonus) + 8
    base = math.floor(effective_level * (equipment_bonus + 64) / 640)
    return math.floor(base * other_bonus)

def calculate_hit_chance(
    attack_level: int,
    equipment_bonus: int,
    target_defence: int,
    target_bonus: int,
    prayer_bonus: float = 1.0
) -> float:
    """Calculate chance to hit"""
    effective_attack = math.floor(attack_level * prayer_bonus) + 8
    attack_roll = effective_attack * (equipment_bonus + 64)
    
    effective_defence = target_defence + 8
    defence_roll = effective_defence * (target_bonus + 64)
    
    if attack_roll > defence_roll:
        return 1 - (defence_roll + 2) / (2 * (attack_roll + 1))
    else:
        return attack_roll / (2 * (defence_roll + 1)) 