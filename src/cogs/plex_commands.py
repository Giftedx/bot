"""Discord commands for Plex integration."""
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from ..core.exceptions import MediaNotFoundError, PlexConnectionError
from ..services.plex.models import MediaInfo, PlaybackState

logger = logging.getLogger(__name__)

class PlexCommands(commands.Cog):
    """Plex commands for Discord."""
    
    def __init__(self, bot):
        """Initialize Plex commands."""
        self.bot = bot
        
    @app_commands.command(name="search")
    @app_commands.describe(query="The media to search for")
    async def search(self, interaction: discord.Interaction, query: str):
        """Search for media on Plex."""
        await interaction.response.defer()
        
        try:
            results = await self.bot.plex.search_media(query)
            if not results:
                await interaction.followup.send("No media found matching your search.")
                return
                
            # Create embed with results
            embed = discord.Embed(
                title="Plex Search Results",
                color=discord.Color.blue()
            )
            
            for i, media in enumerate(results[:5], 1):
                embed.add_field(
                    name=f"{i}. {media.title}",
                    value=f"Type: {media.type}\nDuration: {media.duration//60} minutes",
                    inline=False
                )
                
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error searching media: {e}")
            await interaction.followup.send(f"An error occurred: {str(e)}")
            
    @app_commands.command(name="play")
    @app_commands.describe(query="The media to play")
    async def play(self, interaction: discord.Interaction, query: str):
        """Play media in voice channel."""
        if not interaction.user.voice:
            await interaction.response.send_message(
                "You need to be in a voice channel!",
                ephemeral=True
            )
            return
            
        await interaction.response.defer()
        
        try:
            # Search for media
            results = await self.bot.plex.search_media(query)
            if not results:
                await interaction.followup.send("No media found matching your search.")
                return
                
            # Get voice client
            voice_client = await self.bot.get_voice_client(interaction.user.voice.channel)
            if not voice_client:
                await interaction.followup.send("Failed to join voice channel.")
                return
                
            # Get stream URL
            media = results[0]
            stream = await self.bot.plex.get_stream_url(media.id)
            
            # Start playback
            if voice_client.is_playing():
                voice_client.stop()
                
            # Create FFmpeg audio source
            audio_source = discord.FFmpegPCMAudio(
                stream.url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
            )
            
            voice_client.play(
                audio_source,
                after=lambda e: print(f'Player error: {e}') if e else None
            )
            
            # Create embed for now playing
            embed = discord.Embed(
                title="Now Playing",
                color=discord.Color.green()
            )
            embed.add_field(name="Title", value=media.title, inline=False)
            if media.thumb:
                embed.set_thumbnail(url=media.thumb)
                
            await interaction.followup.send(embed=embed)
            
            # Update playback state
            state = PlaybackState(
                media_id=media.id,
                position=0,
                duration=media.duration,
                is_playing=True,
                volume=1.0,
                timestamp=discord.utils.utcnow()
            )
            
            # Emit WebSocket event
            self.bot.redis.publish(
                'playback_state',
                state.dict()
            )
        except Exception as e:
            logger.error(f"Error playing media: {e}")
            await interaction.followup.send(f"An error occurred: {str(e)}")
            
    @app_commands.command(name="pause")
    async def pause(self, interaction: discord.Interaction):
        """Pause current playback."""
        if not interaction.guild.voice_client:
            await interaction.response.send_message(
                "Nothing is playing!",
                ephemeral=True
            )
            return
            
        if not interaction.guild.voice_client.is_playing():
            await interaction.response.send_message(
                "Nothing is playing!",
                ephemeral=True
            )
            return
            
        interaction.guild.voice_client.pause()
        await interaction.response.send_message("Playback paused.")
        
        # Emit WebSocket event
        self.bot.redis.publish(
            'playback_state',
            {'action': 'pause'}
        )
        
    @app_commands.command(name="resume")
    async def resume(self, interaction: discord.Interaction):
        """Resume paused playback."""
        if not interaction.guild.voice_client:
            await interaction.response.send_message(
                "Nothing is paused!",
                ephemeral=True
            )
            return
            
        if not interaction.guild.voice_client.is_paused():
            await interaction.response.send_message(
                "Nothing is paused!",
                ephemeral=True
            )
            return
            
        interaction.guild.voice_client.resume()
        await interaction.response.send_message("Playback resumed.")
        
        # Emit WebSocket event
        self.bot.redis.publish(
            'playback_state',
            {'action': 'resume'}
        )
        
    @app_commands.command(name="stop")
    async def stop(self, interaction: discord.Interaction):
        """Stop current playback."""
        if not interaction.guild.voice_client:
            await interaction.response.send_message(
                "Nothing is playing!",
                ephemeral=True
            )
            return
            
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Playback stopped.")
        
        # Emit WebSocket event
        self.bot.redis.publish(
            'playback_state',
            {'action': 'stop'}
        )
        
async def setup(bot):
    """Set up the Plex commands cog."""
    await bot.add_cog(PlexCommands(bot)) 