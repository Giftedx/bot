"""Base cog containing core bot functionality."""

from discord.ext import commands
import discord
import logging
from typing import Optional, Any
from discord_bot.config import Config
import asyncio
import datetime

class BaseCog(commands.Cog, name="Core"):
    """Core bot functionality and essential commands.
    
    This category includes commands for:
    - Bot information
    - Ping and latency
    - Bot statistics
    - System status
    - Basic utility functions
    
    These commands are always available and don't require special permissions.
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.start_time = datetime.datetime.utcnow()
        
    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle errors that occur in this cog's commands."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument provided. Check !help for correct usage.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        else:
            self.logger.error(f"Error in {ctx.command}: {str(error)}", exc_info=error)
            await ctx.send("An error occurred while processing the command.")
            
    def get_embed(self, title: str, description: Optional[str] = None, color: int = discord.Color.blue().value) -> discord.Embed:
        """Create a standardized embed for the bot."""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=f"Requested by {self.bot.user.name}")
        return embed
        
    async def confirm_action(self, ctx: commands.Context, message: str) -> bool:
        """Ask for confirmation before proceeding with an action."""
        confirm_msg = await ctx.send(f"{message}\nReact with ✅ to confirm or ❌ to cancel.")
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]
            
        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            return str(reaction.emoji) == "✅"
        except TimeoutError:
            await ctx.send("Confirmation timed out.")
            return False
            
    async def paginate(self, ctx: commands.Context, items: list, per_page: int = 10, 
                      title: str = "Results", empty_message: str = "No items to display.") -> None:
        """Create a paginated embed for long lists of items."""
        if not items:
            await ctx.send(empty_message)
            return
            
        pages = [items[i:i + per_page] for i in range(0, len(items), per_page)]
        current_page = 0
        
        embed = self.get_embed(f"{title} (Page {current_page + 1}/{len(pages)})")
        embed.description = "\n".join(pages[current_page])
        message = await ctx.send(embed=embed)
        
        if len(pages) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            
            def check(reaction: discord.Reaction, user: discord.User) -> bool:
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]
                
            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                        current_page += 1
                    elif str(reaction.emoji) == "⬅️" and current_page > 0:
                        current_page -= 1
                        
                    embed.title = f"{title} (Page {current_page + 1}/{len(pages)})"
                    embed.description = "\n".join(pages[current_page])
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)
                    
                except TimeoutError:
                    break
                    
            await message.clear_reactions()
            
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in seconds to a human-readable string."""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
            
        return " ".join(parts)

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check the bot's latency.
        
        Shows the bot's current WebSocket latency.
        
        Examples:
        ---------
        !ping
        
        Notes:
        ------
        - Shows latency in milliseconds
        - Updates in real-time
        - Useful for checking bot responsiveness
        """
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
    
    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Check how long the bot has been running.
        
        Shows the time since the bot was last started.
        
        Examples:
        ---------
        !uptime
        
        Notes:
        ------
        - Shows days, hours, minutes, seconds
        - Updates in real-time
        - Resets when bot restarts
        """
        current_time = datetime.datetime.utcnow()
        delta = current_time - self.start_time
        
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        await ctx.send(f"⏱️ Uptime: {uptime_str}")
    
    @commands.command(name="about")
    async def about(self, ctx):
        """Display information about the bot.
        
        Shows detailed information about the bot's features and statistics.
        
        Examples:
        ---------
        !about
        
        Notes:
        ------
        - Shows version info
        - Lists key features
        - Displays bot statistics
        - Shows support information
        """
        embed = discord.Embed(
            title="About Bot",
            description="A versatile Discord bot with moderation, music, games, and more!",
            color=discord.Color.blue()
        )
        
        # Bot statistics
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        total_channels = sum(len(guild.channels) for guild in self.bot.guilds)
        
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Members", value=str(total_members), inline=True)
        embed.add_field(name="Channels", value=str(total_channels), inline=True)
        
        # Feature list
        features = [
            "✨ Powerful moderation tools",
            "🎵 High-quality music playback",
            "🎮 Fun games and activities",
            "🎬 Media integration with Plex",
            "⚙️ Custom commands system"
        ]
        embed.add_field(name="Features", value="\n".join(features), inline=False)
        
        # System info
        embed.add_field(name="Version", value="1.0.0", inline=True)
        embed.add_field(name="Python", value=discord.__version__, inline=True)
        embed.add_field(name="Support", value="[GitHub](https://github.com/yourusername/bot)", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="invite")
    async def invite(self, ctx):
        """Get the bot's invite link.
        
        Generates an invite link to add the bot to other servers.
        
        Examples:
        ---------
        !invite
        
        Notes:
        ------
        - Requires proper permissions
        - Shows required bot permissions
        - Includes support server link
        """
        permissions = discord.Permissions(
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_messages=True,
            manage_messages=True,
            connect=True,
            speak=True,
            use_voice_activation=True,
            add_reactions=True
        )
        
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions
        )
        
        embed = discord.Embed(
            title="Invite Bot",
            description="Add me to your server!",
            color=discord.Color.blue()
        )
        embed.add_field(name="Bot Invite", value=f"[Click Here]({invite_url})", inline=True)
        embed.add_field(name="Support Server", value="[Join Here](https://discord.gg/support)", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="stats")
    async def stats(self, ctx):
        """View bot statistics.
        
        Shows detailed statistics about the bot's usage and performance.
        
        Examples:
        ---------
        !stats
        
        Notes:
        ------
        - Shows server count
        - Displays member reach
        - Lists command usage
        - Shows system performance
        """
        embed = discord.Embed(
            title="Bot Statistics",
            color=discord.Color.blue()
        )
        
        # Server stats
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        total_channels = sum(len(guild.channels) for guild in self.bot.guilds)
        total_voice = sum(len(guild.voice_channels) for guild in self.bot.guilds)
        total_text = sum(len(guild.text_channels) for guild in self.bot.guilds)
        
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Members", value=str(total_members), inline=True)
        embed.add_field(name="Channels", value=f"📝 {total_text} | 🔊 {total_voice}", inline=True)
        
        # Performance stats
        latency = round(self.bot.latency * 1000)
        current_time = datetime.datetime.utcnow()
        delta = current_time - self.start_time
        uptime = f"{delta.days}d {delta.seconds//3600}h {(delta.seconds//60)%60}m"
        
        embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="Uptime", value=uptime, inline=True)
        embed.add_field(name="Commands", value=str(len(self.bot.commands)), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(BaseCog(bot)) 