# Discord Bot Project

This repository contains a feature-rich Discord bot built with Python, integrating Old School RuneScape (OSRS) mechanics, Plex media streaming, and various interactive features.

## Architecture Overview

The project is structured into several key components:

-   **`src/`**: The main source code directory.
    -   **`src/bot/`**: Contains the Discord bot implementation using `discord.py`. It manages commands, events (cogs), and interactions.
    -   **`src/core/`**: The core logic and systems. This includes configuration management, database interactions, battle systems, media player logic, and other shared utilities.
    -   **`src/osrs/`**: A dedicated module for the OSRS RPG simulation. It handles player stats, items, combat, skilling, and the game economy.
    -   **`src/server/`**: A TypeScript-based WebSocket game server (`GameServer.ts`) that likely powers real-time interactions or a separate game client.
    -   **`src/web_server/`**: A lightweight Flask web server, potentially for health checks, dashboards, or webhooks.

-   **Data Persistence**:
    -   SQLite is used for local data storage (`data/bot.db`), managed via `UnifiedDatabaseManager`.
    -   Redis is used for caching and potentially for managing state in distributed setups.

-   **Configuration**:
    -   Configuration is managed by `ConfigManager` in `src/core/config.py`.
    -   Settings are stored in YAML files (`config/config.yaml`, `config/secrets.yaml`) and environment variables.

## Setup and Running the Bot

### Prerequisites

-   Python 3.11 or higher
-   Node.js and npm (for the TypeScript server)
-   Redis (optional, but recommended for full feature set)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -e .[dev]
    ```
    Or use the Makefile:
    ```bash
    make dev-install
    ```

3.  **Install Node.js dependencies (if running the game server):**
    ```bash
    cd src/server
    npm install
    ```

4.  **Configuration:**
    -   Create a `.env` file in the project root based on the example.
    -   Set `DISCORD_TOKEN` and other secrets.
    -   Alternatively, populate `config/secrets.yaml`.

### Running the Application

-   **Run the Discord Bot:**
    ```bash
    python src/main.py
    ```

-   **Run the Game Server (TypeScript):**
    ```bash
    cd src/server
    npm start
    ```

## Repository Layout

-   `src/bot/`: Discord bot cogs and event handlers.
-   `src/core/`: Core business logic (Config, DB, Battle, Plex).
-   `src/osrs/`: OSRS game mechanics implementation.
-   `src/server/`: Real-time game server (TypeScript).
-   `tests/`: Unit and integration tests.
-   `docs/`: Documentation.

## Features

### OSRS Module
Simulates the Old School RuneScape experience.
-   **Skilling**: Train skills like Woodcutting, Mining, etc.
-   **Combat**: Fight monsters and bosses.
-   **Economy**: Trade items via a Grand Exchange system.

### Plex Integration
Control your Plex server from Discord.
-   **Search & Play**: Search for media and control playback.
-   **Status**: View current activity.

### Pokemon
Catch and battle Pokemon (if enabled/implemented).

## Contributing

1.  Fork the repository.
2.  Create a feature branch.
3.  Ensure code is documented and tested.
4.  Submit a Pull Request.

## License

MIT License. See `LICENSE` for details.
