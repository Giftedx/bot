import discord
from discord.ext import commands
import asyncio
from typing import Optional

from src.core.game_client import GameClient
# from src.core.config import Config # Removed Config import
from src.core.config import ConfigManager # Added ConfigManager import

class OSRSBot(commands.Bot):
    """Discord bot for OSRS game integration"""
    
    # def __init__(self, config: Config): # Old __init__
    def __init__(self): # New __init__
        self.config_manager = ConfigManager(config_dir="config") # Instantiated ConfigManager

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=self.config_manager.get('osrs_bot.command_prefix', '!'), # Example, adjust key if needed
            intents=intents,
            description=self.config_manager.get('osrs_bot.description', "OSRS Discord Game") # Example
        )
        
        # Assuming GameClient will be refactored to accept ConfigManager
        # or specific values fetched from it.
        self.game_client = GameClient(self.config_manager) # Passing ConfigManager to GameClient
        self.display_channels = {}
        
    async def setup_hook(self):
        """Set up bot and load extensions"""
        # Add commands
        self.add_command(self.register)
        self.add_command(self.display)
        self.add_command(self.train)
        self.add_command(self.stats)
        self.add_command(self.inventory)
        self.add_command(self.bank)
        
    @commands.command()
    async def register(self, ctx):
        """Register as a new player"""
        player = await self.game_client.register_player(
            str(ctx.author.id),
            ctx.author.name
        )
        await ctx.send(f"Welcome to OSRS, {player.username}! Type !help to see available commands.")
        
    @commands.command()
    async def display(self, ctx, mode: str = "text"):
        """Set display mode (text/graphical)"""
        try:
            await self.game_client.set_display_mode(str(ctx.author.id), mode)
            self.display_channels[str(ctx.author.id)] = ctx.channel.id
            
            if mode == "graphical":
                # Create initial iframe display
                display = self.game_client.displays[str(ctx.author.id)]
                await ctx.send(
                    content="Game Display (updates every second):",
                    embed=discord.Embed(description=display.get_iframe_html())
                )
            else:
                await ctx.send(f"Display mode set to {mode}")
                
        except ValueError as e:
            await ctx.send(str(e))
            
    @commands.command()
    async def train(self, ctx, skill: str):
        """Train a skill"""
        response = await self.game_client.process_command(
            str(ctx.author.id),
            "train",
            [skill]
        )
        await ctx.send(response)
        await self._update_display(ctx.author.id)
        
    @commands.command()
    async def stats(self, ctx):
        """View your stats"""
        response = await self.game_client.process_command(
            str(ctx.author.id),
            "stats",
            []
        )
        await ctx.send(response)
        
    @commands.command()
    async def inventory(self, ctx):
        """View your inventory"""
        response = await self.game_client.process_command(
            str(ctx.author.id),
            "inventory",
            []
        )
        await ctx.send(response)
        
    @commands.command()
    async def bank(self, ctx):
        """View your bank"""
        response = await self.game_client.process_command(
            str(ctx.author.id),
            "bank",
            []
        )
        await ctx.send(response)
        
    async def _update_display(self, user_id: int):
        """Update player's game display"""
        str_id = str(user_id)
        if str_id not in self.display_channels:
            return
            
        channel_id = self.display_channels[str_id]
        channel = self.get_channel(channel_id)
        if not channel:
            return
            
        await self.game_client.update_display(str_id)
        display = self.game_client.displays[str_id]
        
        if display.state.mode == "graphical":
            # Update iframe
            await channel.send(
                content="Game Display Updated:",
                embed=discord.Embed(description=display.get_iframe_html())
            )
        else:
            # Update text
            data = display.get_display_data()
            await channel.send(data["content"])
            
    async def start_display_updates(self):
        """Start background task to update displays"""
        while True:
            for user_id in self.display_channels:
                await self._update_display(int(user_id))
            await asyncio.sleep(1)  # Update every second

    async def start(self, *args, **kwargs): # New start method
        """Start the bot, fetching the token from ConfigManager."""
        discord_token = self.config_manager.get('discord.token')
        if not discord_token:
            # Consider logging an error or raising an exception
            print("Error: Discord token not found in configuration for OSRSBot.")
            return

        # Re-add the token to kwargs if it was there, or add it if it wasn't
        # The base class start method expects the token as the first argument.
        # args = (discord_token,) + args # This might be problematic if token is also in kwargs

        # Check if 'token' is already a kwarg. If so, this is complex.
        # The simplest is to assume super().start() takes token as first arg, and others as kwargs.
        await super().start(discord_token, *args, **kwargs)