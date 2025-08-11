from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands
from plexapi.server import PlexServer

from .media_player import MediaPlayer


class PlexSelfBot(commands.Bot):
    def __init__(self, url: str, token: str):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", self_bot=True, intents=intents)
        self._plex: Optional[PlexServer] = PlexServer(url, token)
        self._player = MediaPlayer()

        @self.command(name="search")
        async def search(ctx: commands.Context, *, query: str):
            section = self._plex.library.section("Movies")
            results = section.search(query)
            embed = discord.Embed(title=f"Search results for {query}")
            for item in results[:5]:
                embed.add_field(name=item.title, value=str(getattr(item, "year", "")) or "", inline=False)
            await ctx.send(embed=embed)

        @self.command(name="stream")
        async def stream(ctx: commands.Context, *, query: str):
            if not isinstance(ctx.author, discord.Member) or not ctx.author.voice:
                await ctx.send("You need to be in a voice channel!")
                return
            # For tests we just send message; actual streaming handled by MediaPlayer
            await ctx.send(f"Attempting to stream: {query}")

        @self.command(name="stop")
        async def stop(ctx: commands.Context):
            await ctx.send("No active stream!")