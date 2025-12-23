# Discord Bot Project

This repository contains a feature-rich Discord bot built with Python.

## Project Goals

This project aims to provide a modular, high-performance Discord platform that bridges the gap between gaming utilities, media streaming, and community interaction.

*   **Primary Goals**:
    *   **OSRS Integration**: Deliver a comprehensive Old School RuneScape experience (Grand Exchange, Quests, Stats) directly within Discord.
    *   **Media Streaming**: seamless integration with Plex for searching and controlling media playback.
    *   **Community Engagement**: Foster interaction through social features, events, and utility commands (e.g., Pokémon data).
*   **Key Features**:
    *   **Microservices Architecture**: Built on Docker for scalability, separating the Bot, Game Server, and Web Dashboard.
    *   **Modern Stack**: Python 3.11+ (FastAPI, Discord.py), TypeScript (Node.js), and Redis for caching.
    *   **Dashboard**: A web interface for managing bot settings and viewing statistics.

## Architecture Overview

- **Python Backend**:
  - Built using `discord.py` for Discord integration.
  - Slash command based architecture for modular and extensible commands.
  - SQLite for data persistence.

- **Discord Integration**:
  - Command handling via slash commands.
  - Rich embed messages for clean display.

## Installation

### Prerequisites
*   **Python 3.11+**
*   **Docker & Docker Compose** (Recommended for full feature set)
*   **Make** (for build automation)

### Quick Start (Development)

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Dependencies:**
    Initialize the virtual environment and install Python dependencies:
    ```bash
    make dev-install
    ```

3.  **Setup Environment:**
    Run the setup script to generate configuration files (`config/config.yaml`, `config/secrets.yaml`) and your `.env` file:
    ```bash
    make setup
    ```

4.  **Configuration:**
    *   Edit `.env` to add your **DISCORD_TOKEN** and other environment variables.
    *   Edit `config/secrets.yaml` for sensitive API keys (Plex, OpenAI, etc.).

5.  **Run the Project:**

    *   **Option A: Docker (Recommended)**
        Launches the Bot, Redis, Prometheus, and Grafana with hot-reloading.
        ```bash
        make run-dev
        ```

    *   **Option B: Local (Python only)**
        Requires a local Redis instance running on port 6379.
        ```bash
        python -m src.main
        ```

6.  **Verify Installation:**
    Run the test suite to ensure everything is working correctly:
    ```bash
    make test
    ```

## Repository Layout

- `src/`: Python source code
  - `src/bot/`: Discord bot implementation (cogs, commands)
  - `src/core/`: core systems (battle, economy, config, persistence)
  - `src/services/`: external integrations (e.g., Plex)
  - `src/web_server/`: lightweight Flask API and Socket.IO events
  - `src/server/`: TypeScript-based game server (Node.js). Build/run with `npm run build` / `npm start`.
- `docs/`: MkDocs documentation (see `mkdocs.yml`). Serve with `make docs-serve`.
- `docker/`: Dockerfiles and compose configurations for dev/prod/monitoring
- `tests/`: automated tests
- `prometheus/`, `grafana/`: monitoring configuration

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

For a full list of commands and their usage, please see the [Command Reference](./docs/commands/command-reference.md).

## Contributing

1.  Fork the repository.
2.  Create a feature branch.
3.  Implement your changes.
4.  Test thoroughly.
5.  Submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 