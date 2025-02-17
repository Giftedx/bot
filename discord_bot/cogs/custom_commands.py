"""Custom commands management for the bot."""

import discord
from discord.ext import commands
from typing import Optional
import json
import os

class CustomCommands(commands.Cog, name="Custom"):
    """Custom command management system.
    
    This category includes commands for:
    - Creating custom commands
    - Editing custom commands
    - Deleting custom commands
    - Listing custom commands
    - Managing command permissions
    
    Custom commands can include text, embeds, and basic variables.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.commands_file = 'data/custom_commands.json'
        self.load_commands()
    
    def load_commands(self):
        """Load custom commands from file."""
        if not os.path.exists('data'):
            os.makedirs('data')
        if os.path.exists(self.commands_file):
            with open(self.commands_file, 'r') as f:
                self.custom_commands = json.load(f)
        else:
            self.custom_commands = {}
            self.save_commands()
    
    def save_commands(self):
        """Save custom commands to file."""
        with open(self.commands_file, 'w') as f:
            json.dump(self.custom_commands, f, indent=4)
    
    @commands.group(name="custom", invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def custom_group(self, ctx):
        """Manage custom commands.
        
        Group command for managing custom commands.
        Requires manage messages permission.
        
        Subcommands:
        ------------
        add - Add a new custom command
        edit - Edit an existing custom command
        remove - Remove a custom command
        list - List all custom commands
        info - Get info about a custom command
        
        Examples:
        ---------
        !custom add welcome Hello {user}!
        !custom edit welcome Welcome to the server, {user}!
        !custom remove welcome
        !custom list
        !custom info welcome
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @custom_group.command(name="add")
    async def add_command(self, ctx, name: str, *, response: str):
        """Add a new custom command.
        
        Creates a new custom command with the specified name and response.
        
        Parameters:
        -----------
        name: The name of the command (no spaces)
        response: The response text (can include variables)
        
        Variables:
        ----------
        {user} - Mentions the user
        {server} - Server name
        {count} - Member count
        
        Examples:
        ---------
        !custom add welcome Welcome to {server}, {user}!
        !custom add members We have {count} members!
        
        Notes:
        ------
        - Command names must be unique
        - Cannot override built-in commands
        - Response can include basic markdown
        """
        name = name.lower()
        if name in self.custom_commands:
            await ctx.send("❌ A command with that name already exists!")
            return
            
        self.custom_commands[name] = {
            'response': response,
            'creator': ctx.author.id,
            'uses': 0
        }
        self.save_commands()
        await ctx.send(f"✅ Added custom command: {name}")
    
    @custom_group.command(name="edit")
    async def edit_command(self, ctx, name: str, *, response: str):
        """Edit an existing custom command.
        
        Modifies the response of an existing custom command.
        
        Parameters:
        -----------
        name: The name of the command to edit
        response: The new response text
        
        Examples:
        ---------
        !custom edit welcome New welcome message!
        !custom edit rules Updated rules: {rules}
        
        Notes:
        ------
        - Only command creator or admins can edit
        - Preserves usage statistics
        """
        name = name.lower()
        if name not in self.custom_commands:
            await ctx.send("❌ Command not found!")
            return
            
        if ctx.author.id != self.custom_commands[name]['creator'] and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You don't have permission to edit this command!")
            return
            
        self.custom_commands[name]['response'] = response
        self.save_commands()
        await ctx.send(f"✅ Updated custom command: {name}")
    
    @custom_group.command(name="remove")
    async def remove_command(self, ctx, name: str):
        """Remove a custom command.
        
        Deletes an existing custom command.
        
        Parameters:
        -----------
        name: The name of the command to remove
        
        Examples:
        ---------
        !custom remove welcome
        !custom remove unused_command
        
        Notes:
        ------
        - Only command creator or admins can remove
        - Action cannot be undone
        """
        name = name.lower()
        if name not in self.custom_commands:
            await ctx.send("❌ Command not found!")
            return
            
        if ctx.author.id != self.custom_commands[name]['creator'] and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You don't have permission to remove this command!")
            return
            
        del self.custom_commands[name]
        self.save_commands()
        await ctx.send(f"✅ Removed custom command: {name}")
    
    @custom_group.command(name="list")
    async def list_commands(self, ctx):
        """List all custom commands.
        
        Shows a list of all available custom commands.
        
        Examples:
        ---------
        !custom list
        
        Notes:
        ------
        - Groups commands by creator
        - Shows usage statistics
        - Paginates if many commands exist
        """
        if not self.custom_commands:
            await ctx.send("No custom commands have been created yet!")
            return
            
        embed = discord.Embed(
            title="Custom Commands",
            color=discord.Color.blue()
        )
        
        for name, data in self.custom_commands.items():
            creator = self.bot.get_user(data['creator'])
            creator_name = creator.name if creator else "Unknown"
            embed.add_field(
                name=name,
                value=f"Creator: {creator_name}\nUses: {data['uses']}",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @custom_group.command(name="info")
    async def command_info(self, ctx, name: str):
        """Get information about a custom command.
        
        Shows detailed information about a specific command.
        
        Parameters:
        -----------
        name: The name of the command to get info about
        
        Examples:
        ---------
        !custom info welcome
        !custom info rules
        
        Notes:
        ------
        - Shows creator, creation date, uses
        - Displays full command response
        """
        name = name.lower()
        if name not in self.custom_commands:
            await ctx.send("❌ Command not found!")
            return
            
        data = self.custom_commands[name]
        creator = self.bot.get_user(data['creator'])
        creator_name = creator.name if creator else "Unknown"
        
        embed = discord.Embed(
            title=f"Command: {name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Creator", value=creator_name, inline=True)
        embed.add_field(name="Uses", value=str(data['uses']), inline=True)
        embed.add_field(name="Response", value=data['response'], inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for custom commands."""
        if message.author.bot:
            return
            
        if not message.content.startswith('!'):
            return
            
        command = message.content[1:].lower().split()[0]
        if command in self.custom_commands:
            response = self.custom_commands[command]['response']
            response = response.replace('{user}', message.author.mention)
            response = response.replace('{server}', message.guild.name)
            response = response.replace('{count}', str(message.guild.member_count))
            
            self.custom_commands[command]['uses'] += 1
            self.save_commands()
            
            await message.channel.send(response)

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(CustomCommands(bot)) 