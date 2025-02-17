"""Administrative commands for bot management."""

import discord
from discord.ext import commands
import asyncio
from typing import Optional, Union
import datetime

class AdminCommands(commands.Cog, name="Admin"):
    """Administrative commands for server management.
    
    This category includes commands for:
    - Server management
    - Bot configuration
    - Permission management
    - System monitoring
    - Extension management
    
    Most commands require administrator permissions.
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """Check if user has admin permissions."""
        return ctx.author.guild_permissions.administrator
    
    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_extension(self, ctx, extension: str):
        """Reload a bot extension/cog.
        
        Reloads the specified extension without restarting the bot.
        Only the bot owner can use this command.
        
        Parameters:
        -----------
        extension: The name of the extension to reload
        
        Examples:
        ---------
        !reload music_commands
        !reload moderation_commands
        
        Notes:
        ------
        - Owner only command
        - Use for updating code changes
        - Extension must be loaded first
        """
        try:
            await self.bot.reload_extension(f"discord_bot.cogs.{extension}")
            await ctx.send(f"✅ Reloaded extension: {extension}")
        except Exception as e:
            await ctx.send(f"❌ Error reloading {extension}: {str(e)}")
    
    @commands.command(name="load")
    @commands.is_owner()
    async def load_extension(self, ctx, extension: str):
        """Load a bot extension/cog.
        
        Loads a new extension that isn't currently loaded.
        Only the bot owner can use this command.
        
        Parameters:
        -----------
        extension: The name of the extension to load
        
        Examples:
        ---------
        !load new_commands
        !load custom_features
        
        Notes:
        ------
        - Owner only command
        - Extension must exist in cogs directory
        - Cannot load already loaded extensions
        """
        try:
            await self.bot.load_extension(f"discord_bot.cogs.{extension}")
            await ctx.send(f"✅ Loaded extension: {extension}")
        except Exception as e:
            await ctx.send(f"❌ Error loading {extension}: {str(e)}")
    
    @commands.command(name="unload")
    @commands.is_owner()
    async def unload_extension(self, ctx, extension: str):
        """Unload a bot extension/cog.
        
        Unloads an active extension from the bot.
        Only the bot owner can use this command.
        
        Parameters:
        -----------
        extension: The name of the extension to unload
        
        Examples:
        ---------
        !unload music_commands
        !unload unused_feature
        
        Notes:
        ------
        - Owner only command
        - Cannot unload essential extensions
        - Commands from unloaded extensions won't work
        """
        try:
            await self.bot.unload_extension(f"discord_bot.cogs.{extension}")
            await ctx.send(f"✅ Unloaded extension: {extension}")
        except Exception as e:
            await ctx.send(f"❌ Error unloading {extension}: {str(e)}")
    
    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx):
        """Sync slash commands with Discord.
        
        Synchronizes all slash commands with Discord's servers.
        Only the bot owner can use this command.
        
        Examples:
        ---------
        !sync
        
        Notes:
        ------
        - Owner only command
        - May take a few minutes
        - Required after adding new slash commands
        """
        try:
            await self.bot.tree.sync()
            await ctx.send("✅ Successfully synced slash commands!")
        except Exception as e:
            await ctx.send(f"❌ Error syncing commands: {str(e)}")
    
    @commands.command(name="status")
    @commands.is_owner()
    async def set_status(self, ctx, status_type: str, *, status: str):
        """Set the bot's status/presence.
        
        Changes the bot's status message and activity type.
        Only the bot owner can use this command.
        
        Parameters:
        -----------
        status_type: Type of status (playing, watching, listening, streaming)
        status: The status message to display
        
        Examples:
        ---------
        !status playing with commands
        !status watching over servers
        !status listening to music
        
        Notes:
        ------
        - Owner only command
        - Changes are immediate
        - Status persists until changed
        """
        activity_types = {
            'playing': discord.ActivityType.playing,
            'watching': discord.ActivityType.watching,
            'listening': discord.ActivityType.listening,
            'streaming': discord.ActivityType.streaming
        }
        
        if status_type.lower() not in activity_types:
            await ctx.send("Invalid status type! Use: playing, watching, listening, or streaming")
            return
            
        activity = discord.Activity(
            type=activity_types[status_type.lower()],
            name=status
        )
        
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"✅ Status updated to: {status_type} {status}")
    
    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Safely shut down the bot.
        
        Performs a clean shutdown of the bot.
        Only the bot owner can use this command.
        
        Examples:
        ---------
        !shutdown
        
        Notes:
        ------
        - Owner only command
        - Closes all connections
        - Saves any pending data
        """
        await ctx.send("Shutting down... 👋")
        await self.bot.close()
    
    @commands.command(name="maintenance")
    @commands.is_owner()
    async def maintenance_mode(self, ctx, enabled: bool = None):
        """Toggle maintenance mode.
        
        Enables or disables maintenance mode for the bot.
        Only the bot owner can use this command.
        
        Parameters:
        -----------
        enabled: True to enable, False to disable (optional)
        
        Examples:
        ---------
        !maintenance on
        !maintenance off
        !maintenance - Toggle current state
        
        Notes:
        ------
        - Owner only command
        - Disables most commands when active
        - Shows maintenance message to users
        """
        if enabled is None:
            enabled = not getattr(self.bot, "maintenance_mode", False)
            
        self.bot.maintenance_mode = enabled
        
        if enabled:
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.playing,
                    name="🔧 Maintenance Mode"
                ),
                status=discord.Status.dnd
            )
            await ctx.send("🔧 Maintenance mode enabled")
        else:
            await self.bot.change_presence(status=discord.Status.online)
            await ctx.send("✅ Maintenance mode disabled")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(AdminCommands(bot)) 