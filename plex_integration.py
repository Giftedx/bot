from discord.ext import commands
import discord
from plexapi.server import PlexServer
from plexapi.video import Video
import asyncio
import platform
import os
from typing import Dict, List, Optional

class PlexManager:
    def __init__(self, url: str, token: str):
        self.server = PlexServer(url, token)
        self.current_sessions = {}
        self.stream_settings = self.get_platform_settings()
        
    def get_platform_settings(self) -> Dict[str, str]:
        """Get platform-specific settings"""
        system = platform.system().lower()
        if system == 'windows':
            return {
                'player': 'plex-media-player',
                'client_profile': 'Windows'
            }
        elif system == 'linux':
            return {
                'player': 'mpv',
                'client_profile': 'Linux'
            }
        elif system == 'darwin':
            return {
                'player': 'plex-media-player',
                'client_profile': 'MacOS'
            }
        return {
            'player': 'web',
            'client_profile': 'Generic'
        }
        
    async def search_media(self, query: str) -> List[Dict]:
        """Search for media on Plex server"""
        results = self.server.library.search(query)
        return [
            {
                'title': item.title,
                'type': item.type,
                'duration': item.duration,
                'key': item.key,
                'thumb': item.thumb
            }
            for item in results
            if isinstance(item, Video)
        ]
        
    async def get_stream_url(self, media_key: str) -> str:
        """Get streaming URL for media"""
        media = self.server.fetchItem(int(media_key))
        return media.getStreamURL()
        
    async def start_playback(self, media_key: str, voice_channel) -> bool:
        """Start media playback in voice channel"""
        try:
            media = self.server.fetchItem(int(media_key))
            stream_url = media.getStreamURL()
            
            # Store session info
            self.current_sessions[voice_channel.id] = {
                'media': media,
                'start_time': asyncio.get_event_loop().time(),
                'stream_url': stream_url
            }
            
            return True
        except Exception as e:
            print(f"Error starting playback: {e}")
            return False

class PlexCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.plex = PlexManager(
            self.bot.config['plex']['url'],
            self.bot.config['plex']['token']
        )
        
    @commands.group(invoke_without_command=True)
    async def plex(self, ctx):
        """Plex command group"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
            
    @plex.command()
    async def search(self, ctx, *, query: str):
        """Search for media on Plex"""
        results = await self.plex.search_media(query)
        if not results:
            return await ctx.send("No media found matching your search.")
            
        # Create embed with results
        embed = discord.Embed(title=f"Plex Search Results", color=discord.Color.blue())
        for i, media in enumerate(results[:5], 1):
            embed.add_field(
                name=f"{i}. {media['title']}",
                value=f"Type: {media['type']}\nDuration: {media['duration']//60} minutes",
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    @plex.command()
    async def play(self, ctx, *, query: str):
        """Play media from Plex"""
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel!")
            
        # Search for media
        results = await self.plex.search_media(query)
        if not results:
            return await ctx.send("No media found matching your search.")
            
        # Get voice channel
        voice_channel = ctx.author.voice.channel
        
        # Connect to voice if not already connected
        if not ctx.voice_client:
            try:
                await voice_channel.connect()
            except Exception as e:
                return await ctx.send(f"Error connecting to voice: {e}")
                
        # Start playback
        success = await self.plex.start_playback(results[0]['key'], voice_channel)
        if success:
            await ctx.send(f"Now playing: {results[0]['title']}")
        else:
            await ctx.send("Error starting playback.")
            
    @plex.command()
    async def stop(self, ctx):
        """Stop current playback"""
        if not ctx.voice_client:
            return await ctx.send("Not playing anything!")
            
        # Stop playback
        ctx.voice_client.stop()
        
        # Clear session
        if ctx.voice_client.channel.id in self.plex.current_sessions:
            del self.plex.current_sessions[ctx.voice_client.channel.id]
            
        await ctx.send("Playback stopped.")
        
    @plex.command()
    async def pause(self, ctx):
        """Pause current playback"""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("Nothing is playing!")
            
        ctx.voice_client.pause()
        await ctx.send("Playback paused.")
        
    @plex.command()
    async def resume(self, ctx):
        """Resume paused playback"""
        if not ctx.voice_client or not ctx.voice_client.is_paused():
            return await ctx.send("Nothing is paused!")
            
        ctx.voice_client.resume()
        await ctx.send("Playback resumed.")
        
    @plex.command()
    async def nowplaying(self, ctx):
        """Show currently playing media"""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("Nothing is playing!")
            
        session = self.plex.current_sessions.get(ctx.voice_client.channel.id)
        if not session:
            return await ctx.send("No active session found.")
            
        media = session['media']
        elapsed = int(asyncio.get_event_loop().time() - session['start_time'])
        
        embed = discord.Embed(title="Now Playing", color=discord.Color.blue())
        embed.add_field(name="Title", value=media.title, inline=False)
        embed.add_field(name="Duration", value=f"{media.duration//60} minutes", inline=True)
        embed.add_field(name="Elapsed", value=f"{elapsed//60} minutes", inline=True)
        
        if media.thumb:
            embed.set_thumbnail(url=media.thumb)
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PlexCommands(bot)) 