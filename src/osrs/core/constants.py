"""Core constants and enums for OSRS."""
from enum import Enum, auto
from dataclasses import dataclass


class SkillType(Enum):
    """OSRS skill types."""

    ATTACK = "attack"
    STRENGTH = "strength"
    DEFENCE = "defence"
    RANGED = "ranged"
    PRAYER = "prayer"
    MAGIC = "magic"
    RUNECRAFT = "runecraft"
    HITPOINTS = "hitpoints"
    CRAFTING = "crafting"
    MINING = "mining"
    SMITHING = "smithing"
    FISHING = "fishing"
    COOKING = "cooking"
    FIREMAKING = "firemaking"
    WOODCUTTING = "woodcutting"
    AGILITY = "agility"
    HERBLORE = "herblore"
    THIEVING = "thieving"
    FLETCHING = "fletching"
    SLAYER = "slayer"
    FARMING = "farming"
    CONSTRUCTION = "construction"
    HUNTER = "hunter"
    SHARED = "shared"  # For shared XP gains


@dataclass
class SkillLevel:
    """Represents a skill's level and experience."""

    type: SkillType
    level: int = 1
    xp: int = 0

    def add_xp(self, amount: int) -> bool:
        """Add XP to the skill and return True if leveled up."""
        self.xp += amount
        old_level = self.level
        self.level = self._xp_to_level(self.xp)
        return self.level > old_level

    @staticmethod
    def _xp_to_level(xp: int) -> int:
        """Convert XP to level using OSRS formula."""
        for level in range(1, 100):
            if xp < SkillLevel.xp_for_level(level):
                return level - 1
        return 99

    @staticmethod
    def xp_for_level(level: int) -> int:
        """Calculate XP required for a given level using OSRS formula."""
        total = 0
        for i in range(1, level):
            total += int(i + 300 * (2 ** (i / 7.0)))
        return int(total / 4)


class BitField(Enum):
    """User bitfield flags."""

    MINION_IRONMAN = auto()
    BOUGHT_INFINITE_AGILITY = auto()
    BOUGHT_TIER_1_BANK = auto()
    BOUGHT_TIER_2_BANK = auto()
    BOUGHT_TIER_3_BANK = auto()
    BOUGHT_TIER_4_BANK = auto()
    BOUGHT_TIER_5_BANK = auto()
    BOUGHT_TIER_6_BANK = auto()
    BOUGHT_TIER_7_BANK = auto()
    BOUGHT_TIER_8_BANK = auto()
    BOUGHT_TIER_9_BANK = auto()
    BOUGHT_TIER_10_BANK = auto()
    BOUGHT_FARMERS_OUTFIT = auto()
    BOUGHT_GRACEFUL_RECOLOR = auto()
    BOUGHT_HERB_SACK = auto()
    BOUGHT_GEM_BAG = auto()
    BOUGHT_COAL_BAG = auto()
    BOUGHT_BIGGER_SACK = auto()
    BOUGHT_BIGGER_COFFERS = auto()
    BOUGHT_STAMINA_POOL = auto()
    BOUGHT_RUNE_POUCH = auto()
    COMBAT_ACHIEVEMENTS_BANNER = auto()
    HAS_CRAFTED_MAX_CAPE = auto()
    HAS_BOUGHT_QUEST_CAPE = auto()
    HAS_BOUGHT_MUSIC_CAPE = auto()
    HAS_BOUGHT_ACHIEVEMENT_DIARY_CAPE = auto()
    HAS_BOUGHT_CHAMPIONS_CAPE = auto()
    HAS_BOUGHT_MAX_CAPE = auto()
    HAS_UNLOCKED_PRIFDDINAS = auto()
    HAS_COMPLETED_DRAGON_SLAYER = auto()
    HAS_COMPLETED_MONKEY_MADNESS = auto()
    HAS_COMPLETED_DESERT_TREASURE = auto()
    HAS_COMPLETED_LEGENDS_QUEST = auto()
    HAS_COMPLETED_RECIPE_FOR_DISASTER = auto()
    HAS_COMPLETED_DREAM_MENTOR = auto()
    HAS_COMPLETED_LUNAR_DIPLOMACY = auto()
    HAS_COMPLETED_KINGS_RANSOM = auto()
    HAS_COMPLETED_HORROR_FROM_DEEP = auto()
    HAS_COMPLETED_ANIMAL_MAGNETISM = auto()
    HAS_COMPLETED_BONE_VOYAGE = auto()
    HAS_COMPLETED_FAIRYTALE_II = auto()
    HAS_COMPLETED_FAMILY_CREST = auto()
    HAS_COMPLETED_HEROES_QUEST = auto()
    HAS_COMPLETED_LOST_CITY = auto()
    HAS_COMPLETED_MONKEY_MADNESS_II = auto()
    HAS_COMPLETED_MOURNINGS_END_PART_II = auto()
    HAS_COMPLETED_REGICIDE = auto()
    HAS_COMPLETED_ROVING_ELVES = auto()
    HAS_COMPLETED_SWAN_SONG = auto()
    HAS_COMPLETED_TAI_BWO_WANNAI_TRIO = auto()
    HAS_COMPLETED_THRONE_OF_MISCELLANIA = auto()
    HAS_COMPLETED_TREE_GNOME_VILLAGE = auto()
    HAS_COMPLETED_UNDERGROUND_PASS = auto()
    HAS_COMPLETED_WATCHTOWER = auto()
    HAS_COMPLETED_WATERFALL_QUEST = auto()
    HAS_COMPLETED_WHAT_LIES_BELOW = auto()
    HAS_COMPLETED_DRAGON_SLAYER_II = auto()
    HAS_COMPLETED_SONG_OF_THE_ELVES = auto()
    HAS_COMPLETED_SINS_OF_THE_FATHER = auto()
    HAS_COMPLETED_A_KINGDOM_DIVIDED = auto()
    HAS_COMPLETED_BENEATH_CURSED_SANDS = auto()
    HAS_COMPLETED_LAND_OF_THE_GOBLINS = auto()
    HAS_COMPLETED_TEMPLE_OF_THE_EYE = auto()
    HAS_COMPLETED_SECRETS_OF_THE_NORTH = auto()
    HAS_COMPLETED_DESERT_TREASURE_II = auto()
    HAS_COMPLETED_SLEEPING_GIANTS = auto()
    HAS_COMPLETED_TWILIGHT_CURSE = auto()
    HAS_COMPLETED_CHILDREN_OF_THE_SUN = auto()
    HAS_COMPLETED_PATH_OF_GLOUPHRIE = auto()
    HAS_COMPLETED_SECRETS_OF_THE_NORTH_II = auto()
    HAS_COMPLETED_QUEST_POINT_CAPE = auto()
    HAS_COMPLETED_ACHIEVEMENT_DIARY_CAPE = auto()
    HAS_COMPLETED_MUSIC_CAPE = auto()
    HAS_COMPLETED_MAX_CAPE = auto()
    HAS_COMPLETED_CHAMPIONS_CAPE = auto()
    HAS_COMPLETED_INFERNAL_CAPE = auto()
    HAS_COMPLETED_FIRE_CAPE = auto()
    HAS_COMPLETED_MYTHICAL_CAPE = auto()
    HAS_COMPLETED_ARDOUGNE_CLOAK_4 = auto()
    HAS_COMPLETED_DESERT_AMULET_4 = auto()
    HAS_COMPLETED_FALADOR_SHIELD_4 = auto()
    HAS_COMPLETED_FREMENNIK_BOOTS_4 = auto()
    HAS_COMPLETED_KANDARIN_HEADGEAR_4 = auto()
    HAS_COMPLETED_KARAMJA_GLOVES_4 = auto()
    HAS_COMPLETED_LUMBRIDGE_DIARY_4 = auto()
    HAS_COMPLETED_MORYTANIA_LEGS_4 = auto()
    HAS_COMPLETED_VARROCK_ARMOUR_4 = auto()
    HAS_COMPLETED_WESTERN_BANNER_4 = auto()
    HAS_COMPLETED_WILDERNESS_SWORD_4 = auto()
    HAS_COMPLETED_KOUREND_BLESSING_4 = auto()
    HAS_COMPLETED_COMBAT_TASK_GRANDMASTER = auto()
    HAS_COMPLETED_COMBAT_TASK_MASTER = auto()
    HAS_COMPLETED_COMBAT_TASK_ELITE = auto()
    HAS_COMPLETED_COMBAT_TASK_HARD = auto()
    HAS_COMPLETED_COMBAT_TASK_MEDIUM = auto()
    HAS_COMPLETED_COMBAT_TASK_EASY = auto()
    HAS_COMPLETED_COLLECTION_LOG = auto()
    HAS_COMPLETED_ALL_PETS = auto()
    HAS_COMPLETED_ALL_CLUES = auto()
    HAS_COMPLETED_ALL_MINIGAMES = auto()
    HAS_COMPLETED_ALL_RAIDS = auto()
    HAS_COMPLETED_ALL_BOSSES = auto()
    HAS_COMPLETED_ALL_SLAYER = auto()
    HAS_COMPLETED_ALL_SKILLING = auto()
    HAS_COMPLETED_ALL_QUESTS = auto()
    HAS_COMPLETED_ALL_DIARIES = auto()
    HAS_COMPLETED_ALL_MUSIC = auto()
    HAS_COMPLETED_ALL_COMBAT_TASKS = auto()
    HAS_COMPLETED_ALL_COLLECTION_LOG = auto()
    HAS_COMPLETED_ALL_PETS_COLLECTION = auto()
    HAS_COMPLETED_ALL_CLUES_COLLECTION = auto()
    HAS_COMPLETED_ALL_MINIGAMES_COLLECTION = auto()
    HAS_COMPLETED_ALL_RAIDS_COLLECTION = auto()
    HAS_COMPLETED_ALL_BOSSES_COLLECTION = auto()
    HAS_COMPLETED_ALL_SLAYER_COLLECTION = auto()
    HAS_COMPLETED_ALL_SKILLING_COLLECTION = auto()
    HAS_COMPLETED_ALL_QUESTS_COLLECTION = auto()
    HAS_COMPLETED_ALL_DIARIES_COLLECTION = auto()
    HAS_COMPLETED_ALL_MUSIC_COLLECTION = auto()
    HAS_COMPLETED_ALL_COMBAT_TASKS_COLLECTION = auto()
