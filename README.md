# Discord Bot with OSRS, Pokemon, and Plex Integration

A feature-rich Discord bot that combines OSRS gameplay, Pokemon mechanics, and Plex media streaming capabilities.

## Features

### Core Features
- Modular command system
- Custom command creation
- Permission management
- Database integration
- Error handling and logging

### Game Systems
- OSRS Simulation
  - Character creation
  - Skill training
  - World system
  - Basic economy
- Pokemon Features
  - Pokemon catching
  - Battle system
  - Training and evolution
  - Trading system

### Media Integration
- Plex Integration
  - Media browsing and search
  - Playback controls
  - Multi-platform support
  - Voice channel streaming
- Additional Media
  - YouTube playback
  - Spotify integration
  - GIPHY support
  - Sound effects

### Fun Commands
- Social interactions
- Mini-games
- Profile customization
- Pet system
- Marriage system

## Setup

### Prerequisites
- Python 3.9 or higher
- PostgreSQL database
- Plex Media Server
- Discord Bot Token
- Plex Token

### Installation
1. Clone the repository
```bash
git clone <repository-url>
cd discord-bot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up configuration
Create a `config.yaml` file with the following structure:
```yaml
discord:
  token: your_discord_token
  prefix: "!"

database:
  url: your_database_url
  pool_size: 20

plex:
  url: your_plex_url
  token: your_plex_token
```

4. Initialize database
```bash
psql -U your_user -d your_database -f schema.sql
```

5. Run the bot
```bash
python bot.py
```

## Commands

### OSRS Commands
- `!create <name>` - Create a new OSRS character
- `!world` - Show your current world
- `!worlds [type]` - List available game worlds
- `!join <world_id>` - Join a different game world
- `!stats` - Show character stats

### Pokemon Commands
- `!pokemon catch <name>` - Attempt to catch a Pokemon
- `!pokemon battle @user` - Challenge another trainer
- `!pokemon list` - View your Pokemon
- `!pokemon train <pokemon> <minutes>` - Train your Pokemon

### Plex Commands
- `!plex search <query>` - Search for media
- `!plex play <query>` - Play media in voice channel
- `!plex stop` - Stop playback
- `!plex pause` - Pause playback
- `!plex resume` - Resume playback
- `!plex nowplaying` - Show current media info

### Fun Commands
- Various social interaction commands
- Mini-games and activities
- Profile customization
- Pet system commands
- Marriage system commands

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- discord.py - Discord API wrapper
- plexapi - Plex Media Server API
- asyncpg - PostgreSQL database driver
- Various open-source projects for inspiration and code patterns
