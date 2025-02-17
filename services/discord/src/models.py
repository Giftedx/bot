from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class CommandType(Enum):
    """Types of Discord commands"""
    SLASH = "slash"
    USER = "user"
    MESSAGE = "message"

class InteractionType(Enum):
    """Types of Discord interactions"""
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5

@dataclass
class CommandOption:
    """Command option structure"""
    name: str
    description: str
    type: int
    required: bool = False
    choices: Optional[List[Dict[str, str]]] = None

@dataclass
class Command:
    """Discord command structure"""
    name: str
    description: str
    type: CommandType
    options: Optional[List[CommandOption]] = None
    guild_id: Optional[str] = None

@dataclass
class Interaction:
    """Discord interaction structure"""
    id: str
    type: InteractionType
    data: Dict[str, Any]
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    member: Optional[Dict[str, Any]] = None
    user: Optional[Dict[str, Any]] = None

@dataclass
class InteractionResponse:
    """Response to a Discord interaction"""
    type: int
    data: Optional[Dict[str, Any]] = None

@dataclass
class EmbedField:
    """Discord embed field"""
    name: str
    value: str
    inline: bool = False

@dataclass
class Embed:
    """Discord embed structure"""
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    color: Optional[int] = None
    fields: List[EmbedField] = None
    thumbnail: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    footer: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None

@dataclass
class ComponentButton:
    """Discord button component"""
    custom_id: str
    label: str
    style: int
    emoji: Optional[Dict[str, Any]] = None
    disabled: bool = False

@dataclass
class ComponentSelect:
    """Discord select menu component"""
    custom_id: str
    options: List[Dict[str, Any]]
    placeholder: Optional[str] = None
    min_values: int = 1
    max_values: int = 1
    disabled: bool = False

@dataclass
class ActionRow:
    """Discord action row component"""
    components: List[Union[ComponentButton, ComponentSelect]]

# Command Categories
GAME_COMMANDS = {
    "stats": Command(
        name="stats",
        description="View your game statistics",
        type=CommandType.SLASH,
        options=[
            CommandOption(
                name="skill",
                description="Specific skill to view",
                type=3,
                required=False
            )
        ]
    ),
    "inventory": Command(
        name="inventory",
        description="View your inventory",
        type=CommandType.SLASH
    ),
    "equipment": Command(
        name="equipment",
        description="View your equipped items",
        type=CommandType.SLASH
    ),
    "train": Command(
        name="train",
        description="Start training a skill",
        type=CommandType.SLASH,
        options=[
            CommandOption(
                name="skill",
                description="Skill to train",
                type=3,
                required=True,
                choices=[
                    {"name": "Woodcutting", "value": "woodcutting"},
                    {"name": "Mining", "value": "mining"},
                    {"name": "Fishing", "value": "fishing"},
                    {"name": "Crafting", "value": "crafting"},
                    {"name": "Smithing", "value": "smithing"},
                    {"name": "Fletching", "value": "fletching"},
                    {"name": "Herblore", "value": "herblore"},
                    {"name": "Cooking", "value": "cooking"},
                    {"name": "Runecraft", "value": "runecraft"},
                    {"name": "Agility", "value": "agility"},
                    {"name": "Thieving", "value": "thieving"},
                    {"name": "Farming", "value": "farming"},
                    {"name": "Hunter", "value": "hunter"},
                    {"name": "Construction", "value": "construction"},
                    {"name": "Prayer", "value": "prayer"},
                    {"name": "Magic", "value": "magic"}
                ]
            ),
            CommandOption(
                name="method",
                description="Training method",
                type=3,
                required=True
            ),
            CommandOption(
                name="duration",
                description="Training duration in minutes (max 60)",
                type=4,
                required=False
            )
        ]
    ),
    "combat": Command(
        name="combat",
        description="Engage in combat activities",
        type=CommandType.SLASH,
        options=[
            CommandOption(
                name="action",
                description="Combat action to perform",
                type=3,
                required=True,
                choices=[
                    {"name": "Attack NPC", "value": "attack_npc"},
                    {"name": "Auto Combat", "value": "auto_combat"},
                    {"name": "Stop Combat", "value": "stop_combat"}
                ]
            ),
            CommandOption(
                name="target",
                description="Target NPC to attack",
                type=3,
                required=False
            ),
            CommandOption(
                name="style",
                description="Combat style to use",
                type=3,
                required=False,
                choices=[
                    {"name": "Accurate", "value": "accurate"},
                    {"name": "Aggressive", "value": "aggressive"},
                    {"name": "Defensive", "value": "defensive"},
                    {"name": "Controlled", "value": "controlled"}
                ]
            )
        ]
    ),
    "gear": Command(
        name="gear",
        description="Manage your combat gear",
        type=CommandType.SLASH,
        options=[
            CommandOption(
                name="action",
                description="Gear action to perform",
                type=3,
                required=True,
                choices=[
                    {"name": "Equip", "value": "equip"},
                    {"name": "Unequip", "value": "unequip"},
                    {"name": "View Setup", "value": "view"}
                ]
            ),
            CommandOption(
                name="slot",
                description="Equipment slot",
                type=3,
                required=False,
                choices=[
                    {"name": "Weapon", "value": "weapon"},
                    {"name": "Shield", "value": "shield"},
                    {"name": "Head", "value": "head"},
                    {"name": "Body", "value": "body"},
                    {"name": "Legs", "value": "legs"},
                    {"name": "Boots", "value": "boots"},
                    {"name": "Gloves", "value": "gloves"},
                    {"name": "Amulet", "value": "amulet"},
                    {"name": "Ring", "value": "ring"}
                ]
            ),
            CommandOption(
                name="item",
                description="Item to equip",
                type=3,
                required=False
            )
        ]
    ),
    "location": Command(
        name="location",
        description="View or change your location",
        type=CommandType.SLASH,
        options=[
            CommandOption(
                name="action",
                description="Location action",
                type=3,
                required=True,
                choices=[
                    {"name": "View Current", "value": "view"},
                    {"name": "Travel To", "value": "travel"},
                    {"name": "List Areas", "value": "list"}
                ]
            ),
            CommandOption(
                name="destination",
                description="Where to travel",
                type=3,
                required=False
            )
        ]
    ),
    "bank": Command(
        name="bank",
        description="Access your bank",
        type=CommandType.SLASH,
        options=[
            CommandOption(
                name="action",
                description="Bank action",
                type=3,
                required=True,
                choices=[
                    {"name": "View", "value": "view"},
                    {"name": "Deposit", "value": "deposit"},
                    {"name": "Withdraw", "value": "withdraw"}
                ]
            ),
            CommandOption(
                name="item",
                description="Item to deposit/withdraw",
                type=3,
                required=False
            ),
            CommandOption(
                name="amount",
                description="Amount to deposit/withdraw",
                type=4,
                required=False
            )
        ]
    )
}

UTILITY_COMMANDS = {
    "help": Command(
        name="help",
        description="Show help information",
        type=CommandType.SLASH,
        options=[
            CommandOption(
                name="command",
                description="Specific command to get help for",
                type=3,
                required=False
            )
        ]
    ),
    "profile": Command(
        name="profile",
        description="View or edit your profile",
        type=CommandType.SLASH,
        options=[
            CommandOption(
                name="action",
                description="Action to perform",
                type=3,
                required=True,
                choices=[
                    {"name": "view", "value": "view"},
                    {"name": "edit", "value": "edit"}
                ]
            )
        ]
    )
}

# Skilling Locations
TRAINING_LOCATIONS = {
    "woodcutting": [
        {"name": "Lumbridge Trees", "level": 1, "trees": ["Tree", "Oak"]},
        {"name": "Draynor Village", "level": 15, "trees": ["Willow"]},
        {"name": "Varrock", "level": 1, "trees": ["Tree", "Oak", "Willow"]},
        {"name": "Seers Village", "level": 30, "trees": ["Maple"]},
        {"name": "Woodcutting Guild", "level": 60, "trees": ["Yew", "Magic"]},
        {"name": "Isafdar", "level": 75, "trees": ["Magic", "Crystal"]}
    ],
    "mining": [
        {"name": "Lumbridge Swamp", "level": 1, "ores": ["Copper", "Tin"]},
        {"name": "Varrock West", "level": 15, "ores": ["Iron"]},
        {"name": "Al Kharid", "level": 1, "ores": ["Copper", "Tin", "Iron"]},
        {"name": "Mining Guild", "level": 60, "ores": ["Coal", "Mithril"]},
        {"name": "Wilderness Rune Rocks", "level": 85, "ores": ["Runite"]},
        {"name": "Motherlode Mine", "level": 30, "ores": ["Mixed Ores", "Gold Nuggets"]}
    ],
    "fishing": [
        {"name": "Lumbridge", "level": 1, "spots": ["Shrimp", "Anchovies"]},
        {"name": "Draynor Village", "level": 15, "spots": ["Shrimp", "Sardine", "Herring"]},
        {"name": "Karamja", "level": 30, "spots": ["Tuna", "Lobster"]},
        {"name": "Fishing Guild", "level": 68, "spots": ["Shark"]},
        {"name": "Deep Sea Platform", "level": 80, "spots": ["Anglerfish"]},
        {"name": "Infernal Eels", "level": 80, "spots": ["Infernal Eel"]}
    ],
    "crafting": [
        {"name": "Lumbridge Spinning", "level": 1, "methods": ["Wool Spinning", "Flax Spinning"]},
        {"name": "Al Kharid Furnace", "level": 1, "methods": ["Silver Jewelry", "Gold Jewelry"]},
        {"name": "Edgeville Furnace", "level": 20, "methods": ["Sapphire", "Emerald", "Ruby"]},
        {"name": "Crafting Guild", "level": 40, "methods": ["Green D'hide", "Blue D'hide", "Red D'hide"]}
    ],
    "smithing": [
        {"name": "Lumbridge Furnace", "level": 1, "methods": ["Bronze Bars", "Iron Bars"]},
        {"name": "Al Kharid Furnace", "level": 15, "methods": ["Steel Bars", "Mithril Bars"]},
        {"name": "Edgeville Furnace", "level": 30, "methods": ["Steel Platebody", "Mithril Platebody"]},
        {"name": "Blast Furnace", "level": 60, "methods": ["Rune Bars", "Adamant Bars"]}
    ],
    "fletching": [
        {"name": "Anywhere", "level": 1, "methods": ["Arrow Shafts", "Shortbow", "Longbow"]},
        {"name": "Grand Exchange", "level": 20, "methods": ["Oak Shortbow", "Oak Longbow"]},
        {"name": "Seers Village", "level": 40, "methods": ["Maple Shortbow", "Maple Longbow"]},
        {"name": "Fletching Guild", "level": 60, "methods": ["Magic Shortbow", "Magic Longbow"]}
    ],
    "herblore": [
        {"name": "Anywhere", "level": 1, "methods": ["Attack Potion", "Strength Potion"]},
        {"name": "Grand Exchange", "level": 20, "methods": ["Energy Potion", "Combat Potion"]},
        {"name": "Nardah", "level": 40, "methods": ["Prayer Potion", "Super Attack"]},
        {"name": "Herblore Guild", "level": 60, "methods": ["Super Restore", "Saradomin Brew"]}
    ],
    "cooking": [
        {"name": "Lumbridge Kitchen", "level": 1, "methods": ["Shrimp", "Meat", "Chicken"]},
        {"name": "Al Kharid", "level": 15, "methods": ["Trout", "Salmon"]},
        {"name": "Catherby", "level": 30, "methods": ["Lobster", "Swordfish"]},
        {"name": "Cooking Guild", "level": 60, "methods": ["Shark", "Anglerfish"]}
    ],
    "runecraft": [
        {"name": "Air Altar", "level": 1, "methods": ["Air Runes"]},
        {"name": "Water Altar", "level": 5, "methods": ["Water Runes"]},
        {"name": "Law Altar", "level": 54, "methods": ["Law Runes"]},
        {"name": "Blood Altar", "level": 77, "methods": ["Blood Runes"]}
    ],
    "agility": [
        {"name": "Gnome Stronghold", "level": 1, "methods": ["Gnome Course"]},
        {"name": "Draynor Village", "level": 10, "methods": ["Rooftop Course"]},
        {"name": "Seers Village", "level": 60, "methods": ["Rooftop Course"]},
        {"name": "Ardougne", "level": 90, "methods": ["Rooftop Course"]}
    ],
    "thieving": [
        {"name": "Lumbridge", "level": 1, "methods": ["Men", "Women"]},
        {"name": "Ardougne Market", "level": 20, "methods": ["Stalls", "Knights"]},
        {"name": "Pyramid Plunder", "level": 50, "methods": ["Mummy", "Urns"]},
        {"name": "Dorgesh-Kaan", "level": 80, "methods": ["Rich Chests"]}
    ],
    "farming": [
        {"name": "Lumbridge", "level": 1, "methods": ["Potato", "Onion", "Cabbage"]},
        {"name": "Catherby", "level": 15, "methods": ["Tomato", "Sweetcorn"]},
        {"name": "Farming Guild", "level": 45, "methods": ["Snapdragon", "Torstol"]},
        {"name": "Tree Patches", "level": 75, "methods": ["Magic Trees", "Palm Trees"]}
    ],
    "hunter": [
        {"name": "Feldip Hills", "level": 1, "methods": ["Crimson Swift", "Tropical Wagtail"]},
        {"name": "Piscatoris", "level": 20, "methods": ["Grey Chinchompa"]},
        {"name": "Desert", "level": 40, "methods": ["Orange Salamander"]},
        {"name": "Red Chinchompas", "level": 80, "methods": ["Red Chinchompa"]}
    ],
    "construction": [
        {"name": "Player House", "level": 1, "methods": ["Crude Chair", "Wooden Bookcase"]},
        {"name": "Player House", "level": 20, "methods": ["Oak Furniture"]},
        {"name": "Player House", "level": 50, "methods": ["Teak Furniture"]},
        {"name": "Player House", "level": 75, "methods": ["Mahogany Furniture"]}
    ],
    "prayer": [
        {"name": "Lumbridge Church", "level": 1, "methods": ["Bones"]},
        {"name": "Wilderness Altar", "level": 1, "methods": ["Dragon Bones"]},
        {"name": "Gilded Altar", "level": 1, "methods": ["Dragon Bones", "Superior Bones"]},
        {"name": "Chaos Temple", "level": 1, "methods": ["Superior Dragon Bones"]}
    ],
    "magic": [
        {"name": "Lumbridge", "level": 1, "methods": ["Strike Spells", "Bolt Spells"]},
        {"name": "Wizard Tower", "level": 20, "methods": ["Curse Spells", "Bind Spells"]},
        {"name": "Mage Training Arena", "level": 50, "methods": ["High Alchemy", "Enchanting"]},
        {"name": "Ancient Magicks", "level": 80, "methods": ["Ice Barrage", "Blood Barrage"]}
    ]
}

# Combat Areas
COMBAT_AREAS = {
    "Lumbridge": {
        "npcs": ["Goblin", "Giant Rat", "Cow"],
        "level_range": (1, 10),
        "multi_combat": False
    },
    "Al Kharid": {
        "npcs": ["Warrior", "Scorpion", "Thief"],
        "level_range": (10, 30),
        "multi_combat": False
    },
    "Varrock Sewers": {
        "npcs": ["Giant Spider", "Zombie", "Moss Giant"],
        "level_range": (20, 50),
        "multi_combat": True
    },
    "Edgeville Dungeon": {
        "npcs": ["Hill Giant", "Hobgoblin", "Giant Spider"],
        "level_range": (30, 60),
        "multi_combat": True
    }
}

# Response Templates
ERROR_EMBED = Embed(
    title="Error",
    color=0xFF0000,
    fields=[EmbedField(name="Details", value="An error occurred")]
)

SUCCESS_EMBED = Embed(
    title="Success",
    color=0x00FF00,
    fields=[EmbedField(name="Details", value="Operation completed successfully")]
)

LOADING_EMBED = Embed(
    title="Processing",
    description="Please wait...",
    color=0xFFFF00
)

# Minigames for Skills
SKILL_MINIGAMES = {
    "agility": [
        {
            "name": "Hallowed Sepulchre",
            "level": 52,
            "rewards": ["Dark Graceful", "Ring of Endurance", "Dark Squirrel Pet"],
            "xp_multiplier": 2.0
        },
        {
            "name": "Penguin Agility Course",
            "level": 30,
            "rewards": ["Penguin Suit", "XP Lamps"],
            "xp_multiplier": 1.2
        },
        {
            "name": "Werewolf Agility Course",
            "level": 60,
            "rewards": ["Agile Set", "Mark of Grace"],
            "xp_multiplier": 1.5
        }
    ],
    "fishing": [
        {
            "name": "Fishing Trawler",
            "level": 15,
            "rewards": ["Angler's Outfit", "Fish Barrel", "Spirit Angler's Outfit"],
            "xp_multiplier": 1.3
        },
        {
            "name": "Tempoross",
            "level": 35,
            "rewards": ["Spirit Fish", "Tome of Water", "Fish Barrel", "Tiny Tempor Pet"],
            "xp_multiplier": 1.8
        }
    ],
    "mining": [
        {
            "name": "Volcanic Mine",
            "level": 50,
            "rewards": ["Mining Outfit", "Volcanic Ash", "Ore Pack"],
            "xp_multiplier": 1.6
        },
        {
            "name": "Shooting Stars",
            "level": 10,
            "rewards": ["Star Fragments", "Ring of the Stars", "Celestial Ring"],
            "xp_multiplier": 1.4
        }
    ],
    "thieving": [
        {
            "name": "Sorceress's Garden",
            "level": 1,
            "rewards": ["Sq'irk Juice", "Thieving XP", "Garden Teleport"],
            "xp_multiplier": 1.3
        },
        {
            "name": "Rogues' Den",
            "level": 50,
            "rewards": ["Rogue Outfit", "Rogue's Kit", "Lockpick"],
            "xp_multiplier": 1.2
        }
    ],
    "hunter": [
        {
            "name": "Herbiboar",
            "level": 80,
            "rewards": ["Herblore Ingredients", "Herbi Pet", "Hunter XP"],
            "xp_multiplier": 1.7
        }
    ],
    "runecraft": [
        {
            "name": "Guardians of the Rift",
            "level": 27,
            "rewards": ["Raiments of the Eye", "Abyssal Needle", "Abyssal Protector Pet"],
            "xp_multiplier": 1.5
        },
        {
            "name": "Ourania Altar",
            "level": 1,
            "rewards": ["Combination Runes", "Runecrafting XP"],
            "xp_multiplier": 1.3
        }
    ],
    "crafting": [
        {
            "name": "Stealing Creation",
            "level": 30,
            "rewards": ["Sacred Clay Tools", "Bonus XP", "Crafting Supplies"],
            "xp_multiplier": 1.4
        }
    ],
    "smithing": [
        {
            "name": "Artisans Workshop",
            "level": 20,
            "rewards": ["Smiths Outfit", "Respect Points", "Burial Armor"],
            "xp_multiplier": 1.5
        }
    ],
    "cooking": [
        {
            "name": "Gnome Restaurant",
            "level": 30,
            "rewards": ["Gnome Goggles", "Cooking XP", "Rare Ingredients"],
            "xp_multiplier": 1.3
        },
        {
            "name": "Recipe for Disaster",
            "level": 70,
            "rewards": ["Culinaromancer's Chest", "Kitchen Upgrades", "Cooking Gauntlets"],
            "xp_multiplier": 1.6
        }
    ],
    "farming": [
        {
            "name": "Tithe Farm",
            "level": 34,
            "rewards": ["Farmers Outfit", "Seed Box", "Auto-Weed", "Grape Seeds"],
            "xp_multiplier": 1.8
        },
        {
            "name": "Hespori",
            "level": 65,
            "rewards": ["Attas Seeds", "Kronos Seeds", "Iasor Seeds", "Bucket Pack"],
            "xp_multiplier": 1.5
        }
    ],
    "magic": [
        {
            "name": "Mage Training Arena",
            "level": 45,
            "rewards": ["Infinity Robes", "Master Wand", "Mages Book"],
            "xp_multiplier": 1.6
        },
        {
            "name": "Creature Creation",
            "level": 72,
            "rewards": ["Magic XP", "Rare Ingredients", "Magical Tokens"],
            "xp_multiplier": 1.4
        }
    ],
    "fletching": [
        {
            "name": "Arrow Shaft Competition",
            "level": 20,
            "rewards": ["Fletcher's Kit", "Arrow Shaft Box", "Fletching XP"],
            "xp_multiplier": 1.4
        },
        {
            "name": "Bow String Making",
            "level": 40,
            "rewards": ["String Storage", "Flax Collector", "Spinning Wheel"],
            "xp_multiplier": 1.5
        }
    ],
    "construction": [
        {
            "name": "Mahogany Homes",
            "level": 20,
            "rewards": ["Builder's Outfit", "Plank Sack", "Amy's Saw"],
            "xp_multiplier": 1.7
        },
        {
            "name": "Temple Trekking",
            "level": 30,
            "rewards": ["Construction XP Tomes", "Planks", "Nails"],
            "xp_multiplier": 1.3
        }
    ],
    "prayer": [
        {
            "name": "Ectofuntus",
            "level": 1,
            "rewards": ["Prayer XP", "Ghost Speak Amulet", "Ectophial"],
            "xp_multiplier": 1.8
        },
        {
            "name": "Demonic Offering",
            "level": 60,
            "rewards": ["Prayer XP", "Demon Ashes", "Unholy Symbols"],
            "xp_multiplier": 1.6
        }
    ]
}

# Skill-specific Rewards and Unlocks
SKILL_REWARDS = {
    "woodcutting": {
        "items": [
            {"name": "Lumberjack Outfit", "level": 44, "bonus": "Woodcutting XP +2.5%"},
            {"name": "Infernal Axe", "level": 61, "bonus": "Auto-burns logs"},
            {"name": "Beaver Pet", "level": 1, "bonus": "Rare pet from any tree"}
        ],
        "perks": [
            {"name": "Better Nests", "level": 80, "description": "Increased bird nest drops"},
            {"name": "Crystal Memories", "level": 90, "description": "Chance to note logs"}
        ]
    },
    "mining": {
        "items": [
            {"name": "Prospector Outfit", "level": 30, "bonus": "Mining XP +2.5%"},
            {"name": "Crystal Pick", "level": 71, "bonus": "Faster mining speed"},
            {"name": "Rock Golem Pet", "level": 1, "bonus": "Rare pet from any rock"}
        ],
        "perks": [
            {"name": "Gem Finding", "level": 70, "description": "Increased gem drops"},
            {"name": "Double Ores", "level": 85, "description": "Chance for double ore"}
        ]
    },
    "fishing": {
        "items": [
            {"name": "Angler Outfit", "level": 15, "bonus": "Fishing XP +2.5%"},
            {"name": "Dragon Harpoon", "level": 61, "bonus": "Faster fishing speed"},
            {"name": "Heron Pet", "level": 1, "bonus": "Rare pet from any fishing spot"}
        ],
        "perks": [
            {"name": "Fish Barrel", "level": 75, "description": "Store extra fish"},
            {"name": "Double Catch", "level": 80, "description": "Chance for double fish"}
        ]
    },
    "agility": {
        "items": [
            {"name": "Graceful Outfit", "level": 40, "bonus": "Run energy restore +30%"},
            {"name": "Dark Graceful", "level": 52, "bonus": "Hallowed Sepulchre bonus"},
            {"name": "Giant Squirrel Pet", "level": 1, "bonus": "Rare pet from any course"}
        ],
        "perks": [
            {"name": "Double Marks", "level": 80, "description": "Double Mark of Grace drops"},
            {"name": "Energy Master", "level": 90, "description": "Run energy drains 30% slower"}
        ]
    },
    "crafting": {
        "items": [
            {"name": "Crafting Guild Access", "level": 40, "bonus": "Extra resources and tools"},
            {"name": "Crystal Tool Seed", "level": 76, "bonus": "Create crystal tools"},
            {"name": "Crafting Cape", "level": 99, "bonus": "Teleport to Crafting Guild"}
        ],
        "perks": [
            {"name": "Master Crafter", "level": 85, "description": "Chance to create extra jewelry"},
            {"name": "Gem Expert", "level": 90, "description": "Never fail gem cutting"}
        ]
    },
    "smithing": {
        "items": [
            {"name": "Smiths Outfit", "level": 50, "bonus": "Smithing XP +2.5%"},
            {"name": "Crystal Hammer", "level": 76, "bonus": "Faster smithing speed"},
            {"name": "Smithing Cape", "level": 99, "bonus": "Coal bag auto-fills"}
        ],
        "perks": [
            {"name": "Master Smith", "level": 85, "description": "Chance to save bars"},
            {"name": "Heat Expert", "level": 90, "description": "Items stay hot longer"}
        ]
    },
    "herblore": {
        "items": [
            {"name": "Herblore Outfit", "level": 50, "bonus": "Herblore XP +2.5%"},
            {"name": "Herb Sack", "level": 58, "bonus": "Store more herbs"},
            {"name": "Herblore Cape", "level": 99, "bonus": "Clean herbs instantly"}
        ],
        "perks": [
            {"name": "Master Mixer", "level": 85, "description": "Chance to create extra potions"},
            {"name": "Herb Expert", "level": 90, "description": "Never fail cleaning herbs"}
        ]
    },
    "cooking": {
        "items": [
            {"name": "Cooking Outfit", "level": 50, "bonus": "Cooking XP +2.5%"},
            {"name": "Cooking Gauntlets", "level": 25, "bonus": "Never burn certain foods"},
            {"name": "Cooking Cape", "level": 99, "bonus": "Never burn food"}
        ],
        "perks": [
            {"name": "Master Chef", "level": 85, "description": "Chance to cook extra food"},
            {"name": "Kitchen Expert", "level": 90, "description": "Cook food faster"}
        ]
    },
    "farming": {
        "items": [
            {"name": "Farmers Outfit", "level": 34, "bonus": "Farming XP +2.5%"},
            {"name": "Magic Secateurs", "level": 40, "bonus": "Better crop yields"},
            {"name": "Farming Cape", "level": 99, "bonus": "Teleport to farming guild"}
        ],
        "perks": [
            {"name": "Master Farmer", "level": 85, "description": "Crops never die"},
            {"name": "Seed Expert", "level": 90, "description": "Chance to save seeds"}
        ]
    },
    "fletching": {
        "items": [
            {"name": "Fletcher's Outfit", "level": 40, "bonus": "Fletching XP +2.5%"},
            {"name": "Arrow Storage", "level": 60, "bonus": "Store more arrows"},
            {"name": "Fletching Cape", "level": 99, "bonus": "String bows instantly"}
        ],
        "perks": [
            {"name": "Master Fletcher", "level": 85, "description": "Chance to save materials"},
            {"name": "Arrow Expert", "level": 90, "description": "Create extra arrows"}
        ]
    },
    "construction": {
        "items": [
            {"name": "Builder's Outfit", "level": 40, "bonus": "Construction XP +2.5%"},
            {"name": "Crystal Saw", "level": 50, "bonus": "+3 invisible Construction levels"},
            {"name": "Construction Cape", "level": 99, "bonus": "Unlimited house teleports"}
        ],
        "perks": [
            {"name": "Master Builder", "level": 85, "description": "Chance to save planks"},
            {"name": "Design Expert", "level": 90, "description": "Build furniture faster"}
        ]
    },
    "prayer": {
        "items": [
            {"name": "Proselyte Armor", "level": 30, "bonus": "Prayer bonus +6-13"},
            {"name": "Holy Wrench", "level": 50, "bonus": "Enhanced prayer potion restore"},
            {"name": "Prayer Cape", "level": 99, "bonus": "Acts as holy symbol"}
        ],
        "perks": [
            {"name": "Master Prayer", "level": 85, "description": "Prayer points drain 15% slower"},
            {"name": "Bone Expert", "level": 90, "description": "Chance for double XP from bones"}
        ]
    }
}

# Special Training Areas
SPECIAL_TRAINING = {
    "woodcutting": {
        "Sulliuscep Mushrooms": {
            "level": 65,
            "xp_rate": "85k-110k/hr",
            "requirements": ["Fossil Island Access"],
            "benefits": ["Rare Fossils", "High XP Rate", "Mushroom Spores"]
        },
        "Blisterwood Tree": {
            "level": 76,
            "xp_rate": "120k-140k/hr",
            "requirements": ["Darkmeyer Access"],
            "benefits": ["Very High XP", "Blisterwood Logs", "Vampyre Slaying"]
        }
    },
    "mining": {
        "Blast Mine": {
            "level": 50,
            "xp_rate": "60k-80k/hr",
            "requirements": ["Lovakengj Favor"],
            "benefits": ["Mining XP", "Smithing XP", "Valuable Ores"]
        },
        "Amethyst Mine": {
            "level": 92,
            "xp_rate": "22k-25k/hr",
            "requirements": ["Mining Guild Access"],
            "benefits": ["Amethyst", "AFK Mining", "Good Profit"]
        }
    },
    "runecraft": {
        "True Blood Altar": {
            "level": 77,
            "xp_rate": "45k-55k/hr",
            "requirements": ["Morytania Hard Diary"],
            "benefits": ["Blood Runes", "High Profit", "Semi-AFK"]
        },
        "Zeah RC": {
            "level": 77,
            "xp_rate": "38k-45k/hr",
            "requirements": ["Arceuus Favor"],
            "benefits": ["Blood/Soul Runes", "Very AFK", "Decent Profit"]
        }
    },
    "thieving": {
        "Underwater Agility/Thieving": {
            "level": 65,
            "xp_rate": "70k-90k/hr",
            "requirements": ["Fossil Island Access"],
            "benefits": ["Thieving XP", "Agility XP", "Mermaids Tears"]
        }
    },
    "crafting": {
        "Gem Mining": {
            "level": 40,
            "xp_rate": "50k-65k/hr",
            "requirements": ["Shilo Village Access"],
            "benefits": ["Crafting XP", "Mining XP", "Valuable Gems"]
        },
        "Charter Ships": {
            "level": 77,
            "xp_rate": "350k-400k/hr",
            "requirements": ["Lots of GP"],
            "benefits": ["Very Fast XP", "Glass Making", "Seaweed Collecting"]
        }
    },
    "herblore": {
        "Farming Guild": {
            "level": 65,
            "xp_rate": "250k-300k/hr",
            "requirements": ["Farming Guild Access"],
            "benefits": ["Herb Patches", "Fast XP", "Profit Making"]
        },
        "Raids Potions": {
            "level": 90,
            "xp_rate": "400k-450k/hr",
            "requirements": ["Chambers of Xeric Access"],
            "benefits": ["Overload Making", "Very Fast XP", "Raid Preparations"]
        }
    },
    "farming": {
        "Hespori": {
            "level": 65,
            "xp_rate": "Special",
            "requirements": ["Farming Guild Access"],
            "benefits": ["Unique Seeds", "Special Effects", "Bucket Packs"]
        },
        "Spirit Trees": {
            "level": 83,
            "xp_rate": "Special",
            "requirements": ["Spirit Tree Seeds"],
            "benefits": ["Teleport Network", "High XP Drops", "Passive Training"]
        }
    },
    "magic": {
        "Alchemist Playground": {
            "level": 55,
            "xp_rate": "120k-150k/hr",
            "requirements": ["MTA Access"],
            "benefits": ["Alchemy XP", "Free Runes", "MTA Points"]
        },
        "Plank Make": {
            "level": 86,
            "xp_rate": "180k-200k/hr",
            "requirements": ["Lunars Spellbook"],
            "benefits": ["Fast XP", "Profit Making", "Construction Materials"]
        }
    },
    "fletching": {
        "Broad Arrows": {
            "level": 52,
            "xp_rate": "850k-950k/hr",
            "requirements": ["Slayer Points for Broad Arrows"],
            "benefits": ["Extremely Fast XP", "AFK Training", "Slayer Ammunition"]
        },
        "Dragon Arrows": {
            "level": 90,
            "xp_rate": "450k-500k/hr",
            "requirements": ["Dragon Arrow Heads"],
            "benefits": ["High XP Rate", "Valuable Arrows", "Profit Making"]
        }
    },
    "construction": {
        "Mahogany Tables": {
            "level": 52,
            "xp_rate": "900k-1000k/hr",
            "requirements": ["Mahogany Planks", "Butler"],
            "benefits": ["Fastest Construction XP", "Achievement Diary Req", "House Style"]
        },
        "Mythical Cape Racks": {
            "level": 82,
            "xp_rate": "380k-420k/hr",
            "requirements": ["Myths Guild Access"],
            "benefits": ["Good XP Rate", "Achievement Diary Req", "House Style"]
        }
    },
    "prayer": {
        "Chaos Temple": {
            "level": 1,
            "xp_rate": "500k-700k/hr",
            "requirements": ["Dragon Bones", "Wilderness Access"],
            "benefits": ["Double XP Rate", "Fast Prayer Training", "Risky Training"]
        },
        "Gilded Altar": {
            "level": 1,
            "xp_rate": "400k-600k/hr",
            "requirements": ["Player Owned House", "Marrentill"],
            "benefits": ["Safe Training", "350% XP Rate", "Community Training"]
        }
    }
}

# Skill Achievements
SKILL_ACHIEVEMENTS = {
    "woodcutting": [
        {"name": "Novice Logger", "level": 20, "task": "Cut 100 regular trees", "reward": "Woodcutting XP Lamp"},
        {"name": "Oak Master", "level": 40, "task": "Cut 500 oak trees", "reward": "Oak Seedling"},
        {"name": "Yew Expert", "level": 60, "task": "Cut 1000 yew trees", "reward": "Lumberjack Piece"},
        {"name": "Magic Champion", "level": 85, "task": "Cut 2000 magic trees", "reward": "Magic Seedling"},
        {"name": "Tree Spirit", "level": 99, "task": "Cut 5000 trees total", "reward": "Woodcutting Pet Chance x2"}
    ],
    "mining": [
        {"name": "Rock Collector", "level": 15, "task": "Mine 100 copper and tin", "reward": "Mining XP Lamp"},
        {"name": "Iron Veteran", "level": 35, "task": "Mine 500 iron ore", "reward": "Prospector Piece"},
        {"name": "Gem Hunter", "level": 55, "task": "Find 100 gems while mining", "reward": "Uncut Dragonstone"},
        {"name": "Runite Master", "level": 85, "task": "Mine 200 runite ore", "reward": "Runite Ore Pack"},
        {"name": "Living Rock", "level": 99, "task": "Mine 5000 ores total", "reward": "Mining Pet Chance x2"}
    ],
    "fishing": [
        {"name": "Net Fisher", "level": 20, "task": "Catch 200 fish with nets", "reward": "Fishing XP Lamp"},
        {"name": "Lobster Pro", "level": 40, "task": "Catch 500 lobsters", "reward": "Angler Piece"},
        {"name": "Shark Hunter", "level": 76, "task": "Catch 1000 sharks", "reward": "Spirit Angler Piece"},
        {"name": "Deep Sea Master", "level": 85, "task": "Catch 100 anglerfish", "reward": "Fish Barrel"},
        {"name": "Ocean Spirit", "level": 99, "task": "Catch 5000 fish total", "reward": "Fishing Pet Chance x2"}
    ],
    "crafting": [
        {"name": "Jewelry Maker", "level": 20, "task": "Craft 100 pieces of jewelry", "reward": "Crafting XP Lamp"},
        {"name": "Glass Master", "level": 46, "task": "Craft 500 glass items", "reward": "Glass Blowing Pipe"},
        {"name": "Dragon Expert", "level": 84, "task": "Craft 200 dragon items", "reward": "Dragon Hide Pack"},
        {"name": "Gem Virtuoso", "level": 90, "task": "Cut 1000 gems", "reward": "Gem Bag Upgrade"},
        {"name": "Master Artisan", "level": 99, "task": "Craft 5000 items total", "reward": "Bonus XP Scroll"}
    ],
    "fletching": [
        {"name": "Arrow Maker", "level": 15, "task": "Fletch 500 arrows", "reward": "Arrow Shaft Box"},
        {"name": "Bow Stringer", "level": 35, "task": "String 300 bows", "reward": "Fletching XP Lamp"},
        {"name": "Magic Fletcher", "level": 80, "task": "Fletch 200 magic bows", "reward": "Magic Logs Pack"},
        {"name": "Dragon Expert", "level": 90, "task": "Fletch 100 dragon arrows", "reward": "Dragon Arrow Tips"},
        {"name": "Master Fletcher", "level": 99, "task": "Fletch 5000 items total", "reward": "Bonus XP Scroll"}
    ],
    "construction": [
        {"name": "Home Designer", "level": 20, "task": "Build 100 furniture pieces", "reward": "Construction XP Lamp"},
        {"name": "Oak Master", "level": 40, "task": "Build 200 oak items", "reward": "Oak Plank Pack"},
        {"name": "Teak Expert", "level": 60, "task": "Build 300 teak items", "reward": "Teak Plank Pack"},
        {"name": "Mahogany King", "level": 80, "task": "Build 400 mahogany items", "reward": "Mahogany Plank Pack"},
        {"name": "Master Builder", "level": 99, "task": "Build 2000 items total", "reward": "Construction Cape Ornament Kit"}
    ],
    "prayer": [
        {"name": "Bone Collector", "level": 20, "task": "Bury 500 bones", "reward": "Prayer XP Lamp"},
        {"name": "Dragon Priest", "level": 40, "task": "Offer 300 dragon bones", "reward": "Dragon Bone Pack"},
        {"name": "Holy Champion", "level": 70, "task": "Complete 100 altar runs", "reward": "Prayer Potion Pack"},
        {"name": "Soul Guardian", "level": 85, "task": "Use 200 superior bones", "reward": "Superior Bone Pack"},
        {"name": "Divine Master", "level": 99, "task": "Reach max prayer points 1000 times", "reward": "Prayer Cape Ornament Kit"}
    ],
    "agility": [
        {"name": "Course Runner", "level": 20, "task": "Complete 100 course laps", "reward": "Agility XP Lamp"},
        {"name": "Grace Collector", "level": 40, "task": "Collect 100 marks of grace", "reward": "Graceful Piece"},
        {"name": "Obstacle Master", "level": 60, "task": "Complete advanced obstacles 500 times", "reward": "Stamina Potion Pack"},
        {"name": "Sepulchre Champion", "level": 82, "task": "Complete Hallowed Sepulchre 50 times", "reward": "Dark Graceful Piece"},
        {"name": "Perfect Balance", "level": 99, "task": "Complete 1000 course laps", "reward": "Agility Pet Chance x2"}
    ],
    "herblore": [
        {"name": "Potion Mixer", "level": 20, "task": "Make 100 basic potions", "reward": "Herblore XP Lamp"},
        {"name": "Herb Master", "level": 40, "task": "Clean 500 herbs", "reward": "Herb Sack"},
        {"name": "Super Brewer", "level": 65, "task": "Make 300 super potions", "reward": "Herb Pack"},
        {"name": "Divine Mixer", "level": 85, "task": "Make 200 divine potions", "reward": "Divine Potion Pack"},
        {"name": "Master Herbalist", "level": 99, "task": "Make 2000 potions total", "reward": "Bonus XP Scroll"}
    ],
    "magic": [
        {"name": "Spell Caster", "level": 20, "task": "Cast 200 spells", "reward": "Magic XP Lamp"},
        {"name": "Enchanter", "level": 40, "task": "Enchant 300 items", "reward": "Cosmic Rune Pack"},
        {"name": "Alchemist", "level": 55, "task": "High alch 500 items", "reward": "Nature Rune Pack"},
        {"name": "Ancient Master", "level": 85, "task": "Cast ancient spells 300 times", "reward": "Blood Rune Pack"},
        {"name": "Arcane Master", "level": 99, "task": "Cast 5000 spells total", "reward": "Magic Cape Ornament Kit"}
    ]
} 