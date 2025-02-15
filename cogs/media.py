from discord.ext import commands
import discord
import wavelink
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import giphy_client
from giphy_client.rest import ApiException
import random
from typing import Optional, Dict, List

class MediaCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues: Dict[int, List[wavelink.Track]] = {}
        self.now_playing: Dict[int, wavelink.Track] = {}
        
    async def cog_load(self):
        """Initialize wavelink nodes when cog loads"""
        node = wavelink.Node(
            uri='http://localhost:2333',  # Lavalink server
            password='youshallnotpass'
        )
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

    @commands.group(invoke_without_command=True)
    async def music(self, ctx):
        """Music command group"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @music.command()
    async def play(self, ctx, *, query: str):
        """Play music from YouTube/Spotify"""
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel!")

        # Connect to voice if not already connected
        if not ctx.voice_client:
            try:
                await ctx.author.voice.channel.connect(cls=wavelink.Player)
            except Exception as e:
                return await ctx.send(f"Error connecting to voice: {e}")

        # Search for track
        try:
            tracks = await wavelink.YouTubeTrack.search(query)
            if not tracks:
                return await ctx.send("No tracks found.")

            track = tracks[0]
            
            # Add to queue or play immediately
            if ctx.voice_client.is_playing():
                self.queues.setdefault(ctx.guild.id, []).append(track)
                await ctx.send(f"Added to queue: {track.title}")
            else:
                await ctx.voice_client.play(track)
                self.now_playing[ctx.guild.id] = track
                await ctx.send(f"Now playing: {track.title}")
        except Exception as e:
            await ctx.send(f"Error playing track: {e}")

    @music.command()
    async def skip(self, ctx):
        """Skip current track"""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("Nothing is playing!")

        await ctx.voice_client.stop()
        await ctx.send("Skipped current track.")

        # Play next in queue if exists
        if self.queues.get(ctx.guild.id):
            next_track = self.queues[ctx.guild.id].pop(0)
            await ctx.voice_client.play(next_track)
            self.now_playing[ctx.guild.id] = next_track
            await ctx.send(f"Now playing: {next_track.title}")

    @music.command()
    async def queue(self, ctx):
        """Show music queue"""
        if not self.queues.get(ctx.guild.id):
            return await ctx.send("Queue is empty.")

        queue_list = "\n".join(
            f"{i+1}. {track.title}"
            for i, track in enumerate(self.queues[ctx.guild.id][:10])
        )
        
        embed = discord.Embed(title="Music Queue", description=queue_list)
        if len(self.queues[ctx.guild.id]) > 10:
            embed.set_footer(text=f"And {len(self.queues[ctx.guild.id]) - 10} more...")
            
        await ctx.send(embed=embed)

    @music.command()
    async def stop(self, ctx):
        """Stop music and clear queue"""
        if not ctx.voice_client:
            return await ctx.send("Not playing anything!")

        # Clear queue and stop playback
        self.queues[ctx.guild.id] = []
        await ctx.voice_client.stop()
        await ctx.send("Stopped playback and cleared queue.")

    @commands.command()
    async def gif(self, ctx, *, query: str):
        """Search for a GIF"""
        try:
            api_instance = giphy_client.DefaultApi()
            api_response = api_instance.gifs_search_get(
                self.bot.config.get('giphy_api_key', 'your_api_key'),
                query,
                limit=10
            )
            if not api_response.data:
                return await ctx.send("No GIFs found.")

            gif = random.choice(api_response.data)
            await ctx.send(gif.url)
        except ApiException as e:
            await ctx.send(f"Error searching for GIF: {e}")

    @commands.command()
    async def sound(self, ctx, name: str):
        """Play a sound effect"""
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel!")

        # Get sound effect file path
        sound_path = f"sounds/{name}.mp3"  # You'll need to create this directory
        
        if not ctx.voice_client:
            try:
                await ctx.author.voice.channel.connect(cls=wavelink.Player)
            except Exception as e:
                return await ctx.send(f"Error connecting to voice: {e}")

        try:
            track = await wavelink.LocalTrack.search(sound_path)
            if not track:
                return await ctx.send("Sound effect not found.")

            await ctx.voice_client.play(track[0])
            await ctx.message.add_reaction('🔊')
        except Exception as e:
            await ctx.send(f"Error playing sound effect: {e}")

async def setup(bot):
    await bot.add_cog(MediaCommands(bot)) 