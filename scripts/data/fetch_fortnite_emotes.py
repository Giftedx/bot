import requests
import json
from pathlib import Path
from datetime import datetime
import os

def fetch_fortnite_emotes():
    """
    Fetches Fortnite emote data and creates custom integration settings
    """
    emote_data = {
        'timestamp': datetime.now().isoformat(),
        'emotes': fetch_emote_list(),
        'custom_emotes': fetch_custom_emotes(),
        'integration': fetch_integration_settings(),
        'animations': fetch_animation_data(),
        'sound_effects': fetch_sound_effects()
    }
    
    # Save the data
    output_dir = Path("src/data/fortnite")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "emote_data.json", 'w') as f:
        json.dump(emote_data, f, indent=4)
    
    return emote_data

def fetch_emote_list():
    """Fetch official Fortnite emotes"""
    api_key = os.getenv('FORTNITE_API_KEY')
    if not api_key:
        print("Fortnite API key not found")
        return {}
    
    try:
        headers = {
            'Authorization': api_key
        }
        response = requests.get(
            "https://fortnite-api.com/v2/cosmetics/br/search/all",
            headers=headers,
            params={'type': 'emote'}
        )
        response.raise_for_status()
        
        emotes = {}
        for item in response.json()['data']:
            emotes[item['id']] = {
                'name': item['name'],
                'description': item['description'],
                'rarity': item['rarity']['value'],
                'type': item['type']['value'],
                'introduction': item.get('introduction', {}),
                'images': item['images']
            }
        
        return emotes
    
    except Exception as e:
        print(f"Error fetching Fortnite emotes: {str(e)}")
        return {}

def fetch_custom_emotes():
    """Fetch custom emote data for bot integration"""
    return {
        'pokemon_emotes': {
            'catch': {
                'name': 'Poké Catch',
                'animation': 'throw_ball',
                'sound': 'pokeball_throw',
                'trigger': ['!catch', 'catching a Pokemon']
            },
            'evolution': {
                'name': 'Evolution Dance',
                'animation': 'evolution_spin',
                'sound': 'evolution_complete',
                'trigger': ['Pokemon evolving']
            }
        },
        'osrs_emotes': {
            'level_up': {
                'name': 'Level Up',
                'animation': 'fireworks_dance',
                'sound': 'level_up_jingle',
                'trigger': ['gaining a level']
            },
            'rare_drop': {
                'name': 'Rare Drop',
                'animation': 'treasure_dance',
                'sound': 'rare_drop_sound',
                'trigger': ['getting a rare drop']
            }
        },
        'cookie_clicker_emotes': {
            'golden_cookie': {
                'name': 'Cookie Rain',
                'animation': 'cookie_shower',
                'sound': 'cookie_crunch',
                'trigger': ['golden cookie appears']
            },
            'grandmapocalypse': {
                'name': 'Grandma Rage',
                'animation': 'angry_grandma',
                'sound': 'grandma_mumble',
                'trigger': ['grandmapocalypse triggers']
            }
        },
        'plex_emotes': {
            'movie_time': {
                'name': 'Movie Night',
                'animation': 'popcorn_dance',
                'sound': 'movie_start',
                'trigger': ['starting a movie']
            },
            'binge_watch': {
                'name': 'Binge Mode',
                'animation': 'couch_potato',
                'sound': 'next_episode',
                'trigger': ['auto-playing next episode']
            }
        }
    }

def fetch_integration_settings():
    """Fetch integration settings for emote system"""
    return {
        'trigger_settings': {
            'auto_trigger': True,
            'command_trigger': True,
            'context_trigger': True
        },
        'display_settings': {
            'show_in_chat': True,
            'show_in_voice': True,
            'show_in_status': True
        },
        'permission_settings': {
            'user_level_required': 0,
            'cooldown': 30,  # seconds
            'channel_restrictions': []
        },
        'reward_settings': {
            'unlock_system': True,
            'achievement_rewards': True,
            'special_event_rewards': True
        },
        'cross_game_triggers': {
            'pokemon': {
                'catch_success': 'catch',
                'evolution': 'evolution_dance'
            },
            'osrs': {
                'level_milestone': 'level_up',
                'rare_drop': 'treasure_dance'
            },
            'cookie_clicker': {
                'golden_cookie': 'cookie_rain',
                'grandmapocalypse': 'grandma_rage'
            }
        }
    }

def fetch_animation_data():
    """Fetch animation data for emotes"""
    return {
        'throw_ball': {
            'frames': 24,
            'duration': 1000,  # ms
            'loop': False,
            'sprite_sheet': 'throw_ball.png'
        },
        'evolution_spin': {
            'frames': 36,
            'duration': 1500,
            'loop': True,
            'sprite_sheet': 'evolution_spin.png'
        },
        'fireworks_dance': {
            'frames': 48,
            'duration': 2000,
            'loop': True,
            'sprite_sheet': 'fireworks_dance.png'
        },
        'treasure_dance': {
            'frames': 32,
            'duration': 1800,
            'loop': True,
            'sprite_sheet': 'treasure_dance.png'
        },
        'cookie_shower': {
            'frames': 40,
            'duration': 2200,
            'loop': True,
            'sprite_sheet': 'cookie_shower.png'
        },
        'angry_grandma': {
            'frames': 28,
            'duration': 1600,
            'loop': True,
            'sprite_sheet': 'angry_grandma.png'
        },
        'popcorn_dance': {
            'frames': 36,
            'duration': 2000,
            'loop': True,
            'sprite_sheet': 'popcorn_dance.png'
        },
        'couch_potato': {
            'frames': 24,
            'duration': 1400,
            'loop': True,
            'sprite_sheet': 'couch_potato.png'
        }
    }

def fetch_sound_effects():
    """Fetch sound effect data for emotes"""
    return {
        'pokeball_throw': {
            'file': 'pokeball_throw.mp3',
            'duration': 800,
            'volume': 0.8
        },
        'evolution_complete': {
            'file': 'evolution_complete.mp3',
            'duration': 1200,
            'volume': 0.9
        },
        'level_up_jingle': {
            'file': 'level_up_jingle.mp3',
            'duration': 1000,
            'volume': 0.85
        },
        'rare_drop_sound': {
            'file': 'rare_drop_sound.mp3',
            'duration': 900,
            'volume': 0.9
        },
        'cookie_crunch': {
            'file': 'cookie_crunch.mp3',
            'duration': 500,
            'volume': 0.75
        },
        'grandma_mumble': {
            'file': 'grandma_mumble.mp3',
            'duration': 1100,
            'volume': 0.7
        },
        'movie_start': {
            'file': 'movie_start.mp3',
            'duration': 1500,
            'volume': 0.8
        },
        'next_episode': {
            'file': 'next_episode.mp3',
            'duration': 700,
            'volume': 0.75
        }
    }

if __name__ == "__main__":
    fetch_fortnite_emotes() 