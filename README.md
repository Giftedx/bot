# Plex Discord Selfbot

A Discord selfbot that allows you to stream Plex media in voice channels and watch together with friends.

## Features

- Stream movies and TV shows from your Plex server in Discord voice channels
- Search your Plex library directly from Discord
- Basic playback controls (pause/resume, stop)
- Watch together with friends in voice channels

## Requirements

- Python 3.8 or higher
- VLC Media Player installed
- A Plex Media Server
- Discord account token
- Plex server URL and token

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd plex-discord-selfbot
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
DISCORD_TOKEN=your_discord_token
PLEX_URL=your_plex_server_url
PLEX_TOKEN=your_plex_token
```

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

## Usage

1. Start the bot:
```bash
python src/run_selfbot.py
```

2. Join a voice channel in Discord

3. Available commands:
- `!search <query>` - Search for media on your Plex server
- `!stream <query>` - Start streaming media in the voice channel
- `!pause` - Pause/Resume the current stream
- `!stop` - Stop the current stream

4. When streaming:
   - Start the stream with `!stream <movie name>`
   - Once VLC opens, start screensharing in Discord
   - Select the VLC window in your screenshare
   - Everyone in the voice channel can now watch together!

## Important Notes

- This is a selfbot, which means it runs on your personal Discord account
- Be aware that selfbots are against Discord's Terms of Service
- Use responsibly and at your own risk
- Make sure your Plex server has enough bandwidth for streaming
- VLC must be installed on your system

## Troubleshooting

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
