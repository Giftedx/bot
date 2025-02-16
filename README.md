# Discord Plex Bot

A Discord bot that integrates with Plex Media Server, allowing users to browse and stream media content directly in Discord voice channels.

## Features

- Browse Plex libraries
- Search for media content
- Stream media in Discord voice channels
- Web interface for media browsing
- Transcoding support for optimal playback
- Authentication and authorization
- Cross-platform compatibility

## Prerequisites

- Python 3.8 or higher
- FFmpeg (for media transcoding)
- Redis (for caching)
- Plex Media Server
- Discord Bot Token
- Node.js and npm (for frontend development)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd discord-plex-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with the following variables:
```
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CLIENT_ID=your_discord_client_id
PLEX_URL=your_plex_server_url
PLEX_TOKEN=your_plex_token
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your_jwt_secret
```

5. Install frontend dependencies:
```bash
cd frontend
npm install
```

## Usage

1. Start the Discord bot:
```bash
python discord_bot/bot.py
```

2. Start the web server:
```bash
python web_server/server.py
```

3. Start the frontend development server:
```bash
cd frontend
npm start
```

## Discord Commands

- `!libraries` - List all available Plex libraries
- `!search <query>` - Search for media across libraries
- `!play <media_id>` - Play media in current voice channel
- `!stop` - Stop current playback

## API Endpoints

- `GET /api/libraries` - Get all Plex libraries
- `GET /api/search?q=<query>&library=<library_id>` - Search for media
- `GET /api/media/<media_id>` - Get media details
- `GET /api/stream/<media_id>` - Get media stream URL
- `POST /api/auth` - Authenticate user

## Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest
```

3. Format code:
```bash
black .
```

4. Run linting:
```bash
flake8
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

- [discord.py](https://github.com/Rapptz/discord.py)
- [PlexAPI](https://github.com/pkkid/python-plexapi)
- [Flask](https://flask.palletsprojects.com/)

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 