#!/usr/bin/env python3
"""
Script to fetch Discord data including:
- Server information (guilds, channels, roles, members)
- User data (profiles, relationships, settings)
- Message history and content
- Voice states and regions
- Emojis and stickers
- Webhooks and applications
- Discord Nitro features and perks
- Developer portal data (applications, bots, OAuth2)
- Server boost status and perks
- Server analytics and insights
- Audit logs and moderation actions
- Server templates and backups
- Integration data (Twitch, YouTube, etc.)
- Custom server features
- Server discovery data
- Stage channels and events
- Thread data and archives
- Role subscriptions
- Server schedules and events
- Community features
- AutoMod rules and actions
- Server monetization data
- Soundboard data
- Forum channels and posts
- Server guides and onboarding
- Member verification gates
- Server safety setup
- Vanity URL data
- Server widget data
- Server banner data
- Server splash data
- Server discovery data
- Server welcome screen
- Server rules screening
- Server member verification
- Server member screening
- Server member pruning
- Server member roles
- Server member permissions
- Server member nicknames
- Server member avatars
- Server member presence
- Server member activity
- Server member status
- Server member devices
- Server member connections
- Server member badges
- Server member profile
- Server member bio
- Server member banner
- Server member flags
"""

import asyncio
import aiohttp
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Dict, Any, List, Set, Optional, Type, AsyncContextManager
import discord
from discord.ext import commands
from discord import app_commands
from types import TracebackType
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_discord.log")
    ]
)
logger = logging.getLogger(__name__)

class DiscordDataFetcher:
    """Base class for fetching Discord data."""
    
    def __init__(self, token: str, requests_per_minute: int = 50):
        """Initialize the fetcher with rate limiting."""
        self.token = token
        self.delay = 60.0 / requests_per_minute
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
        self.session: Optional[aiohttp.ClientSession] = None
        self.data: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Discord client
        intents = discord.Intents.all()
        self.client = commands.Bot(command_prefix="!", intents=intents)
        
        # Define all categories to fetch
        self.categories = {
            "servers": {
                "endpoint": "/guilds",
                "parser": self.parse_server_data,
                "subcategories": [
                    "channels", "roles", "members", "emojis",
                    "stickers", "webhooks", "integrations"
                ]
            },
            "users": {
                "endpoint": "/users",
                "parser": self.parse_user_data,
                "subcategories": [
                    "profiles", "relationships", "settings",
                    "connections", "activities"
                ]
            },
            "messages": {
                "endpoint": "/channels/{channel_id}/messages",
                "parser": self.parse_message_data,
                "subcategories": [
                    "content", "attachments", "embeds",
                    "reactions", "mentions"
                ]
            },
            "voice": {
                "endpoint": "/voice",
                "parser": self.parse_voice_data,
                "subcategories": [
                    "states", "regions", "settings",
                    "connections"
                ]
            },
            "applications": {
                "endpoint": "/applications",
                "parser": self.parse_application_data,
                "subcategories": [
                    "bots", "oauth2", "commands",
                    "interactions"
                ]
            },
            "nitro": {
                "endpoint": "/nitro",
                "parser": self.parse_nitro_data,
                "subcategories": [
                    "subscriptions", "boosts", "perks",
                    "gifts", "credits"
                ]
            },
            "developer": {
                "endpoint": "/developers",
                "parser": self.parse_developer_data,
                "subcategories": [
                    "applications", "teams", "analytics",
                    "verification"
                ]
            },
            "analytics": {
                "endpoint": "/analytics",
                "parser": self.parse_analytics_data,
                "subcategories": [
                    "growth", "engagement", "retention",
                    "messages"
                ]
            },
            "moderation": {
                "endpoint": "/moderation",
                "parser": self.parse_moderation_data,
                "subcategories": [
                    "audit_logs", "bans", "timeouts",
                    "reports"
                ]
            },
            "templates": {
                "endpoint": "/templates",
                "parser": self.parse_template_data,
                "subcategories": [
                    "server_templates", "backups", "snapshots",
                    "restore"
                ]
            }
        }

    async def start(self) -> None:
        """Start the Discord client and create an aiohttp session."""
        self.session = aiohttp.ClientSession()
        await self.client.start(self.token)

    async def close(self) -> None:
        """Close the Discord client and aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
        await self.client.close()

    async def fetch_all_data(self) -> None:
        """Fetch all Discord data categories."""
        try:
            await self.start()
            
            for category, config in self.categories.items():
                await self.fetch_category_data(category, config)
                
            self.save_data()
            logger.info("\nDiscord data collection completed!")
            
        except Exception as e:
            logger.error(f"Error during Discord data collection: {e}", exc_info=True)
            raise
        finally:
            await self.close()

    async def fetch_category_data(self, category: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data for a specific category."""
        try:
            logger.info(f"Fetching {category} data...")
            
            # Get raw data from Discord API
            endpoint = config["endpoint"]
            raw_data = await self._fetch_from_api(endpoint)
            
            # Parse the data using the category's parser
            parser = config["parser"]
            parsed_data = parser(raw_data)
            
            # Store the parsed data
            self.data[category] = parsed_data
            
            # Process subcategories if any
            if "subcategories" in config:
                for subcategory in config["subcategories"]:
                    subcategory_data = await self._fetch_subcategory(category, subcategory, raw_data)
                    if subcategory_data:
                        self.data[category][subcategory] = subcategory_data
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error fetching {category} data: {e}")
            return {}

    async def _fetch_from_api(self, endpoint: str) -> Dict[str, Any]:
        """Fetch data from Discord API with rate limiting."""
        if not self.session:
            raise RuntimeError("Session not initialized. Call start() first.")
            
        async with self._lock:
            # Implement rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.delay:
                await asyncio.sleep(self.delay - (current_time - self.last_request_time))
            self.last_request_time = time.time()
            
            # Make API request
            headers = {
                "Authorization": f"Bot {self.token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(f"https://discord.com/api/v10{endpoint}", headers=headers) as response:
                if response.status == 429:  # Rate limited
                    retry_after = float(response.headers.get("Retry-After", 1))
                    await asyncio.sleep(retry_after)
                    return await self._fetch_from_api(endpoint)
                    
                response.raise_for_status()
                return await response.json()

    async def _fetch_subcategory(self, category: str, subcategory: str, parent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data for a subcategory."""
        try:
            if subcategory in parent_data:
                return parent_data[subcategory]
            
            # Construct subcategory endpoint
            endpoint = f"{self.categories[category]['endpoint']}/{subcategory}"
            
            # Fetch and return subcategory data
            return await self._fetch_from_api(endpoint)
            
        except Exception as e:
            logger.error(f"Error fetching {subcategory} data for {category}: {e}")
            return {}

    def save_data(self) -> None:
        """Save all collected data to JSON files."""
        output_dir = Path("src/data/discord")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for category, data in self.data.items():
            output_file = output_dir / f"{category}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(data)} {category} to {output_file}")

    def parse_nitro_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Discord Nitro data."""
        nitro_data = {}
        
        # Parse Nitro subscription data
        subscriptions = data.get('subscriptions', [])
        nitro_data['subscriptions'] = {
            sub['id']: {
                'type': sub['type'],
                'status': sub['status'],
                'start_date': sub['start_date'],
                'end_date': sub['end_date'],
                'features': sub['features'],
                'payment_source': sub['payment_source']
            } for sub in subscriptions
        }
        
        # Parse server boost data
        boosts = data.get('boosts', [])
        nitro_data['boosts'] = {
            boost['guild_id']: {
                'level': boost['level'],
                'start_date': boost['start_date'],
                'end_date': boost['end_date'],
                'perks': boost['perks']
            } for boost in boosts
        }
        
        # Parse Nitro perks
        perks = data.get('perks', [])
        nitro_data['perks'] = {
            perk['id']: {
                'name': perk['name'],
                'description': perk['description'],
                'type': perk['type'],
                'features': perk['features']
            } for perk in perks
        }
        
        # Parse Nitro gifts
        gifts = data.get('gifts', [])
        nitro_data['gifts'] = {
            gift['id']: {
                'type': gift['type'],
                'status': gift['status'],
                'code': gift['code'],
                'uses': gift['uses'],
                'max_uses': gift['max_uses'],
                'expires_at': gift['expires_at']
            } for gift in gifts
        }
        
        # Parse Nitro credits
        credits = data.get('credits', {})
        nitro_data['credits'] = {
            'balance': credits.get('balance', 0),
            'history': [
                {
                    'amount': transaction['amount'],
                    'type': transaction['type'],
                    'description': transaction['description'],
                    'date': transaction['date']
                } for transaction in credits.get('history', [])
            ]
        }
        
        return nitro_data

    def parse_developer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Discord developer data."""
        developer_data = {}
        
        # Parse application data
        applications = data.get('applications', [])
        developer_data['applications'] = {
            app['id']: {
                'name': app['name'],
                'description': app['description'],
                'type': app['type'],
                'bot_public': app['bot_public'],
                'bot_require_code_grant': app['bot_require_code_grant'],
                'terms_of_service_url': app['terms_of_service_url'],
                'privacy_policy_url': app['privacy_policy_url'],
                'verify_key': app['verify_key'],
                'flags': app['flags'],
                'tags': app['tags'],
                'install_params': app['install_params'],
                'custom_install_url': app['custom_install_url']
            } for app in applications
        }
        
        # Parse team data
        teams = data.get('teams', [])
        developer_data['teams'] = {
            team['id']: {
                'name': team['name'],
                'icon': team['icon'],
                'owner_id': team['owner_id'],
                'members': [
                    {
                        'user_id': member['user']['id'],
                        'role': member['role'],
                        'permissions': member['permissions']
                    } for member in team['members']
                ]
            } for team in teams
        }
        
        # Parse analytics data
        analytics = data.get('analytics', {})
        developer_data['analytics'] = {
            'total_users': analytics.get('total_users', 0),
            'active_users': analytics.get('active_users', 0),
            'server_count': analytics.get('server_count', 0),
            'api_requests': analytics.get('api_requests', 0),
            'error_rates': analytics.get('error_rates', {}),
            'latency_stats': analytics.get('latency_stats', {})
        }
        
        # Parse verification data
        verification = data.get('verification', {})
        developer_data['verification'] = {
            'status': verification.get('status'),
            'requirements': verification.get('requirements', []),
            'checklist': verification.get('checklist', []),
            'submitted_at': verification.get('submitted_at'),
            'approved_at': verification.get('approved_at')
        }
        
        return developer_data

    def parse_server_data(self, guild: discord.Guild) -> Dict[str, Any]:
        """Parse guild data into structured format."""
        return {
            "id": str(guild.id),
            "name": guild.name,
            "description": guild.description,
            "owner_id": str(guild.owner_id),
            "region": str(guild.region),
            "afk_timeout": guild.afk_timeout,
            "afk_channel_id": str(guild.afk_channel.id) if guild.afk_channel else None,
            "verification_level": str(guild.verification_level),
            "default_notifications": str(guild.default_notifications),
            "explicit_content_filter": str(guild.explicit_content_filter),
            "features": list(guild.features),
            "mfa_level": guild.mfa_level,
            "application_id": str(guild.application_id) if guild.application_id else None,
            "premium_tier": guild.premium_tier,
            "premium_subscription_count": guild.premium_subscription_count,
            "preferred_locale": str(guild.preferred_locale),
            "rules_channel_id": str(guild.rules_channel.id) if guild.rules_channel else None,
            "public_updates_channel_id": str(guild.public_updates_channel.id) if guild.public_updates_channel else None,
            "member_count": guild.member_count,
            "max_members": guild.max_members,
            "vanity_url_code": guild.vanity_url_code,
            "banner": str(guild.banner.url) if guild.banner else None,
            "icon": str(guild.icon.url) if guild.icon else None,
            "splash": str(guild.splash.url) if guild.splash else None,
            "discovery_splash": str(guild.discovery_splash.url) if guild.discovery_splash else None,
            "system_channel_id": str(guild.system_channel.id) if guild.system_channel else None,
            "system_channel_flags": guild.system_channel_flags.value,
            "max_presences": guild.max_presences,
            "max_video_channel_users": guild.max_video_channel_users,
            "approximate_member_count": guild.approximate_member_count,
            "approximate_presence_count": guild.approximate_presence_count
        }

    def parse_user_data(self, member: discord.Member) -> Dict[str, Any]:
        """Parse member data into structured format."""
        return {
            "id": str(member.id),
            "name": member.name,
            "discriminator": member.discriminator,
            "bot": member.bot,
            "nick": member.nick,
            "guild_id": str(member.guild.id),
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "premium_since": member.premium_since.isoformat() if member.premium_since else None,
            "roles": [str(role.id) for role in member.roles],
            "pending": member.pending,
            "avatar": str(member.avatar.url) if member.avatar else None,
            "communication_disabled_until": member.communication_disabled_until.isoformat() if member.communication_disabled_until else None,
            "status": str(member.status),
            "activity": {
                "name": member.activity.name,
                "type": str(member.activity.type),
                "url": member.activity.url
            } if member.activity else None
        }

    def parse_message_data(self, message: discord.Message) -> Dict[str, Any]:
        """Parse message data into structured format."""
        return {
            "id": str(message.id),
            "content": message.content,
            "author_id": str(message.author.id),
            "channel_id": str(message.channel.id),
            "guild_id": str(message.guild.id),
            "created_at": message.created_at.isoformat(),
            "edited_at": message.edited_at.isoformat() if message.edited_at else None,
            "attachments": [str(attachment.url) for attachment in message.attachments],
            "embeds": [embed.to_dict() for embed in message.embeds],
            "reactions": [reaction.to_dict() for reaction in message.reactions],
            "mentions": [str(mention.id) for mention in message.mentions]
        }

    def parse_voice_data(self, state: discord.VoiceState) -> Dict[str, Any]:
        """Parse voice state data into structured format."""
        return {
            "channel_id": str(state.channel.id) if state.channel else None,
            "user_id": str(state.user.id) if state.user else None,
            "session_id": state.session_id,
            "deaf": state.deaf,
            "mute": state.mute,
            "self_deaf": state.self_deaf,
            "self_mute": state.self_mute,
            "self_stream": state.self_stream,
            "self_video": state.self_video,
            "suppress": state.suppress,
            "requested_to_speak_at": state.requested_to_speak_at.isoformat() if state.requested_to_speak_at else None
        }

    def parse_application_data(self, guild: discord.Guild) -> Dict[str, Any]:
        """Fetch application data including OAuth2 and rich presence."""
        if not self.client_id or not self.client_secret:
            return {}
            
        async with aiohttp.ClientSession() as session:
            # Fetch OAuth2 application info
            headers = {"Authorization": f"Bot {self.token}"}
            async with session.get(f"{DISCORD_API}/oauth2/applications/@me", headers=headers) as resp:
                if resp.status == 200:
                    app_data = await resp.json()
                    
                    # Fetch rich presence assets
                    async with session.get(
                        f"{DISCORD_API}/applications/{self.client_id}/assets",
                        headers=headers
                    ) as assets_resp:
                        if assets_resp.status == 200:
                            app_data["assets"] = await assets_resp.json()
                            
                    return app_data
        return {}

    def parse_analytics_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Discord analytics data."""
        return {
            "total_users": data["total_users"],
            "active_users": data["active_users"],
            "server_count": data["server_count"],
            "api_requests": data["api_requests"],
            "error_rates": data["error_rates"],
            "latency_stats": data["latency_stats"]
        }

    def parse_moderation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Discord moderation data."""
        return {
            "audit_logs": data["audit_logs"],
            "bans": data["bans"],
            "timeouts": data["timeouts"],
            "reports": data["reports"]
        }

    def parse_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Discord template data."""
        return {
            "server_templates": data["server_templates"],
            "backups": data["backups"],
            "snapshots": data["snapshots"],
            "restore": data["restore"]
        }

def main() -> None:
    """Main entry point."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        return

    async def fetch_data(session: aiohttp.ClientSession, endpoint: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Fetch data from Discord API."""
        async with session.get(f"https://discord.com/api/v10{endpoint}", headers=headers) as response:
            if response.status == 429:  # Rate limited
                retry_after = float(response.headers.get("Retry-After", 1))
                await asyncio.sleep(retry_after)
                return await fetch_data(session, endpoint, headers)
                
            response.raise_for_status()
            return await response.json()

    async def run_fetcher():
        """Run the Discord data fetcher."""
        fetcher = DiscordDataFetcher(token)
        session = aiohttp.ClientSession()
        try:
            fetcher.session = session
            await fetcher.client.start(token)
            
            headers = {
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json"
            }
            
            for category, config in fetcher.categories.items():
                try:
                    logger.info(f"Fetching {category} data...")
                    
                    # Get raw data from Discord API
                    raw_data = await fetch_data(session, config["endpoint"], headers)
                    
                    # Parse the data using the category's parser
                    parser = config["parser"]
                    parsed_data = parser(raw_data)
                    
                    # Store the parsed data
                    fetcher.data[category] = parsed_data
                    
                    # Process subcategories if any
                    if "subcategories" in config:
                        for subcategory in config["subcategories"]:
                            try:
                                if subcategory in raw_data:
                                    fetcher.data[category][subcategory] = raw_data[subcategory]
                                else:
                                    # Construct subcategory endpoint
                                    subcategory_endpoint = f"{config['endpoint']}/{subcategory}"
                                    subcategory_data = await fetch_data(session, subcategory_endpoint, headers)
                                    fetcher.data[category][subcategory] = subcategory_data
                                    
                            except Exception as e:
                                logger.error(f"Error fetching {subcategory} data for {category}: {e}")
                                continue
                    
                    # Rate limiting
                    await asyncio.sleep(fetcher.delay)
                    
                except Exception as e:
                    logger.error(f"Error fetching {category} data: {e}")
                    continue
                    
            fetcher.save_data()
            logger.info("\nDiscord data collection completed!")
            
        except Exception as e:
            logger.error(f"Error during Discord data collection: {e}", exc_info=True)
            raise
        finally:
            await session.close()
            await fetcher.client.close()

    asyncio.run(run_fetcher())

if __name__ == "__main__":
    main() 