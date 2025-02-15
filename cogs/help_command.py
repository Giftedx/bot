import discord
from discord.ext import commands


class HelpCommand(commands.Cog):
    """Custom help command implementation"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="games")
    async def games_help(self, ctx):
        """Complete Game System Guide"""
        embed = discord.Embed(
            title="🎮 Complete Game Systems Guide",
            description="All games and activities available:",
            color=discord.Color.blue(),
        )

        # Major RPG Systems
        rpg = """**Old School RuneScape (!osrs)**
• Create & develop character
• Train multiple skills
• Explore different worlds
• PvP combat system

**Pokemon (!pokemon)**
• Catch wild Pokemon
• Battle other trainers
• Train & evolve Pokemon
• Type-based combat

**Pets (!pet)**
• Adopt different pets
• Train and play with pets
• Pet battles & skills
• Pet care system"""
        embed.add_field(name="🎯 Major Game Systems", value=rpg, inline=False)

        # Battle Systems
        battles = """**Pet Battles (!pet battle)**
• Turn-based pet combat
• Use pet skills
• Train through battles

**Pokemon Battles (!pokemon battle)**
• Type advantages/weaknesses
• Move sets & abilities
• Team battles

**OSRS Combat (!osrs attack)**
• PvP combat system
• Combat styles
• Equipment bonuses

Use `!battle` for battle guide!"""
        embed.add_field(name="⚔️ Battle Systems", value=battles, inline=False)

        # Mini-Games
        mini = """**Word Games**
• !hangman - Word guessing
• !wordle - Daily puzzle
• !wordchain - Word chain game

**Knowledge Games**
• !trivia - Multi-category quiz
• !quiz - Knowledge test
• !memory - Memory game"""
        embed.add_field(name="🎲 Mini-Games", value=mini, inline=False)

        # Quick Games
        quick = """**Quick Games**
• !rps - Rock Paper Scissors
• !dice - Roll dice
• !flip - Coin flip
• !8ball - Fortune telling"""
        embed.add_field(name="🎲 Quick Games", value=quick, inline=False)

        # Navigation
        nav = """• Use `!help <game>` for specific help
• Use `!battle` for battle guide
• Use `!pet` for pet system help
• Use `!pokemon` or `!osrs` for those systems"""
        embed.add_field(name="📍 Navigation", value=nav, inline=False)

        embed.set_footer(text="Try !help battle for combat system details!")
        await ctx.send(embed=embed)

    @commands.command(name="help")
    async def help(self, ctx: commands.Context, command_name: str = None):
        """Show help about commands"""
        if command_name == "games":
            return await self.games_help(ctx)

        if command_name == "battle":
            embed = discord.Embed(
                title="⚔️ Battle Systems Guide",
                description="Learn about the different battle systems!",
                color=discord.Color.red(),
            )

            pet_battles = """• Pet vs Pet combat
• Use pet skills
• Turn-based battles
• Train through combat

Commands:
`!pet battle @user` - Start battle
`!pet accept` - Accept challenge
`!pet move <skill>` - Use skill"""
            embed.add_field(name="🐾 Pet Battles", value=pet_battles, inline=False)

            pokemon_battles = """• Type advantages matter
• Move sets & abilities
• Status effects
• Team management

Commands:
`!pokemon battle @user` - Battle
`!pokemon accept` - Accept
`!pokemon move <name>` - Use move"""
            embed.add_field(
                name="🌟 Pokemon Battles", value=pokemon_battles, inline=False
            )

            osrs_combat = """• PvP combat system
• Combat styles
• Equipment effects
• Accuracy system

Commands:
`!osrs attack @user` - PvP
`!osrs accept` - Accept
`!osrs style <type>` - Combat style"""
            embed.add_field(name="⚔️ OSRS Combat", value=osrs_combat, inline=False)

            tips = """• Each system has unique mechanics
• Watch status effects
• Strategic moves win battles
• Train between fights"""
            embed.add_field(name="💡 Battle Tips", value=tips, inline=False)

            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="Bot Commands Help",
            description="Here's what I can help you with! Use !help <command> for more details.",
            color=discord.Color.blue(),
        )

        if command_name:
            cmd = self.bot.get_command(command_name)
            if cmd:
                embed.title = f"Help: {cmd.name}"
                embed.description = cmd.help or "No description available."
                return await ctx.send(embed=embed)

        # Main Game Systems
        main_games = """Our main game systems to explore:

`!osrs` - Old School RuneScape
• Character creation & development
• Multiple skills to train
• World exploration system
• Achievement system

`!pokemon` - Pokemon Adventures
• Catch & collect Pokemon
• Battle system with trainers
• Training & evolution system
• Collection management

`!games` - Shows all available games"""
        embed.add_field(name="🎮 Main Game Systems", value=main_games, inline=False)

        # Mini-Games Category
        mini_games = """Word Games:
`!hangman` - Word guessing game
`!wordle` - Daily word puzzle
`!wordchain` - Word association

Knowledge Games:
`!trivia [category]` - Multi-category quiz
`!quiz` - General knowledge test

Quick Games:
`!rps <choice>` - Rock Paper Scissors
`!dice [sides]` - Roll dice
`!flip` - Coin flip
`!8ball <question>` - Ask the magic 8-ball"""
        embed.add_field(name="🎲 Mini-Games", value=mini_games, inline=False)

        # Social & Fun Category
        social = """Social Interactions:
`!hug @user` - Give hugs
`!boop @user` - Boop someone
`!highfive @user` - Give high fives

Fun Commands:
`!ship @user1 @user2` - Check compatibility
`!rate <thing>` - Bot rates things
`!mock <text>` - MoCk TeXt
`!emojify <text>` - Convert to emoji"""
        embed.add_field(name="🤝 Social & Fun", value=social, inline=False)

        # Tips Section
        tips = """• Use `!games` for complete game guide
• Use `!help osrs` for OSRS details
• Use `!help pokemon` for Pokemon details
• Use `!help <command>` for specific help
• Use `!fun` to see social commands"""
        embed.add_field(name="💡 Tips", value=tips, inline=False)

        embed.set_footer(
            text="Type !help <command> for detailed help with any command!"
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
