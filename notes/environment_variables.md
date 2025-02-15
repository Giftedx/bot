# Environment Variables

## Required Variables

### Discord Configuration
- `DISCORD_BOT_TOKEN`: Main bot authentication token
- `DISCORD_TOKEN`: Legacy token reference, consolidate with BOT_TOKEN
- `DISCORD_TEXT_CHANNEL_ID`: Default text channel for notifications

### Plex Configuration
- `PLEX_URL`: Base URL of the Plex server (e.g., http://192.168.1.100:32400)
- `PLEX_TOKEN`: Authentication token for Plex API access
- `PLEX_MOVIE_LIBRARY_NAME`: Name of movie library section
- `PLEX_TV_LIBRARY_NAME`: Name of TV shows library section

### External Services
- `REDIS_URL`: Redis connection string for caching (e.g., redis://localhost:6379)
- `VAULT_ADDR`: HashiCorp Vault address for secrets
- `VAULT_TOKEN`: Authentication token for Vault access

### Optional Variables
- `GIPHY_API_KEY`: For gif command functionality
- `SPOTIFY_CLIENT_ID`: For music integration
- `SPOTIFY_CLIENT_SECRET`: For music integration authentication

## Development Variables
- `DEBUG`: Enable debug logging (default: False)
- `LOG_LEVEL`: Logging verbosity (default: INFO)
- `TEST_MODE`: Enable test mode features

## Production Variables
- `PORT`: Service port (default: 8080)
- `HOST`: Service host (default: 0.0.0.0)
- `WORKERS`: Number of worker processes

## Environment File Template
```env
# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_TEXT_CHANNEL_ID=your_channel_id

# Plex Configuration
PLEX_URL=http://your_plex_server:32400
PLEX_TOKEN=your_plex_token
PLEX_MOVIE_LIBRARY_NAME=Movies
PLEX_TV_LIBRARY_NAME=TV Shows

# External Services
REDIS_URL=redis://localhost:6379
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=your_vault_token

# Optional Services
GIPHY_API_KEY=optional_giphy_key
SPOTIFY_CLIENT_ID=optional_spotify_id
SPOTIFY_CLIENT_SECRET=optional_spotify_secret

# Runtime Configuration
DEBUG=false
LOG_LEVEL=INFO
PORT=8080
HOST=0.0.0.0
WORKERS=4
```

## Security Notes
1. Never commit .env files to version control
2. Use separate .env files for development and production
3. Consider using Vault for production secrets
4. Rotate tokens periodically
5. Use least-privilege tokens when possible