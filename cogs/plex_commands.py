import discord
from discord.ext import commands
from plexapi.server import PlexServer
import logging

logger = logging.getLogger('DiscordBot')

class PlexCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.plex = None

    async def init_plex(self, url: str, token: str):
        """Initialize Plex connection"""
        try:
            self.plex = PlexServer(url, token)
            logger.info("Connected to Plex Server")
            return True
        except Exception as e:
            logger.error(f"Plex connection failed: {e}")
            return False

    @commands.command(name='play')
    async def play(self, ctx, *, query):
        """Play media matching query"""
        if not self.plex:
            await ctx.send("Plex server not connected. Try again later.")
            return
        try:
            results = self.plex.library.search(query, limit=1)
            if results:
                embed = discord.Embed(
                    title="🎵 Found Media",
                    description=f"Found: {results[0].title}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("No results found.")
        except Exception as e:
            logger.error(f"Error in play command: {e}")
            await ctx.send(f"Error searching Plex: {e}")

    @commands.command(name='search')
    async def search(self, ctx, *, query):
        """Search for media"""
        if not self.plex:
            await ctx.send("Plex server not connected. Try again later.")
            return
        try:
            results = self.plex.library.search(query, limit=5)
            if results:
                embed = discord.Embed(
                    title="🔍 Search Results",
                    color=discord.Color.blue()
                )
                for item in results:
                    embed.add_field(
                        name=item.title,
                        value=f"Type: {item.type}\nYear: {getattr(item, 'year', 'N/A')}",
                        inline=False
                    )
                await ctx.send(embed=embed)
            else:
                await ctx.send("No results found.")
        except Exception as e:
            logger.error(f"Error in search command: {e}")
            await ctx.send(f"Error searching Plex: {e}")

async def setup(bot):
    plex_cog = PlexCommands(bot)
    if await plex_cog.init_plex(bot.PLEX_URL, bot.PLEX_TOKEN):
        await bot.add_cog(plex_cog)