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

# --- Enhanced Logging Setup ---
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

# Will continue with remaining sections...