import discord
import os
import asyncio
import json
import logging
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Union, Set, Tuple
from discord.ext import commands, tasks
from dotenv import load_dotenv
from plexapi.server import PlexServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("discord_bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger("DiscordBot")

# --- Load Environment Variables ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

# --- Bot Configuration ---
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

# --- Initialize Global Variables ---
plex = None
text_channel = None
chat_log = []

# Game Systems - Moving Enums and Dataclasses first
class PetType(Enum):
    FIRE = "🔥"
    WATER = "💧" 
    EARTH = "🌍"
    AIR = "💨"
    LIGHT = "✨"
    DARK = "🌑"

class StatusEffect(Enum):
    BURN = "🔥"
    POISON = "🤢" 
    PARALYZE = "⚡"
    SLEEP = "💤"
    NONE = ""

@dataclass
class PetMove:
    name: str
    damage: int
    element: PetType
    accuracy: int
    cooldown: int
    emoji: str
    status_effect: StatusEffect = StatusEffect.NONE
    status_chance: int = 0
    current_cooldown: int = 0

@dataclass
class BattlePet:
    pet: 'Pet'
    moves: List[PetMove]
    current_hp: int
    max_hp: int
    element: PetType
    status: StatusEffect = StatusEffect.NONE
    status_turns: int = 0

# Then bot class 

# Then cogs

# Then main