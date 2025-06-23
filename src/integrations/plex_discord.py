"""
Plex-Discord integration module for embedded media playback.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import discord
from discord.ext import commands
from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.audio import Track
from plexapi.exceptions import NotFound, Unauthorized, BadRequest, PlexApiException
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout as RequestsTimeout, RequestException
from discord_sdk import DiscordSDK, MediaSession

from src.core.config import ConfigManager
from src.core.exceptions import PlexConnectionError, PlexAPIError, MediaNotFoundError, StreamingError # Updated import path
import av
import websockets

logger = logging.getLogger(__name__)

@dataclass
class MediaState:
    """Represents the current state of media playback."""
    media_id: str
    title: str
    duration: int
    position: int
    is_playing: bool
    started_at: datetime
    thumbnail_url: str
    session_id: str

def _format_ms_to_time(ms: int) -> str:
    """Formats milliseconds to HH:MM:SS or MM:SS string."""
    seconds = ms // 1000
    minutes = seconds // 60
    hours = minutes // 60

    if hours > 0:
        return f"{hours:02d}:{minutes % 60:02d}:{seconds % 60:02d}"
    else:
        return f"{minutes:02d}:{seconds % 60:02d}"

class PlexDiscordPlayer:
    """Handles Plex media playback through Discord's embedded player."""
    
    def __init__(self, bot: commands.Bot, plex_url: str, plex_token: str):
        self.bot = bot

        if not plex_url or not plex_token:
            logger.error("Plex URL or Token not provided. PlexDiscordPlayer cannot initialize.")
            raise ValueError("Plex URL and/or Token is not configured. PlexDiscordPlayer cannot operate.")

        try:
            self.plex = PlexServer(plex_url, plex_token, timeout=10)
            logger.info(f"Successfully connected to Plex server for PlexDiscordPlayer: {plex_url}")
        except Unauthorized:
            logger.error(f"Plex authentication failed for PlexDiscordPlayer: Invalid token or credentials for {plex_url}.")
            raise PlexConnectionError(f"Invalid Plex credentials for {plex_url}.")
        except RequestsConnectionError as e:
            logger.error(f"Plex connection failed for PlexDiscordPlayer: Could not connect to server at {plex_url}. Error: {e}")
            raise PlexConnectionError(f"Could not connect to Plex server at {plex_url}.")
        except RequestsTimeout as e:
            logger.error(f"Plex connection timed out for PlexDiscordPlayer while trying to reach {plex_url}. Error: {e}")
            raise PlexConnectionError(f"Connection to Plex server {plex_url} timed out.")
        except PlexApiException as e:
            logger.error(f"Plex API error during PlexDiscordPlayer connection to {plex_url}: {e}")
            raise PlexAPIError(f"Plex API error during connection to {plex_url}: {e}")
        except RequestException as e:
            logger.error(f"Network error during PlexDiscordPlayer connection to {plex_url}: {e}")
            raise PlexConnectionError(f"Network error connecting to Plex at {plex_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to Plex for PlexDiscordPlayer ({plex_url}): {e}", exc_info=True)
            raise StreamingError(f"An unexpected error occurred while connecting to Plex ({plex_url}): {e}")

        self.sdk = DiscordSDK()
        self.media_sessions: Dict[str, MediaSession] = {}
        self.current_states: Dict[str, MediaState] = {}
        
    async def initialize(self):
        """Initialize the Plex-Discord player."""
        await self.sdk.connect()
        logger.info("Plex-Discord player initialized")
        
    async def cleanup(self):
        """Cleanup resources."""
        for session in self.media_sessions.values():
            await session.close()
        await self.sdk.disconnect()
        
    async def create_embed_player(self, ctx: commands.Context, media_id: str) -> Optional[discord.Embed]:
        """Create an embedded player for Plex media."""
        try:
            # Get media from Plex
            try:
                media = self.plex.fetchItem(media_id) # media_id should be int for fetchItem usually
                if not media: # Should be caught by NotFound, but defensive
                    raise MediaNotFoundError(f"Media item {media_id} resulted in None.")
            except NotFound:
                logger.warning(f"Plex media not found for ID: {media_id}")
                raise MediaNotFoundError(f"Media with ID {media_id} not found on Plex.")
            except Unauthorized as e:
                logger.error(f"Plex unauthorized while fetching media ID {media_id}: {e}")
                raise PlexConnectionError(f"Plex authorization failed while fetching media: {e}")
            except PlexApiException as e:
                logger.error(f"Plex API error fetching media ID {media_id}: {e}")
                raise PlexAPIError(f"Plex API error fetching media {media_id}: {e}")
            except RequestException as e: # Covers ConnectionError, Timeout, etc.
                logger.error(f"Network error fetching Plex media ID {media_id}: {e}")
                raise PlexConnectionError(f"Network error fetching media {media_id} from Plex: {e}")
                
            # Create media session
            session = await self.sdk.create_media_session(
                title=media.title,
                duration=media.duration,
                thumbnail_url=media.thumbUrl,
                media_type="video" if isinstance(media, Video) else "audio"
            )
            
            # Store session
            self.media_sessions[str(ctx.guild.id)] = session
            
            # Create state
            state = MediaState(
                media_id=media_id,
                title=media.title,
                duration=media.duration,
                position=0,
                is_playing=False,
                started_at=datetime.now(),
                thumbnail_url=media.thumbUrl,
                session_id=session.id
            )
            self.current_states[str(ctx.guild.id)] = state
            
            # Create embed
            embed = discord.Embed(title=media.title, description=media.summary)
            embed.set_thumbnail(url=media.thumbUrl)
            embed.add_field(name="Duration", value=str(media.duration))
            embed.add_field(name="Quality", value=media.mediaStreams[0].videoResolution)
            
            # Add player iframe
            player_html = await session.get_player_html()
            embed.add_field(name="Player", value=f"```html\n{player_html}\n```", inline=False)
            
            return embed
            
        except Exception as e:
            logger.error(f"Error creating embed player: {e}")
            return None
            
    async def start_playback(self, ctx: commands.Context):
        """Start media playback."""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.media_sessions:
            return
            
        session = self.media_sessions[guild_id]
        state = self.current_states[guild_id]
        
        try:
            # Get media stream URL
            media = self.plex.fetchItem(state.media_id)
            stream_url = media.getStreamURL()
            
            # Start playback
            await session.start_playback(stream_url)
            state.is_playing = True
            
            # Start progress tracking
            asyncio.create_task(self._track_progress(ctx))
            
        except MediaNotFoundError: # Re-raise if already specific
            raise
        except PlexConnectionError: # Re-raise
            raise
        except PlexAPIError: # Re-raise
            raise
        except Exception as e: # General errors for SDK or other issues
            logger.error(f"Error starting playback for media {state.media_id if state else 'unknown'}: {e}", exc_info=True)
            # Potentially raise a more generic StreamingError here if needed by calling code
            
    async def _track_progress(self, ctx: commands.Context):
        """Track media playback progress."""
        guild_id = str(ctx.guild.id)

        # Initial state check
        if guild_id not in self.media_sessions or guild_id not in self.current_states:
            logger.warning(f"Progress tracking for guild {guild_id} aborted: session or state not found.")
            return

        session = self.media_sessions[guild_id]
        state = self.current_states[guild_id]
        
        logger.info(f"Starting progress tracking for '{state.title}' in guild {guild_id}.")

        while state.is_playing:
            # Loop validity check
            if guild_id not in self.media_sessions or not self.current_states.get(guild_id, {}).get('is_playing'):
                logger.info(f"Progress tracking loop for guild {guild_id} terminating: session ended or playback stopped.")
                break

            try:
                position_ms = await session.get_position() # Assuming this returns ms
                state.position = position_ms

                # Calculate remaining time and end timestamp
                # Ensure duration and position are in the same units (milliseconds)
                duration_ms = state.duration
                remaining_ms = max(0, duration_ms - position_ms)
                
                current_time_sec = datetime.now().timestamp()
                end_timestamp_sec = int(current_time_sec + (remaining_ms / 1000))

                # Update Discord presence
                activity = discord.Activity(
                    type=discord.ActivityType.watching,
                    name=state.title,
                    # details field removed as it's redundant with name
                    state=f"{_format_ms_to_time(position_ms)} / {_format_ms_to_time(duration_ms)}",
                    timestamps={
                        "start": int(state.started_at.timestamp()), # Keeps original start time
                        "end": end_timestamp_sec
                    }
                )
                await self.bot.change_presence(activity=activity)
                
                await asyncio.sleep(15) # Changed update frequency
                
            except Exception as e:
                logger.error(f"Error tracking progress for '{state.title}' in guild {guild_id}: {e}", exc_info=True)
                break

        logger.info(f"Progress tracking for '{state.title}' in guild {guild_id} finished.")
                
    async def pause_playback(self, ctx: commands.Context):
        """Pause media playback."""
        guild_id = str(ctx.guild.id)
        if guild_id in self.media_sessions:
            session = self.media_sessions[guild_id]
            state = self.current_states[guild_id]
            await session.pause()
            state.is_playing = False
            
    async def resume_playback(self, ctx: commands.Context):
        """Resume media playback."""
        guild_id = str(ctx.guild.id)
        if guild_id in self.media_sessions:
            session = self.media_sessions[guild_id]
            state = self.current_states[guild_id]
            await session.resume()
            state.is_playing = True
            
    async def seek(self, ctx: commands.Context, position: int):
        """Seek to a specific position."""
        guild_id = str(ctx.guild.id)
        if guild_id in self.media_sessions:
            session = self.media_sessions[guild_id]
            await session.seek(position)
            self.current_states[guild_id].position = position
            
    async def stop_playback(self, ctx: commands.Context):
        """Stop media playback."""
        guild_id = str(ctx.guild.id)
        if guild_id in self.media_sessions:
            session = self.media_sessions[guild_id]
            await session.stop()
            del self.media_sessions[guild_id]
            del self.current_states[guild_id]
            await self.bot.change_presence(activity=None)
            
    async def handle_player_event(self, event: Dict[str, Any]):
        """Handle player events from Discord SDK."""
        event_type = event.get("type")
        session_id = event.get("session_id")
        
        if not session_id:
            return
            
        # Find corresponding guild
        guild_id = next(
            (gid for gid, session in self.media_sessions.items() 
             if session.id == session_id),
            None
        )
        
        if not guild_id:
            return
            
        if event_type == "pause":
            self.current_states[guild_id].is_playing = False
        elif event_type == "resume":
            self.current_states[guild_id].is_playing = True
        elif event_type == "seek":
            position = event.get("position", 0)
            self.current_states[guild_id].position = position
        elif event_type == "end":
            await self.stop_playback(guild_id)
            
    def get_current_state(self, guild_id: str) -> Optional[MediaState]:
        """Get current media state for a guild."""
        return self.current_states.get(str(guild_id)) 