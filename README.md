# Discord Integration Bot

A powerful Discord bot that integrates various services and games, including Plex media playback, Pokemon game data, and more.

## Features

### Plex Integration
- Watch Together: Stream Plex content in Discord voice channels
- Media Controls: Play, pause, seek, and manage playback
- Rich Presence: Show what you're watching in Discord
- Voice Channel Sync: Synchronized playback for group watching

### Game Integrations
- Pokemon ROM Data:
  - Parse and analyze Pokemon games (GB, GBC, GBA)
  - Extract game data (Pokemon, moves, maps, items)
  - Support for multiple Pokemon generations
- OSRS Integration:
  - Item database and Grand Exchange tracking
  - Player stats and hiscores
  - Quest and achievement tracking

### Discord Activities
- Custom Activity Implementation
- Rich Presence Integration
- Voice Channel Activities
- Group Gaming Features

### Data Collection
- Repository Analysis
- API Integration
- Game Data Parsing
- Caching System

## Setup

### Prerequisites
- Python 3.7+
- Redis (optional, for caching)
- FFmpeg (for voice channel streaming)
- Git (for repository scanning)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/discord-integration-bot.git
cd discord-integration-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```env
# Discord
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret

# Plex
PLEX_SERVER_URL=your_plex_server_url
PLEX_TOKEN=your_plex_token

# GitHub/GitLab
GITHUB_TOKEN=your_github_token
GITLAB_TOKEN=your_gitlab_token

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Game Data
POKEMON_GB_ROMS_PATH=path/to/gb/roms
POKEMON_GBC_ROMS_PATH=path/to/gbc/roms
POKEMON_GBA_ROMS_PATH=path/to/gba/roms
```

## Usage

### Starting the Bot
```bash
python src/bot.py
```

### Running Data Collection
```bash
python src/data_collection/run_collection.py
```

### Discord Commands

#### Plex Commands
- `!plex start` - Start a Plex Activity in the current voice channel
- `!plex play <media_id>` - Play specific media
- `!plex pause` - Pause playback
- `!plex resume` - Resume playback
- `!plex stop` - Stop playback
- `!plex seek <timestamp>` - Seek to specific time (e.g., "1:30:00")

#### Pokemon Commands
- `!pokemon info <pokemon>` - Get Pokemon information
- `!pokemon move <move>` - Get move information
- `!pokemon map <location>` - View map data
- `!pokemon item <item>` - Get item information

#### Repository Commands
- `!repo scan` - Scan configured repositories
- `!repo info <repo>` - Get repository information
- `!repo stats` - View repository statistics

## Development

### Project Structure
```
src/
├── bot.py                    # Main bot file
├── data_collection/         # Data collection system
│   ├── config.py           # Configuration
│   ├── base_collector.py   # Base collector class
│   ├── run_collection.py   # Collection script
│   ├── game_data/         # Game data collectors
│   └── api_integration/   # API integration
├── cogs/                   # Bot commands
└── utils/                 # Utility functions

data/
├── collected/            # Collected data
├── cache/               # Cache directory
└── roms/                # ROM files (not included)
```

### Adding New Features
1. Create a new collector in the appropriate directory
2. Implement the collector interface
3. Add configuration to `config.py`
4. Update the orchestrator in `run_collection.py`
5. Create corresponding bot commands in `cogs/`

### Testing
```bash
pytest tests/
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
- [Discord.py](https://github.com/Rapptz/discord.py)
- [PlexAPI](https://github.com/pkkid/python-plexapi)
- [PokeAPI](https://pokeapi.co/)
- [OSRSBox](https://github.com/osrsbox/osrsbox-db)
- All other open-source projects used in this bot
