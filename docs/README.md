# Discord Plex Player

A Discord bot that allows you to stream media from your Plex server directly in Discord voice channels, with a beautiful web-based player interface.

## Features

- Stream movies, TV shows, and music from your Plex server
- Beautiful web-based player interface
- Real-time playback synchronization across users
- Discord voice channel integration
- Media library browsing
- Search functionality
- Playlist/queue management
- Caching for improved performance

## Requirements

- Python 3.8+
- Node.js 14+
- Redis server
- Plex Media Server
- Discord bot token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/discord-plex-player.git
cd discord-plex-player
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install frontend dependencies:
```bash
cd src/frontend
npm install
```

5. Copy the environment template and fill in your values:
```bash
cp .env.template .env
```

## Configuration

Edit the `.env` file with your settings:

1. Plex Configuration:
   - `PLEX_URL`: Your Plex server URL
   - `PLEX_TOKEN`: Your Plex authentication token
   - `PLEX_CLIENT_ID`: Client identifier (default: discord-plex-player)
   - `PLEX_DEVICE_NAME`: Device name in Plex (default: Discord Player)

2. Discord Configuration:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `DISCORD_CLIENT_ID`: Discord application client ID
   - `DISCORD_CLIENT_SECRET`: Discord application client secret
   - `DISCORD_REDIRECT_URI`: OAuth2 redirect URI

3. Redis Configuration:
   - `REDIS_HOST`: Redis server host
   - `REDIS_PORT`: Redis server port
   - `REDIS_DB`: Redis database number
   - `REDIS_PASSWORD`: Redis password (if required)

4. Web Server Configuration:
   - `WEB_HOST`: Web server host
   - `WEB_PORT`: Web server port
   - `WEB_DEBUG`: Enable debug mode
   - `WEB_SECRET_KEY`: Secret key for session management
   - `CORS_ORIGINS`: Allowed CORS origins

## Usage

1. Start the Redis server:
```bash
redis-server
```

2. Start the web server:
```bash
python src/web_server/app.py
```

3. Start the Discord bot:
```bash
python src/bot.py
```

4. Start the frontend development server:
```bash
cd src/frontend
npm start
```

## Discord Commands

- `/plex search <query>` - Search for media
- `/plex play <query>` - Play media in current voice channel
- `/plex pause` - Pause playback
- `/plex resume` - Resume playback
- `/plex stop` - Stop playback
- `/plex queue` - Show current queue
- `/plex nowplaying` - Show currently playing media

## Development

### Project Structure

```
discord-plex-player/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── bot.py
│   │   └── cogs/
│   ├── web_server/
│   │   ├── __init__.py
│   │   └── app.py
│   ├── services/
│   │   └── plex/
│   ├── core/
│   │   ├── config.py
│   │   └── exceptions.py
│   └── frontend/
│       ├── src/
│       └── public/
├── tests/
├── requirements.txt
└── .env
```

### Running Tests

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

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Plex](https://www.plex.tv/)
- [Discord.py](https://discordpy.readthedocs.io/)
- [Flask](https://flask.palletsprojects.com/)
- [React](https://reactjs.org/)
- [Video.js](https://videojs.com/)
