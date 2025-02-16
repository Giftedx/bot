#!/usr/bin/env python3
"""
Script to generate base OSRS game data files.
This creates comprehensive local data files with accurate OSRS stats and mechanics.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def generate_monster_data() -> Dict[str, Any]:
    """Generate comprehensive monster data."""
    return {
        # Slayer Monsters
        "abyssal_demon": {
            "id": "abyssal_demon",
            "name": "Abyssal demon",
            "type": "SLAYER",
            "combat_level": 124,
            "stats": {
                "attack": 97,
                "strength": 67,
                "defence": 135,
                "ranged": 1,
                "magic": 1,
                "hitpoints": 150,
                "prayer": 1
            },
            "bonuses": {
                "attack_stab": 0,
                "attack_slash": 0,
                "attack_crush": 0,
                "attack_magic": 0,
                "attack_ranged": 0,
                "defence_stab": 20,
                "defence_slash": 20,
                "defence_crush": 20,
                "defence_magic": 0,
                "defence_ranged": 20,
                "melee_strength": 0,
                "ranged_strength": 0,
                "magic_damage": 0,
                "prayer": 0
            },
            "attack_style": "MELEE",
            "attack_speed": 4,
            "aggressive": True,
            "max_hit": 8,
            "size": 1,
            "poisonous": False,
            "venomous": False,
            "slayer_level": 85,
            "slayer_xp": 150,
            "weakness": ["magic"],
            "immune": [],
            "attributes": ["demon"],
            "examine": "A denizen of the Abyss.",
            "wiki_url": "https://oldschool.runescape.wiki/w/Abyssal_demon",
            "respawn_time": 50,
            "aggro_range": 4,
            "locations": [
                {
                    "area": "Slayer Tower",
                    "coordinates": [3417, 3562, 2],
                    "quantity": 8
                },
                {
                    "area": "Catacombs of Kourend",
                    "coordinates": [1674, 10089, 0],
                    "quantity": 10
                },
                {
                    "area": "Abyssal Area",
                    "coordinates": [3029, 4842, 0],
                    "quantity": 4
                }
            ],
            "drop_table": {
                "always": {
                    "ashes": [1, 1]
                },
                "common": {
                    "chaos_rune": [10, 0.5],
                    "death_rune": [5, 0.5],
                    "blood_rune": [5, 0.5],
                    "coins": [44, 0.8],
                    "adamant_chainbody": [1, 0.4],
                    "black_sword": [1, 0.4]
                },
                "uncommon": {
                    "grimy_cadantine": [1, 0.2],
                    "grimy_lantadyme": [1, 0.2],
                    "law_rune": [3, 0.2],
                    "rune_chainbody": [1, 0.1],
                    "rune_med_helm": [1, 0.1]
                },
                "rare": {
                    "abyssal_head": [1, 0.0013],
                    "elite_clue_scroll": [1, 0.0021]
                },
                "unique": {
                    "abyssal_whip": 0.0021
                }
            }
        },
        
        # God Wars Dungeon Bosses
        "general_graardor": {
            "id": "general_graardor",
            "name": "General Graardor",
            "type": "BOSS",
            "combat_level": 624,
            "stats": {
                "attack": 280,
                "strength": 350,
                "defence": 250,
                "ranged": 350,
                "magic": 80,
                "hitpoints": 255,
                "prayer": 220
            },
            "bonuses": {
                "attack_stab": 0,
                "attack_slash": 0,
                "attack_crush": 0,
                "attack_magic": 0,
                "attack_ranged": 0,
                "defence_stab": 90,
                "defence_slash": 90,
                "defence_crush": 90,
                "defence_magic": 80,
                "defence_ranged": 90,
                "melee_strength": 0,
                "ranged_strength": 0,
                "magic_damage": 0,
                "prayer": 0
            },
            "attack_style": "MIXED",
            "attack_speed": 6,
            "aggressive": True,
            "max_hit": 60,
            "size": 5,
            "poisonous": False,
            "venomous": False,
            "slayer_level": 0,
            "slayer_xp": 0,
            "weakness": [],
            "immune": [],
            "attributes": ["boss", "bandosian"],
            "examine": "The mighty warlord of Bandos.",
            "wiki_url": "https://oldschool.runescape.wiki/w/General_Graardor",
            "respawn_time": 90,
            "aggro_range": 3,
            "special_attacks": [
                {
                    "name": "Ranged Attack",
                    "style": "RANGED",
                    "max_hit": 35,
                    "accuracy": 1.0,
                    "cooldown": 4,
                    "effects": {},
                    "area_effect": True,
                    "area_size": 3
                }
            ],
            "phases": [
                {
                    "hp_threshold": 100,
                    "stats": {
                        "attack": 280,
                        "strength": 350,
                        "defence": 250,
                        "ranged": 350,
                        "magic": 80,
                        "hitpoints": 255,
                        "prayer": 220
                    },
                    "attack_style": "MIXED",
                    "max_hit": 60,
                    "mechanics": {
                        "minions": True,
                        "heal": {
                            "interval": 20,
                            "min_amount": 1,
                            "max_amount": 5
                        }
                    }
                }
            ],
            "locations": [
                {
                    "area": "God Wars Dungeon",
                    "coordinates": [2864, 5354, 2],
                    "quantity": 1,
                    "requirements": {
                        "items": ["hammer"],
                        "kill_count": 40
                    }
                }
            ],
            "drop_table": {
                "always": {
                    "big_bones": [1, 1]
                },
                "common": {
                    "coins": [19362, 0.5],
                    "rune_2h_sword": [1, 0.4],
                    "rune_pickaxe": [1, 0.4],
                    "rune_longsword": [1, 0.4]
                },
                "uncommon": {
                    "grimy_snapdragon": [3, 0.2],
                    "super_restore(4)": [3, 0.2],
                    "adamant_bar": [3, 0.2]
                },
                "rare": {
                    "elite_clue_scroll": [1, 0.0042],
                    "curved_bone": [1, 0.0021]
                },
                "unique": {
                    "bandos_chestplate": 0.0087,
                    "bandos_tassets": 0.0087,
                    "bandos_boots": 0.0087,
                    "bandos_hilt": 0.0087,
                    "pet_general_graardor": 0.0021
                }
            }
        },
        
        # Dragons
        "green_dragon": {
            "id": "green_dragon",
            "name": "Green dragon",
            "type": "REGULAR",
            "combat_level": 79,
            "stats": {
                "attack": 68,
                "strength": 68,
                "defence": 68,
                "ranged": 1,
                "magic": 1,
                "hitpoints": 75,
                "prayer": 1
            },
            "bonuses": {
                "attack_stab": 0,
                "attack_slash": 0,
                "attack_crush": 0,
                "attack_magic": 0,
                "attack_ranged": 0,
                "defence_stab": 50,
                "defence_slash": 50,
                "defence_crush": 50,
                "defence_magic": 50,
                "defence_ranged": 50,
                "melee_strength": 0,
                "ranged_strength": 0,
                "magic_damage": 0,
                "prayer": 0
            },
            "attack_style": "MIXED",
            "attack_speed": 4,
            "aggressive": True,
            "max_hit": 8,
            "size": 3,
            "poisonous": False,
            "venomous": False,
            "slayer_level": 0,
            "slayer_xp": 0,
            "weakness": [],
            "immune": [],
            "attributes": ["dragon", "chromatic"],
            "examine": "A powerful green dragon.",
            "wiki_url": "https://oldschool.runescape.wiki/w/Green_dragon",
            "respawn_time": 30,
            "aggro_range": 8,
            "special_attacks": [
                {
                    "name": "Dragonfire",
                    "style": "DRAGON_FIRE",
                    "max_hit": 50,
                    "accuracy": 1.0,
                    "cooldown": 6,
                    "effects": {
                        "antifire": True
                    }
                }
            ],
            "locations": [
                {
                    "area": "Wilderness",
                    "coordinates": [3168, 3677, 0],
                    "quantity": 6
                },
                {
                    "area": "Myths' Guild Dungeon",
                    "coordinates": [1832, 9008, 1],
                    "quantity": 4,
                    "requirements": {
                        "quests": ["dragon_slayer_2"]
                    }
                }
            ],
            "drop_table": {
                "always": {
                    "dragon_bones": [1, 1],
                    "green_dragonhide": [1, 1]
                },
                "common": {
                    "coins": [44, 0.8],
                    "steel_platelegs": [1, 0.4],
                    "mithril_axe": [1, 0.4]
                },
                "uncommon": {
                    "grimy_ranarr_weed": [1, 0.1],
                    "law_rune": [2, 0.2],
                    "adamant_full_helm": [1, 0.1]
                },
                "rare": {
                    "ensouled_dragon_head": [1, 0.0125],
                    "hard_clue_scroll": [1, 0.0064]
                }
            }
        }
    }

def generate_npc_data() -> Dict[str, Any]:
    """Generate NPC data."""
    return {
        "wise_old_man": {
            "id": "wise_old_man",
            "name": "Wise Old Man",
            "type": "QUEST",
            "examine": "He has a cape made from fine silk.",
            "wiki_url": "https://oldschool.runescape.wiki/w/Wise_Old_Man",
            "locations": [
                {
                    "area": "Draynor Village",
                    "coordinates": [3088, 3253, 0],
                    "quantity": 1
                }
            ],
            "options": [
                "Talk-to",
                "Trade",
                "Teleport",
                "View-quest-log"
            ],
            "dialogue": {
                "greeting": "Ah, hello there adventurer.",
                "topics": [
                    "Quest Cape",
                    "Bank Organization",
                    "Life Story"
                ]
            },
            "shop": {
                "name": "Wise Old Man's Shop",
                "items": [
                    {
                        "id": "quest_cape",
                        "price": 99000,
                        "requirements": {
                            "quest_points": 290
                        }
                    }
                ]
            }
        }
    }

def generate_shop_data() -> Dict[str, Any]:
    """Generate shop data."""
    return {
        "general_store": {
            "id": "general_store",
            "name": "General Store",
            "type": "GENERAL",
            "examine": "A shop that sells various general items.",
            "locations": [
                {
                    "area": "Lumbridge",
                    "coordinates": [3211, 3247, 0],
                    "quantity": 1
                }
            ],
            "stock": [
                {
                    "id": "pot",
                    "price": 1,
                    "quantity": 5
                },
                {
                    "id": "jug",
                    "price": 1,
                    "quantity": 5
                },
                {
                    "id": "shears",
                    "price": 1,
                    "quantity": 2
                },
                {
                    "id": "bucket",
                    "price": 2,
                    "quantity": 5
                }
            ]
        }
    }

def main():
    """Main function to generate base data files."""
    try:
        # Create data directory
        data_dir = Path(__file__).parent.parent.parent / "src" / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Generate and save monster data
        monster_data = generate_monster_data()
        with open(data_dir / "monsters.json", "w") as f:
            json.dump(monster_data, f, indent=4)
        logger.info(f"Generated {len(monster_data)} monsters")
        
        # Generate and save NPC data
        npc_data = generate_npc_data()
        with open(data_dir / "npcs.json", "w") as f:
            json.dump(npc_data, f, indent=4)
        logger.info(f"Generated {len(npc_data)} NPCs")
        
        # Generate and save shop data
        shop_data = generate_shop_data()
        with open(data_dir / "shops.json", "w") as f:
            json.dump(shop_data, f, indent=4)
        logger.info(f"Generated {len(shop_data)} shops")
        
        logger.info("Successfully generated all base data files!")
        
    except Exception as e:
        logger.error(f"Error generating data: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 