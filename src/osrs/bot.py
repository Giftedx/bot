import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Create bot instance
bot = commands.Bot(command_prefix="!osrs ", intents=discord.Intents.all())


@bot.event
async def on_ready():
    """When the bot is ready"""
    print(f"{bot.user} has connected to Discord!")
    print("Connected to the following guilds:")
    for guild in bot.guilds:
        print(f"- {guild.name} (id: {guild.id})")


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. Please check the command usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument type. Please check the command usage.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")


@bot.command(name="help")
async def custom_help(ctx):
    """Show custom help message"""
    embed = discord.Embed(
        title="OSRS Bot Commands", description="All commands use the prefix !osrs", color=0x00FF00
    )

    commands_list = {
        "Combat": {
            "combat <attack> <strength> <defence> <ranged> <magic> <hitpoints> <prayer>": "Calculate combat level",
            "maxhit <base_level> <effective_level> <strength_bonus> [void]": "Calculate max hit",
            "accuracy <attack_level> <equipment_bonus> <defence_level> <defence_bonus>": "Calculate hit chance",
            "spec <weapon>": "Show special attack information",
            "potion <potion_name> <base_level>": "Calculate potion boost effects",
        },
        "Equipment": {"equipment <item_name>": "Show detailed equipment stats and requirements"},
        "Skills": {
            "xp <level>": "Calculate XP required for level",
            "agility <course_name>": "Show agility course information",
            "xprate <course_name>": "Calculate agility XP and mark rates",
            "farming [patch_type] [crop_type] [stages]": "Show farming information and growth times",
            "construction [room_type] [portal_dest]": "Show construction room information",
        },
        "Prayer": {
            "prayer <type>": "Show prayer bonuses (types: attack, strength, defence, ranged, magic)"
        },
        "Items": {
            "droprate <base_chance> [ring_of_wealth] [kill_count]": "Calculate drop rates and pet chances"
        },
        "Movement": {
            "runenergy <weight> <agility_level>": "Calculate run energy drain and restore rates"
        },
        "Minigames": {
            "nmz [boss_name] [mode]": "Show NMZ boss information and power-ups",
            "barrows [brother]": "Show Barrows brother information and rewards",
        },
        "Bosses": {
            "gwd [boss] [kc]": "Show GWD boss information and drop rates",
            "zulrah [phase] [dps]": "Show Zulrah phase information and profit calculations",
            "vorkath [dps] [woox_walk]": "Show Vorkath information and profit calculations",
            "cox [boss] [team_size] [points] [personal_points] [challenge_mode]": "Show Chambers of Xeric information",
            "tob [boss] [team_size] [deaths] [completion_time]": "Show Theatre of Blood information",
            "inferno [wave]": "Show Inferno wave information and supply calculations",
        },
        "Slayer": {
            "slayer [master] [task]": "Show Slayer master task information and superior monsters"
        },
        "PvP": {
            "wild [combat_level] [wilderness_level] [skull_type]": "Show Wilderness level ranges and PvP information"
        },
        "Achievement Diaries": {
            "diary [area] [difficulty]": "Show Achievement Diary requirements and rewards"
        },
        "Clue Scrolls": {"clue [type] [step_type]": "Show Clue Scroll information and rewards"},
        "Utility": {"ping": "Check bot latency", "help": "Show this help message"},
    }

    for category, cmds in commands_list.items():
        commands_text = ""
        for cmd, desc in cmds.items():
            commands_text += f"`{cmd}`\n{desc}\n\n"
        embed.add_field(name=category, value=commands_text, inline=False)

    await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latency: {latency}ms")


def main():
    """Main entry point"""
    # Load OSRS commands
    from .discord_commands import setup

    setup(bot)

    # Start the bot
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
