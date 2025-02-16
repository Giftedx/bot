"""Custom help command implementation."""
import discord
from discord.ext import commands


class HelpCommands(commands.Cog):
    """Help command system."""
    
    def __init__(self, bot):
        self.bot = bot
        # Remove default help command
        bot.remove_command('help')
    
    @commands.command()
    async def help(self, ctx, command: str = None):
        """Show help for all commands or a specific command."""
        if command is None:
            # Show general help
            embed = discord.Embed(
                title="OSRS Bot Commands",
                description="Use `!help <command>` for more details about a command.",
                color=discord.Color.blue()
            )
            
            # Group commands by cog
            for cog_name, cog in self.bot.cogs.items():
                # Skip help commands in the main list
                if cog_name == "HelpCommands":
                    continue
                    
                # Get commands for this cog
                cog_commands = [cmd for cmd in cog.get_commands() if not cmd.hidden]
                if not cog_commands:
                    continue
                
                # Add field for this category
                command_list = "\n".join(
                    f"`!{cmd.name}` - {cmd.short_doc or 'No description'}"
                    for cmd in cog_commands
                )
                embed.add_field(
                    name=cog_name.replace("Commands", ""),
                    value=command_list,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        else:
            # Show help for specific command
            cmd = self.bot.get_command(command)
            if not cmd:
                return await ctx.send(f"Command `{command}` not found.")
            
            embed = discord.Embed(
                title=f"Help: !{cmd.name}",
                description=cmd.help or "No description available.",
                color=discord.Color.blue()
            )
            
            # Add usage if available
            if cmd.usage:
                embed.add_field(name="Usage", value=cmd.usage, inline=False)
            
            # Add aliases if any
            if cmd.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join(f"`!{alias}`" for alias in cmd.aliases),
                    inline=False
                )
            
            # Add subcommands if any
            if isinstance(cmd, commands.Group):
                subcommands = "\n".join(
                    f"`!{cmd.name} {subcmd.name}` - {subcmd.short_doc or 'No description'}"
                    for subcmd in cmd.commands
                )
                if subcommands:
                    embed.add_field(
                        name="Subcommands",
                        value=subcommands,
                        inline=False
                    )
            
            await ctx.send(embed=embed)


async def setup(bot):
    """Set up the help commands cog."""
    await bot.add_cog(HelpCommands(bot)) 