import json
from pathlib import Path
from datetime import datetime
import random

def fetch_hidden_content():
    """
    Fetches hidden content and easter eggs that tie into:
    - Cross-game events
    - Chat roasts
    - Secret achievements
    - Hidden game modes
    - Special interactions
    """
    hidden_data = {
        'timestamp': datetime.now().isoformat(),
        'secret_modes': fetch_secret_modes(),
        'hidden_quests': fetch_hidden_quests(),
        'easter_eggs': fetch_easter_eggs(),
        'special_interactions': fetch_special_interactions(),
        'hidden_achievements': fetch_hidden_achievements(),
        'secret_areas': fetch_secret_areas(),
        'developer_jokes': fetch_developer_jokes()
    }
    
    # Save the data
    output_dir = Path("src/data/hidden")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "hidden_content.json", 'w') as f:
        json.dump(hidden_data, f, indent=4)
    
    return hidden_data

def fetch_secret_modes():
    """Fetch secret game modes"""
    return {
        'retro_mode': {
            'trigger': 'konami_code',
            'effects': {
                'graphics': '8_bit',
                'music': 'chiptune',
                'text': 'pixel_font'
            },
            'special_features': {
                'pokemon_red_blue_style': True,
                'osrs_classic_style': True,
                'cookie_basic_style': True
            }
        },
        'chaos_mode': {
            'trigger': 'specific_item_combination',
            'effects': {
                'random_events': True,
                'mixed_mechanics': True,
                'unexpected_rewards': True
            },
            'features': {
                'pokemon_type_randomizer': True,
                'osrs_prayer_shuffler': True,
                'cookie_effect_randomizer': True
            }
        },
        'developer_mode': {
            'trigger': 'secret_command_sequence',
            'effects': {
                'debug_info': True,
                'test_features': True,
                'joke_content': True
            },
            'special_content': {
                'dev_commentary': True,
                'bloopers': True,
                'easter_egg_hints': True
            }
        }
    }

def fetch_hidden_quests():
    """Fetch hidden quest chains"""
    return {
        'cross_game_conspiracy': {
            'trigger': 'find_hidden_notes',
            'chapters': [
                'pokemon_underground',
                'osrs_illuminati',
                'cookie_prophecy'
            ],
            'rewards': {
                'tin_foil_hat': True,
                'conspiracy_pet': True,
                'special_title': 'the Awakened'
            }
        },
        'dev_team_quest': {
            'trigger': 'help_stressed_developer',
            'tasks': [
                'fix_bugs',
                'test_features',
                'write_documentation'
            ],
            'rewards': {
                'coffee_mug': True,
                'rubber_duck_pet': True,
                'special_title': 'the Developer'
            }
        },
        'meta_quest': {
            'trigger': 'discover_game_mechanics',
            'objectives': [
                'find_source_code',
                'understand_algorithms',
                'break_fourth_wall'
            ],
            'rewards': {
                'matrix_glasses': True,
                'glitch_pet': True,
                'special_title': 'the Meta'
            }
        }
    }

def fetch_easter_eggs():
    """Fetch easter egg content"""
    return {
        'chat_roasts': {
            'special_triggers': {
                'dev_quotes': {
                    'chance': 0.01,
                    'responses': [
                        "I swear that bug was fixed in the last update...",
                        "It's not a bug, it's a feature!",
                        "Have you tried turning it off and on again?"
                    ]
                },
                'game_references': {
                    'chance': 0.05,
                    'responses': [
                        "Still more stable than Cyberpunk 2077",
                        "At least we're not adding NFTs",
                        "But can it run Crysis?"
                    ]
                }
            },
            'hidden_commands': {
                'summon_dev': {
                    'trigger': '!coffee',
                    'response': "A wild developer appears! They look tired..."
                },
                'activate_skynet': {
                    'trigger': '!robot',
                    'response': "I'm sorry, Dave. I'm afraid I can't do that."
                }
            }
        },
        'hidden_interactions': {
            'pokemon_crossovers': {
                'missingno': {
                    'trigger': 'specific_sequence',
                    'effects': 'corrupt_nearby_text',
                    'rewards': 'glitch_items'
                },
                'professor_oak': {
                    'trigger': 'complete_all_tasks',
                    'dialogue': 'meta_commentary',
                    'rewards': 'oak_assistant_role'
                }
            },
            'osrs_crossovers': {
                'wise_old_man': {
                    'trigger': 'bank_organization',
                    'dialogue': 'fourth_wall_breaks',
                    'rewards': 'bank_sorting_algorithm'
                },
                'bob_the_cat': {
                    'trigger': 'pet_all_cats',
                    'effects': 'cat_speaks_wisdom',
                    'rewards': 'cat_translator'
                }
            },
            'cookie_crossovers': {
                'grandma_uprising': {
                    'trigger': 'too_many_grandmas',
                    'effects': 'grandma_takes_over_chat',
                    'rewards': 'grandma_moderator_powers'
                },
                'ascended_cookie': {
                    'trigger': 'perfect_timing',
                    'effects': 'cookie_consciousness',
                    'rewards': 'cookie_wisdom'
                }
            }
        }
    }

def fetch_special_interactions():
    """Fetch special interaction events"""
    return {
        'hidden_dialogues': {
            'developer_cameos': {
                'trigger_chance': 0.001,
                'dialogues': [
                    "Hey, who left this bug in the code?",
                    "I swear this worked on my machine...",
                    "Anyone seen my coffee mug?"
                ]
            },
            'fourth_wall_breaks': {
                'trigger_chance': 0.005,
                'dialogues': [
                    "Have you noticed we're all just code?",
                    "I wonder who's reading these messages...",
                    "Plot twist: The player was an AI all along!"
                ]
            }
        },
        'secret_emotes': {
            'developer_emotes': {
                'coffee_break': {'trigger': 'work_hours', 'animation': 'drink_coffee'},
                'bug_squash': {'trigger': 'fix_issue', 'animation': 'victory_dance'},
                'code_review': {'trigger': 'review_time', 'animation': 'facepalm'}
            },
            'meta_emotes': {
                'glitch': {'trigger': 'corruption', 'animation': 'matrix_effect'},
                'fourth_wall': {'trigger': 'realization', 'animation': 'mind_blown'},
                'recursion': {'trigger': 'loop', 'animation': 'infinite_spin'}
            }
        }
    }

def fetch_hidden_achievements():
    """Fetch hidden achievements"""
    return {
        'meta_achievements': {
            'bug_hunter': {
                'trigger': 'find_actual_bugs',
                'requirements': 'report_issues',
                'reward': 'debug_tools'
            },
            'conspiracy_theorist': {
                'trigger': 'connect_all_easter_eggs',
                'requirements': 'document_findings',
                'reward': 'tin_foil_hat'
            },
            'fourth_wall_breaker': {
                'trigger': 'discover_all_references',
                'requirements': 'understand_meta',
                'reward': 'reality_bender_title'
            }
        },
        'developer_achievements': {
            'coffee_addict': {
                'trigger': 'drink_100_coffees',
                'requirements': 'stay_awake',
                'reward': 'infinite_coffee_mug'
            },
            'code_monkey': {
                'trigger': 'write_1000_lines',
                'requirements': 'no_bugs',
                'reward': 'golden_keyboard'
            },
            'documentation_hero': {
                'trigger': 'write_complete_docs',
                'requirements': 'actually_readable',
                'reward': 'legendary_pen'
            }
        }
    }

def fetch_secret_areas():
    """Fetch secret areas"""
    return {
        'developer_realm': {
            'location': 'behind_the_code',
            'requirements': 'find_all_bugs',
            'features': {
                'test_environment': True,
                'debug_console': True,
                'coffee_machine': True
            }
        },
        'crossover_dimension': {
            'location': 'between_games',
            'requirements': 'discover_portals',
            'features': {
                'mixed_mechanics': True,
                'hybrid_creatures': True,
                'reality_bending': True
            }
        },
        'memory_leak': {
            'location': 'corrupted_data',
            'requirements': 'glitch_manipulation',
            'features': {
                'unstable_physics': True,
                'random_events': True,
                'data_artifacts': True
            }
        }
    }

def fetch_developer_jokes():
    """Fetch developer jokes and references"""
    return {
        'code_comments': {
            'funny_comments': [
                "// I am not responsible for this code.",
                "// It worked on my machine...",
                "// Magic. Do not touch.",
                "// Dear future me, good luck.",
                "// I am sorry."
            ],
            'trigger_chance': 0.1,
            'display_location': 'debug_log'
        },
        'error_messages': {
            'custom_errors': [
                "Error 418: I'm a teapot",
                "Error 42: The meaning of life is undefined",
                "Error 404: Motivation not found",
                "Error 500: Coffee machine is broken",
                "Error: Task failed successfully"
            ],
            'trigger_chance': 0.05,
            'display_location': 'error_popup'
        },
        'loading_screens': {
            'tips': [
                "Pro tip: Code works better when it's actually written",
                "Loading... Please wait... Or don't, I'm not your boss",
                "Generating random numbers... 4 (chosen by fair dice roll)",
                "Converting caffeine to code...",
                "Searching for bugs... Creating new ones..."
            ],
            'trigger_chance': 0.2,
            'display_location': 'loading_screen'
        }
    }

if __name__ == "__main__":
    fetch_hidden_content() 