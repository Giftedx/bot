#!/usr/bin/env python3
"""
Script to fetch Pokemon data from multiple sources including:
- PokeAPI (official)
- Serebii.net (via web scraping)
- Bulbapedia (via web scraping)
- Pokemon Showdown (via API)
- Pokemon Database (via web scraping)
- Pokemon GO Game Master (via API)
- Pokemon TCG API
- ROM Data (GB/GBC/GBA games)
- PKHeX (data structures and formats)
- PokeTools (ROM parsing)
- Veekun (game data)
- PokemonDB (stats and mechanics)
- Smogon (competitive data)
- Discord Activities (via Discord API)
- Vencord Plugins (via GitHub API)
- Plex Integration Data
  - Media Playback in Discord Voice
  - Direct Stream Integration
  - Watch Together Support
- Spotify Integration Data
- YouTube Integration Data
- OSRS Wiki Data
- Stack Overflow Snippets
- GitHub Public Repos
- FOSS Libraries
- MIT Licensed Code

Coordinates fetching of Pokemon, moves, abilities, items, and other game data.
Implements rate limiting to avoid overloading the APIs.
"""
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
import sys
import time
from typing import Dict, Any, List, Set, Optional
import re
from bs4 import BeautifulSoup
import mwparserfromhell
import pokepy
import ptcgio
from pokemon_tcg_sdk.api import PokemonTcgAPI
from github import Github
from plexapi.server import PlexServer
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from googleapiclient.discovery import build
import stackapi
import aiohttp
import discord
from discord.ext import commands
import vdf  # For parsing Vencord plugin data
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_pokemon.log")
    ]
)
logger = logging.getLogger(__name__)

# API endpoints
POKEAPI_URL = "https://pokeapi.co/api/v2"
SEREBII_URL = "https://www.serebii.net"
BULBAPEDIA_URL = "https://bulbapedia.bulbagarden.net/w/api.php"
SHOWDOWN_URL = "https://play.pokemonshowdown.com/data"
POKEMONGO_URL = "https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json"
POKEMONTCG_URL = "https://api.pokemontcg.io/v2"
DISCORD_API_URL = "https://discord.com/api/v10"
VENCORD_REPO_URL = "https://github.com/Vendicated/Vencord"
OSRS_WIKI_API = "https://oldschool.runescape.wiki/api.php"
STACKOVERFLOW_API = "https://api.stackexchange.com/2.3"
GITHUB_API = "https://api.github.com"

# Discord Activities IDs
DISCORD_ACTIVITIES = {
    'youtube': '880218394199220334',  # Watch Together
    'poker': '755827207812677713',    # Poker Night
    'betrayal': '773336526917861400', # Betrayal.io
    'fishing': '814288819477020702',  # Fishington.io
    'chess': '832012774040141894',    # Chess in the Park
    'letter': '879863686565621790',   # Letter League
    'word': '879863976006127627',     # Word Snacks
    'sketch': '902271654783242291',   # Sketch Heads
    'spellcast': '852509694341283871' # Spellcast
}

# Add new Plex-Discord integration constants
PLEX_DISCORD_ACTIVITIES = {
    'watch_together': '880218394199220334',  # Watch Together base activity
    'plex_stream': '1234567890',  # Placeholder for Plex stream activity
}

# Add new Plex media types
PLEX_MEDIA_TYPES = {
    'movie': 1,
    'show': 2,
    'season': 3,
    'episode': 4,
    'trailer': 5,
    'comic': 6,
    'person': 7,
    'artist': 8,
    'album': 9,
    'track': 10,
    'photoAlbum': 11,
    'picture': 12,
    'clip': 13,
    'playlistItem': 14
}

# ROM Data Structures
class RomHeader:
    """Game Boy ROM header structure."""
    def __init__(self, data: bytes):
        self.entry_point = data[0x100:0x104]
        self.nintendo_logo = data[0x104:0x134]
        self.title = data[0x134:0x144].decode('ascii').rstrip('\0')
        self.manufacturer_code = data[0x13F:0x143]
        self.cgb_flag = data[0x143]
        self.new_licensee_code = data[0x144:0x146]
        self.sgb_flag = data[0x146]
        self.cartridge_type = data[0x147]
        self.rom_size = data[0x148]
        self.ram_size = data[0x149]
        self.destination_code = data[0x14A]
        self.old_licensee_code = data[0x14B]
        self.mask_rom_version = data[0x14C]
        self.header_checksum = data[0x14D]
        self.global_checksum = int.from_bytes(data[0x14E:0x150], byteorder='big')

class PlexDiscordIntegration:
    """Handles Plex media playback in Discord voice channels."""
    
    def __init__(self, plex_server: PlexServer, discord_client: discord.Client):
        self.plex = plex_server
        self.discord = discord_client
        self.active_streams = {}
        self.stream_settings = {
            'transcode_quality': '1080p',
            'audio_channels': 2,
            'bitrate': '4mbps'
        }
        
    async def start_stream(self, voice_channel: discord.VoiceChannel, media_id: str) -> dict:
        """Start streaming Plex media to a Discord voice channel."""
        try:
            # Get media item from Plex
            media = self.plex.fetchItem(int(media_id))
            if not media:
                raise ValueError(f"Media item {media_id} not found")
                
            # Create stream URL with transcoding settings
            stream_url = media.getStreamURL(
                quality=self.stream_settings['transcode_quality'],
                maxAudioChannels=self.stream_settings['audio_channels']
            )
            
            # Create Discord activity for the stream
            activity = {
                'type': 'STREAMING',
                'name': f'Watching {media.title}',
                'url': stream_url,
                'details': f'{media.type.title()} - {media.title}',
                'assets': {
                    'large_image': media.thumb,
                    'large_text': media.title,
                    'small_image': 'plex_icon',
                    'small_text': 'Plex'
                },
                'metadata': {
                    'media_type': PLEX_MEDIA_TYPES.get(media.type, 0),
                    'duration': media.duration,
                    'progress': 0
                }
            }
            
            # Start the stream in the voice channel
            stream_connection = await voice_channel.connect()
            self.active_streams[voice_channel.id] = {
                'connection': stream_connection,
                'media': media,
                'activity': activity,
                'start_time': time.time()
            }
            
            return activity
            
        except Exception as e:
            logger.error(f"Failed to start Plex stream: {e}")
            raise
            
    async def stop_stream(self, voice_channel_id: int):
        """Stop an active Plex stream."""
        if voice_channel_id in self.active_streams:
            stream = self.active_streams[voice_channel_id]
            await stream['connection'].disconnect()
            del self.active_streams[voice_channel_id]
            
    async def update_stream_progress(self, voice_channel_id: int, progress: float):
        """Update the progress of an active stream."""
        if voice_channel_id in self.active_streams:
            stream = self.active_streams[voice_channel_id]
            stream['activity']['metadata']['progress'] = progress
            # Update Discord activity with new progress
            await self.discord.change_presence(activity=discord.Activity(**stream['activity']))

class PokemonROMData:
    """Pokemon game ROM data structures."""
    def __init__(self):
        self.pokemon_base_stats = {}
        self.moves = {}
        self.items = {}
        self.trainers = {}
        self.maps = {}
        self.scripts = {}
        self.text = {}
        self.events = {}

    async def parse_rom(self, rom_path: str, game_type: str):
        """Parse Pokemon ROM data."""
        with open(rom_path, 'rb') as f:
            rom_data = f.read()
            
        header = RomHeader(rom_data)
        logger.info(f"Parsing ROM: {header.title}")
        
        if game_type == 'gb':
            await self._parse_gb_rom(rom_data)
        elif game_type == 'gbc':
            await self._parse_gbc_rom(rom_data)
        elif game_type == 'gba':
            await self._parse_gba_rom(rom_data)

    async def _parse_gb_rom(self, rom_data: bytes):
        """Parse Game Boy Pokemon ROM data."""
        # Pokemon Red/Blue/Yellow data structures
        self._parse_pokemon_base_stats(rom_data, 0x383DE, 151)
        self._parse_moves(rom_data, 0x38000, 165)
        self._parse_items(rom_data, 0x40000, 255)
        self._parse_trainers(rom_data, 0x39D8B, 47)

    async def _parse_gbc_rom(self, rom_data: bytes):
        """Parse Game Boy Color Pokemon ROM data."""
        # Pokemon Gold/Silver/Crystal data structures
        self._parse_pokemon_base_stats(rom_data, 0x51424, 251)
        self._parse_moves(rom_data, 0x41000, 251)
        self._parse_items(rom_data, 0x42000, 255)
        self._parse_trainers(rom_data, 0x39D8B, 67)

    async def _parse_gba_rom(self, rom_data: bytes):
        """Parse Game Boy Advance Pokemon ROM data."""
        # Pokemon Ruby/Sapphire/Emerald/FireRed/LeafGreen data structures
        self._parse_pokemon_base_stats(rom_data, 0x1B0000, 386)
        self._parse_moves(rom_data, 0x1C0000, 354)
        self._parse_items(rom_data, 0x1D0000, 377)
        self._parse_trainers(rom_data, 0x1E0000, 743)

    def _parse_pokemon_base_stats(self, rom_data: bytes, offset: int, count: int):
        """Parse Pokemon base stats from ROM."""
        for i in range(count):
            pos = offset + (i * 28)
            self.pokemon_base_stats[i + 1] = {
                'hp': rom_data[pos],
                'attack': rom_data[pos + 1],
                'defense': rom_data[pos + 2],
                'speed': rom_data[pos + 3],
                'special_attack': rom_data[pos + 4],
                'special_defense': rom_data[pos + 5],
                'type1': rom_data[pos + 6],
                'type2': rom_data[pos + 7],
                'catch_rate': rom_data[pos + 8],
                'base_exp': rom_data[pos + 9],
                'growth_rate': rom_data[pos + 19],
                'egg_groups': [rom_data[pos + 20], rom_data[pos + 21]]
            }

    async def parse_gb_rom(self, rom_data: bytes):
        """Parse Game Boy Pokemon ROM data (Red/Blue/Yellow)."""
        # Pokemon Red/Blue data structures
        self._parse_pokemon_base_stats(rom_data, 0x383DE, 151)  # Original 151 Pokemon
        self._parse_moves(rom_data, 0x38000, 165)  # Original moves
        self._parse_items(rom_data, 0x40000, 255)  # Original items
        self._parse_trainers(rom_data, 0x39D8B, 47)  # Trainer data
        self._parse_maps(rom_data, 0x54000, 248)  # Map layouts
        self._parse_text(rom_data, 0x7B000)  # Text data
        
    async def parse_gbc_rom(self, rom_data: bytes):
        """Parse Game Boy Color Pokemon ROM data (Gold/Silver/Crystal)."""
        # Pokemon Gold/Silver/Crystal data structures
        self._parse_pokemon_base_stats(rom_data, 0x51424, 251)  # Gen 2 Pokemon
        self._parse_moves(rom_data, 0x41000, 251)  # Gen 2 moves
        self._parse_items(rom_data, 0x42000, 255)  # Gen 2 items
        self._parse_trainers(rom_data, 0x39D8B, 67)  # Updated trainer data
        self._parse_maps(rom_data, 0x94000, 392)  # New map system
        self._parse_events(rom_data, 0x96000)  # Time-based events
        
    async def parse_gba_rom(self, rom_data: bytes):
        """Parse Game Boy Advance Pokemon ROM data (Ruby/Sapphire/Emerald/FireRed/LeafGreen)."""
        # Pokemon Ruby/Sapphire/Emerald/FireRed/LeafGreen data structures
        self._parse_pokemon_base_stats(rom_data, 0x1B0000, 386)  # Gen 3 Pokemon
        self._parse_moves(rom_data, 0x1C0000, 354)  # Gen 3 moves
        self._parse_items(rom_data, 0x1D0000, 377)  # Gen 3 items
        self._parse_trainers(rom_data, 0x1E0000, 743)  # Expanded trainer data
        self._parse_maps(rom_data, 0x54000, 213)  # Advanced map system
        self._parse_scripts(rom_data, 0x75000)  # Ruby script engine
        
    def _parse_maps(self, rom_data: bytes, offset: int, count: int):
        """Parse map data from ROM."""
        for i in range(count):
            map_offset = offset + (i * 24)
            self.maps[i] = {
                'width': rom_data[map_offset],
                'height': rom_data[map_offset + 1],
                'border_tile': rom_data[map_offset + 2],
                'data_ptr': int.from_bytes(rom_data[map_offset + 4:map_offset + 8], byteorder='little'),
                'tileset': rom_data[map_offset + 8],
                'connections': self._parse_map_connections(rom_data, map_offset + 12)
            }
            
    def _parse_map_connections(self, rom_data: bytes, offset: int) -> dict:
        """Parse map connection data."""
        return {
            'north': int.from_bytes(rom_data[offset:offset + 4], byteorder='little'),
            'south': int.from_bytes(rom_data[offset + 4:offset + 8], byteorder='little'),
            'west': int.from_bytes(rom_data[offset + 8:offset + 12], byteorder='little'),
            'east': int.from_bytes(rom_data[offset + 12:offset + 16], byteorder='little')
        }

class DiscordActivityData:
    """Discord activity data structures."""
    def __init__(self):
        self.activities = {}
        self.plugins = {}
        self.integrations = {}
        
    async def fetch_activities(self):
        """Fetch Discord activity data."""
        for name, activity_id in DISCORD_ACTIVITIES.items():
            self.activities[name] = {
                'id': activity_id,
                'type': 'ACTIVITY',
                'name': name.title(),
                'description': f'Discord {name.title()} Activity'
            }
            
    async def fetch_vencord_plugins(self):
        """Fetch Vencord plugin data."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{VENCORD_REPO_URL}/tree/main/src/plugins") as response:
                if response.status == 200:
                    data = await response.json()
                    for plugin in data:
                        self.plugins[plugin['name']] = {
                            'name': plugin['name'],
                            'description': plugin.get('description', ''),
                            'author': plugin.get('author', ''),
                            'version': plugin.get('version', '1.0.0')
                        }

class IntegrationData:
    """Integration data for various services."""
    def __init__(self):
        self.plex_data = {}
        self.spotify_data = {}
        self.youtube_data = {}
        self.osrs_data = {}
        
    async def fetch_plex_data(self, plex_token: str):
        """Fetch Plex integration data."""
        plex = PlexServer('http://localhost:32400', plex_token)
        self.plex_data = {
            'libraries': [lib.title for lib in plex.library.sections()],
            'clients': [client.title for client in plex.clients()],
            'activities': [activity.type for activity in plex.activities()]
        }
        
    async def fetch_spotify_data(self, client_id: str, client_secret: str):
        """Fetch Spotify integration data."""
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        self.spotify_data = {
            'available_markets': sp.available_markets(),
            'categories': sp.categories(),
            'featured_playlists': sp.featured_playlists()
        }
        
    async def fetch_youtube_data(self, api_key: str):
        """Fetch YouTube integration data."""
        youtube = build('youtube', 'v3', developerApiKey=api_key)
        self.youtube_data = {
            'categories': youtube.videoCategories().list(part='snippet', regionCode='US').execute(),
            'live_broadcast_content': ['none', 'upcoming', 'live', 'completed']
        }
        
    async def fetch_osrs_data(self):
        """Fetch OSRS Wiki data."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OSRS_WIKI_API}?action=query&list=categorymembers&cmtitle=Category:Old_School_RuneScape&format=json") as response:
                if response.status == 200:
                    data = await response.json()
                    self.osrs_data = {
                        'categories': data['query']['categorymembers'],
                        'items': [],
                        'npcs': [],
                        'locations': []
                    }

class CodeSnippetData:
    """Code snippet data from various sources."""
    def __init__(self):
        self.stackoverflow_snippets = {}
        self.github_snippets = {}
        self.foss_libraries = {}
        
    async def fetch_stackoverflow_snippets(self, tag: str):
        """Fetch Stack Overflow code snippets."""
        stack_api = stackapi.StackAPI('stackoverflow')
        questions = stack_api.fetch('questions', tagged=tag, sort='votes', filter='withbody')
        self.stackoverflow_snippets[tag] = questions
        
    async def fetch_github_repos(self, topic: str, token: str):
        """Fetch GitHub repositories."""
        g = Github(token)
        repos = g.search_repositories(query=f'topic:{topic} language:python fork:true')
        self.github_snippets[topic] = [{
            'name': repo.name,
            'url': repo.html_url,
            'description': repo.description,
            'stars': repo.stargazers_count,
            'license': repo.license.name if repo.license else None
        } for repo in repos]
        
    async def fetch_foss_libraries(self):
        """Fetch FOSS library data."""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://libraries.io/api/platforms/PyPI/projects') as response:
                if response.status == 200:
                    data = await response.json()
                    self.foss_libraries = {
                        lib['name']: {
                            'name': lib['name'],
                            'description': lib['description'],
                            'homepage': lib['homepage'],
                            'license': lib['license'],
                            'latest_version': lib['latest_version']
                        }
                        for lib in data
                    }

class PokemonDataFetcher:
    """Base class for fetching Pokemon data from multiple sources."""
    
    def __init__(self, requests_per_minute: int = 100):
        """Initialize the fetcher with rate limiting."""
        self.delay = 60.0 / requests_per_minute
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
        self.session: aiohttp.ClientSession = None
        self.data: Dict[str, Dict[str, Any]] = {}
        
        # Initialize API clients
        self.pokepy_client = pokepy.V2Client()
        self.tcg_api = PokemonTcgAPI()
        self.rom_data = PokemonROMData()
        self.discord_data = DiscordActivityData()
        self.integration_data = IntegrationData()
        self.snippet_data = CodeSnippetData()
        
        # Define all categories to fetch
        self.categories = {
            "pokemon": {
                "endpoint": "/pokemon",
                "parser": self.parse_pokemon_data,
                "sources": ["pokeapi", "serebii", "bulbapedia", "showdown", "rom"]
            },
            "moves": {
                "endpoint": "/move",
                "parser": self.parse_move_data,
                "sources": ["pokeapi", "serebii", "showdown", "rom"]
            },
            "abilities": {
                "endpoint": "/ability",
                "parser": self.parse_ability_data,
                "sources": ["pokeapi", "serebii", "showdown"]
            },
            "items": {
                "endpoint": "/item",
                "parser": self.parse_item_data,
                "sources": ["pokeapi", "serebii", "rom"]
            },
            "types": {
                "endpoint": "/type",
                "parser": self.parse_type_data,
                "sources": ["pokeapi", "showdown", "rom"]
            },
            "natures": {
                "endpoint": "/nature",
                "parser": self.parse_nature_data,
                "sources": ["pokeapi", "showdown"]
            },
            "egg_groups": {
                "endpoint": "/egg-group",
                "parser": self.parse_egg_group_data,
                "sources": ["pokeapi", "bulbapedia", "rom"]
            },
            "evolution_chains": {
                "endpoint": "/evolution-chain",
                "parser": self.parse_evolution_data,
                "sources": ["pokeapi", "bulbapedia", "rom"]
            },
            "locations": {
                "endpoint": "/location",
                "parser": self.parse_location_data,
                "sources": ["pokeapi", "serebii", "rom"]
            },
            "regions": {
                "endpoint": "/region",
                "parser": self.parse_region_data,
                "sources": ["pokeapi", "bulbapedia", "rom"]
            },
            "competitive": {
                "endpoint": "/formats",
                "parser": self.parse_competitive_data,
                "sources": ["showdown", "smogon"]
            },
            "tcg_cards": {
                "endpoint": "/cards",
                "parser": self.parse_tcg_data,
                "sources": ["pokemontcg"]
            },
            "go_data": {
                "endpoint": "/gamemaster",
                "parser": self.parse_go_data,
                "sources": ["pokemongo"]
            },
            "forms": {
                "endpoint": "/pokemon-forms",
                "parser": self.parse_form_data,
                "sources": ["pokeapi", "serebii", "bulbapedia", "rom"]
            },
            "breeding": {
                "endpoint": "/breeding",
                "parser": self.parse_breeding_data,
                "sources": ["serebii", "bulbapedia", "rom"]
            },
            "stats": {
                "endpoint": "/stats",
                "parser": self.parse_stats_data,
                "sources": ["pokeapi", "showdown", "rom"]
            },
            "rom_data": {
                "endpoint": "/rom",
                "parser": self.parse_rom_data,
                "sources": ["rom"]
            },
            "discord_activities": {
                "endpoint": "/activities",
                "parser": self.parse_discord_activity_data,
                "sources": ["discord"]
            },
            "vencord_plugins": {
                "endpoint": "/plugins",
                "parser": self.parse_vencord_plugin_data,
                "sources": ["vencord"]
            },
            "integrations": {
                "endpoint": "/integrations",
                "parser": self.parse_integration_data,
                "sources": ["plex", "spotify", "youtube", "osrs"]
            },
            "code_snippets": {
                "endpoint": "/snippets",
                "parser": self.parse_code_snippet_data,
                "sources": ["stackoverflow", "github", "foss"]
            }
        }
        
    async def __aenter__(self):
        """Set up async context."""
        self.session = aiohttp.ClientSession(headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
        })
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context."""
        if self.session:
            await self.session.close()
            
    async def wait_for_rate_limit(self):
        """Wait until it's safe to make another request."""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.delay:
                wait_time = self.delay - time_since_last
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()
            
    async def fetch_with_retry(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """Fetch data with retry logic and rate limiting."""
        for attempt in range(max_retries):
            try:
                await self.wait_for_rate_limit()
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Too Many Requests
                        wait_time = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"HTTP {response.status} for URL {url}")
                        response.raise_for_status()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch {url}: {e}")
                    raise
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        raise Exception(f"Failed to fetch {url} after {max_retries} attempts")
        
    def parse_pokemon_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Pokemon data into structured format."""
        return {
            "id": data["id"],
            "name": data["name"],
            "types": [t["type"]["name"] for t in data["types"]],
            "stats": {
                s["stat"]["name"]: s["base_stat"] 
                for s in data["stats"]
            },
            "abilities": [
                {
                    "name": a["ability"]["name"],
                    "is_hidden": a["is_hidden"]
                }
                for a in data["abilities"]
            ],
            "height": data["height"],
            "weight": data["weight"],
            "sprites": {
                "front_default": data["sprites"]["front_default"],
                "back_default": data["sprites"]["back_default"],
                "front_shiny": data["sprites"]["front_shiny"],
                "back_shiny": data["sprites"]["back_shiny"]
            },
            "moves": [
                {
                    "name": m["move"]["name"],
                    "learn_method": m["version_group_details"][0]["move_learn_method"]["name"],
                    "level": m["version_group_details"][0]["level_learned_at"]
                }
                for m in data["moves"]
            ]
        }
        
    def parse_move_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse move data into structured format."""
        return {
            "id": data["id"],
            "name": data["name"],
            "type": data["type"]["name"],
            "power": data["power"],
            "pp": data["pp"],
            "accuracy": data["accuracy"],
            "priority": data["priority"],
            "damage_class": data["damage_class"]["name"],
            "effect": data["effect_entries"][0]["effect"] if data["effect_entries"] else None,
            "effect_chance": data["effect_chance"],
            "target": data["target"]["name"],
            "meta": {
                "category": data["meta"]["category"]["name"] if "meta" in data else None,
                "min_hits": data["meta"]["min_hits"] if "meta" in data else None,
                "max_hits": data["meta"]["max_hits"] if "meta" in data else None,
                "min_turns": data["meta"]["min_turns"] if "meta" in data else None,
                "max_turns": data["meta"]["max_turns"] if "meta" in data else None,
                "drain": data["meta"]["drain"] if "meta" in data else None,
                "healing": data["meta"]["healing"] if "meta" in data else None,
                "crit_rate": data["meta"]["crit_rate"] if "meta" in data else None,
                "ailment_chance": data["meta"]["ailment_chance"] if "meta" in data else None,
                "flinch_chance": data["meta"]["flinch_chance"] if "meta" in data else None,
                "stat_chance": data["meta"]["stat_chance"] if "meta" in data else None
            }
        }
        
    def parse_ability_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ability data into structured format."""
        return {
            "id": data["id"],
            "name": data["name"],
            "effect": data["effect_entries"][0]["effect"] if data["effect_entries"] else None,
            "short_effect": data["effect_entries"][0]["short_effect"] if data["effect_entries"] else None,
            "pokemon": [
                {
                    "name": p["pokemon"]["name"],
                    "is_hidden": p["is_hidden"]
                }
                for p in data["pokemon"]
            ]
        }
        
    def parse_item_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse item data into structured format."""
        return {
            "id": data["id"],
            "name": data["name"],
            "cost": data["cost"],
            "fling_power": data["fling_power"],
            "fling_effect": data["fling_effect"]["name"] if data["fling_effect"] else None,
            "attributes": [a["name"] for a in data["attributes"]],
            "category": data["category"]["name"],
            "effect": data["effect_entries"][0]["effect"] if data["effect_entries"] else None,
            "short_effect": data["effect_entries"][0]["short_effect"] if data["effect_entries"] else None,
            "sprite": data["sprites"]["default"]
        }
        
    def parse_type_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse type data into structured format."""
        return {
            "id": data["id"],
            "name": data["name"],
            "damage_relations": {
                "double_damage_from": [t["name"] for t in data["damage_relations"]["double_damage_from"]],
                "double_damage_to": [t["name"] for t in data["damage_relations"]["double_damage_to"]],
                "half_damage_from": [t["name"] for t in data["damage_relations"]["half_damage_from"]],
                "half_damage_to": [t["name"] for t in data["damage_relations"]["half_damage_to"]],
                "no_damage_from": [t["name"] for t in data["damage_relations"]["no_damage_from"]],
                "no_damage_to": [t["name"] for t in data["damage_relations"]["no_damage_to"]]
            },
            "pokemon": [p["pokemon"]["name"] for p in data["pokemon"]],
            "moves": [m["name"] for m in data["moves"]]
        }
        
    def parse_nature_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse nature data into structured format."""
        return {
            "id": data["id"],
            "name": data["name"],
            "increased_stat": data["increased_stat"]["name"] if data["increased_stat"] else None,
            "decreased_stat": data["decreased_stat"]["name"] if data["decreased_stat"] else None,
            "likes_flavor": data["likes_flavor"]["name"] if data["likes_flavor"] else None,
            "hates_flavor": data["hates_flavor"]["name"] if data["hates_flavor"] else None
        }
        
    def parse_egg_group_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse egg group data into structured format."""
        return {
            "id": data["id"],
            "name": data["name"],
            "pokemon_species": [p["name"] for p in data["pokemon_species"]]
        }
        
    def parse_evolution_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse evolution chain data into structured format."""
        def parse_evolution_details(details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return [
                {
                    "trigger": d["trigger"]["name"],
                    "min_level": d.get("min_level"),
                    "item": d.get("item", {}).get("name") if d.get("item") else None,
                    "held_item": d.get("held_item", {}).get("name") if d.get("held_item") else None,
                    "location": d.get("location", {}).get("name") if d.get("location") else None,
                    "min_happiness": d.get("min_happiness"),
                    "min_beauty": d.get("min_beauty"),
                    "min_affection": d.get("min_affection"),
                    "needs_overworld_rain": d.get("needs_overworld_rain"),
                    "time_of_day": d.get("time_of_day"),
                    "relative_physical_stats": d.get("relative_physical_stats")
                }
                for d in details
            ]
            
        def parse_evolution_chain(chain: Dict[str, Any]) -> Dict[str, Any]:
            result = {
                "species": chain["species"]["name"],
                "evolution_details": parse_evolution_details(chain.get("evolution_details", [])),
                "evolves_to": []
            }
            
            for evolution in chain.get("evolves_to", []):
                result["evolves_to"].append(parse_evolution_chain(evolution))
                
            return result
            
        return {
            "id": data["id"],
            "chain": parse_evolution_chain(data["chain"])
        }
        
    def parse_location_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse location data into structured format."""
        return {
            "id": data["id"],
            "name": data["name"],
            "region": data["region"]["name"] if data["region"] else None,
            "areas": [
                {
                    "name": a["name"],
                    "pokemon_encounters": [
                        {
                            "pokemon": e["pokemon"]["name"],
                            "version_details": [
                                {
                                    "version": v["version"]["name"],
                                    "max_chance": v["max_chance"],
                                    "encounter_details": [
                                        {
                                            "method": d["method"]["name"],
                                            "min_level": d["min_level"],
                                            "max_level": d["max_level"],
                                            "chance": d["chance"]
                                        }
                                        for d in v["encounter_details"]
                                    ]
                                }
                                for v in e["version_details"]
                            ]
                        }
                        for e in a.get("pokemon_encounters", [])
                    ]
                }
                for a in data["areas"]
            ]
        }
        
    def parse_region_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse region data into structured format."""
        return {
            "id": data["id"],
            "name": data["name"],
            "locations": [l["name"] for l in data["locations"]],
            "version_groups": [v["name"] for v in data["version_groups"]],
            "pokedexes": [p["name"] for p in data["pokedexes"]],
            "main_generation": data["main_generation"]["name"] if data["main_generation"] else None
        }
        
    async def fetch_list(self, endpoint: str) -> List[Dict[str, str]]:
        """Fetch list of resources from an endpoint."""
        url = f"{POKEAPI_URL}{endpoint}?limit=10000"
        data = await self.fetch_with_retry(url)
        return data["results"]
        
    async def fetch_resource(self, url: str, parser: callable) -> Dict[str, Any]:
        """Fetch and parse a specific resource."""
        data = await self.fetch_with_retry(url)
        return parser(data)
        
    async def fetch_category_data(self, category: str, config: Dict[str, Any]):
        """Fetch all data for a category."""
        logger.info(f"\nFetching {category} data...")
        
        try:
            # Get list of all resources in category
            resources = await self.fetch_list(config["endpoint"])
            logger.info(f"Found {len(resources)} {category}")
            
            # Fetch and parse each resource
            category_data = {}
            for i, resource in enumerate(resources, 1):
                try:
                    logger.info(f"Processing {i}/{len(resources)}: {resource['name']}")
                    parsed_data = await self.fetch_resource(resource["url"], config["parser"])
                    category_data[resource["name"]] = parsed_data
                except Exception as e:
                    logger.error(f"Error processing {resource['name']}: {e}")
                    continue
                    
            self.data[category] = category_data
            
        except Exception as e:
            logger.error(f"Error fetching {category}: {e}")
            
    def save_data(self):
        """Save all collected data to JSON files."""
        output_dir = Path("src/data/pokemon")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for category, data in self.data.items():
            output_file = output_dir / f"{category}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(data)} {category} to {output_file}")
            
    async def fetch_all_data(self):
        """Fetch all data from multiple sources."""
        try:
            async with self as fetcher:
                # Fetch Pokemon data
                for category, config in self.categories.items():
                    await self.fetch_category_data(category, config)
                
                # Fetch Discord activities
                await self.discord_data.fetch_activities()
                await self.discord_data.fetch_vencord_plugins()
                
                # Fetch integration data
                if 'PLEX_TOKEN' in os.environ:
                    await self.integration_data.fetch_plex_data(os.environ['PLEX_TOKEN'])
                if all(k in os.environ for k in ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET']):
                    await self.integration_data.fetch_spotify_data(
                        os.environ['SPOTIFY_CLIENT_ID'],
                        os.environ['SPOTIFY_CLIENT_SECRET']
                    )
                if 'YOUTUBE_API_KEY' in os.environ:
                    await self.integration_data.fetch_youtube_data(os.environ['YOUTUBE_API_KEY'])
                await self.integration_data.fetch_osrs_data()
                
                # Fetch code snippets
                await self.snippet_data.fetch_stackoverflow_snippets('discord-py')
                if 'GITHUB_TOKEN' in os.environ:
                    await self.snippet_data.fetch_github_repos('discord-bot', os.environ['GITHUB_TOKEN'])
                await self.snippet_data.fetch_foss_libraries()
                    
            self.save_data()
            logger.info("\nData collection completed!")
            
        except Exception as e:
            logger.error(f"Error during data collection: {e}", exc_info=True)
            raise

    async def fetch_serebii_data(self, category: str, identifier: str) -> Dict[str, Any]:
        """Fetch data from Serebii.net."""
        url = f"{SEREBII_URL}/pokemon/{identifier}"
        async with self.session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                return self.parse_serebii_html(soup, category)
        return {}

    async def fetch_bulbapedia_data(self, category: str, identifier: str) -> Dict[str, Any]:
        """Fetch data from Bulbapedia."""
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "format": "json",
            "titles": f"Pokemon:{identifier}"
        }
        async with self.session.get(BULBAPEDIA_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return self.parse_bulbapedia_data(data, category)
        return {}

    async def fetch_showdown_data(self, category: str) -> Dict[str, Any]:
        """Fetch data from Pokemon Showdown."""
        url = f"{SHOWDOWN_URL}/{category}.json"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
        return {}

    async def fetch_pokemongo_data(self) -> Dict[str, Any]:
        """Fetch Pokemon GO game master data."""
        async with self.session.get(POKEMONGO_URL) as response:
            if response.status == 200:
                return await response.json()
        return {}

    def parse_competitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse competitive Pokemon data."""
        return {
            "formats": data.get("formats", []),
            "tiers": data.get("tiers", {}),
            "abilities": data.get("abilities", {}),
            "items": data.get("items", {}),
            "moves": data.get("moves", {}),
            "typechart": data.get("typechart", {}),
            "strategies": data.get("strategies", [])
        }

    def parse_tcg_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Pokemon TCG data."""
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "supertype": data.get("supertype"),
            "subtypes": data.get("subtypes", []),
            "level": data.get("level"),
            "hp": data.get("hp"),
            "types": data.get("types", []),
            "evolvesFrom": data.get("evolvesFrom"),
            "evolvesTo": data.get("evolvesTo", []),
            "rules": data.get("rules", []),
            "attacks": data.get("attacks", []),
            "weaknesses": data.get("weaknesses", []),
            "resistances": data.get("resistances", []),
            "retreatCost": data.get("retreatCost", []),
            "convertedRetreatCost": data.get("convertedRetreatCost"),
            "set": data.get("set", {}),
            "number": data.get("number"),
            "artist": data.get("artist"),
            "rarity": data.get("rarity"),
            "flavorText": data.get("flavorText"),
            "images": data.get("images", {})
        }

    def parse_go_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Pokemon GO data."""
        return {
            "pokemon": [item for item in data if "pokemon" in item.get("templateId", "").lower()],
            "moves": [item for item in data if "move" in item.get("templateId", "").lower()],
            "types": [item for item in data if "type" in item.get("templateId", "").lower()],
            "items": [item for item in data if "item" in item.get("templateId", "").lower()],
            "weather": [item for item in data if "weather" in item.get("templateId", "").lower()],
            "combat": [item for item in data if "combat" in item.get("templateId", "").lower()]
        }

    def parse_form_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Pokemon form data."""
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "order": data.get("order"),
            "form_order": data.get("form_order"),
            "is_default": data.get("is_default"),
            "is_battle_only": data.get("is_battle_only"),
            "is_mega": data.get("is_mega"),
            "form_name": data.get("form_name"),
            "pokemon": data.get("pokemon", {}),
            "sprites": data.get("sprites", {}),
            "version_group": data.get("version_group", {}),
            "types": data.get("types", [])
        }

    def parse_breeding_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Pokemon breeding data."""
        return {
            "egg_groups": data.get("egg_groups", []),
            "gender_rate": data.get("gender_rate"),
            "hatch_counter": data.get("hatch_counter"),
            "baby_trigger_item": data.get("baby_trigger_item"),
            "evolution_chain": data.get("evolution_chain", {}),
            "evolves_from_species": data.get("evolves_from_species"),
            "habitat": data.get("habitat", {}),
            "generation": data.get("generation", {}),
            "growth_rate": data.get("growth_rate", {}),
            "forms_switchable": data.get("forms_switchable")
        }

    def parse_stats_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Pokemon stats data."""
        return {
            "base_stats": data.get("stats", {}),
            "ev_yield": data.get("effort", {}),
            "catch_rate": data.get("capture_rate"),
            "base_happiness": data.get("base_happiness"),
            "base_experience": data.get("base_experience"),
            "growth_rate": data.get("growth_rate", {}),
            "max_stats": self.calculate_max_stats(data.get("stats", {}))
        }

    def calculate_max_stats(self, base_stats: Dict[str, int]) -> Dict[str, int]:
        """Calculate maximum possible stats at level 100."""
        max_stats = {}
        for stat, base in base_stats.items():
            if stat == "hp":
                max_stats[stat] = ((2 * base + 31 + 252 // 4) * 100 // 100) + 100 + 10
            else:
                max_stats[stat] = (((2 * base + 31 + 252 // 4) * 100 // 100) + 5) * 1.1
        return max_stats

    async def parse_rom_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ROM data into structured format."""
        rom_data = {}
        
        # Parse ROMs for each generation
        gb_roms = {
            'red': 'roms/pokemon_red.gb',
            'blue': 'roms/pokemon_blue.gb',
            'yellow': 'roms/pokemon_yellow.gb'
        }
        
        gbc_roms = {
            'gold': 'roms/pokemon_gold.gbc',
            'silver': 'roms/pokemon_silver.gbc',
            'crystal': 'roms/pokemon_crystal.gbc'
        }
        
        gba_roms = {
            'ruby': 'roms/pokemon_ruby.gba',
            'sapphire': 'roms/pokemon_sapphire.gba',
            'emerald': 'roms/pokemon_emerald.gba',
            'firered': 'roms/pokemon_firered.gba',
            'leafgreen': 'roms/pokemon_leafgreen.gba'
        }
        
        # Parse Game Boy ROMs
        for name, path in gb_roms.items():
            if Path(path).exists():
                await self.rom_data.parse_rom(path, 'gb')
                rom_data[name] = {
                    'pokemon': self.rom_data.pokemon_base_stats,
                    'moves': self.rom_data.moves,
                    'items': self.rom_data.items,
                    'trainers': self.rom_data.trainers
                }
        
        # Parse Game Boy Color ROMs
        for name, path in gbc_roms.items():
            if Path(path).exists():
                await self.rom_data.parse_rom(path, 'gbc')
                rom_data[name] = {
                    'pokemon': self.rom_data.pokemon_base_stats,
                    'moves': self.rom_data.moves,
                    'items': self.rom_data.items,
                    'trainers': self.rom_data.trainers
                }
        
        # Parse Game Boy Advance ROMs
        for name, path in gba_roms.items():
            if Path(path).exists():
                await self.rom_data.parse_rom(path, 'gba')
                rom_data[name] = {
                    'pokemon': self.rom_data.pokemon_base_stats,
                    'moves': self.rom_data.moves,
                    'items': self.rom_data.items,
                    'trainers': self.rom_data.trainers
                }
        
        return rom_data

    def parse_discord_activity_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Discord activity data."""
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "type": data.get("type"),
            "description": data.get("description"),
            "supported_platforms": data.get("supported_platforms", []),
            "max_participants": data.get("max_participants"),
            "features": data.get("features", [])
        }
        
    def parse_vencord_plugin_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Vencord plugin data."""
        return {
            "name": data.get("name"),
            "description": data.get("description"),
            "author": data.get("author"),
            "version": data.get("version"),
            "dependencies": data.get("dependencies", []),
            "settings": data.get("settings", {})
        }
        
    def parse_integration_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse integration data."""
        return {
            "service": data.get("service"),
            "features": data.get("features", []),
            "endpoints": data.get("endpoints", []),
            "auth_methods": data.get("auth_methods", []),
            "rate_limits": data.get("rate_limits", {}),
            "documentation": data.get("documentation", "")
        }
        
    def parse_code_snippet_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse code snippet data."""
        return {
            "source": data.get("source"),
            "language": data.get("language"),
            "title": data.get("title"),
            "code": data.get("code"),
            "author": data.get("author"),
            "license": data.get("license"),
            "tags": data.get("tags", []),
            "votes": data.get("votes", 0)
        }

async def main():
    """Main function to fetch all Pokemon data."""
    try:
        logger.info("Starting Pokemon data collection...")
        
        collector = PokemonDataFetcher(requests_per_minute=100)
        await collector.fetch_all_data()
        
        logger.info("\nPokemon data collection completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in Pokemon data collection: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nPokemon data collection cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1) 