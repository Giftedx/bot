from discord.ext import commands
import discord
import logging
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from plex_api.client import PlexClient
from config.config import Config

logger = logging.getLogger(__name__)

class MediaCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.plex_client = PlexClient(Config.PLEX_URL, Config.PLEX_TOKEN)
        
    @commands.command(name='libraries')
    async def list_libraries(self, ctx):
        """List all available Plex libraries."""
        try:
            libraries = self.plex_client.get_libraries()
            if not libraries:
                await ctx.send("No libraries found.")
                return
                
            embed = discord.Embed(title="Plex Libraries", color=discord.Color.blue())
            for library in libraries:
                embed.add_field(name=library.title, value=f"Type: {library.type}", inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error listing libraries: {e}")
            await ctx.send("Failed to retrieve libraries. Please try again later.")
            
    @commands.command(name='search')
    async def search_media(self, ctx, *, query: str):
        """Search for media across all libraries."""
        try:
            results = self.plex_client.search(query)
            if not results:
                await ctx.send(f"No results found for '{query}'")
                return
                
            embed = discord.Embed(title=f"Search Results for '{query}'", color=discord.Color.green())
            for item in results[:10]:  # Limit to 10 results
                embed.add_field(
                    name=item.title,
                    value=f"Type: {item.type}\nYear: {getattr(item, 'year', 'N/A')}",
                    inline=False
                )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error searching media: {e}")
            await ctx.send("An error occurred while searching. Please try again later.")
            
    @commands.command(name='play')
    async def play_media(self, ctx, media_id: str):
        """Start playing media in the voice channel."""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel to use this command.")
            return
            
        try:
            # Get media info and stream URL
            media_info = self.plex_client.get_media_info(media_id)
            if not media_info:
                await ctx.send("Media not found.")
                return
                
            # Join voice channel
            voice_channel = ctx.author.voice.channel
            voice_client = await voice_channel.connect()
            
            # Start playback
            stream_url = media_info['stream_url']
            voice_client.play(
                discord.FFmpegPCMAudio(stream_url),
                after=lambda e: print(f'Player error: {e}') if e else None
            )
            
            await ctx.send(f"Now playing: {media_info['title']}")
        except Exception as e:
            logger.error(f"Error playing media: {e}")
            await ctx.send("Failed to start playback. Please try again later.")
            
    @commands.command(name='stop')
    async def stop_playback(self, ctx):
        """Stop the current playback."""
        if not ctx.voice_client:
            await ctx.send("No active playback to stop.")
            return
            
        try:
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("Playback stopped.")
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            await ctx.send("Failed to stop playback. Please try again later.")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(MediaCommands(bot)) 