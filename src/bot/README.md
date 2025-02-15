# Discord Bot with Plex Integration

## Directory Structure

```
src/bot/
├── core/                   # Core bot implementation
│   ├── __init__.py        # Package exports
│   └── bot.py             # Main bot class and runner
├── cogs/                  # Bot commands organized by functionality
│   ├── __init__.py
│   ├── base_cog.py        # Base cog class
│   ├── error_handler.py   # Global error handling
│   ├── help_command.py    # Custom help command
│   │
│   ├── # Feature Cogs
│   ├── media_commands.py  # Media playback and control
│   ├── plex_commands.py   # Plex server integration
│   ├── audio_commands.py  # Audio streaming features
│   │
│   ├── # Utility Cogs
│   ├── moderation.py      # Server moderation
│   ├── user_utilities.py  # User management
│   ├── utility_commands.py # General utilities
│   │
│   ├── # Optional Cogs
│   ├── fun_commands.py    # Fun/entertainment commands
│   └── game_commands.py   # Game-related features
└── main.py               # Application entry point

```

## Components

### Core

- `core/bot.py`: Main bot implementation with configuration and error handling
- `core/__init__.py`: Exports DiscordBot and run_bot function

### Cogs

Organized into categories based on functionality:

1. Core Cogs
   - error_handler.py: Global error handling
   - help_command.py: Custom help command implementation

2. Feature Cogs
   - media_commands.py: Media playback and control
   - plex_commands.py: Plex server integration
   - audio_commands.py: Audio streaming features

3. Utility Cogs
   - moderation.py: Server moderation tools
   - user_utilities.py: User management features
   - utility_commands.py: General utility commands

4. Optional Cogs
   - fun_commands.py: Entertainment commands
   - game_commands.py: Game-related features

### Entry Point

- `main.py`: Application entry point with logging setup and error handling

## Usage

1. Set up environment variables in `.env`:
   ```
   DISCORD_TOKEN=your_token_here
   COMMAND_PREFIX=!
   ```

2. Run the bot:
   ```bash
   python -m src.bot.main
   ```

## Development

- New cogs should inherit from `base_cog.py`
- Core functionality belongs in `core/bot.py`
- Utility functions should go in appropriate utility cogs
- Error handling is centralized in `error_handler.py`
