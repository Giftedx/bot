# Configuration Guide

This guide explains the YAML-based configuration system used in this application, managed by the `ConfigManager` class.

## 1. Overview

The application has transitioned from a Python-based configuration (dataclasses in `config.py`) to a more flexible YAML-based system. Configuration is now managed through two main files: `config.yaml` for general settings and `secrets.yaml` for sensitive information like API keys and tokens. The `ConfigManager` class (in `src/core/config.py`) is responsible for loading, accessing, and managing these configurations.

## 2. File Locations

Configuration files are expected to be located in a `config/` directory at the root of the project:

-   `config/config.yaml`
-   `config/secrets.yaml`

If these files do not exist when the application starts, `ConfigManager` will attempt to create `config.yaml` with default values. `secrets.yaml` should be created manually.

## 3. `config.yaml` Structure and Examples

This file holds non-sensitive application settings. If `config.yaml` is not found, `ConfigManager` will create one with default values.

**Example `config.yaml`:**

```yaml
bot:
  command_prefix: '!'
  description: 'Personal content and cross-game features bot'
  status_message: 'Watching for roastable moments'
  roast_cooldown_minutes: 5
  roast_min_score: 0.7
  roast_chance: 0.3
  # For OSRSBot, you might add specific settings under an 'osrs_bot' key if needed:
  # osrs_bot:
  #   command_prefix: '.osrs'
  #   description: 'OSRS Specific Bot'

channels:
  event_channel_id: null # Replace null with your Discord Channel ID for events
  roast_channel_ids: []   # Add a list of Channel IDs for roast command outputs
  # Example:
  # roast_channel_ids:
  #   - "123456789012345678"
  #   - "987654321098765432"
  watch_party_channel_id: null # Channel ID for watch party announcements
  pet_channel_id: null         # Channel ID for pet-related announcements

database:
  path: 'data/bot.db'
  backup_interval_hours: 24
  max_backups: 7

events:
  check_interval_minutes: 1
  cleanup_interval_minutes: 5
  roast_interval_minutes: 15

pets:
  max_pets: 10
  interaction_cooldown_minutes: 30
  happiness_decay_rate: 0.1
  experience_multiplier: 1.0

watch_parties:
  max_members: 10
  auto_end_minutes: 360
  min_duration_minutes: 15

effects:
  max_active: 5
  stack_limit: 3
  default_duration_minutes: 60

easter_eggs:
  trigger_chance: 0.1
  rare_event_chance: 0.01
  special_date_multiplier: 2.0

redis: # Configuration for Redis, used by some components
  host: 'localhost'
  port: 6379
  db: 0
  password: null # Set password if your Redis server requires it
```

**Common Configuration Sections:**

-   `bot`: General bot settings like command prefix and status messages. You can add sub-sections (e.g., `osrs_bot`) for different bot personalities if needed.
-   `channels`: Discord channel IDs for specific features (events, roasts).
-   `database`: Settings for the application's database, including backup parameters.
-   `redis`: Connection details for Redis, if used by any components.
-   Other sections (`events`, `pets`, etc.) control specific features of the application.

## 4. `secrets.yaml` Structure and Examples

This file is for sensitive information like API keys, tokens, and other credentials. **It should NOT be committed to your Git repository.**

**Create this file manually at `config/secrets.yaml`.**

**Example `secrets.yaml`:**

```yaml
discord:
  token: "YOUR_DISCORD_BOT_TOKEN_HERE"
  client_id: "YOUR_DISCORD_CLIENT_ID_HERE"       # Optional, if used
  client_secret: "YOUR_DISCORD_CLIENT_SECRET_HERE" # Optional, if used

plex:
  url: "http://localhost:32400" # Your Plex server URL
  token: "YOUR_PLEX_TOKEN_HERE"

api_keys:
  openai: "YOUR_OPENAI_API_KEY_HERE"     # If using OpenAI
  weather: "YOUR_WEATHER_API_KEY_HERE" # If using a weather API
  # Add other API keys as needed
```

**Important Security Note:**

-   Add `config/secrets.yaml` to your `.gitignore` file to prevent accidental commits of your secrets.
    Example `.gitignore` entry:
    ```
    # Configuration files
    config/secrets.yaml
    ```

## 5. Environment Variables

`ConfigManager` can also load values for secrets directly from environment variables. This is often preferred for production deployments.

The following environment variables will be checked by `ConfigManager` and will take precedence over values in `secrets.yaml` if both are set:

-   `DISCORD_TOKEN` (maps to `discord.token`)
-   `DISCORD_CLIENT_ID` (maps to `discord.client_id`)
-   `DISCORD_CLIENT_SECRET` (maps to `discord.client_secret`)
-   `PLEX_URL` or `PLEX_SERVER_URL` (maps to `plex.url` or `plex.server_url` - internally `ConfigManager` checks for `PLEX_SERVER_URL` from env first for this key)
-   `PLEX_TOKEN` (maps to `plex.token`)
-   `OPENAI_API_KEY` (maps to `api_keys.openai`)
-   `WEATHER_API_KEY` (maps to `api_keys.weather`)

**Precedence:**
1.  Environment Variables (highest precedence)
2.  Values in `secrets.yaml`
3.  Default values specified in `ConfigManager.default_secrets` (which are typically `None` for secrets).

## 6. Accessing Configuration (for developers)

If you are developing a new feature or module that requires configuration:

1.  **Ensure `ConfigManager` is available:**
    Your class or module should typically receive a `ConfigManager` instance through dependency injection or instantiate it.
    ```python
    from src.core.config import ConfigManager

    # If instantiated within a class that doesn't get it passed in:
    # self.config_manager = ConfigManager(config_dir="config")
    # (Adjust config_dir path if not running from project root, though "config" is standard)
    ```

2.  **Access configuration values:**
    Use the `get()` method, which checks secrets first, then `config.yaml`.
    ```python
    # Get a value from config.yaml
    command_prefix = config_manager.get('bot.command_prefix', default_value='!')

    # Get a secret (checks environment, then secrets.yaml)
    discord_token = config_manager.get('discord.token')
    if not discord_token:
        raise ValueError("Discord token is not configured!")

    # Accessing nested keys
    openai_key = config_manager.get('api_keys.openai')
    ```

3.  **Adding new configuration items:**
    -   For non-sensitive settings, add them to `ConfigManager.default_config` in `src/core/config.py` and provide a corresponding entry in your example `config.yaml`.
    -   For sensitive settings, add them to `ConfigManager.default_secrets` (usually with a `None` default) and document the corresponding key for `secrets.yaml` and the environment variable name. Update `ConfigManager.load_secrets` to load this new secret from its environment variable.
```
