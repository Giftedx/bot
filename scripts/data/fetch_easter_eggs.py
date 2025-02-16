import json
from pathlib import Path
from datetime import datetime, timedelta
import random
import re
import sqlite3
import os

def fetch_easter_egg_data():
    """
    Fetches easter egg system data including:
    - Chat roast system
    - Hidden commands
    - Special events
    - Cross-game secrets
    """
    easter_egg_data = {
        'timestamp': datetime.now().isoformat(),
        'chat_roast': fetch_chat_roast_settings(),
        'hidden_commands': fetch_hidden_commands(),
        'special_events': fetch_special_events(),
        'cross_game_secrets': fetch_cross_game_secrets()
    }
    
    # Save the data
    output_dir = Path("src/data/easter_eggs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "easter_egg_data.json", 'w') as f:
        json.dump(easter_egg_data, f, indent=4)
    
    return easter_egg_data

def fetch_chat_roast_settings():
    """Fetch chat roast system settings"""
    return {
        'enabled': True,
        'database': {
            'path': 'data/easter_eggs/chat_logs.db',
            'tables': {
                'messages': '''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        channel_id TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        score FLOAT,
                        used_in_roast BOOLEAN DEFAULT FALSE
                    )
                ''',
                'roasts': '''
                    CREATE TABLE IF NOT EXISTS roasts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id INTEGER,
                        roast_message TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        FOREIGN KEY (message_id) REFERENCES messages (id)
                    )
                '''
            }
        },
        'scoring': {
            'weights': {
                'length': 0.2,        # Weight for message length
                'complexity': 0.3,    # Weight for message complexity
                'engagement': 0.2,    # Weight for reactions/replies
                'randomness': 0.3     # Random factor
            },
            'thresholds': {
                'min_length': 10,     # Minimum message length
                'max_length': 500,    # Maximum message length
                'min_score': 0.5      # Minimum score to be considered
            }
        },
        'cooldown': {
            'min_days': 3,
            'max_days': 7,
            'per_channel': True,
            'per_user': True
        },
        'triggers': {
            'random_chance': 0.001,   # 0.1% chance per message
            'time_window': {
                'min_days': 1,
                'max_days': 30
            },
            'excluded_channels': [
                'announcements',
                'rules',
                'admin',
                'mod-chat'
            ],
            'excluded_users': [
                'bot',
                'admin',
                'moderator'
            ]
        },
        'responses': {
            'templates': [
                "Remember when {user} said '{message}'? That was... something.",
                "Let's take a moment to appreciate this gem from {user}: '{message}'",
                "In today's episode of 'Things That Make You Go Hmm', brought to you by {user}: '{message}'",
                "Breaking news: {user} once thought this was worth saying: '{message}'",
                "Historians will look back at the time {user} said '{message}' and wonder why.",
                "Top 10 Messages That Didn't Age Well, featuring {user}'s '{message}'",
                "If I had a cookie for every time someone said something like {user}'s '{message}', I'd have exactly one cookie.",
                "In a parallel universe, {user} didn't say '{message}'. But in this one, they did.",
                "Plot twist: {user} actually typed '{message}' and thought it was a good idea.",
                "Today's 'What Were They Thinking?' award goes to {user} for '{message}'"
            ],
            'reactions': ['😂', '🤔', '👀', '💀', '🤦', '😅', '🎭'],
            'follow_up_chance': 0.2,  # 20% chance for a follow-up comment
            'follow_up_templates': [
                "I mean... wow.",
                "Still can't believe that happened.",
                "The silence is deafening.",
                "Anyone else need a moment to process that?",
                "This is going in the hall of fame.",
                "I'll just let that sink in."
            ]
        },
        'message_analysis': {
            'cringe_patterns': [
                r'actually[,.]\s',
                r'um[,.]\s',
                r'literally\s',
                r'(?:^|\s)i mean\s',
                r'(?:^|\s)like\s',
                r'!!+',
                r'\?{3,}',
                r'(?:^|\s)lol{3,}',
                r'(?:^|\s)omg{2,}'
            ],
            'bonus_scores': {
                'all_caps': 0.2,
                'excessive_punctuation': 0.3,
                'cringe_patterns': 0.4,
                'self_reply': 0.5
            }
        },
        'special_cases': {
            'rare_achievements': {
                'triple_cringe': {
                    'description': 'Message matches 3+ cringe patterns',
                    'bonus_score': 0.8
                },
                'self_roast': {
                    'description': 'User acknowledges their cringe',
                    'bonus_score': 0.6
                },
                'legendary_fail': {
                    'description': 'Message gets significant negative reactions',
                    'bonus_score': 1.0
                }
            },
            'seasonal_events': {
                'april_fools': {
                    'trigger_chance': 0.01,
                    'special_templates': [
                        "Breaking: {user}'s message '{message}' wins 'Most Serious Comment of the Year'",
                        "Scientists study {user}'s '{message}' as peak human communication"
                    ]
                }
            }
        }
    }

def fetch_hidden_commands():
    """Fetch hidden command data"""
    return {
        'cookie_clicker': {
            'trigger': '!cookie',
            'visibility': 'hidden',
            'chance_to_hint': 0.01,
            'hints': [
                "I sure could use a cookie right now...",
                "Anyone else craving something sweet?",
                "Click click click...",
                "Grandma's been asking about cookies lately."
            ]
        },
        'grandma_mode': {
            'trigger': '!grandma',
            'visibility': 'hidden',
            'effects': [
                'changes all responses to grandma-speak',
                'adds random cookie references',
                'occasionally complains about arthritis'
            ]
        },
        'roast_history': {
            'trigger': '!roastme',
            'visibility': 'hidden',
            'effects': [
                'shows user their most cringe messages',
                'generates custom roast based on message history'
            ]
        },
        'conspiracy': {
            'trigger': '!truth',
            'visibility': 'hidden',
            'effects': [
                'reveals random "conspiracy" about the bot',
                'generates fake "classified" documents'
            ]
        }
    }

def fetch_special_events():
    """Fetch special event data"""
    return {
        'message_milestone': {
            'trigger': 'every 10000 messages',
            'effect': 'reveals random chat statistics'
        },
        'rare_occurrence': {
            'trigger': '0.001% chance per message',
            'effect': 'creates unique event based on chat history'
        },
        'seasonal': {
            'april_fools': {
                'date': '04-01',
                'effects': ['increased roast chance', 'special roast templates']
            },
            'halloween': {
                'date': '10-31',
                'effects': ['spooky roasts', 'ghost stories from chat logs']
            }
        }
    }

def fetch_cross_game_secrets():
    """Fetch cross-game secret data"""
    return {
        'pokemon_reference': {
            'trigger': 'mentioning specific Pokemon',
            'effect': 'adds related roast template'
        },
        'osrs_reference': {
            'trigger': 'mentioning OSRS items/activities',
            'effect': 'adds game-specific roast'
        },
        'cookie_clicker_reference': {
            'trigger': 'mentioning cookies/grandmas',
            'effect': 'adds cookie-themed roast'
        },
        'combined_triggers': {
            'multi_game_reference': {
                'description': 'Message references multiple games',
                'effect': 'generates combined roast'
            }
        }
    }

def initialize_database():
    """Initialize the chat log database"""
    db_path = Path("data/easter_eggs/chat_logs.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            score FLOAT,
            used_in_roast BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Create roasts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            roast_message TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fetch_easter_egg_data()
    initialize_database() 