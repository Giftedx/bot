# Discord Bot Project

This repository contains a feature-rich Discord bot built with Python.

## Architecture Overview

- **Python Backend**:
  - Built using `discord.py` for Discord integration.
  - Cog-based architecture for modular and extensible commands.
  - SQLite for data persistence.
  - Features a pet battling game.

- **Discord Integration**:
  - Command handling via `!` prefix.
  - Rich embed messages for clean display.

## Setup and Running the Bot

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install dependencies:**
    This project uses Poetry for dependency management. If you don't have Poetry installed, you can find installation instructions [here](https://python-poetry.org/docs/#installation).

    Once you have Poetry, install the dependencies from `pyproject.toml`:
    ```bash
    poetry install
    ```

3.  **Configuration:**
    -   Create a `config/secrets.yaml` file.
    -   Edit `config/secrets.yaml` and add your Discord bot token:
        ```yaml
        discord:
          token: YOUR_BOT_TOKEN_HERE
        ```
    -   Alternatively, you can set the `DISCORD_TOKEN` environment variable.

4.  **Run the bot:**
    ```bash
    poetry run python -m src.main
    ```
    Or, if you have activated the virtual environment with `poetry shell`:
    ```bash
    python -m src.main
    ```

## Features

### OSRS Module
A full-featured Old School RuneScape RPG experience right in your Discord server.

- **Character System**: Create your own character with `/create`, view your skills with `/stats`, and see your inventory with `/inventory` and `/bank`.
- **Combat**: Fight a variety of monsters using the `/fight`, `/attack`, and `/flee` commands. Gain XP and get drops!
- **Quests**: Embark on quests with `/quests` and check your progress with `/quest_info`.
- **Player Trading**: Trade items securely with other players using the `/trade` command group.
- **Progression**: Track your `/achievements` and fill up your `/collection_log` with unique items.
- **Grand Exchange (WIP)**: A server-wide marketplace to buy and sell items is under construction. Placeholder commands (`/ge`) are available.

### Pet Battling
- `!pets`: See a list of your pets.
- `!battle @user`: (Under construction) Start a battle with another user.

## Contributing

1.  Fork the repository.
2.  Create a feature branch.
3.  Implement your changes.
4.  Test thoroughly.
5.  Submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 