# Quick Start Guide

## Introduction

Discord Plex Player is a Discord bot that allows you to stream media from your Plex server directly in Discord voice channels. This guide will help you get started quickly.

## Prerequisites

- Discord account with admin permissions on your server
- Plex Media Server
- Python 3.8 or higher
- Redis server

## 5-Minute Setup

### 1. Invite the Bot

1. Click [this link](https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=36768832&scope=bot%20applications.commands) to invite the bot
2. Select your server
3. Authorize the required permissions

### 2. Get Your Plex Token

1. Sign in to Plex
2. Go to Settings > Account
3. Copy your Plex token (or use [this guide](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/))

### 3. Basic Configuration

Create a `.env` file with these essential settings:

```env
DISCORD_TOKEN=your_discord_token
PLEX_URL=https://your-plex-server:32400
PLEX_TOKEN=your_plex_token
```

### 4. Start the Bot

```bash
# Install dependencies
pip install -r requirements.txt

# Start the bot
python -m src.bot
```

### 5. Basic Commands

Try these commands to get started:

```
!join           # Join your voice channel
!search Matrix  # Search for "Matrix"
!play           # Play the first result
!help           # Show all commands
```

## Basic Usage

### Playing Media

1. Join a voice channel
2. Search for media:
   ```
   !search Inception
   ```
3. Play from search results:
   ```
   !play 1
   ```
   Or play directly:
   ```
   !play Inception
   ```

### Playback Controls

```
!pause    # Pause playback
!resume   # Resume playback
!stop     # Stop playback
!volume 80 # Set volume to 80%
```

### Queue Management

```
!queue    # Show current queue
!skip     # Skip current media
!clear    # Clear the queue
```

## Common Tasks

### Finding Media

1. **Search Movies**
   ```
   !movie Inception
   ```

2. **Search TV Shows**
   ```
   !show Breaking Bad
   ```

3. **Play Specific Episode**
   ```
   !episode "Breaking Bad" S01E01
   ```

### Managing Playback

1. **Adjust Volume**
   ```
   !volume 80
   ```

2. **Seek in Media**
   ```
   !seek 1:30
   ```

3. **Change Quality**
   ```
   !quality 1080p
   ```

## Quick Tips

### Voice Channel Tips

1. Bot automatically joins your channel when you play media
2. Use `!summon` to move bot to your channel
3. Bot leaves after 5 minutes of inactivity

### Playback Tips

1. Use arrow up to repeat last command
2. Add multiple items to queue with `!play`
3. Use `!loop` for continuous playback

### Quality Tips

1. Default quality is 1080p
2. Lower quality if experiencing buffering
3. Use `!bitrate` to adjust audio quality

## Troubleshooting

### Common Issues

1. **Bot Won't Join Channel**
   - Ensure you're in a voice channel
   - Check bot permissions
   - Try `!join` manually

2. **Media Won't Play**
   - Verify Plex server is running
   - Check media exists in Plex
   - Ensure correct permissions

3. **Poor Playback Quality**
   - Lower stream quality
   - Check internet connection
   - Adjust bitrate settings

### Quick Fixes

1. **Bot Not Responding**
   ```
   !ping  # Check if bot is alive
   ```

2. **Playback Issues**
   ```
   !stop   # Stop current playback
   !leave  # Make bot leave channel
   !join   # Rejoin channel
   ```

3. **Audio Issues**
   ```
   !reconnect  # Reconnect to voice channel
   ```

## Next Steps

### Advanced Features

1. Create playlists
   ```
   !playlist create Movies
   !playlist add Movies Inception
   ```

2. Set up auto-disconnect
   ```
   !disconnect 30  # Leave after 30 minutes
   ```

3. Configure server settings
   ```
   !setup  # Run initial setup
   ```

### Customization

1. Change command prefix
   ```
   !prefix ?
   ```

2. Set default volume
   ```
   !settings volume 70
   ```

3. Configure notifications
   ```
   !settings notifications on
   ```

## Getting Help

### Quick Help

1. Use `!help` command
   ```
   !help         # General help
   !help play    # Help with play command
   ```

2. Check bot status
   ```
   !status       # Show bot status
   !ping         # Check response time
   ```

### Additional Support

1. Join our [Discord Server](https://discord.gg/your-invite)
2. Check [Documentation](https://github.com/yourusername/discord-plex-player/docs)
3. Create [GitHub Issue](https://github.com/yourusername/discord-plex-player/issues)

## Command Reference

### Essential Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!play` | Play media | `!play Inception` |
| `!pause` | Pause playback | `!pause` |
| `!resume` | Resume playback | `!resume` |
| `!stop` | Stop playback | `!stop` |
| `!volume` | Set volume | `!volume 80` |

### Quick Reference

| Category | Commands |
|----------|----------|
| Playback | `!play`, `!pause`, `!resume`, `!stop` |
| Queue | `!queue`, `!skip`, `!clear` |
| Voice | `!join`, `!leave`, `!summon` |
| Info | `!help`, `!status`, `!ping` |

## Security Note

- Never share your Plex token
- Keep `.env` file secure
- Use strong Redis password
- Regularly update bot

## Updates

Stay updated:
1. Watch our GitHub repository
2. Join Discord for announcements
3. Use `!update` to check for updates

## Support

Need help?
1. Check documentation
2. Use `!help` command
3. Join Discord support
4. Create GitHub issue 