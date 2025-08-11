from __future__ import annotations
from typing import Optional
import discord
from discord.ext import commands
from plexapi.server import PlexServer

from .media_player import MediaPlayer


class PlexSelfBot(commands.Bot):
    def __init__(self, url: str, token: str):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        # Validate URL/token by constructing PlexServer (mocked in tests)
        self._plex = PlexServer(url, token)
        self._media_player = MediaPlayer()
        self._active_stream: Optional[str] = None

        @self.command(name="search")
        async def search(ctx: commands.Context, *, query: str):
            section = self._plex.library.section("Movies")
            results = section.search(query)
            embed = discord.Embed(title="Search Results")
            for item in results[:5]:
                embed.add_field(name=getattr(item, "title", "Unknown"), value="", inline=False)
            await ctx.send(embed=embed)

        @self.command(name="stream")
        async def stream(ctx: commands.Context, *, query: str):
            if not isinstance(ctx.author, discord.Member) or not ctx.author.voice:
                await ctx.send("You need to be in a voice channel!")
                return
            self._active_stream = query
            await ctx.send(f"Streaming {query}...")

        @self.command(name="stop")
        async def stop(ctx: commands.Context):
            if not self._active_stream:
                await ctx.send("No active stream!")
                return
            self._active_stream = None
            await ctx.send("Stopped streaming.")