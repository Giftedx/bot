import logging
import asyncio
from logging.handlers import RotatingFileHandler
from src.bot.discord.core.bot import Bot
from src.core.di_container import Container
from dependency_injector.wiring import inject, Provide

# Setup logging
logger = logging.getLogger('DiscordBot')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'logs/discord_bot.log',
    maxBytes=5_000_000,
    backupCount=5,
    encoding='utf-8'
)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

@inject
async def main(bot: Bot = Provide[Container.bot]) -> None:
    #Start bot

    try:
        await bot.start(bot.config["DISCORD_BOT_TOKEN"])

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=e)

if __name__ == "__main__":
    container = Container()
    container.init_resources()
    container.wire(modules=[__name__])

    asyncio.run(main())
