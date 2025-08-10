from typing import Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConsumableEffect:
    heal: int = 0
    attack_boost: int = 0
    strength_boost: int = 0
    defence_boost: int = 0
    ranged_boost: int = 0
    magic_boost: int = 0
    prayer_restore: int = 0
    duration: float = 0  # Duration in minutes, 0 for instant effects
    special_effects: Set[str] = None  # Special effects like anglerfish boost
    cooldown: float = 0  # Cooldown in seconds before next food can be eaten
    combo_food: bool = False  # Can be eaten in combination with other food


class ConsumableItem:
    def __init__(
        self, name: str, effect: ConsumableEffect, level_req: int = 1, description: str = ""
    ):
        self.name = name
        self.effect = effect
        self.level_req = level_req
        self.description = description
        self.last_consumed: Optional[datetime] = None


class ConsumableDatabase:
    """Database of all consumable items."""

    FOOD = {
        # Basic Food
        "shrimps": ConsumableItem(
            name="Shrimps",
            effect=ConsumableEffect(heal=3, cooldown=1.8),
            description="A nice little fish.",
        ),
        "cooked_chicken": ConsumableItem(
            name="Cooked Chicken",
            effect=ConsumableEffect(heal=3, cooldown=1.8),
            description="Mmm, chicken...",
        ),
        "cooked_meat": ConsumableItem(
            name="Cooked Meat",
            effect=ConsumableEffect(heal=3, cooldown=1.8),
            description="Some nicely cooked beef.",
        ),
        "sardine": ConsumableItem(
            name="Sardine",
            effect=ConsumableEffect(heal=4, cooldown=1.8),
            description="A small fish.",
        ),
        "herring": ConsumableItem(
            name="Herring",
            effect=ConsumableEffect(heal=5, cooldown=1.8),
            description="A tasty fish.",
        ),
        "mackerel": ConsumableItem(
            name="Mackerel",
            effect=ConsumableEffect(heal=6, cooldown=1.8),
            description="A nice fish.",
        ),
        "trout": ConsumableItem(
            name="Trout",
            effect=ConsumableEffect(heal=7, cooldown=1.8),
            description="A freshwater fish.",
        ),
        "cod": ConsumableItem(
            name="Cod", effect=ConsumableEffect(heal=7, cooldown=1.8), description="A big fish."
        ),
        "pike": ConsumableItem(
            name="Pike", effect=ConsumableEffect(heal=8, cooldown=1.8), description="A long fish."
        ),
        "salmon": ConsumableItem(
            name="Salmon",
            effect=ConsumableEffect(heal=9, cooldown=1.8),
            description="A healthy fish.",
        ),
        "tuna": ConsumableItem(
            name="Tuna", effect=ConsumableEffect(heal=10, cooldown=1.8), description="A big fish."
        ),
        "lobster": ConsumableItem(
            name="Lobster",
            effect=ConsumableEffect(heal=12, cooldown=1.8),
            description="A delicious crustacean.",
        ),
        "bass": ConsumableItem(
            name="Bass", effect=ConsumableEffect(heal=13, cooldown=1.8), description="A tasty fish."
        ),
        "swordfish": ConsumableItem(
            name="Swordfish",
            effect=ConsumableEffect(heal=14, cooldown=1.8),
            description="A mighty fish.",
        ),
        "monkfish": ConsumableItem(
            name="Monkfish",
            effect=ConsumableEffect(heal=16, cooldown=1.8),
            description="A rare fish.",
        ),
        "shark": ConsumableItem(
            name="Shark",
            effect=ConsumableEffect(heal=20, cooldown=1.8),
            description="A fearsome fish.",
        ),
        "manta_ray": ConsumableItem(
            name="Manta Ray",
            effect=ConsumableEffect(heal=22, cooldown=1.8),
            description="A rare sea creature.",
        ),
        # Special Food
        "karambwan": ConsumableItem(
            name="Karambwan",
            effect=ConsumableEffect(
                heal=18, cooldown=0.6, combo_food=True  # Reduced cooldown  # Can be combo eaten
            ),
            description="A strange, exotic fish.",
        ),
        "anglerfish": ConsumableItem(
            name="Anglerfish",
            effect=ConsumableEffect(
                heal=22, cooldown=1.8, special_effects={"overheal"}  # Can heal above max HP
            ),
            description="A rare deep-sea fish.",
        ),
        "dark_crab": ConsumableItem(
            name="Dark Crab",
            effect=ConsumableEffect(heal=22, cooldown=1.8),
            description="A rare crab from deep waters.",
        ),
        "purple_sweets": ConsumableItem(
            name="Purple Sweets",
            effect=ConsumableEffect(
                heal=3,
                cooldown=0.6,
                combo_food=True,
                special_effects={"run_energy"},  # Restores run energy
            ),
            description="Sweet, energy-restoring candy.",
        ),
    }

    POTIONS = {
        # Regular Combat Potions
        "attack_potion": ConsumableItem(
            name="Attack Potion",
            effect=ConsumableEffect(attack_boost=3, duration=3),
            description="Boosts Attack by 3 levels.",
        ),
        "strength_potion": ConsumableItem(
            name="Strength Potion",
            effect=ConsumableEffect(strength_boost=3, duration=3),
            description="Boosts Strength by 3 levels.",
        ),
        "defence_potion": ConsumableItem(
            name="Defence Potion",
            effect=ConsumableEffect(defence_boost=3, duration=3),
            description="Boosts Defence by 3 levels.",
        ),
        # Super Combat Potions
        "super_attack": ConsumableItem(
            name="Super Attack",
            effect=ConsumableEffect(attack_boost=5, duration=3),
            description="Boosts Attack by 5 levels.",
        ),
        "super_strength": ConsumableItem(
            name="Super Strength",
            effect=ConsumableEffect(strength_boost=5, duration=3),
            description="Boosts Strength by 5 levels.",
        ),
        "super_defence": ConsumableItem(
            name="Super Defence",
            effect=ConsumableEffect(defence_boost=5, duration=3),
            description="Boosts Defence by 5 levels.",
        ),
        "super_combat": ConsumableItem(
            name="Super Combat Potion",
            effect=ConsumableEffect(attack_boost=5, strength_boost=5, defence_boost=5, duration=3),
            description="Boosts all combat stats by 5 levels.",
        ),
        # Ranged Potions
        "ranging_potion": ConsumableItem(
            name="Ranging Potion",
            effect=ConsumableEffect(ranged_boost=4, duration=3),
            description="Boosts Ranged by 4 levels.",
        ),
        # Magic Potions
        "magic_potion": ConsumableItem(
            name="Magic Potion",
            effect=ConsumableEffect(magic_boost=4, duration=3),
            description="Boosts Magic by 4 levels.",
        ),
        # Prayer Potions
        "prayer_potion": ConsumableItem(
            name="Prayer Potion",
            effect=ConsumableEffect(prayer_restore=7),
            description="Restores 7 Prayer points.",
        ),
        "super_restore": ConsumableItem(
            name="Super Restore",
            effect=ConsumableEffect(
                prayer_restore=8,
                attack_boost=8,
                strength_boost=8,
                defence_boost=8,
                ranged_boost=8,
                magic_boost=8,
            ),
            description="Restores all stats and Prayer points.",
        ),
        # Combination Potions
        "divine_super_combat": ConsumableItem(
            name="Divine Super Combat Potion",
            effect=ConsumableEffect(
                attack_boost=5,
                strength_boost=5,
                defence_boost=5,
                duration=5,
                special_effects={"divine"},  # Maintains boost
            ),
            description="Maintains combat stat boosts.",
        ),
        "divine_ranging": ConsumableItem(
            name="Divine Ranging Potion",
            effect=ConsumableEffect(ranged_boost=4, duration=5, special_effects={"divine"}),
            description="Maintains ranged boost.",
        ),
        "divine_magic": ConsumableItem(
            name="Divine Magic Potion",
            effect=ConsumableEffect(magic_boost=4, duration=5, special_effects={"divine"}),
            description="Maintains magic boost.",
        ),
        # Saradomin Brews
        "saradomin_brew": ConsumableItem(
            name="Saradomin Brew",
            effect=ConsumableEffect(
                heal=16,
                defence_boost=2,
                attack_boost=-2,
                strength_boost=-2,
                ranged_boost=-2,
                magic_boost=-2,
                duration=3,
                special_effects={"overheal"},
            ),
            description="Heals and boosts Defence, but lowers other combat stats.",
        ),
        # Zamorak Brews
        "zamorak_brew": ConsumableItem(
            name="Zamorak Brew",
            effect=ConsumableEffect(
                attack_boost=2,
                strength_boost=2,
                defence_boost=-2,
                duration=2,
                special_effects={"damage"},  # Deals damage
            ),
            description="Boosts Attack and Strength, but lowers Defence.",
        ),
    }


class ConsumableManager:
    def __init__(self):
        self.database = ConsumableDatabase()
        self.active_effects: Dict[str, ConsumableEffect] = {}
        self.last_food_time: Optional[datetime] = None

    def get_food(self, name: str) -> Optional[ConsumableItem]:
        """Get food item by name."""
        return self.database.FOOD.get(name.lower())

    def get_potion(self, name: str) -> Optional[ConsumableItem]:
        """Get potion by name."""
        return self.database.POTIONS.get(name.lower())

    def can_consume_food(self, food: ConsumableItem) -> bool:
        """Check if food can be consumed based on cooldowns."""
        now = datetime.utcnow()

        # Check food's own cooldown
        if food.last_consumed:
            time_since_consumed = (now - food.last_consumed).total_seconds()
            if time_since_consumed < food.effect.cooldown:
                return False

        # Check global food cooldown
        if self.last_food_time and not food.effect.combo_food:
            time_since_food = (now - self.last_food_time).total_seconds()
            if time_since_food < 1.8:  # Global food cooldown
                return False

        return True

    def consume_food(self, name: str) -> Optional[ConsumableEffect]:
        """Consume a food item and get its effect."""
        food = self.get_food(name)
        if not food or not self.can_consume_food(food):
            return None

        # Update cooldowns
        now = datetime.utcnow()
        food.last_consumed = now
        if not food.effect.combo_food:
            self.last_food_time = now

        return food.effect

    def consume_potion(self, name: str) -> Optional[ConsumableEffect]:
        """Consume a potion and get its effect."""
        potion = self.get_potion(name)
        if not potion:
            return None

        effect = potion.effect
        if effect.duration > 0:
            # Handle divine potions
            if effect.special_effects and "divine" in effect.special_effects:
                # Remove any existing divine effects
                self.active_effects = {
                    name: effect
                    for name, effect in self.active_effects.items()
                    if not (effect.special_effects and "divine" in effect.special_effects)
                }

            self.active_effects[name] = effect

        return effect

    def update_effects(self, delta_time: float):
        """Update active effects based on time passed (in minutes)."""
        expired = []
        for name, effect in self.active_effects.items():
            effect.duration -= delta_time

            # Handle divine potions
            if effect.special_effects and "divine" in effect.special_effects:
                if effect.duration <= 0:
                    effect.duration = effect.duration % 5  # Reset duration

            elif effect.duration <= 0:
                expired.append(name)

        for name in expired:
            del self.active_effects[name]

    def get_combined_boosts(self) -> ConsumableEffect:
        """Get combined stat boosts from all active effects."""
        combined = ConsumableEffect()

        for effect in self.active_effects.values():
            combined.attack_boost = max(combined.attack_boost, effect.attack_boost)
            combined.strength_boost = max(combined.strength_boost, effect.strength_boost)
            combined.defence_boost = max(combined.defence_boost, effect.defence_boost)
            combined.ranged_boost = max(combined.ranged_boost, effect.ranged_boost)
            combined.magic_boost = max(combined.magic_boost, effect.magic_boost)

            # Combine special effects
            if effect.special_effects:
                if not combined.special_effects:
                    combined.special_effects = set()
                combined.special_effects.update(effect.special_effects)

        return combined

    def clear_effects(self):
        """Clear all active effects."""
        self.active_effects.clear()
