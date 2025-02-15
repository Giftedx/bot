# OSRS Discord Bot

A Discord bot that simulates Old School RuneScape gameplay, featuring world management, combat, skills, and media playback capabilities.

## Features

- **OSRS Simulation**
  - Character creation and management
  - Combat system
  - Skill progression
  - World hopping
  - Item management

- **Media Features**
  - Voice channel support
  - Music playback
  - Queue management
  - Volume control

## Requirements

- Python 3.8 or higher
- Discord.py 2.3.2 or higher
- Redis server (for caching and rate limiting)
- SQLite (for persistent storage)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/osrs-discord-bot.git
cd osrs-discord-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -e ".[dev]"
```

4. Create a `.env` file with your configuration:
```env
DISCORD_TOKEN=your_discord_token
REDIS_URL=redis://localhost:6379/0
COMMAND_PREFIX=!
```

## Usage

1. Start the bot:
```bash
python -m src.main
```

2. In Discord, use the following commands:
- `!create <name>` - Create a new OSRS character
- `!stats` - View your character's stats
- `!world` - View your current world
- `!worlds` - List available worlds
- `!join <world_id>` - Join a different world
- `!join` - Join a voice channel
- `!play <query>` - Play music
- `!queue` - View music queue
- `!stop` - Stop music playback
- `!leave` - Leave voice channel

## Development

### Running Tests

Run all tests:
```bash
pytest
```

Run specific test categories:
```bash
pytest tests/unit  # Unit tests
pytest tests/integration  # Integration tests
```

Generate coverage report:
```bash
pytest --cov=src --cov-report=html
```

### Code Quality

Format code:
```bash
black src tests
isort src tests
```

Type checking:
```bash
mypy src tests
```

Linting:
```bash
flake8 src tests
```

## Project Structure

```
src/
├── bot/
│   ├── cogs/
│   │   ├── media_commands.py
│   │   └── osrs_commands.py
│   └── core/
│       └── bot.py
├── osrs/
│   ├── core/
│   │   ├── game_math.py
│   │   └── world_manager.py
│   ├── database/
│   │   └── models.py
│   └── models.py
└── main.py

tests/
├── integration/
│   └── test_bot_integration.py
├── unit/
│   ├── test_media_commands.py
│   └── test_osrs_commands.py
└── conftest.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [RuneLite](https://github.com/runelite/runelite) - OSRS client and game data
- [OSRS Wiki](https://oldschool.runescape.wiki/) - Game information and mechanics
