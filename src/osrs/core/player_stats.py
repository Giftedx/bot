from typing import Dict
from dataclasses import dataclass
import math


@dataclass
class PlayerStats:
    # Combat stats
    attack: int = 1
    strength: int = 1
    defence: int = 1
    ranged: int = 1
    magic: int = 1
    prayer: int = 1
    hitpoints: int = 10

    # Non-combat stats
    mining: int = 1
    smithing: int = 1
    fishing: int = 1
    cooking: int = 1
    woodcutting: int = 1
    firemaking: int = 1
    crafting: int = 1
    fletching: int = 1
    herblore: int = 1
    agility: int = 1
    thieving: int = 1
    slayer: int = 1
    farming: int = 1
    runecrafting: int = 1
    construction: int = 1
    hunter: int = 1

    # Experience values
    attack_xp: float = 0
    strength_xp: float = 0
    defence_xp: float = 0
    ranged_xp: float = 0
    magic_xp: float = 0
    prayer_xp: float = 0
    hitpoints_xp: float = 1154  # Level 10 starting XP
    mining_xp: float = 0
    smithing_xp: float = 0
    fishing_xp: float = 0
    cooking_xp: float = 0
    woodcutting_xp: float = 0
    firemaking_xp: float = 0
    crafting_xp: float = 0
    fletching_xp: float = 0
    herblore_xp: float = 0
    agility_xp: float = 0
    thieving_xp: float = 0
    slayer_xp: float = 0
    farming_xp: float = 0
    runecrafting_xp: float = 0
    construction_xp: float = 0
    hunter_xp: float = 0


class PlayerStatsManager:
    # XP table for levels 1-99
    XP_TABLE = [0]  # Level 1 = 0 XP
    for level in range(1, 99):
        points = 0
        for lvl in range(1, level):
            points += math.floor(lvl + 300 * (2 ** (lvl / 7.0)))
        XP_TABLE.append(math.floor(points / 4))

    @classmethod
    def get_level(cls, xp: float) -> int:
        """Get the level for a given XP amount."""
        for level, req_xp in enumerate(cls.XP_TABLE):
            if xp < req_xp:
                return max(1, level - 1)
        return 99

    @classmethod
    def get_xp_for_level(cls, level: int) -> float:
        """Get the XP required for a given level."""
        if level < 1 or level > 99:
            raise ValueError("Level must be between 1 and 99")
        return cls.XP_TABLE[level - 1]

    @classmethod
    def get_xp_to_next_level(cls, xp: float) -> float:
        """Get the XP remaining until next level."""
        current_level = cls.get_level(xp)
        if current_level >= 99:
            return 0
        next_level_xp = cls.get_xp_for_level(current_level + 1)
        return next_level_xp - xp

    @classmethod
    def get_level_progress(cls, xp: float) -> float:
        """Get the progress to next level as a percentage."""
        current_level = cls.get_level(xp)
        if current_level >= 99:
            return 100.0

        current_level_xp = cls.get_xp_for_level(current_level)
        next_level_xp = cls.get_xp_for_level(current_level + 1)

        xp_in_level = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp

        return (xp_in_level / xp_needed) * 100

    def __init__(self):
        self.xp_rates = {
            # Combat XP rates
            "attack": 4.0,
            "strength": 4.0,
            "defence": 4.0,
            "ranged": 4.0,
            "magic": 4.0,
            "prayer": 4.0,
            "hitpoints": 1.33,  # 1/3 of combat XP
            # Skilling XP rates are defined per action
        }

    def update_stats(self, stats: PlayerStats, skill: str, xp_gained: float) -> bool:
        """
        Update stats with gained XP. Returns True if a level was gained.
        """
        if not hasattr(stats, f"{skill}_xp"):
            raise ValueError(f"Invalid skill: {skill}")

        old_level = getattr(stats, skill)
        old_xp = getattr(stats, f"{skill}_xp")
        new_xp = old_xp + xp_gained

        # Update XP
        setattr(stats, f"{skill}_xp", new_xp)

        # Update level
        new_level = self.get_level(new_xp)
        setattr(stats, skill, new_level)

        return new_level > old_level

    def calculate_combat_xp(self, damage: int, skill: str) -> float:
        """Calculate combat XP gained from dealing damage."""
        base_xp = damage * self.xp_rates[skill]

        # Add hitpoints XP
        if skill in ["attack", "strength", "defence", "ranged", "magic"]:
            hitpoints_xp = damage * self.xp_rates["hitpoints"]
            return base_xp, hitpoints_xp

        return base_xp, 0

    def get_all_levels(self, stats: PlayerStats) -> Dict[str, int]:
        """Get all skill levels as a dictionary."""
        return {skill: getattr(stats, skill) for skill in vars(stats) if not skill.endswith("_xp")}

    def get_total_level(self, stats: PlayerStats) -> int:
        """Get the total level of all skills."""
        return sum(self.get_all_levels(stats).values())

    def get_combat_level(self, stats: PlayerStats) -> int:
        """Calculate combat level based on combat stats."""
        base = 0.25 * (stats.defence + stats.hitpoints + math.floor(stats.prayer / 2))
        melee = 0.325 * (stats.attack + stats.strength)
        ranged = 0.325 * (math.floor(3 * stats.ranged / 2))
        magic = 0.325 * (math.floor(3 * stats.magic / 2))

        return math.floor(base + max(melee, ranged, magic))
