from typing import Dict, Optional, Set, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PrayerBonus:
    attack: float = 1.0
    strength: float = 1.0
    defence: float = 1.0
    ranged_attack: float = 1.0
    ranged_strength: float = 1.0
    magic_attack: float = 1.0
    magic_strength: float = 1.0
    protection: float = 0.0  # Damage reduction percentage
    leech: float = 0.0  # Stat drain percentage
    smite: float = 0.0  # Prayer drain on hit


class Prayer:
    def __init__(
        self,
        name: str,
        level_req: int,
        drain_rate: float,
        bonuses: PrayerBonus,
        description: str,
        prayer_book: str = "normal",
        overhead: bool = False,
    ):
        self.name = name
        self.level_req = level_req
        self.drain_rate = drain_rate  # Points per minute
        self.bonuses = bonuses
        self.description = description
        self.prayer_book = prayer_book
        self.overhead = overhead
        self.last_flick: Optional[datetime] = None
        self.flick_active: bool = False


class PrayerBook:
    """Contains all available prayers and their effects."""

    PRAYERS = {
        # Protection Prayers
        "protect_from_melee": Prayer(
            name="Protect from Melee",
            level_req=43,
            drain_rate=12,
            bonuses=PrayerBonus(protection=0.4),
            description="Protects against melee attacks",
            overhead=True,
        ),
        "protect_from_missiles": Prayer(
            name="Protect from Missiles",
            level_req=40,
            drain_rate=12,
            bonuses=PrayerBonus(protection=0.4),
            description="Protects against ranged attacks",
            overhead=True,
        ),
        "protect_from_magic": Prayer(
            name="Protect from Magic",
            level_req=37,
            drain_rate=12,
            bonuses=PrayerBonus(protection=0.4),
            description="Protects against magic attacks",
            overhead=True,
        ),
        # Combat Prayers
        "thick_skin": Prayer(
            name="Thick Skin",
            level_req=1,
            drain_rate=3,
            bonuses=PrayerBonus(defence=1.05),
            description="+5% Defence",
        ),
        "burst_of_strength": Prayer(
            name="Burst of Strength",
            level_req=4,
            drain_rate=3,
            bonuses=PrayerBonus(strength=1.05),
            description="+5% Strength",
        ),
        "clarity_of_thought": Prayer(
            name="Clarity of Thought",
            level_req=7,
            drain_rate=3,
            bonuses=PrayerBonus(attack=1.05),
            description="+5% Attack",
        ),
        # Improved Combat Prayers
        "rock_skin": Prayer(
            name="Rock Skin",
            level_req=10,
            drain_rate=6,
            bonuses=PrayerBonus(defence=1.10),
            description="+10% Defence",
        ),
        "superhuman_strength": Prayer(
            name="Superhuman Strength",
            level_req=13,
            drain_rate=6,
            bonuses=PrayerBonus(strength=1.10),
            description="+10% Strength",
        ),
        "improved_reflexes": Prayer(
            name="Improved Reflexes",
            level_req=16,
            drain_rate=6,
            bonuses=PrayerBonus(attack=1.10),
            description="+10% Attack",
        ),
        # Advanced Combat Prayers
        "steel_skin": Prayer(
            name="Steel Skin",
            level_req=28,
            drain_rate=12,
            bonuses=PrayerBonus(defence=1.15),
            description="+15% Defence",
        ),
        "ultimate_strength": Prayer(
            name="Ultimate Strength",
            level_req=31,
            drain_rate=12,
            bonuses=PrayerBonus(strength=1.15),
            description="+15% Strength",
        ),
        "incredible_reflexes": Prayer(
            name="Incredible Reflexes",
            level_req=34,
            drain_rate=12,
            bonuses=PrayerBonus(attack=1.15),
            description="+15% Attack",
        ),
        # Ranged Prayers
        "sharp_eye": Prayer(
            name="Sharp Eye",
            level_req=8,
            drain_rate=3,
            bonuses=PrayerBonus(ranged_attack=1.05, ranged_strength=1.05),
            description="+5% Ranged Attack and Strength",
        ),
        "hawk_eye": Prayer(
            name="Hawk Eye",
            level_req=26,
            drain_rate=6,
            bonuses=PrayerBonus(ranged_attack=1.10, ranged_strength=1.10),
            description="+10% Ranged Attack and Strength",
        ),
        "eagle_eye": Prayer(
            name="Eagle Eye",
            level_req=44,
            drain_rate=12,
            bonuses=PrayerBonus(ranged_attack=1.15, ranged_strength=1.15),
            description="+15% Ranged Attack and Strength",
        ),
        # Magic Prayers
        "mystic_will": Prayer(
            name="Mystic Will",
            level_req=9,
            drain_rate=3,
            bonuses=PrayerBonus(magic_attack=1.05, magic_strength=1.05),
            description="+5% Magic Attack and Damage",
        ),
        "mystic_lore": Prayer(
            name="Mystic Lore",
            level_req=27,
            drain_rate=6,
            bonuses=PrayerBonus(magic_attack=1.10, magic_strength=1.10),
            description="+10% Magic Attack and Damage",
        ),
        "mystic_might": Prayer(
            name="Mystic Might",
            level_req=45,
            drain_rate=12,
            bonuses=PrayerBonus(magic_attack=1.15, magic_strength=1.15),
            description="+15% Magic Attack and Damage",
        ),
        # Special Prayers
        "smite": Prayer(
            name="Smite",
            level_req=52,
            drain_rate=18,
            bonuses=PrayerBonus(smite=0.25),  # Drain 1/4 of damage dealt
            description="Drain prayer points from opponents",
            overhead=True,
        ),
        # Ancient Curses
        "sap_warrior": Prayer(
            name="Sap Warrior",
            level_req=50,
            drain_rate=12,
            bonuses=PrayerBonus(leech=0.1),
            description="Drains 10% of enemy Attack and Strength",
            prayer_book="curses",
        ),
        "sap_ranger": Prayer(
            name="Sap Ranger",
            level_req=52,
            drain_rate=12,
            bonuses=PrayerBonus(leech=0.1),
            description="Drains 10% of enemy Ranged",
            prayer_book="curses",
        ),
        "sap_mage": Prayer(
            name="Sap Mage",
            level_req=54,
            drain_rate=12,
            bonuses=PrayerBonus(leech=0.1),
            description="Drains 10% of enemy Magic",
            prayer_book="curses",
        ),
        "leech_attack": Prayer(
            name="Leech Attack",
            level_req=65,
            drain_rate=18,
            bonuses=PrayerBonus(leech=0.15, attack=1.05),
            description="Drains and steals 15% of enemy Attack",
            prayer_book="curses",
        ),
        "leech_strength": Prayer(
            name="Leech Strength",
            level_req=65,
            drain_rate=18,
            bonuses=PrayerBonus(leech=0.15, strength=1.05),
            description="Drains and steals 15% of enemy Strength",
            prayer_book="curses",
        ),
        "leech_defence": Prayer(
            name="Leech Defence",
            level_req=65,
            drain_rate=18,
            bonuses=PrayerBonus(leech=0.15, defence=1.05),
            description="Drains and steals 15% of enemy Defence",
            prayer_book="curses",
        ),
        "leech_ranged": Prayer(
            name="Leech Ranged",
            level_req=68,
            drain_rate=18,
            bonuses=PrayerBonus(leech=0.15, ranged_attack=1.05, ranged_strength=1.05),
            description="Drains and steals 15% of enemy Ranged",
            prayer_book="curses",
        ),
        "leech_magic": Prayer(
            name="Leech Magic",
            level_req=70,
            drain_rate=18,
            bonuses=PrayerBonus(leech=0.15, magic_attack=1.05, magic_strength=1.05),
            description="Drains and steals 15% of enemy Magic",
            prayer_book="curses",
        ),
        "soul_split": Prayer(
            name="Soul Split",
            level_req=92,
            drain_rate=24,
            bonuses=PrayerBonus(leech=0.2),  # Heal for 20% of damage dealt
            description="Heals you for 20% of damage dealt",
            prayer_book="curses",
            overhead=True,
        ),
        "turmoil": Prayer(
            name="Turmoil",
            level_req=95,
            drain_rate=30,
            bonuses=PrayerBonus(leech=0.15, attack=1.23, strength=1.23, defence=1.15),
            description="Drains and massively boosts melee stats",
            prayer_book="curses",
        ),
    }


class PrayerManager:
    def __init__(self):
        self.prayer_book = PrayerBook()
        self.active_prayers: Dict[str, Prayer] = {}
        self.quick_prayers: Set[str] = set()
        self.prayer_points: float = 1.0  # Start with 1 point
        self.current_book: str = "normal"  # or 'curses'
        self.last_flick_check: Optional[datetime] = None

    def can_activate(self, prayer_name: str, prayer_level: int, for_flick: bool = False) -> bool:
        """Check if a prayer can be activated."""
        prayer = self.prayer_book.PRAYERS.get(prayer_name)
        if not prayer:
            return False

        # Check prayer book
        if prayer.prayer_book != self.current_book:
            return False

        # Check level requirement
        if prayer_level < prayer.level_req:
            return False

        # Check prayer points (not needed for flicking)
        if not for_flick and self.prayer_points <= 0:
            return False

        # Check conflicting prayers
        if self._has_conflicting_prayer(prayer_name):
            return False

        return True

    def activate_prayer(self, prayer_name: str, for_flick: bool = False) -> bool:
        """Activate a prayer."""
        prayer = self.prayer_book.PRAYERS.get(prayer_name)
        if not prayer:
            return False

        # Handle prayer flicking
        if for_flick:
            now = datetime.utcnow()
            prayer.last_flick = now
            prayer.flick_active = True
            self.last_flick_check = now

        # Deactivate conflicting prayers
        self._deactivate_conflicting_prayers(prayer_name)

        # Activate the prayer
        self.active_prayers[prayer_name] = prayer
        return True

    def deactivate_prayer(self, prayer_name: str) -> bool:
        """Deactivate a prayer."""
        if prayer_name in self.active_prayers:
            prayer = self.active_prayers[prayer_name]
            prayer.flick_active = False
            del self.active_prayers[prayer_name]
            return True
        return False

    def deactivate_all(self):
        """Deactivate all prayers."""
        for prayer in self.active_prayers.values():
            prayer.flick_active = False
        self.active_prayers.clear()

    def set_quick_prayers(self, prayer_names: List[str]) -> bool:
        """Set quick prayers configuration."""
        valid_prayers = set()
        for name in prayer_names:
            if name in self.prayer_book.PRAYERS:
                valid_prayers.add(name)

        self.quick_prayers = valid_prayers
        return bool(valid_prayers)

    def toggle_quick_prayers(self) -> bool:
        """Toggle all quick prayers on/off."""
        if self.active_prayers:
            self.deactivate_all()
            return False

        success = True
        for prayer_name in self.quick_prayers:
            if not self.activate_prayer(prayer_name):
                success = False

        return success

    def switch_prayer_book(self, book: str) -> bool:
        """Switch between normal prayers and curses."""
        if book not in ["normal", "curses"]:
            return False

        if book != self.current_book:
            self.deactivate_all()
            self.current_book = book
            return True

        return False

    def get_combined_bonuses(self) -> PrayerBonus:
        """Get combined bonuses from all active prayers."""
        combined = PrayerBonus()

        for prayer in self.active_prayers.values():
            # Skip prayers that aren't properly flicked
            if prayer.flick_active and not self._is_flick_active(prayer):
                continue

            combined.attack *= prayer.bonuses.attack
            combined.strength *= prayer.bonuses.strength
            combined.defence *= prayer.bonuses.defence
            combined.ranged_attack *= prayer.bonuses.ranged_attack
            combined.ranged_strength *= prayer.bonuses.ranged_strength
            combined.magic_attack *= prayer.bonuses.magic_attack
            combined.magic_strength *= prayer.bonuses.magic_strength
            combined.protection = max(combined.protection, prayer.bonuses.protection)
            combined.leech = max(combined.leech, prayer.bonuses.leech)
            combined.smite = max(combined.smite, prayer.bonuses.smite)

        return combined

    def get_drain_rate(self) -> float:
        """Get total prayer point drain rate per minute."""
        return sum(
            prayer.drain_rate for prayer in self.active_prayers.values() if not prayer.flick_active
        )

    def update_points(self, delta_time: float):
        """Update prayer points based on time passed (in minutes)."""
        now = datetime.utcnow()

        # Update flick status
        if self.last_flick_check:
            time_since_flick = (now - self.last_flick_check).total_seconds()
            if time_since_flick > 0.6:  # 600ms flick window
                for prayer in self.active_prayers.values():
                    if prayer.flick_active:
                        prayer.flick_active = False

        # Calculate drain
        if self.active_prayers:
            drain = self.get_drain_rate() * delta_time
            self.prayer_points = max(0, self.prayer_points - drain)

            # Deactivate all prayers if we run out of points
            if self.prayer_points <= 0:
                self.deactivate_all()

    def restore_points(self, amount: float):
        """Restore prayer points."""
        self.prayer_points = min(99, self.prayer_points + amount)

    def _has_conflicting_prayer(self, prayer_name: str) -> bool:
        """Check if there are any conflicting prayers active."""
        prayer = self.prayer_book.PRAYERS.get(prayer_name)
        if not prayer:
            return False

        # Overhead prayers conflict with each other
        if prayer.overhead:
            return any(p.overhead for p in self.active_prayers.values())

        # Combat style prayers of the same type conflict
        prayer_type = self._get_prayer_type(prayer_name)
        if prayer_type:
            return any(self._get_prayer_type(name) == prayer_type for name in self.active_prayers)

        return False

    def _deactivate_conflicting_prayers(self, prayer_name: str):
        """Deactivate any prayers that conflict with the given prayer."""
        prayer = self.prayer_book.PRAYERS.get(prayer_name)
        if not prayer:
            return

        # Deactivate overhead prayers
        if prayer.overhead:
            for name, active_prayer in list(self.active_prayers.items()):
                if active_prayer.overhead:
                    self.deactivate_prayer(name)

        # Deactivate combat style prayers of the same type
        prayer_type = self._get_prayer_type(prayer_name)
        if prayer_type:
            for name in list(self.active_prayers.keys()):
                if self._get_prayer_type(name) == prayer_type:
                    self.deactivate_prayer(name)

    def _get_prayer_type(self, prayer_name: str) -> Optional[str]:
        """Get the type of a prayer for conflict checking."""
        if "skin" in prayer_name or "reflexes" in prayer_name:
            return "melee_accuracy"
        if "strength" in prayer_name:
            return "melee_strength"
        if "eye" in prayer_name:
            return "ranged"
        if "mystic" in prayer_name:
            return "magic"
        if "leech" in prayer_name:
            return prayer_name.split("_")[1]  # leech_attack -> attack
        if prayer_name == "turmoil":
            return "melee_all"
        return None

    def _is_flick_active(self, prayer: Prayer) -> bool:
        """Check if a prayer flick is currently active."""
        if not prayer.flick_active or not prayer.last_flick:
            return False

        time_since_flick = (datetime.utcnow() - prayer.last_flick).total_seconds()
        return time_since_flick <= 0.6  # 600ms flick window
