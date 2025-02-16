# Plex Discord Selfbot Extension

Stream Plex media in Discord voice channels and watch together with friends.

## Quick Setup

1. Install VLC Media Player from [videolan.org](https://www.videolan.org/vlc/)
2. Run the setup script:
```bash
python setup_plex.py
```
3. Configure your `.env` file with:
```env
DISCORD_TOKEN=your_discord_token
PLEX_URL=your_plex_server_url
PLEX_TOKEN=your_plex_token
```
4. Start the bot:
```bash
python src/run_selfbot.py
```

## Available Commands

- `!search <query>` - Search your Plex library
- `!stream <query>` - Play media in voice channel
- `!pause` - Toggle pause/resume
- `!stop` - Stop playback

## How to Use

1. Join a Discord voice channel
2. Search for media: `!search movie_name`
3. Start streaming: `!stream movie_name`
4. Start Discord screenshare
5. Select the VLC window
6. Everyone can now watch together!

## Getting Required Tokens

### Discord Token
1. Open Discord in browser
2. Press Ctrl+Shift+I
3. Go to Network tab
4. Send a message in any channel
5. Find a request starting with "messages"
6. Look for "authorization" in request headers

### Plex Token
1. Log into Plex
2. Go to https://plex.tv/claim
3. Copy your token

## Troubleshooting

### VLC Issues
- Verify VLC is installed
- Check it's in your system PATH
- Try reinstalling VLC

### Playback Issues
- Confirm Plex server is running
- Check your Plex token
- Verify media exists in library

### Connection Issues
- Validate Discord token
- Ensure you're in a voice channel
- Check internet connection

## Important Notes

⚠️ **Please be aware:**
- This is a selfbot (runs on your personal Discord account)
- Selfbots are against Discord's Terms of Service
- Use responsibly and at your own risk
- Ensure adequate bandwidth for streaming

## Requirements

- Python 3.8+
- VLC Media Player
- Discord account
- Plex Media Server
- Stable internet connection

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Verify your configuration
3. Ensure all requirements are met
4. Check your internet connection
5. Try restarting VLC/Discord

## Security

- Never share your Discord token
- Keep your Plex token private
- Use secure connections only
- Regularly update dependencies
