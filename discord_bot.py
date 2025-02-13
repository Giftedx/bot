import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
import asyncio
from plexapi.server import PlexServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        extensions = [
            'cogs.fun_commands',
            'cogs.plex_commands',
            'cogs.pet_commands',
            'cogs.shop_commands',
            'cogs.quest_commands'
        ]
        for ext in extensions:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.text_channel = None

    async def setup_hook(self):
        """Initialize bot and load extensions"""
        logger.info("Loading extensions...")
        for ext in ['cogs.fun_commands', 'cogs.plex_commands']:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.text_channel = self.get_channel(TEXT_CHANNEL_ID)
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(TOKEN)
```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/discord_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')