"""Custom command management for servers."""

import discord
from discord.ext import commands
import json
import os
from typing import Dict, Optional
import asyncio

class CustomCommands(commands.Cog):
    """Manage custom commands for the server."""
    
    def __init__(self, bot):
        self.bot = bot
        self.commands_file = "data/custom_commands.json"
        self.commands: Dict[str, Dict[str, Dict[str, str]]] = {}  # guild_id -> command_name -> command_data
        self.load_commands()
        
    def load_commands(self):
        """Load custom commands from file."""
        os.makedirs("data", exist_ok=True)
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r') as f:
                    self.commands = json.load(f)
        except Exception as e:
            print(f"Error loading custom commands: {e}")
            self.commands = {}
    
    def save_commands(self):
        """Save custom commands to file."""
        try:
            with open(self.commands_file, 'w') as f:
                json.dump(self.commands, f, indent=4)
        except Exception as e:
            print(f"Error saving custom commands: {e}")
    
    @commands.group(name="custom", invoke_without_command=True)
    async def custom(self, ctx):
        """Manage custom commands. Use subcommands add/remove/list."""
        await ctx.send_help(ctx.command)
    
    @custom.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def add_command(self, ctx, name: str, *, response: str):
        """Add a custom command."""
        guild_id = str(ctx.guild.id)
        name = name.lower()
        
        # Check if command already exists
        if guild_id in self.commands and name in self.commands[guild_id]:
            await ctx.send(f"Command `{name}` already exists! Use `custom edit` to modify it.")
            return
            
        # Check for command name conflicts
        if self.bot.get_command(name):
            await ctx.send(f"Cannot create command `{name}` as it conflicts with a built-in command.")
            return
            
        # Add command
        if guild_id not in self.commands:
            self.commands[guild_id] = {}
            
        self.commands[guild_id][name] = {
            "response": response,
            "creator": str(ctx.author.id),
            "created_at": ctx.message.created_at.isoformat()
        }
        
        self.save_commands()
        await ctx.send(f"Added custom command `{name}`!")
    
    @custom.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def remove_command(self, ctx, name: str):
        """Remove a custom command."""
        guild_id = str(ctx.guild.id)
        name = name.lower()
        
        if (guild_id not in self.commands or 
            name not in self.commands[guild_id]):
            await ctx.send(f"Command `{name}` doesn't exist!")
            return
            
        del self.commands[guild_id][name]
        if not self.commands[guild_id]:  # If guild has no more commands
            del self.commands[guild_id]
            
        self.save_commands()
        await ctx.send(f"Removed custom command `{name}`!")
    
    @custom.command(name="edit")
    @commands.has_permissions(manage_guild=True)
    async def edit_command(self, ctx, name: str, *, new_response: str):
        """Edit an existing custom command."""
        guild_id = str(ctx.guild.id)
        name = name.lower()
        
        if (guild_id not in self.commands or 
            name not in self.commands[guild_id]):
            await ctx.send(f"Command `{name}` doesn't exist!")
            return
            
        self.commands[guild_id][name]["response"] = new_response
        self.save_commands()
        await ctx.send(f"Updated custom command `{name}`!")
    
    @custom.command(name="list")
    async def list_commands(self, ctx):
        """List all custom commands for this server."""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.commands or not self.commands[guild_id]:
            await ctx.send("No custom commands set up for this server!")
            return
            
        # Create embed
        embed = discord.Embed(
            title="Custom Commands",
            description="Here are all custom commands for this server:",
            color=discord.Color.blue()
        )
        
        for name, data in self.commands[guild_id].items():
            creator = ctx.guild.get_member(int(data["creator"]))
            creator_name = creator.name if creator else "Unknown"
            
            embed.add_field(
                name=name,
                value=f"Created by: {creator_name}\nResponse: {data['response'][:100]}{'...' if len(data['response']) > 100 else ''}",
                inline=False
            )
            
        await ctx.send(embed=embed)
    
    @custom.command(name="info")
    async def command_info(self, ctx, name: str):
        """Get detailed information about a custom command."""
        guild_id = str(ctx.guild.id)
        name = name.lower()
        
        if (guild_id not in self.commands or 
            name not in self.commands[guild_id]):
            await ctx.send(f"Command `{name}` doesn't exist!")
            return
            
        data = self.commands[guild_id][name]
        creator = ctx.guild.get_member(int(data["creator"]))
        
        embed = discord.Embed(
            title=f"Command: {name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Response", value=data["response"], inline=False)
        embed.add_field(
            name="Creator",
            value=creator.mention if creator else "Unknown",
            inline=True
        )
        embed.add_field(
            name="Created At",
            value=data["created_at"],
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle custom commands in messages."""
        if message.author.bot or not message.guild:
            return
            
        guild_id = str(message.guild.id)
        if guild_id not in self.commands:
            return
            
        # Check if message starts with server's command prefix
        ctx = await self.bot.get_context(message)
        if not ctx.prefix:
            return
            
        # Get command name without prefix
        cmd_name = message.content[len(ctx.prefix):].split()[0].lower()
        
        if cmd_name in self.commands[guild_id]:
            await message.channel.send(self.commands[guild_id][cmd_name]["response"])

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(CustomCommands(bot)) 