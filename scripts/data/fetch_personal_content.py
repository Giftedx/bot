import json
from pathlib import Path
from datetime import datetime
import random

def fetch_personal_content():
    """
    Fetches personal easter eggs and Plex-based content including:
    - Personal pets and references
    - Player-specific content
    - Plex watch rewards
    - Meta challenges
    """
    personal_data = {
        'timestamp': datetime.now().isoformat(),
        'personal_pets': fetch_personal_pets(),
        'player_references': fetch_player_references(),
        'plex_rewards': fetch_plex_rewards(),
        'meta_challenges': fetch_meta_challenges(),
        'hidden_jokes': fetch_hidden_jokes(),
        'special_unlocks': fetch_special_unlocks()
    }
    
    # Save the data
    output_dir = Path("src/data/personal")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "personal_content.json", 'w') as f:
        json.dump(personal_data, f, indent=4)
    
    return personal_data

def fetch_personal_pets():
    """Fetch personal pet data"""
    return {
        'exclusive_pets': {
            'bella': {
                'owner': 'Haggis',
                'type': 'Yorkshire Terrier',
                'description': 'A very protective Yorkshire Terrier, guardian of her home',
                'unlock_condition': 'account_name == "Haggis"',
                'rarity': 'Mythical',
                'abilities': {
                    'home_guard': {
                        'effect': 'Bonus defense when near player house',
                        'power': 'Very high'
                    },
                    'fierce_bark': {
                        'effect': 'Chance to intimidate enemies',
                        'power': 'Medium'
                    },
                    'loyal_companion': {
                        'effect': 'Increased stats when with owner',
                        'power': 'High'
                    }
                }
            },
            'pumpkin': {
                'owner': 'ThePanj',
                'type': 'Cat',
                'description': 'ThePanj and PeachComfort\'s beloved cat',
                'unlock_condition': 'account_name in ["ThePanj", "PeachComfort"]',
                'rarity': 'Legendary',
                'abilities': {
                    'mull_explorer': {
                        'effect': 'Enhanced exploration abilities',
                        'power': 'High'
                    }
                }
            },
            'cheddar': {
                'owner': 'ThePanj',
                'type': 'White Cat',
                'description': 'A majestic white cat from the Isle of Mull',
                'unlock_condition': 'account_name in ["ThePanj", "PeachComfort"]',
                'rarity': 'Legendary',
                'abilities': {
                    'island_spirit': {
                        'effect': 'Water walking in Mull',
                        'power': 'High'
                    }
                }
            }
        },
        'pet_interactions': {
            'bella_protection': {
                'trigger': 'near_home',
                'effect': 'Increases home defense',
                'animation': 'protective_bark'
            },
            'cat_duo': {
                'trigger': 'pumpkin_and_cheddar_together',
                'effect': 'Isle of Mull blessing',
                'animation': 'mull_magic'
            }
        }
    }

def fetch_player_references():
    """Fetch player-specific references"""
    return {
        'player_jokes': {
            'gary_botting': {
                'trigger': 'long_afk_duration',
                'response': "Must be Gary playing again...",
                'chance': 0.1,
                'conditions': {
                    'player': 'ThePanj',
                    'afk_time': '> 15 minutes'
                }
            },
            'customer_support': {
                'trigger': 'banned_reference',
                'response': "Have you tried making a Reddit post?",
                'chance': 0.05,
                'conditions': {
                    'context': 'ban_discussion'
                }
            }
        },
        'special_titles': {
            'haggis': {
                'title': 'the Falsely Accused',
                'unlock': 'complete_special_quest',
                'effects': ['bonus_anti_bot_protection', 'customer_support_priority']
            },
            'thepanj': {
                'title': 'Guardian of Gary',
                'unlock': 'achieve_maximum_afk',
                'effects': ['afk_immunity', 'gary_summoning']
            },
            'peachcomfort': {
                'title': 'Mull Cat Whisperer',
                'unlock': 'obtain_both_cats',
                'effects': ['cat_communication', 'mull_teleport']
            }
        }
    }

def fetch_plex_rewards():
    """Fetch Plex-based rewards and challenges"""
    return {
        'watch_streaks': {
            'daily_rewards': {
                'three_days': {
                    'requirement': 'watch_3_consecutive_days',
                    'reward': 'minor_buff',
                    'buff_duration': '24h'
                },
                'weekly': {
                    'requirement': 'watch_7_consecutive_days',
                    'reward': 'major_buff',
                    'buff_duration': '72h'
                },
                'monthly': {
                    'requirement': '20_days_in_month',
                    'reward': 'epic_buff',
                    'buff_duration': '7d'
                }
            },
            'genre_bonuses': {
                'action': {
                    'buff': 'combat_boost',
                    'duration': 'next_combat'
                },
                'comedy': {
                    'buff': 'luck_boost',
                    'duration': '1h'
                },
                'sci_fi': {
                    'buff': 'technology_boost',
                    'duration': '2h'
                }
            }
        },
        'content_specific': {
            'movie_challenges': {
                'lord_of_the_rings': {
                    'requirement': 'watch_extended_trilogy',
                    'reward': 'ring_of_power',
                    'effects': ['invisibility', 'corruption']
                },
                'matrix': {
                    'requirement': 'watch_trilogy',
                    'reward': 'red_pill',
                    'effects': ['see_code', 'dodge_bullets']
                },
                'star_wars': {
                    'requirement': 'watch_original_trilogy',
                    'reward': 'force_powers',
                    'effects': ['mind_trick', 'lightsaber']
                }
            },
            'series_challenges': {
                'breaking_bad': {
                    'requirement': 'complete_series',
                    'reward': 'heisenberg_hat',
                    'effects': ['chemistry_boost', 'danger_sense']
                },
                'game_of_thrones': {
                    'requirement': 'complete_series',
                    'reward': 'iron_throne',
                    'effects': ['dragon_summon', 'political_power']
                },
                'stranger_things': {
                    'requirement': 'complete_series',
                    'reward': 'upside_down_portal',
                    'effects': ['dimensional_travel', 'psychic_powers']
                }
            }
        },
        'watch_party_events': {
            'group_challenges': {
                'marvel_marathon': {
                    'requirement': 'watch_all_mcu_films',
                    'group_size': '5+',
                    'reward': 'infinity_gauntlet',
                    'duration': '48h'
                },
                'harry_potter_weekend': {
                    'requirement': 'watch_all_films',
                    'group_size': '3+',
                    'reward': 'elder_wand',
                    'duration': '24h'
                }
            }
        }
    }

def fetch_meta_challenges():
    """Fetch meta challenges and achievements"""
    return {
        'cross_media_challenges': {
            'pokemon_master_chef': {
                'requirements': {
                    'watch': 'complete_cooking_show_season',
                    'achieve': 'catch_all_fire_types',
                    'craft': 'cook_special_curry'
                },
                'reward': 'master_chef_hat',
                'effects': ['cooking_boost', 'fire_power']
            },
            'osrs_warrior_poet': {
                'requirements': {
                    'watch': 'complete_historical_drama',
                    'achieve': 'maxed_combat',
                    'craft': 'write_epic_poem'
                },
                'reward': 'bardic_weapon',
                'effects': ['combat_boost', 'inspiration']
            }
        },
        'hidden_achievements': {
            'gary_detector': {
                'trigger': 'catch_someone_botting',
                'response': "Nice try, Gary!",
                'reward': 'bot_detection_goggles'
            },
            'reddit_warrior': {
                'trigger': 'write_passionate_complaint',
                'response': "The neckbeards are pleased",
                'reward': 'karma_crown'
            }
        }
    }

def fetch_hidden_jokes():
    """Fetch hidden jokes and references"""
    return {
        'chat_triggers': {
            'gary_excuses': [
                "Sorry, that was Gary using my account",
                "Gary must have borrowed my PC again",
                "Classic Gary moment",
                "Gary says he wasn't botting"
            ],
            'support_tickets': [
                "Have you tried getting 10k upvotes on Reddit?",
                "Customer support might respond in 2027",
                "Time to write an essay about false bans",
                "The ban appeal system is working as intended™"
            ],
            'mull_references': [
                "Somewhere on Mull, two cats are plotting something",
                "Pumpkin and Cheddar send their regards",
                "The Isle of Mull grows stronger"
            ]
        },
        'rare_events': {
            'bella_guardian': {
                'trigger_chance': 0.01,
                'effect': 'Bella appears to protect Haggis from bans',
                'message': "A Yorkshire Terrier growls at the ban system"
            },
            'cat_conspiracy': {
                'trigger_chance': 0.01,
                'effect': 'Pumpkin and Cheddar cause mischief',
                'message': "Two cats on Mull are planning something..."
            }
        }
    }

def fetch_special_unlocks():
    """Fetch special unlock conditions"""
    return {
        'personal_quests': {
            'haggis_redemption': {
                'title': 'Appeal of the Falsely Banned',
                'steps': [
                    'gather_evidence',
                    'write_reddit_post',
                    'gain_community_support'
                ],
                'reward': 'unban_immunity'
            },
            'panj_gary': {
                'title': 'The Legend of Gary',
                'steps': [
                    'achieve_maximum_afk',
                    'collect_gary_excuses',
                    'master_the_art_of_gary'
                ],
                'reward': 'gary_summoning_stone'
            }
        },
        'location_unlocks': {
            'isle_of_mull': {
                'requirement': 'befriend_cats',
                'features': [
                    'cat_sanctuary',
                    'peaceful_home',
                    'special_teleport'
                ]
            },
            'bella_domain': {
                'requirement': 'earn_bella_trust',
                'features': [
                    'yorkshire_territory',
                    'protective_aura',
                    'anti_ban_field'
                ]
            }
        }
    }

if __name__ == "__main__":
    fetch_personal_content() 