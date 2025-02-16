import json
from pathlib import Path
from datetime import datetime
import random

def fetch_cookie_clicker_data():
    """
    Fetches Cookie Clicker game data and easter egg system settings
    """
    cookie_data = {
        'timestamp': datetime.now().isoformat(),
        'game_mechanics': fetch_game_mechanics(),
        'buildings': fetch_buildings(),
        'upgrades': fetch_upgrades(),
        'achievements': fetch_achievements(),
        'easter_eggs': fetch_easter_eggs(),
        'integration': fetch_integration_settings()
    }
    
    # Save the data
    output_dir = Path("src/data/cookie_clicker")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "cookie_clicker_data.json", 'w') as f:
        json.dump(cookie_data, f, indent=4)
    
    return cookie_data

def fetch_game_mechanics():
    """Fetch core game mechanics data"""
    return {
        'base_cps': 0.1,  # Cookies per second
        'click_power': 1,
        'golden_cookie': {
            'spawn_rate': 0.5,  # % chance per minute
            'duration': 13,     # seconds
            'effects': {
                'frenzy': {'multiplier': 7, 'duration': 77},
                'lucky': {'bonus': 0.15, 'duration': 0},
                'click_frenzy': {'multiplier': 777, 'duration': 13}
            }
        },
        'wrinklers': {
            'max_count': 10,
            'consumption_rate': 0.05,
            'return_multiplier': 1.1
        }
    }

def fetch_buildings():
    """Fetch building data"""
    return {
        'cursor': {
            'base_cost': 15,
            'base_cps': 0.1,
            'description': 'Autoclicks once every 10 seconds.'
        },
        'grandma': {
            'base_cost': 100,
            'base_cps': 1,
            'description': 'A nice grandma to bake more cookies.'
        },
        'farm': {
            'base_cost': 1100,
            'base_cps': 8,
            'description': 'Grows cookie plants from cookie seeds.'
        },
        'mine': {
            'base_cost': 12000,
            'base_cps': 47,
            'description': 'Mines out cookie dough and chocolate chips.'
        }
        # ... more buildings ...
    }

def fetch_upgrades():
    """Fetch upgrade data"""
    return {
        'reinforced_index_finger': {
            'cost': 100,
            'requirement': {'building': 'cursor', 'amount': 1},
            'effect': {'target': 'cursor', 'multiplier': 2}
        },
        'carpal_tunnel_prevention_cream': {
            'cost': 500,
            'requirement': {'building': 'cursor', 'amount': 1},
            'effect': {'target': 'cursor', 'multiplier': 2}
        },
        'forwards_from_grandma': {
            'cost': 1000,
            'requirement': {'building': 'grandma', 'amount': 1},
            'effect': {'target': 'grandma', 'multiplier': 2}
        }
        # ... more upgrades ...
    }

def fetch_achievements():
    """Fetch achievement data"""
    return {
        'wake_and_bake': {
            'description': 'Bake 1 cookie.',
            'requirement': {'cookies': 1},
            'reward': {'achievement_points': 1}
        },
        'making_some_dough': {
            'description': 'Bake 1,000 cookies.',
            'requirement': {'cookies': 1000},
            'reward': {'achievement_points': 5}
        },
        'cookie_monster': {
            'description': 'Bake 100,000 cookies.',
            'requirement': {'cookies': 100000},
            'reward': {'achievement_points': 10}
        }
        # ... more achievements ...
    }

def fetch_easter_eggs():
    """Fetch easter egg system data"""
    return {
        'chat_roast_system': {
            'enabled': True,
            'cooldown': {
                'min_days': 3,
                'max_days': 7
            },
            'trigger_chance': 0.001,  # 0.1% chance per eligible message
            'message_age': {
                'min_days': 1,
                'max_days': 30
            },
            'scoring': {
                'length': 0.2,        # Weight for message length
                'complexity': 0.3,    # Weight for message complexity
                'engagement': 0.2,    # Weight for reactions/replies
                'randomness': 0.3     # Random factor
            },
            'response_templates': [
                "Remember when {user} said '{message}'? That was... something.",
                "Let's take a moment to appreciate this gem from {user}: '{message}'",
                "In today's episode of 'Things That Make You Go Hmm', brought to you by {user}: '{message}'",
                "Breaking news: {user} once thought this was worth saying: '{message}'"
            ],
            'filters': {
                'min_length': 10,
                'max_length': 500,
                'excluded_users': ['bot', 'admin'],
                'excluded_channels': ['announcements', 'rules']
            }
        },
        'hidden_commands': {
            'cookie_clicker': {
                'trigger': '!cookie',
                'visibility': 'hidden',
                'chance_to_hint': 0.01  # 1% chance to drop a hint in responses
            },
            'grandma_mode': {
                'trigger': '!grandma',
                'visibility': 'hidden',
                'effects': ['changes all responses to grandma-speak']
            }
        },
        'special_events': {
            'cookie_rain': {
                'trigger_chance': 0.001,
                'duration': 60,  # seconds
                'bonus_multiplier': 10
            },
            'grandmapocalypse': {
                'trigger_condition': 'grandmas >= 50',
                'effects': ['corrupted_messages', 'evil_grandmas']
            }
        }
    }

def fetch_integration_settings():
    """Fetch integration settings"""
    return {
        'discord_presence': {
            'enabled': True,
            'show_cookies': True,
            'show_cps': True
        },
        'cross_game_rewards': {
            'pokemon': {
                'cookie_milestone_rewards': True,
                'special_pokemon_unlocks': True
            },
            'osrs': {
                'cookie_to_gp': True,
                'special_item_unlocks': True
            },
            'plex': {
                'watch_time_cookies': True,
                'special_theme_unlocks': True
            }
        },
        'achievements': {
            'discord_announcements': True,
            'reward_multipliers': True,
            'special_roles': True
        },
        'seasonal_events': {
            'christmas': {
                'santa_cookies': True,
                'special_upgrades': True
            },
            'halloween': {
                'spooky_cookies': True,
                'special_effects': True
            }
        }
    }

if __name__ == "__main__":
    fetch_cookie_clicker_data() 