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
from discord_sdk import DiscordSDK, MediaSession
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

class PlexDiscordPlayer:
    """Handles Plex media playback through Discord's embedded player."""
    
    def __init__(self, bot: commands.Bot, plex_url: str, plex_token: str):
        self.bot = bot
        self.plex = PlexServer(plex_url, plex_token)
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
            media = self.plex.fetchItem(media_id)
            if not media:
                raise ValueError(f"Media not found: {media_id}")
                
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
            
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            
    async def _track_progress(self, ctx: commands.Context):
        """Track media playback progress."""
        guild_id = str(ctx.guild.id)
        session = self.media_sessions[guild_id]
        state = self.current_states[guild_id]
        
        while state.is_playing:
            try:
                position = await session.get_position()
                state.position = position
                
                # Update Discord presence
                activity = discord.Activity(
                    type=discord.ActivityType.watching,
                    name=state.title,
                    details=f"Watching {state.title}",
                    state=f"{position}/{state.duration}",
                    timestamps={
                        "start": int(state.started_at.timestamp()),
                        "end": int(state.started_at.timestamp() + state.duration)
                    }
                )
                await self.bot.change_presence(activity=activity)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error tracking progress: {e}")
                break
                
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