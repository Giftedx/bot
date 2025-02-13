import discord
import logging
from src.core.config import Settings
from src.bot.discord_bot import MediaBot
from src.bot.discord_selfbot import SelfBot
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
settings = Settings()
bot_type = settings.get_setting_str("BOT_TYPE", default="regular")

if bot_type == "regular":
    bot = MediaBot(settings=settings,
                   command_prefix=settings.COMMAND_PREFIX,
                   intents=intents)
    logger.info("Starting in regular bot mode")
elif bot_type == "selfbot":
    bot = SelfBot(settings=settings,
                  command_prefix=settings.COMMAND_PREFIX,
                  intents=intents)
    logger.info("Starting in selfbot mode.")
else:
    logger.error(f"Invalid BOT_TYPE: {bot_type}. "
                 "Must be 'regular' or 'selfbot'.")
    sys.exit(1)


@bot.event
async def on_ready() -> None:
    logger.info(f"Logged in as {bot.user}")


if __name__ == "__main__":
    discord_token = settings.get_setting_str("DISCORD_TOKEN")
    if discord_token:
        bot.run(discord_token)
    else:
        logger.error("DISCORD_TOKEN is not set.")
        sys.exit(1)
