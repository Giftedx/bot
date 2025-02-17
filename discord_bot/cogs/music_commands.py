from discord.ext import commands
import discord
import logging
import asyncio
import yt_dlp
import wavelink
from collections import deque
from typing import Optional
import datetime
import re

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(
    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»""'']))"
)

class MusicCommands(commands.Cog, name="Music"):
    """Music playback and management commands.
    
    This category includes commands for:
    - Playing music from various sources (YouTube, Spotify, etc.)
    - Queue management
    - Playback control (pause, resume, skip)
    - Volume control
    - Now playing information
    
    Requires:
    - Bot must be in a voice channel
    - Lavalink server must be running
    - User must be in a voice channel
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # Guild ID: Queue
        self.now_playing = {}  # Guild ID: Current Track
        self.volume = {}  # Guild ID: Volume
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        """Connect to Lavalink nodes when the bot is ready."""
        await self.bot.wait_until_ready()
        
        try:
            await wavelink.NodePool.create_node(
                bot=self.bot,
                host='127.0.0.1',
                port=2333,
                password='youshallnotpass'
            )
        except Exception as e:
            logger.error(f"Error connecting to Lavalink: {e}")

    def get_queue(self, guild_id: int) -> deque:
        """Get or create a queue for a guild."""
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        print(f'Node: <{node.identifier}> is ready!')
    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        """Event fired when a track finishes playing."""
        if not player.queue.is_empty and not player.auto_play:
            next_track = player.queue.get()
            await player.play(next_track)

    async def get_player(self, ctx: commands.Context) -> Optional[wavelink.Player]:
        """Get or create a wavelink Player for the guild."""
        if not ctx.guild:
            await ctx.send("Music commands can only be used in a server.")
            return None
            
        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel to use music commands.")
            return None
            
        if not ctx.voice_client:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            player = ctx.voice_client
            
        return player

    @commands.command(name='join')
    async def join(self, ctx):
        """Join your voice channel.
        
        Bot will join the voice channel you are currently in.
        You must be in a voice channel to use this command.
        
        Examples:
        ---------
        !join
        
        Notes:
        ------
        - Bot will automatically join when using play command
        - Bot will not join if you're not in a voice channel
        - Bot will move to your channel if already in another
        """
        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel for me to join.")
            return
            
        channel = ctx.author.voice.channel
        await channel.connect(cls=wavelink.Player)
        await ctx.send(f"Joined {channel.name}!")

    @commands.command(name='leave')
    async def leave(self, ctx):
        """Leave the voice channel."""
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel.")
            return
            
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel!")

    @commands.command(name='play')
    async def play(self, ctx, *, query: str):
        """Play a song or add it to the queue.
        
        Supports various sources:
        - YouTube URLs (videos, playlists)
        - Spotify URLs (tracks, playlists, albums)
        - SoundCloud URLs
        - Direct search queries (searches YouTube)
        
        Parameters:
        -----------
        query: The song to play (URL or search terms)
        
        Examples:
        ---------
        !play https://youtube.com/watch?v=...
        !play Despacito
        !play playlist:https://youtube.com/playlist?list=...
        
        Notes:
        ------
        - Bot will join your voice channel if not already in one
        - Songs are added to queue if something is already playing
        - Playlists are automatically processed and added to queue
        """
        player = await self.get_player(ctx)
        if not player:
            return
            
        # Check if the query is a URL
        if not URL_REGEX.match(query):
            query = f'ytsearch:{query}'
            
        tracks = await wavelink.NodePool.get_node().get_tracks(query=query)
        if not tracks:
            await ctx.send("No songs found.")
            return
            
        if isinstance(tracks, wavelink.TrackPlaylist):
            # Add all tracks from playlist
            for track in tracks.tracks:
                player.queue.put(track)
            await ctx.send(f"Added playlist {tracks.name} ({len(tracks.tracks)} tracks) to the queue!")
        else:
            track = tracks[0]
            if player.is_playing():
                player.queue.put(track)
                await ctx.send(f"Added {track.title} to the queue!")
            else:
                await player.play(track)
                await ctx.send(f"Now playing: {track.title}")

    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pause the current song."""
        player = await self.get_player(ctx)
        if not player:
            return
            
        if player.is_playing():
            await player.pause()
            await ctx.send("Paused the music!")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(name='resume')
    async def resume(self, ctx):
        """Resume the current song."""
        player = await self.get_player(ctx)
        if not player:
            return
            
        if player.is_paused:
            await player.resume()
            await ctx.send("Resumed the music!")
        else:
            await ctx.send("The music isn't paused.")

    @commands.command(name='stop')
    async def stop(self, ctx):
        """Stop playing and clear the queue."""
        player = await self.get_player(ctx)
        if not player:
            return
            
        player.queue.clear()
        await player.stop()
        await ctx.send("Stopped the music and cleared the queue!")

    @commands.command(name='skip')
    async def skip(self, ctx):
        """Skip the current song."""
        player = await self.get_player(ctx)
        if not player:
            return
            
        if player.is_playing():
            await player.stop()
            await ctx.send("Skipped the current song!")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(name='queue')
    async def queue(self, ctx):
        """Show the current music queue.
        
        Displays:
        - Currently playing song
        - Next 10 songs in queue
        - Total number of songs in queue
        - Total queue duration
        
        Examples:
        ---------
        !queue
        
        Notes:
        ------
        - Use !queue page <number> to view different pages
        - Queue is server-specific
        """
        player = await self.get_player(ctx)
        if not player:
            return
            
        if player.queue.is_empty:
            await ctx.send("The queue is empty.")
            return
            
        embed = discord.Embed(
            title="Music Queue",
            color=discord.Color.blue()
        )
        
        queue_list = []
        for i, track in enumerate(player.queue, start=1):
            queue_list.append(f"{i}. {track.title}")
            if i >= 10:  # Only show first 10 tracks
                queue_list.append(f"... and {len(player.queue) - 10} more")
                break
                
        embed.description = "\n".join(queue_list)
        
        if player.is_playing():
            embed.add_field(
                name="Now Playing",
                value=player.track.title,
                inline=False
            )
            
        await ctx.send(embed=embed)

    @commands.command(name='volume')
    async def volume(self, ctx, volume: int = None):
        """Set or show the volume (0-100)."""
        player = await self.get_player(ctx)
        if not player:
            return
            
        if volume is None:
            await ctx.send(f"Current volume: {player.volume}%")
            return
            
        if not 0 <= volume <= 100:
            await ctx.send("Volume must be between 0 and 100.")
            return
            
        await player.set_volume(volume)
        await ctx.send(f"Set volume to {volume}%")

    @commands.command(name='now_playing', aliases=['np'])
    async def now_playing(self, ctx):
        """Show information about the current song."""
        player = await self.get_player(ctx)
        if not player or not player.is_playing():
            await ctx.send("Nothing is playing right now.")
            return
            
        track = player.track
        
        embed = discord.Embed(
            title="Now Playing",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=track.length)))
        embed.add_field(name="Author", value=track.author)
        
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def shuffle_queue(self, ctx):
        """Shuffle the music queue."""
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
            
        queue = self.get_queue(ctx.guild.id)
        if len(queue) < 2:
            await ctx.send("Not enough songs in the queue to shuffle!")
            return
            
        current_queue = list(queue)
        import random
        random.shuffle(current_queue)
        self.queues[ctx.guild.id] = deque(current_queue)
        
        await ctx.send("🔀 Shuffled the queue!")

    @commands.command(name='remove')
    async def remove_from_queue(self, ctx, position: int):
        """Remove a song from the queue by its position.
        
        Parameters:
        -----------
        position: Position in the queue (1-based)
        
        Example:
        --------
        !remove 3
        """
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
            
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            await ctx.send("The queue is empty!")
            return
            
        if not 1 <= position <= len(queue):
            await ctx.send("Invalid position!")
            return
            
        removed = queue[position - 1]
        del queue[position - 1]
        await ctx.send(f"Removed **{removed.title}** from the queue.")

    @commands.command(name='loop')
    async def toggle_loop(self, ctx):
        """Toggle loop mode for the current song."""
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
            
        player = ctx.voice_client
        player.loop = not player.loop
        
        if player.loop:
            await ctx.send("🔁 Loop mode enabled")
        else:
            await ctx.send("➡️ Loop mode disabled")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(MusicCommands(bot)) 