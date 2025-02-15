from discord.ext import commands
import discord
from typing import Optional, Union
import asyncio
import yaml
import json

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = {}

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        """Server configuration commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @config.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, new_prefix: str):
        """Change the bot's prefix for this server"""
        if len(new_prefix) > 5:
            return await ctx.send("Prefix must be 5 characters or less!")
        
        try:
            await self.bot.db.execute(
                'INSERT INTO guild_settings (guild_id, prefix) VALUES ($1, $2) '
                'ON CONFLICT (guild_id) DO UPDATE SET prefix = $2',
                ctx.guild.id, new_prefix
            )
            await ctx.send(f"Prefix changed to: `{new_prefix}`")
        except Exception as e:
            await ctx.send(f"Error changing prefix: {e}")

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def cmd(self, ctx):
        """Custom command management"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @cmd.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add_command(self, ctx, name: str, *, response: str):
        """Add a custom command"""
        try:
            await self.bot.db.execute(
                'INSERT INTO custom_commands (guild_id, name, response) VALUES ($1, $2, $3) '
                'ON CONFLICT (guild_id, name) DO UPDATE SET response = $3',
                ctx.guild.id, name.lower(), response
            )
            await ctx.send(f"Added custom command: `{name}`")
        except Exception as e:
            await ctx.send(f"Error adding command: {e}")

    @cmd.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_command(self, ctx, name: str):
        """Remove a custom command"""
        try:
            result = await self.bot.db.execute(
                'DELETE FROM custom_commands WHERE guild_id = $1 AND name = $2',
                ctx.guild.id, name.lower()
            )
            if result == 'DELETE 0':
                await ctx.send("Command not found!")
            else:
                await ctx.send(f"Removed command: `{name}`")
        except Exception as e:
            await ctx.send(f"Error removing command: {e}")

    @cmd.command(name="list")
    async def list_commands(self, ctx):
        """List all custom commands"""
        try:
            commands = await self.bot.db.fetch(
                'SELECT name, response FROM custom_commands WHERE guild_id = $1',
                ctx.guild.id
            )
            if not commands:
                return await ctx.send("No custom commands found!")

            # Create paginated embed
            commands_per_page = 10
            pages = []
            
            for i in range(0, len(commands), commands_per_page):
                page_commands = commands[i:i + commands_per_page]
                embed = discord.Embed(
                    title="Custom Commands",
                    color=discord.Color.blue()
                )
                for cmd in page_commands:
                    embed.add_field(
                        name=cmd['name'],
                        value=f"{cmd['response'][:100]}...",
                        inline=False
                    )
                pages.append(embed)

            if len(pages) == 1:
                await ctx.send(embed=pages[0])
            else:
                current_page = 0
                message = await ctx.send(embed=pages[current_page])

                # Add reactions for navigation
                await message.add_reaction("◀️")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

                while True:
                    try:
                        reaction, user = await self.bot.wait_for(
                            "reaction_add",
                            timeout=60.0,
                            check=check
                        )

                        if str(reaction.emoji) == "▶️":
                            current_page = (current_page + 1) % len(pages)
                        elif str(reaction.emoji) == "◀️":
                            current_page = (current_page - 1) % len(pages)

                        await message.edit(embed=pages[current_page])
                        await message.remove_reaction(reaction, user)

                    except asyncio.TimeoutError:
                        break

        except Exception as e:
            await ctx.send(f"Error listing commands: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx, channel: discord.TextChannel = None, *, message: str = None):
        """Set up welcome message"""
        if channel is None or message is None:
            current = await self.bot.db.fetchrow(
                'SELECT channel_id, message FROM welcome_settings WHERE guild_id = $1',
                ctx.guild.id
            )
            if current:
                channel = ctx.guild.get_channel(current['channel_id'])
                return await ctx.send(
                    f"Current welcome:\nChannel: {channel.mention}\n"
                    f"Message: {current['message']}\n\n"
                    "Use `!welcome #channel message` to change"
                )
            else:
                return await ctx.send(
                    "No welcome message set!\n"
                    "Use `!welcome #channel message` to set one\n"
                    "Available variables: {user}, {server}, {count}"
                )

        try:
            await self.bot.db.execute(
                'INSERT INTO welcome_settings (guild_id, channel_id, message) '
                'VALUES ($1, $2, $3) ON CONFLICT (guild_id) '
                'DO UPDATE SET channel_id = $2, message = $3',
                ctx.guild.id, channel.id, message
            )
            await ctx.send(
                f"Welcome message set!\nChannel: {channel.mention}\n"
                f"Message: {message}"
            )
        except Exception as e:
            await ctx.send(f"Error setting welcome message: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx, role: discord.Role = None):
        """Set up automatic role for new members"""
        if role is None:
            current = await self.bot.db.fetchrow(
                'SELECT role_id FROM autorole WHERE guild_id = $1',
                ctx.guild.id
            )
            if current:
                role = ctx.guild.get_role(current['role_id'])
                return await ctx.send(f"Current autorole: {role.mention}")
            else:
                return await ctx.send("No autorole set! Use `!autorole @role` to set one")

        try:
            await self.bot.db.execute(
                'INSERT INTO autorole (guild_id, role_id) VALUES ($1, $2) '
                'ON CONFLICT (guild_id) DO UPDATE SET role_id = $2',
                ctx.guild.id, role.id
            )
            await ctx.send(f"Autorole set to: {role.mention}")
        except Exception as e:
            await ctx.send(f"Error setting autorole: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx):
        """Create a backup of server settings"""
        backup_data = {
            'guild_id': ctx.guild.id,
            'guild_name': ctx.guild.name,
            'timestamp': ctx.message.created_at.isoformat(),
            'settings': {}
        }

        try:
            # Get custom commands
            commands = await self.bot.db.fetch(
                'SELECT name, response FROM custom_commands WHERE guild_id = $1',
                ctx.guild.id
            )
            backup_data['settings']['custom_commands'] = [
                {'name': cmd['name'], 'response': cmd['response']}
                for cmd in commands
            ]

            # Get welcome settings
            welcome = await self.bot.db.fetchrow(
                'SELECT channel_id, message FROM welcome_settings WHERE guild_id = $1',
                ctx.guild.id
            )
            if welcome:
                backup_data['settings']['welcome'] = {
                    'channel_id': welcome['channel_id'],
                    'message': welcome['message']
                }

            # Get autorole
            autorole = await self.bot.db.fetchrow(
                'SELECT role_id FROM autorole WHERE guild_id = $1',
                ctx.guild.id
            )
            if autorole:
                backup_data['settings']['autorole'] = autorole['role_id']

            # Save to file
            filename = f"backup_{ctx.guild.id}_{ctx.message.created_at.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(backup_data, f, indent=2)

            await ctx.send("Backup created!", file=discord.File(filename))

        except Exception as e:
            await ctx.send(f"Error creating backup: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def restore(self, ctx):
        """Restore server settings from a backup"""
        if not ctx.message.attachments:
            return await ctx.send("Please attach a backup file!")

        try:
            attachment = ctx.message.attachments[0]
            if not attachment.filename.endswith('.json'):
                return await ctx.send("Please provide a valid backup file!")

            backup_content = await attachment.read()
            backup_data = json.loads(backup_content)

            if backup_data['guild_id'] != ctx.guild.id:
                return await ctx.send("This backup is for a different server!")

            # Restore custom commands
            for cmd in backup_data['settings'].get('custom_commands', []):
                await self.bot.db.execute(
                    'INSERT INTO custom_commands (guild_id, name, response) '
                    'VALUES ($1, $2, $3) ON CONFLICT (guild_id, name) '
                    'DO UPDATE SET response = $3',
                    ctx.guild.id, cmd['name'], cmd['response']
                )

            # Restore welcome settings
            if 'welcome' in backup_data['settings']:
                welcome = backup_data['settings']['welcome']
                await self.bot.db.execute(
                    'INSERT INTO welcome_settings (guild_id, channel_id, message) '
                    'VALUES ($1, $2, $3) ON CONFLICT (guild_id) '
                    'DO UPDATE SET channel_id = $2, message = $3',
                    ctx.guild.id, welcome['channel_id'], welcome['message']
                )

            # Restore autorole
            if 'autorole' in backup_data['settings']:
                await self.bot.db.execute(
                    'INSERT INTO autorole (guild_id, role_id) VALUES ($1, $2) '
                    'ON CONFLICT (guild_id) DO UPDATE SET role_id = $2',
                    ctx.guild.id, backup_data['settings']['autorole']
                )

            await ctx.send("Settings restored successfully!")

        except Exception as e:
            await ctx.send(f"Error restoring backup: {e}")

async def setup(bot):
    await bot.add_cog(Admin(bot)) 