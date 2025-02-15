from discord.ext import commands
import discord
from typing import Optional

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def admin(self, ctx):
        """Admin command group"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @admin.command()
    @commands.has_permissions(administrator=True)
    async def createcmd(self, ctx, name: str, *, response: str):
        """Create a custom command"""
        try:
            await self.bot.db.execute(
                '''INSERT INTO custom_commands (name, response, creator_id)
                   VALUES ($1, $2, $3)
                   ON CONFLICT (name) DO UPDATE
                   SET response = $2, creator_id = $3''',
                name.lower(), response, ctx.author.id
            )
            await ctx.send(f"Command `{name}` created/updated successfully!")
        except Exception as e:
            await ctx.send(f"Error creating command: {e}")

    @admin.command()
    @commands.has_permissions(administrator=True)
    async def deletecmd(self, ctx, name: str):
        """Delete a custom command"""
        try:
            result = await self.bot.db.execute(
                'DELETE FROM custom_commands WHERE name = $1',
                name.lower()
            )
            if result == 'DELETE 0':
                await ctx.send(f"Command `{name}` not found.")
            else:
                await ctx.send(f"Command `{name}` deleted successfully!")
        except Exception as e:
            await ctx.send(f"Error deleting command: {e}")

    @admin.command()
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, extension: str):
        """Reload a bot extension"""
        try:
            await self.bot.reload_extension(f"cogs.{extension}")
            await ctx.send(f"Extension `{extension}` reloaded successfully!")
        except Exception as e:
            await ctx.send(f"Error reloading extension: {e}")

    @admin.command()
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, new_prefix: str):
        """Change the bot's command prefix"""
        self.bot.command_prefix = new_prefix
        await ctx.send(f"Command prefix changed to `{new_prefix}`")

    @admin.command()
    @commands.has_permissions(administrator=True)
    async def cleanup(self, ctx, limit: int = 100):
        """Clean up bot messages"""
        def is_bot(m):
            return m.author == self.bot.user

        try:
            deleted = await ctx.channel.purge(limit=limit, check=is_bot)
            await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
        except Exception as e:
            await ctx.send(f"Error cleaning up messages: {e}")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot)) 