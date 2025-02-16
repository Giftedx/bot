"""Base cog class that all other cogs will inherit from."""

from discord.ext import commands
import discord
import logging
from typing import Optional, Any
from discord_bot.config import Config

class BaseCog(commands.Cog):
    """Base cog class with common functionality."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)
        
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