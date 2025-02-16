import json
from pathlib import Path
from datetime import datetime
import random

def fetch_shop_system_data():
    """
    Fetches unified shop system data that integrates items from:
    - Pokemon items and TMs
    - OSRS items and equipment
    - Cookie Clicker upgrades
    - Custom items and cosmetics
    """
    shop_data = {
        'timestamp': datetime.now().isoformat(),
        'currencies': fetch_currencies(),
        'item_categories': fetch_item_categories(),
        'special_offers': fetch_special_offers(),
        'purchase_limits': fetch_purchase_limits(),
        'unlock_requirements': fetch_unlock_requirements(),
        'seasonal_items': fetch_seasonal_items(),
        'cross_game_items': fetch_cross_game_items()
    }
    
    # Save the data
    output_dir = Path("src/data/shop")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "shop_system_data.json", 'w') as f:
        json.dump(shop_data, f, indent=4)
    
    return shop_data

def fetch_currencies():
    """Fetch currency system data"""
    return {
        'primary_currencies': {
            'universal_coins': {
                'description': 'Main cross-game currency',
                'conversion_rates': {
                    'pokedollars': 1.0,
                    'osrs_gp': 0.001,
                    'cookies': 0.1
                },
                'earn_methods': [
                    'daily_tasks',
                    'achievements',
                    'trading',
                    'events'
                ]
            }
        },
        'game_currencies': {
            'pokemon': {
                'pokedollars': {
                    'conversion_rate': 1.0,
                    'earn_methods': ['battles', 'trading', 'quests']
                },
                'battle_points': {
                    'conversion_rate': 10.0,
                    'earn_methods': ['ranked_battles', 'tournaments']
                }
            },
            'osrs': {
                'gold_pieces': {
                    'conversion_rate': 0.001,
                    'earn_methods': ['skills', 'combat', 'trading']
                },
                'slayer_points': {
                    'conversion_rate': 5.0,
                    'earn_methods': ['slayer_tasks']
                }
            },
            'cookie_clicker': {
                'cookies': {
                    'conversion_rate': 0.1,
                    'earn_methods': ['clicking', 'buildings', 'golden_cookies']
                },
                'heavenly_chips': {
                    'conversion_rate': 100.0,
                    'earn_methods': ['prestige']
                }
            }
        },
        'premium_currency': {
            'crystal_shards': {
                'description': 'Premium cross-game currency',
                'obtain_methods': [
                    'special_achievements',
                    'events',
                    'purchase'
                ],
                'uses': [
                    'exclusive_items',
                    'special_features',
                    'cosmetics'
                ]
            }
        }
    }

def fetch_item_categories():
    """Fetch shop item categories"""
    return {
        'consumables': {
            'healing_items': {
                'pokemon_potions': {
                    'potion': {'price': 100, 'effect': 'heal_20'},
                    'super_potion': {'price': 200, 'effect': 'heal_50'},
                    'hyper_potion': {'price': 500, 'effect': 'heal_100'}
                },
                'osrs_food': {
                    'shark': {'price': 1000, 'effect': 'heal_20'},
                    'manta_ray': {'price': 1200, 'effect': 'heal_22'},
                    'anglerfish': {'price': 1500, 'effect': 'heal_24'}
                },
                'cookies': {
                    'basic_cookie': {'price': 10, 'effect': 'heal_5'},
                    'golden_cookie': {'price': 1000, 'effect': 'heal_50'},
                    'heavenly_cookie': {'price': 10000, 'effect': 'heal_100'}
                }
            },
            'boost_items': {
                'pokemon_items': {
                    'x_attack': {'price': 300, 'effect': 'boost_attack'},
                    'x_defense': {'price': 300, 'effect': 'boost_defense'},
                    'x_speed': {'price': 300, 'effect': 'boost_speed'}
                },
                'osrs_potions': {
                    'super_strength': {'price': 500, 'effect': 'boost_strength'},
                    'super_attack': {'price': 500, 'effect': 'boost_attack'},
                    'super_defense': {'price': 500, 'effect': 'boost_defense'}
                },
                'cookie_powerups': {
                    'sugar_rush': {'price': 200, 'effect': 'boost_production'},
                    'frenzy': {'price': 1000, 'effect': 'boost_all'},
                    'elder_pledge': {'price': 5000, 'effect': 'prevent_grandmapocalypse'}
                }
            }
        },
        'equipment': {
            'weapons': {
                'pokemon_held_items': {
                    'choice_band': {'price': 2000, 'effect': 'boost_attack'},
                    'life_orb': {'price': 3000, 'effect': 'boost_all_moves'},
                    'focus_sash': {'price': 2500, 'effect': 'survive_one_hit'}
                },
                'osrs_weapons': {
                    'dragon_scimitar': {'price': 100000, 'effect': 'strong_slash'},
                    'abyssal_whip': {'price': 500000, 'effect': 'fast_attack'},
                    'godsword': {'price': 1000000, 'effect': 'special_attack'}
                }
            },
            'armor': {
                'pokemon_items': {
                    'leftovers': {'price': 4000, 'effect': 'heal_each_turn'},
                    'rocky_helmet': {'price': 3000, 'effect': 'damage_attacker'},
                    'assault_vest': {'price': 3500, 'effect': 'boost_special_defense'}
                },
                'osrs_armor': {
                    'dragon_armor': {'price': 200000, 'effect': 'high_defense'},
                    'barrows_armor': {'price': 500000, 'effect': 'set_effect'},
                    'bandos_armor': {'price': 1000000, 'effect': 'strength_bonus'}
                }
            }
        },
        'cosmetics': {
            'pet_accessories': {
                'collars': {
                    'basic_collar': {'price': 100, 'effect': 'cosmetic'},
                    'rare_collar': {'price': 1000, 'effect': 'glow'},
                    'legendary_collar': {'price': 10000, 'effect': 'particle_effects'}
                },
                'hats': {
                    'party_hat': {'price': 500, 'effect': 'cosmetic'},
                    'santa_hat': {'price': 2000, 'effect': 'seasonal'},
                    'crown': {'price': 20000, 'effect': 'premium'}
                }
            },
            'visual_effects': {
                'trails': {
                    'sparkle_trail': {'price': 1000, 'effect': 'follow_effect'},
                    'rainbow_trail': {'price': 5000, 'effect': 'premium_effect'},
                    'fire_trail': {'price': 10000, 'effect': 'elemental_effect'}
                },
                'auras': {
                    'basic_aura': {'price': 2000, 'effect': 'glow_effect'},
                    'elemental_aura': {'price': 10000, 'effect': 'changing_effect'},
                    'divine_aura': {'price': 50000, 'effect': 'premium_effect'}
                }
            }
        },
        'special_items': {
            'evolution_items': {
                'pokemon_stones': {
                    'fire_stone': {'price': 5000, 'effect': 'evolve_fire'},
                    'water_stone': {'price': 5000, 'effect': 'evolve_water'},
                    'thunder_stone': {'price': 5000, 'effect': 'evolve_electric'}
                },
                'osrs_crystals': {
                    'crystal_seed': {'price': 10000, 'effect': 'grow_equipment'},
                    'zenyte_shard': {'price': 50000, 'effect': 'craft_jewelry'},
                    'onyx': {'price': 100000, 'effect': 'enhance_items'}
                }
            },
            'rare_items': {
                'pokemon_items': {
                    'master_ball': {'price': 100000, 'effect': 'guaranteed_catch'},
                    'ability_capsule': {'price': 50000, 'effect': 'change_ability'},
                    'golden_bottle_cap': {'price': 75000, 'effect': 'max_ivs'}
                },
                'osrs_items': {
                    'dragon_claws': {'price': 500000, 'effect': 'special_attack'},
                    'twisted_bow': {'price': 1000000, 'effect': 'scale_with_magic'},
                    'scythe_of_vitur': {'price': 2000000, 'effect': 'multi_hit'}
                }
            }
        }
    }

def fetch_special_offers():
    """Fetch special shop offers"""
    return {
        'daily_deals': {
            'rotation_time': 24,  # hours
            'max_purchases': 1,
            'discount_range': {'min': 10, 'max': 50},  # percent
            'item_pool': ['consumables', 'common_equipment']
        },
        'weekly_specials': {
            'rotation_time': 168,  # hours
            'max_purchases': 3,
            'discount_range': {'min': 20, 'max': 70},
            'item_pool': ['rare_equipment', 'cosmetics']
        },
        'limited_time': {
            'event_duration': 72,  # hours
            'appearance_chance': 0.1,  # 10% daily chance
            'discount_range': {'min': 30, 'max': 90},
            'item_pool': ['exclusive_items', 'special_cosmetics']
        },
        'bundle_deals': {
            'types': {
                'starter_bundle': {
                    'items': ['basic_equipment', 'consumables', 'currency'],
                    'discount': 30
                },
                'premium_bundle': {
                    'items': ['rare_equipment', 'premium_currency', 'exclusive_cosmetics'],
                    'discount': 50
                },
                'seasonal_bundle': {
                    'items': ['seasonal_items', 'special_currency', 'limited_cosmetics'],
                    'discount': 40
                }
            }
        }
    }

def fetch_purchase_limits():
    """Fetch shop purchase limits"""
    return {
        'daily_limits': {
            'consumables': {
                'healing_items': 10,
                'boost_items': 5,
                'special_items': 3
            },
            'currency_conversion': {
                'game_currencies': 100000,
                'premium_currency': 1000
            }
        },
        'weekly_limits': {
            'equipment': {
                'weapons': 3,
                'armor': 3,
                'accessories': 5
            },
            'cosmetics': {
                'pet_items': 10,
                'visual_effects': 5,
                'premium_items': 2
            }
        },
        'special_limits': {
            'event_items': {
                'per_event': 5,
                'per_day': 2
            },
            'rare_items': {
                'per_month': 3,
                'per_week': 1
            }
        }
    }

def fetch_unlock_requirements():
    """Fetch shop unlock requirements"""
    return {
        'level_requirements': {
            'basic_shop': 1,
            'advanced_shop': 10,
            'premium_shop': 25,
            'special_shop': 50
        },
        'achievement_requirements': {
            'rare_items': 'complete_basic_achievements',
            'premium_items': 'complete_advanced_achievements',
            'exclusive_items': 'complete_special_achievements'
        },
        'currency_requirements': {
            'basic_items': 0,
            'rare_items': 10000,
            'premium_items': 50000,
            'exclusive_items': 100000
        },
        'special_requirements': {
            'event_shop': 'participate_in_event',
            'seasonal_shop': 'during_season',
            'premium_shop': 'premium_status'
        }
    }

def fetch_seasonal_items():
    """Fetch seasonal shop items"""
    return {
        'christmas': {
            'duration': {'start': '12-01', 'end': '12-31'},
            'items': {
                'santa_hat': {'price': 2000, 'effect': 'festive'},
                'christmas_tree': {'price': 5000, 'effect': 'decoration'},
                'snow_globe': {'price': 1000, 'effect': 'weather'}
            },
            'currency': 'event_tokens',
            'special_offers': True
        },
        'halloween': {
            'duration': {'start': '10-01', 'end': '10-31'},
            'items': {
                'spooky_mask': {'price': 2000, 'effect': 'scary'},
                'haunted_house': {'price': 5000, 'effect': 'decoration'},
                'ghost_pet': {'price': 10000, 'effect': 'companion'}
            },
            'currency': 'candy_corn',
            'special_offers': True
        },
        'summer': {
            'duration': {'start': '06-01', 'end': '08-31'},
            'items': {
                'beach_hat': {'price': 1000, 'effect': 'cooling'},
                'surfboard': {'price': 3000, 'effect': 'transportation'},
                'tropical_pet': {'price': 8000, 'effect': 'companion'}
            },
            'currency': 'seashells',
            'special_offers': True
        }
    }

def fetch_cross_game_items():
    """Fetch cross-game shop items"""
    return {
        'universal_equipment': {
            'master_sword': {
                'price': 100000,
                'usable_in': ['pokemon', 'osrs'],
                'effects': {
                    'pokemon': 'special_move',
                    'osrs': 'special_attack'
                }
            },
            'infinity_gauntlet': {
                'price': 1000000,
                'usable_in': ['pokemon', 'osrs', 'cookie_clicker'],
                'effects': {
                    'pokemon': 'snap_half_hp',
                    'osrs': 'instant_ko_chance',
                    'cookie_clicker': 'double_production'
                }
            }
        },
        'conversion_items': {
            'universal_exp_share': {
                'price': 50000,
                'effect': 'share_experience_across_games'
            },
            'loot_multiplier': {
                'price': 75000,
                'effect': 'increase_rewards_all_games'
            }
        },
        'special_abilities': {
            'cross_game_teleport': {
                'price': 25000,
                'effect': 'teleport_between_game_areas'
            },
            'universal_storage': {
                'price': 100000,
                'effect': 'shared_inventory_across_games'
            }
        }
    }

if __name__ == "__main__":
    fetch_shop_system_data() 