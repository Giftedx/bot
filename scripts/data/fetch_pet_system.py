import json
from pathlib import Path
from datetime import datetime
import random

def fetch_pet_system_data():
    """
    Fetches unified pet system data that integrates pets from:
    - Pokemon (as companions)
    - OSRS pets
    - Cookie Clicker (grandmas and other beings)
    - Custom virtual pets
    """
    pet_data = {
        'timestamp': datetime.now().isoformat(),
        'core_mechanics': fetch_core_mechanics(),
        'pet_types': fetch_pet_types(),
        'training_system': fetch_training_system(),
        'interaction_system': fetch_interaction_system(),
        'battle_system': fetch_battle_system(),
        'reward_system': fetch_reward_system(),
        'evolution_system': fetch_evolution_system(),
        'cross_game_features': fetch_cross_game_features()
    }
    
    # Save the data
    output_dir = Path("src/data/pets")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "pet_system_data.json", 'w') as f:
        json.dump(pet_data, f, indent=4)
    
    return pet_data

def fetch_core_mechanics():
    """Fetch core pet system mechanics"""
    return {
        'stats': {
            'base_stats': {
                'happiness': {'min': 0, 'max': 100, 'default': 50},
                'energy': {'min': 0, 'max': 100, 'default': 100},
                'hunger': {'min': 0, 'max': 100, 'default': 0},
                'experience': {'min': 0, 'max': None, 'default': 0}
            },
            'derived_stats': {
                'level': {'min': 1, 'max': 100, 'formula': 'experience_based'},
                'power': {'formula': 'level_and_happiness_based'},
                'bond': {'min': 0, 'max': 100, 'formula': 'interaction_based'}
            }
        },
        'time_mechanics': {
            'stat_decay': {
                'happiness': -1,  # per day
                'energy': -5,     # per hour of activity
                'hunger': +2      # per hour
            },
            'recovery_rates': {
                'energy': 10,     # per hour of rest
                'happiness': 5,   # per interaction
                'hunger': -20     # per feeding
            }
        },
        'interaction_limits': {
            'feedings_per_day': 3,
            'training_sessions_per_day': 5,
            'battles_per_day': 10,
            'playtime_hours': 4
        }
    }

def fetch_pet_types():
    """Fetch different types of pets and their unique features"""
    return {
        'pokemon_companions': {
            'source': 'pokemon',
            'available_species': 'from_pokedex',
            'special_abilities': {
                'type_moves': True,
                'evolution': True,
                'breeding': True
            },
            'integration': {
                'follows_trainer': True,
                'assists_in_battles': True,
                'special_interactions': ['trade', 'daycare', 'contests']
            }
        },
        'osrs_pets': {
            'source': 'osrs',
            'types': [
                'boss_pets',
                'skilling_pets',
                'companion_pets'
            ],
            'special_abilities': {
                'skill_boosts': True,
                'item_finding': True,
                'combat_assistance': True
            },
            'integration': {
                'follows_player': True,
                'rare_drop_bonus': True,
                'skill_inspiration': True
            }
        },
        'cookie_beings': {
            'source': 'cookie_clicker',
            'types': [
                'grandmas',
                'cookie_spirits',
                'wrinklers'
            ],
            'special_abilities': {
                'cookie_production': True,
                'golden_cookie_sense': True,
                'grandmapocalypse_influence': True
            },
            'integration': {
                'passive_income': True,
                'special_events': True,
                'cookie_upgrades': True
            }
        },
        'virtual_pets': {
            'source': 'custom',
            'types': [
                'digital_companions',
                'element_spirits',
                'mythical_creatures'
            ],
            'special_abilities': {
                'mood_effects': True,
                'channel_bonuses': True,
                'special_commands': True
            },
            'integration': {
                'discord_presence': True,
                'chat_interactions': True,
                'event_participation': True
            }
        }
    }

def fetch_training_system():
    """Fetch pet training system data"""
    return {
        'methods': {
            'basic_training': {
                'requirements': {'level': 1},
                'stats_gained': {
                    'experience': 10,
                    'happiness': 5,
                    'energy_cost': 10
                }
            },
            'advanced_training': {
                'requirements': {'level': 25},
                'stats_gained': {
                    'experience': 25,
                    'happiness': 8,
                    'energy_cost': 20
                }
            },
            'master_training': {
                'requirements': {'level': 50},
                'stats_gained': {
                    'experience': 50,
                    'happiness': 12,
                    'energy_cost': 35
                }
            }
        },
        'skills': {
            'combat': {
                'levels': 100,
                'experience_curve': 'standard',
                'abilities_unlocked': ['attack', 'defend', 'special']
            },
            'agility': {
                'levels': 100,
                'experience_curve': 'fast',
                'abilities_unlocked': ['dodge', 'jump', 'sprint']
            },
            'intelligence': {
                'levels': 100,
                'experience_curve': 'slow',
                'abilities_unlocked': ['solve', 'remember', 'learn']
            }
        },
        'specializations': {
            'battler': {
                'focus': 'combat',
                'bonuses': {'attack': 1.5, 'defense': 1.3}
            },
            'explorer': {
                'focus': 'agility',
                'bonuses': {'speed': 1.5, 'stamina': 1.3}
            },
            'scholar': {
                'focus': 'intelligence',
                'bonuses': {'learning': 1.5, 'memory': 1.3}
            }
        }
    }

def fetch_interaction_system():
    """Fetch pet interaction system data"""
    return {
        'basic_interactions': {
            'pet': {
                'happiness_gain': 5,
                'bond_gain': 1,
                'cooldown': 300  # seconds
            },
            'feed': {
                'hunger_reduction': 20,
                'happiness_gain': 3,
                'bond_gain': 1
            },
            'play': {
                'happiness_gain': 10,
                'energy_cost': 15,
                'bond_gain': 2
            }
        },
        'special_interactions': {
            'groom': {
                'requirements': {'bond': 20},
                'happiness_gain': 15,
                'bond_gain': 3
            },
            'trick': {
                'requirements': {'bond': 40},
                'experience_gain': 20,
                'happiness_gain': 8
            },
            'adventure': {
                'requirements': {'bond': 60},
                'rewards': ['items', 'experience', 'special_events']
            }
        },
        'group_interactions': {
            'pet_playdate': {
                'requirements': {'pets': 2},
                'happiness_gain': 20,
                'bond_gain': 5
            },
            'training_session': {
                'requirements': {'pets': 3},
                'experience_gain': 30,
                'happiness_gain': 15
            },
            'pet_party': {
                'requirements': {'pets': 5},
                'special_rewards': True,
                'unique_experiences': True
            }
        }
    }

def fetch_battle_system():
    """Fetch pet battle system data"""
    return {
        'battle_types': {
            'friendly': {
                'stakes': 'none',
                'experience_gain': 'normal',
                'restrictions': 'none'
            },
            'ranked': {
                'stakes': 'rating',
                'experience_gain': 'high',
                'restrictions': 'level_based'
            },
            'tournament': {
                'stakes': 'prizes',
                'experience_gain': 'very_high',
                'restrictions': 'qualification_based'
            }
        },
        'combat_mechanics': {
            'turn_based': {
                'actions_per_turn': 1,
                'speed_priority': True,
                'status_effects': True
            },
            'stats_used': [
                'attack',
                'defense',
                'speed',
                'special'
            ],
            'effectiveness': {
                'type_matching': True,
                'level_difference': True,
                'bond_bonus': True
            }
        },
        'rewards': {
            'experience': {
                'win': 100,
                'lose': 25,
                'draw': 50
            },
            'items': {
                'win': ['rare', 'common'],
                'lose': ['common'],
                'draw': ['common']
            },
            'rankings': {
                'win': +20,
                'lose': -15,
                'draw': +2
            }
        }
    }

def fetch_reward_system():
    """Fetch pet reward system data"""
    return {
        'daily_rewards': {
            'login_bonus': {
                'items': ['food', 'toys', 'accessories'],
                'frequency': 'daily',
                'streak_bonuses': True
            },
            'care_bonus': {
                'requirements': ['feed', 'play', 'train'],
                'rewards': ['special_items', 'experience_boost']
            },
            'achievement_bonus': {
                'types': ['training', 'battle', 'interaction'],
                'rewards': ['unique_items', 'titles']
            }
        },
        'milestone_rewards': {
            'level_milestones': {
                10: ['special_accessory', 'title'],
                25: ['rare_item', 'emote'],
                50: ['unique_ability', 'skin'],
                100: ['legendary_item', 'effect']
            },
            'bond_milestones': {
                20: ['special_interaction'],
                40: ['unique_trick'],
                60: ['adventure_access'],
                80: ['transformation'],
                100: ['ultimate_ability']
            }
        },
        'special_events': {
            'seasonal': {
                'christmas': ['festive_items', 'snow_effects'],
                'halloween': ['spooky_items', 'ghost_effects'],
                'summer': ['beach_items', 'water_effects']
            },
            'competitive': {
                'tournaments': ['champion_items', 'trophies'],
                'rankings': ['ranked_rewards', 'titles'],
                'challenges': ['challenge_items', 'badges']
            }
        }
    }

def fetch_evolution_system():
    """Fetch pet evolution system data"""
    return {
        'evolution_types': {
            'level_based': {
                'triggers': {'level': [16, 32, 48]},
                'requirements': None,
                'reversible': False
            },
            'bond_based': {
                'triggers': {'bond': [50, 75, 90]},
                'requirements': {'happiness': 80},
                'reversible': True
            },
            'special': {
                'triggers': {'special_items': True},
                'requirements': {'quest_completion': True},
                'reversible': False
            }
        },
        'evolution_effects': {
            'stat_changes': {
                'multiplier': 1.5,
                'new_abilities': True,
                'appearance_change': True
            },
            'special_features': {
                'new_interactions': True,
                'unique_abilities': True,
                'form_changes': True
            }
        },
        'cross_game_evolutions': {
            'pokemon_inspired': {
                'stone_evolution': True,
                'trade_evolution': True,
                'friendship_evolution': True
            },
            'osrs_inspired': {
                'skill_based': True,
                'quest_based': True,
                'achievement_based': True
            },
            'cookie_inspired': {
                'resource_based': True,
                'building_based': True,
                'grandma_based': True
            }
        }
    }

def fetch_cross_game_features():
    """Fetch cross-game integration features"""
    return {
        'shared_resources': {
            'experience': {
                'conversion_rates': {
                    'pokemon_exp': 1.0,
                    'osrs_xp': 0.1,
                    'cookie_power': 0.01
                },
                'max_daily_conversion': 10000
            },
            'currency': {
                'conversion_rates': {
                    'pokedollars': 1.0,
                    'osrs_gp': 0.001,
                    'cookies': 0.1
                },
                'max_daily_conversion': 1000000
            }
        },
        'cross_game_activities': {
            'multi_game_quests': {
                'requirements': ['pokemon_task', 'osrs_task', 'cookie_task'],
                'rewards': ['unique_items', 'special_pets']
            },
            'shared_achievements': {
                'tracking': ['all_games', 'per_game'],
                'special_rewards': ['cross_game_items', 'titles']
            }
        },
        'special_integrations': {
            'pokemon': {
                'pet_abilities': ['pokemon_moves', 'type_advantages'],
                'special_forms': ['regional_variants', 'mega_evolution']
            },
            'osrs': {
                'pet_abilities': ['skill_boosts', 'combat_assistance'],
                'special_features': ['rare_drops', 'skill_pets']
            },
            'cookie_clicker': {
                'pet_abilities': ['cookie_production', 'grandma_synergy'],
                'special_features': ['building_boosts', 'golden_cookies']
            }
        },
        'unified_pet_system': {
            'shared_stats': {
                'happiness': True,
                'experience': True,
                'bond': True
            },
            'cross_breeding': {
                'enabled': True,
                'restrictions': ['type_matching', 'level_requirements']
            },
            'shared_activities': {
                'training': True,
                'battles': True,
                'special_events': True
            }
        }
    }

if __name__ == "__main__":
    fetch_pet_system_data() 