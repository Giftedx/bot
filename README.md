# Discord Bot Multi-Tool

A comprehensive Discord bot project that combines repository analysis capabilities with Plex media integration.

## Core Features

### Repository Analysis
- Repository categorization and analysis
- Data parsing and organization
- Search and filter capabilities
- Repository analysis tools

### Plex Integration
- Stream movies and TV shows from your Plex server in Discord voice channels
- Search your Plex library directly from Discord
- Basic playback controls (pause/resume, stop)
- Watch together with friends in voice channels

## Project Structure
- `src/` - Source code directory
  - `bot/` - Core bot functionality
  - `core/` - Core utilities and systems
  - `data/` - Repository data and categories
  - `utils/` - Utility functions and helpers
  - `plex/` - Plex integration components

## Categories
- Core Discord Libraries
- AI Integration Bots
- Multi-Purpose Bots
- Study Tools
- Media & Voice
- Game Integration
- Image & Media Processing
- Utility Tools
- Plex Integration

## Requirements

- Python 3.8 or higher
- VLC Media Player (for Plex streaming)
- A Plex Media Server (for Plex features)
- Discord account token
- Plex server URL and token (for Plex features)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd discord-bot-multitool
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```env
# Required for all features
DISCORD_TOKEN=your_discord_token

# Required for Plex integration
PLEX_URL=your_plex_server_url
PLEX_TOKEN=your_plex_token
```

## Usage

### Repository Analysis
```bash
python src/main.py
```

### Plex Integration
1. Start the Plex integration:
```bash
python src/run_selfbot.py
```

2. Join a voice channel in Discord

3. Available Plex commands:
- `!search <query>` - Search for media on your Plex server
- `!stream <query>` - Start streaming media in the voice channel
- `!pause` - Pause/Resume the current stream
- `!stop` - Stop the current stream

## Getting Your Tokens

### Discord Token
1. Open Discord in your browser
2. Press Ctrl+Shift+I to open developer tools
3. Go to Network tab
4. Type anything in any channel
5. Look for a request starting with "messages"
6. Find the "authorization" header in the request headers

### Plex Token
1. Sign in to Plex
2. Visit https://plex.tv/claim
3. Copy your token

## Important Notes

- The Plex integration uses a selfbot, which runs on your personal Discord account
- Be aware that selfbots are against Discord's Terms of Service
- Use responsibly and at your own risk
- Make sure your Plex server has enough bandwidth for streaming
- VLC must be installed on your system for Plex streaming

## Troubleshooting

### Repository Analysis Issues
- Verify your internet connection
- Check if the repositories are accessible
- Ensure you have the required permissions

### Plex Integration Issues
1. If VLC doesn't start:
   - Make sure VLC is installed and in your system PATH
   - Try reinstalling VLC

2. If media doesn't play:
   - Check your Plex server is running and accessible
   - Verify your Plex token is correct
   - Ensure the media exists in your Plex library

3. If the bot doesn't connect:
   - Verify your Discord token is correct
   - Make sure you're in a voice channel
   - Check your internet connection

## License

This project is licensed under the MIT License - see the LICENSE file for details.
