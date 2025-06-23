# Discord Bot Project

This repository contains a feature-rich Discord bot built with Python.

## Architecture Overview

- **Python Backend**:
  - Built using `discord.py` for Discord integration.
  - Slash command based architecture for modular and extensible commands.
  - SQLite for data persistence.

- **Discord Integration**:
  - Command handling via slash commands.
  - Rich embed messages for clean display.

## Setup and Running the Bot

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install dependencies:**
    This project uses `make` to streamline the development process. To install all necessary production and development dependencies, simply run:
    ```bash
    make dev-install
    ```
    This command uses `pip` to install all packages defined in the `pyproject.toml` file.

3.  **Configuration:**
    -   Create a `.env` file in the project root.
    -   Add your Discord bot token to the `.env` file:
        ```
        DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
        ```

4.  **Run the bot:**
    To run the bot in development mode, use the following command:
    ```bash
    make run-dev
    ```
    This will launch the bot and all its services inside Docker containers. The bot is configured for live-reloading, so any changes you make to the source code will cause it to automatically restart.

## Features

### OSRS Module
A full-featured Old School RuneScape RPG experience right in your Discord server.

- **Grand Exchange**: A server-wide marketplace to buy and sell items using the `/osrs_ge` command group.
- **Quests**: Check available quests and your progress with `/osrs_quest`.

### Plex Module
- **Search**: Search for media on your Plex server with `/plex_search`.
- **Playback**: Play, pause, resume, and stop media with `/plex_play`, `/plex_pause`, `/plex_resume`, and `/plex_stop`.
- **Status**: Check the status of the current playback with `/plex_status`.
- **Libraries**: List available libraries with `/plex_libraries`.

### Pokémon Module
- **Info**: Get information on Pokémon, abilities, moves, items, types, and natures with the `/pokemon` command group.

## Command Documentation

For a full list of commands and their usage, please see the [Command Documentation](./docs/api/commands).

## Contributing

1.  Fork the repository.
2.  Create a feature branch.
3.  Implement your changes.
4.  Test thoroughly.
5.  Submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 