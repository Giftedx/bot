"""
Plex Activity integration for Discord.
Handles the lifecycle and communication between Plex media playback and Discord Activities.
"""
import asyncio
import logging
from typing import Dict, Optional, Any
import time
import json

import discord
from discord.ext import commands
from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.audio import Track

logger = logging.getLogger(__name__)

class PlexActivity:
    """Manages Plex media playback as a Discord Activity."""
    
    def __init__(self, bot: commands.Bot, plex_url: str, plex_token: str):
        self.bot = bot
        self.plex = PlexServer(plex_url, plex_token)
        self.active_activities: Dict[int, Dict[str, Any]] = {}  # channel_id -> activity_info
        
        # Activity configuration
        self.activity_config = {
            'client_id': bot.config.get('discord_client_id'),
            'activity_id': bot.config.get('plex_activity_id', '1234567890'),  # Replace with your actual Activity ID
            'supported_platforms': ['desktop', 'web'],  # Add 'mobile' if mobile support is implemented
            'activity_types': {
                'movie': 1,
                'show': 2,
                'music': 3
            }
        }
        
        # SDK configuration
        self.sdk_config = {
            'client_id': self.activity_config['client_id'],
            'scopes': [
                'identify',              # Basic user info
                'guilds',               # Server info
                'voice',                # Voice channel features
                'activities.write',     # Activity control
                'rpc',                  # RPC features
                'rpc.activities.write'  # Activity state management
            ]
        }
        
    async def initialize_activity(self, ctx: commands.Context) -> Optional[dict]:
        """Initialize a new Plex Activity instance in a voice channel."""
        try:
            if not ctx.author.voice:
                await ctx.send("You need to be in a voice channel to start a Plex Activity!")
                return None
                
            voice_channel = ctx.author.voice.channel
            
            # Check if activity already exists
            if voice_channel.id in self.active_activities:
                await ctx.send("There's already an active Plex session in this channel!")
                return None
                
            # Create activity launch payload
            activity_config = {
                'type': 'ACTIVITY',
                'name': 'Plex Watch Together',
                'application_id': self.activity_config['client_id'],
                'metadata': {
                    'activity_id': self.activity_config['activity_id'],
                    'supported_platforms': self.activity_config['supported_platforms']
                },
                'details': 'Watching Plex together',
                'state': 'Choosing media',
                'assets': {
                    'large_image': 'plex_logo',
                    'large_text': 'Plex',
                    'small_image': 'discord_logo',
                    'small_text': 'Discord Activity'
                },
                'party': {
                    'id': str(voice_channel.id),
                    'size': [1, voice_channel.user_limit or 99]
                },
                'secrets': {
                    'join': self._generate_join_secret(voice_channel.id)
                },
                'instance': True
            }
            
            # Store activity info with SDK state
            self.active_activities[voice_channel.id] = {
                'config': activity_config,
                'voice_channel': voice_channel,
                'start_time': time.time(),
                'participants': set([ctx.author.id]),
                'current_media': None,
                'state': 'INITIALIZED',
                'sdk_state': {
                    'authorized': False,
                    'authenticated': False,
                    'access_token': None
                }
            }
            
            # Initialize SDK authorization
            await self._initialize_sdk(voice_channel.id)
            
            return activity_config
            
        except Exception as e:
            logger.error(f"Error initializing Plex Activity: {e}")
            await ctx.send("Failed to initialize Plex Activity. Please try again.")
            return None
            
    async def _initialize_sdk(self, channel_id: int):
        """Initialize the Discord SDK for an activity."""
        activity = self.active_activities.get(channel_id)
        if not activity:
            return
            
        try:
            # Authorize with Discord client
            auth_payload = {
                'client_id': self.sdk_config['client_id'],
                'response_type': 'code',
                'state': '',
                'prompt': 'none',
                'scope': self.sdk_config['scopes']
            }
            
            # Store authorization state
            activity['sdk_state']['auth_payload'] = auth_payload
            
            # Update activity state
            activity['state'] = 'AUTHORIZING'
            await self._update_activity_presence(channel_id)
            
        except Exception as e:
            logger.error(f"Error initializing SDK: {e}")
            await self.cleanup_activity(channel_id)
            
    def _generate_join_secret(self, channel_id: int) -> str:
        """Generate a join secret for the activity."""
        secret_data = {
            'channel_id': channel_id,
            'timestamp': int(time.time()),
            'nonce': f"{channel_id}_{int(time.time())}"
        }
        return f"plex_{json.dumps(secret_data)}"
        
    async def _handle_sdk_ready(self, channel_id: int):
        """Handle SDK ready event."""
        activity = self.active_activities.get(channel_id)
        if not activity:
            return
            
        activity['sdk_state']['ready'] = True
        activity['state'] = 'READY'
        await self._update_activity_presence(channel_id)
        
    async def _handle_sdk_error(self, channel_id: int, error: Any):
        """Handle SDK error event."""
        logger.error(f"SDK Error in channel {channel_id}: {error}")
        await self.cleanup_activity(channel_id)
        
    async def _handle_sdk_disconnect(self, channel_id: int):
        """Handle SDK disconnect event."""
        logger.info(f"SDK Disconnected in channel {channel_id}")
        await self.cleanup_activity(channel_id)
        
    async def start_media(self, ctx: commands.Context, media_id: str) -> bool:
        """Start playing media in an active Plex Activity."""
        try:
            if not ctx.author.voice:
                await ctx.send("You need to be in a voice channel!")
                return False
                
            voice_channel = ctx.author.voice.channel
            
            if voice_channel.id not in self.active_activities:
                await ctx.send("No active Plex Activity in this channel! Start one first.")
                return False
                
            # Get media from Plex
            media = self.plex.fetchItem(int(media_id))
            if not media:
                await ctx.send(f"Could not find media with ID {media_id}")
                return False
                
            activity = self.active_activities[voice_channel.id]
            
            # Update activity state
            activity['current_media'] = media
            activity['state'] = 'PLAYING'
            activity['start_time'] = time.time()
            
            # Update activity presence
            await self._update_activity_presence(voice_channel.id)
            
            # Start media playback
            await self._start_playback(ctx, media)
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting media in Plex Activity: {e}")
            await ctx.send(f"Error starting media: {str(e)}")
            return False
            
    async def _update_activity_presence(self, channel_id: int):
        """Update Discord Activity presence with current media info."""
        activity = self.active_activities.get(channel_id)
        if not activity:
            return
            
        media = activity['current_media']
        if not media:
            return
            
        # Create rich presence update
        presence = {
            'type': 'ACTIVITY',
            'name': 'Plex Watch Together',
            'details': self._get_media_details(media),
            'state': activity['state'],
            'timestamps': {
                'start': int(activity['start_time'])
            },
            'assets': {
                'large_image': media.thumb if hasattr(media, 'thumb') else 'plex_logo',
                'large_text': media.title,
                'small_image': 'plex_icon',
                'small_text': 'Plex'
            },
            'party': {
                'id': str(channel_id),
                'size': [len(activity['participants']), activity['voice_channel'].user_limit or 99]
            }
        }
        
        # Update bot presence
        await self.bot.change_presence(activity=discord.Activity(**presence))
        
    def _get_media_details(self, media: Any) -> str:
        """Get formatted media details for activity presence."""
        if isinstance(media, Video):
            if hasattr(media, 'grandparentTitle'):  # TV Show
                return f"Watching {media.grandparentTitle} - {media.title}"
            return f"Watching {media.title}"
        elif isinstance(media, Track):
            if media.grandparentTitle:  # Song in album
                return f"Listening to {media.title} by {media.grandparentTitle}"
            return f"Listening to {media.title}"
        return f"Playing {media.title}"
        
    async def _start_playback(self, ctx: commands.Context, media: Any):
        """Start media playback in voice channel."""
        try:
            # Get optimized stream URL
            stream_url = self._create_stream_url(media)
            
            # Connect to voice channel if not already connected
            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()
                
            # Create FFmpeg audio source
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn -b:a 192k'
            }
            
            audio_source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
            ctx.voice_client.play(audio_source)
            
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            raise
            
    def _create_stream_url(self, media: Any) -> str:
        """Create an optimized stream URL for the media."""
        return media.getStreamURL(
            videoQuality='1080p',
            audioQuality='high',
            maxAudioChannels=2,
            videoBitrate='4mbps'
        )
        
    async def handle_activity_join(self, member: discord.Member, channel_id: int):
        """Handle a user joining the Activity."""
        if channel_id in self.active_activities:
            activity = self.active_activities[channel_id]
            activity['participants'].add(member.id)
            await self._update_activity_presence(channel_id)
            
    async def handle_activity_leave(self, member: discord.Member, channel_id: int):
        """Handle a user leaving the Activity."""
        if channel_id in self.active_activities:
            activity = self.active_activities[channel_id]
            activity['participants'].remove(member.id)
            
            # If no participants left, clean up the activity
            if not activity['participants']:
                await self.cleanup_activity(channel_id)
            else:
                await self._update_activity_presence(channel_id)
                
    async def cleanup_activity(self, channel_id: int):
        """Clean up an Activity instance."""
        if channel_id in self.active_activities:
            activity = self.active_activities[channel_id]
            
            # Disconnect from voice channel if connected
            if activity['voice_channel'].guild.voice_client:
                await activity['voice_channel'].guild.voice_client.disconnect()
                
            # Remove activity data
            del self.active_activities[channel_id]
            
            # Reset bot presence
            await self.bot.change_presence(activity=None) 