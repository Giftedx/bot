# Configuration Guide

## Table of Contents
1. [Environment Variables](#environment-variables)
2. [Discord Configuration](#discord-configuration)
3. [Plex Configuration](#plex-configuration)
4. [Redis Configuration](#redis-configuration)
5. [Web Server Configuration](#web-server-configuration)
6. [Logging Configuration](#logging-configuration)
7. [Media Configuration](#media-configuration)
8. [Advanced Configuration](#advanced-configuration)

## Environment Variables

### Required Variables

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_token
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=https://your-domain.com/auth/callback

# Plex Configuration
PLEX_URL=https://your-plex-server:32400
PLEX_TOKEN=your_plex_token
PLEX_CLIENT_ID=discord-plex-player
PLEX_DEVICE_NAME=Discord Bot

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# Web Server Configuration
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_DEBUG=false
WEB_SECRET_KEY=your_secret_key
CORS_ORIGINS=https://your-domain.com

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/discord-plex/bot.log

# Media Configuration
MAX_SEARCH_RESULTS=10
DEFAULT_VOLUME=0.5
STREAM_QUALITY=1080p
AUTO_DISCONNECT_TIMEOUT=300
```

### Optional Variables

```env
# Performance Tuning
CACHE_TTL=3600
MAX_CONCURRENT_STREAMS=5
BUFFER_SIZE=8192
TRANSCODING_THREADS=2

# Feature Flags
ENABLE_LYRICS=true
ENABLE_RECOMMENDATIONS=true
ENABLE_PLAYLIST_SHARING=true
ENABLE_WATCH_TOGETHER=true

# Integration Settings
GENIUS_API_KEY=your_genius_api_key
LASTFM_API_KEY=your_lastfm_api_key
```

## Discord Configuration

### Bot Token

1. **Creating a Discord Application**
   - Visit [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Name your application
   - Go to "Bot" section
   - Click "Add Bot"
   - Copy the token

2. **Required Permissions**
   ```
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Add Reactions
   - Connect
   - Speak
   - Use Voice Activity
   ```

3. **OAuth2 Configuration**
   - Set redirect URI in Developer Portal
   - Enable required scopes:
     - bot
     - applications.commands
     - identify
     - guilds

### Command Configuration

```python
# config/commands.py
COMMAND_PREFIX = "!"
ENABLE_SLASH_COMMANDS = True
COOLDOWN_DURATION = 3
MAX_QUEUE_SIZE = 100
```

## Plex Configuration

### Server Connection

1. **Getting Plex Token**
   - Sign in to Plex
   - Visit account page
   - Find token in account settings

2. **Server Settings**
   ```env
   PLEX_URL=https://your-plex-server:32400
   PLEX_TOKEN=your_plex_token
   ```

3. **Client Configuration**
   ```env
   PLEX_CLIENT_ID=discord-plex-player
   PLEX_DEVICE_NAME=Discord Bot
   ```

### Media Settings

```env
# Quality Settings
STREAM_QUALITY=1080p
TRANSCODE_QUALITY=8
AUDIO_BOOST=0

# Playback Settings
DEFAULT_VOLUME=0.5
SEEK_INCREMENT=10
MAX_DURATION=14400
```

## Redis Configuration

### Basic Setup

1. **Connection Settings**
   ```env
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_PASSWORD=your_redis_password
   ```

2. **Security Settings**
   ```conf
   # redis.conf
   bind 127.0.0.1
   protected-mode yes
   requirepass your_redis_password
   ```

### Cache Configuration

```python
# config/cache.py
CACHE_CONFIG = {
    'default_timeout': 3600,
    'key_prefix': 'discord_plex:',
    'redis_url': 'redis://:password@localhost:6379/0'
}

CACHE_KEYS = {
    'media_info': 'media:{media_id}',
    'user_settings': 'user:{user_id}:settings',
    'session_state': 'session:{session_id}:state'
}
```

## Web Server Configuration

### Basic Settings

```env
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_DEBUG=false
WEB_SECRET_KEY=your_secret_key
```

### CORS Configuration

```env
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_HEADERS=Content-Type,Authorization
```

### Rate Limiting

```python
# config/web.py
RATE_LIMIT_CONFIG = {
    'default': '100/minute',
    'search': '30/minute',
    'stream': '10/minute'
}
```

## Logging Configuration

### Basic Setup

```env
LOG_LEVEL=INFO
LOG_FILE=/var/log/discord-plex/bot.log
```

### Advanced Logging

```python
# config/logging.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(timestamp)s %(level)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/discord-plex/bot.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'standard'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO'
        }
    }
}
```

## Media Configuration

### Playback Settings

```env
# Quality Settings
STREAM_QUALITY=1080p
DEFAULT_VOLUME=0.5
BUFFER_SIZE=8192

# Timeouts
AUTO_DISCONNECT_TIMEOUT=300
PLAYBACK_TIMEOUT=3600
IDLE_TIMEOUT=600
```

### Search Settings

```env
# Search Configuration
MAX_SEARCH_RESULTS=10
SEARCH_CACHE_TTL=3600
ENABLE_FUZZY_SEARCH=true
MIN_SEARCH_TERM_LENGTH=2
```

### Queue Settings

```python
# config/media.py
QUEUE_CONFIG = {
    'max_size': 100,
    'allow_duplicates': False,
    'shuffle_on_add': False,
    'announce_next_track': True
}

PLAYLIST_CONFIG = {
    'max_playlists': 10,
    'max_items_per_playlist': 100,
    'allow_collaborative': True
}
```

## Advanced Configuration

### Performance Tuning

```env
# Caching
CACHE_TTL=3600
CACHE_MAX_ITEMS=10000
CACHE_STRATEGY=lru

# Concurrency
MAX_CONCURRENT_STREAMS=5
WORKER_THREADS=4
EVENT_LOOP_POLICY=uvloop
```

### Feature Flags

```python
# config/features.py
FEATURE_FLAGS = {
    'enable_lyrics': True,
    'enable_recommendations': True,
    'enable_playlist_sharing': True,
    'enable_watch_together': True,
    'enable_voice_commands': False,
    'enable_media_controls': True
}
```

### Integration Settings

```env
# Third-party APIs
GENIUS_API_KEY=your_genius_api_key
LASTFM_API_KEY=your_lastfm_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

### Custom Commands

```python
# config/commands.py
CUSTOM_COMMANDS = {
    'stats': {
        'enabled': True,
        'cooldown': 60,
        'aliases': ['info', 'status'],
        'help': 'Display bot statistics'
    },
    'cleanup': {
        'enabled': True,
        'cooldown': 300,
        'required_role': 'Admin',
        'help': 'Clean up bot messages'
    }
}
```

### Error Handling

```python
# config/errors.py
ERROR_RESPONSES = {
    'media_not_found': 'Could not find the requested media. Please try again.',
    'permission_denied': 'You do not have permission to use this command.',
    'invalid_command': 'Invalid command. Use !help for available commands.',
    'playback_error': 'An error occurred during playback. Please try again.'
}

ERROR_HANDLERS = {
    'default': 'handle_default_error',
    'media_error': 'handle_media_error',
    'permission_error': 'handle_permission_error'
}
```

## Configuration Examples

### Development Environment

```env
# .env.development
WEB_DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_PROFILING=true
CORS_ORIGINS=*
```

### Production Environment

```env
# .env.production
WEB_DEBUG=false
LOG_LEVEL=INFO
ENABLE_PROFILING=false
CORS_ORIGINS=https://your-domain.com
```

### Testing Environment

```env
# .env.testing
WEB_DEBUG=true
LOG_LEVEL=DEBUG
TESTING=true
REDIS_DB=1
```

## Configuration Management

### Loading Configuration

```python
# config/loader.py
from dotenv import load_dotenv
import os

def load_config():
    """Load configuration from environment and files."""
    # Load .env file
    load_dotenv()
    
    # Load environment-specific config
    env = os.getenv('ENVIRONMENT', 'development')
    load_dotenv(f'.env.{env}')
    
    return {
        'discord': load_discord_config(),
        'plex': load_plex_config(),
        'redis': load_redis_config(),
        'web': load_web_config(),
        'logging': load_logging_config(),
        'media': load_media_config()
    }
```

### Validation

```python
# config/validator.py
from pydantic import BaseSettings

class DiscordConfig(BaseSettings):
    token: str
    client_id: str
    client_secret: str
    redirect_uri: str

class PlexConfig(BaseSettings):
    url: str
    token: str
    client_id: str
    device_name: str

# Validate configuration
config = DiscordConfig()
```

## Support

For configuration support:
1. Check configuration documentation
2. Review environment variables
3. Join Discord support channel
4. Create GitHub issue 