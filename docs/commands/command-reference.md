# Command Reference

## Table of Contents
1. [General Commands](#general-commands)
2. [Media Commands](#media-commands)
3. [Playback Controls](#playback-controls)
4. [Queue Management](#queue-management)
5. [Playlist Commands](#playlist-commands)
6. [Voice Channel Commands](#voice-channel-commands)
7. [Admin Commands](#admin-commands)

## General Commands

### Help and Information

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!help` | Display help menu | `!help [command]` | `!help play` |
| `!about` | Show bot information | `!about` | `!about` |
| `!ping` | Check bot latency | `!ping` | `!ping` |
| `!stats` | Display bot statistics | `!stats` | `!stats` |
| `!invite` | Get bot invite link | `!invite` | `!invite` |

### Settings

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!settings` | View/modify user settings | `!settings [setting] [value]` | `!settings volume 0.8` |
| `!prefix` | Change command prefix | `!prefix <new_prefix>` | `!prefix ?` |
| `!language` | Change language | `!language <code>` | `!language en` |

## Media Commands

### Search and Play

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!search` | Search for media | `!search <query>` | `!search Inception` |
| `!play` | Play media | `!play <query/url>` | `!play The Matrix` |
| `!movie` | Search movies | `!movie <title>` | `!movie Interstellar` |
| `!show` | Search TV shows | `!show <title>` | `!show Breaking Bad` |
| `!episode` | Play specific episode | `!episode <show> S01E01` | `!episode Friends S01E01` |

### Media Information

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!info` | Show media info | `!info` | `!info` |
| `!duration` | Show media duration | `!duration` | `!duration` |
| `!quality` | Show/change quality | `!quality [setting]` | `!quality 1080p` |
| `!subtitles` | Manage subtitles | `!subtitles [language]` | `!subtitles en` |

## Playback Controls

### Basic Controls

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!pause` | Pause playback | `!pause` | `!pause` |
| `!resume` | Resume playback | `!resume` | `!resume` |
| `!stop` | Stop playback | `!stop` | `!stop` |
| `!skip` | Skip current media | `!skip` | `!skip` |
| `!previous` | Play previous media | `!previous` | `!previous` |

### Advanced Controls

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!seek` | Seek to position | `!seek <time>` | `!seek 1:30` |
| `!forward` | Fast forward | `!forward [seconds]` | `!forward 30` |
| `!rewind` | Rewind | `!rewind [seconds]` | `!rewind 30` |
| `!volume` | Adjust volume | `!volume <0-100>` | `!volume 80` |
| `!mute` | Toggle mute | `!mute` | `!mute` |

## Queue Management

### Basic Queue Commands

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!queue` | Show queue | `!queue [page]` | `!queue 2` |
| `!clear` | Clear queue | `!clear` | `!clear` |
| `!remove` | Remove from queue | `!remove <position>` | `!remove 3` |
| `!move` | Move item in queue | `!move <from> <to>` | `!move 2 4` |

### Queue Manipulation

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!shuffle` | Shuffle queue | `!shuffle` | `!shuffle` |
| `!loop` | Toggle loop mode | `!loop [mode]` | `!loop queue` |
| `!save` | Save queue as playlist | `!save <name>` | `!save My Mix` |
| `!load` | Load saved queue | `!load <name>` | `!load My Mix` |

## Playlist Commands

### Playlist Management

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!playlist` | Show playlists | `!playlist list` | `!playlist list` |
| `!playlist create` | Create playlist | `!playlist create <name>` | `!playlist create Movies` |
| `!playlist delete` | Delete playlist | `!playlist delete <name>` | `!playlist delete Movies` |
| `!playlist rename` | Rename playlist | `!playlist rename <old> <new>` | `!playlist rename Movies Films` |

### Playlist Operations

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!playlist add` | Add to playlist | `!playlist add <name> <media>` | `!playlist add Movies Inception` |
| `!playlist remove` | Remove from playlist | `!playlist remove <name> <position>` | `!playlist remove Movies 3` |
| `!playlist play` | Play playlist | `!playlist play <name>` | `!playlist play Movies` |
| `!playlist shuffle` | Shuffle playlist | `!playlist shuffle <name>` | `!playlist shuffle Movies` |

## Voice Channel Commands

### Channel Management

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!join` | Join voice channel | `!join [channel]` | `!join Movie Room` |
| `!leave` | Leave voice channel | `!leave` | `!leave` |
| `!switch` | Switch voice channel | `!switch <channel>` | `!switch Gaming` |
| `!summon` | Move bot to your channel | `!summon` | `!summon` |

### Voice Settings

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!bitrate` | Change bitrate | `!bitrate <kbps>` | `!bitrate 128` |
| `!region` | Change voice region | `!region <region>` | `!region us-west` |
| `!disconnect` | Set disconnect timer | `!disconnect <minutes>` | `!disconnect 30` |

## Admin Commands

### Server Management

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!setup` | Initial server setup | `!setup` | `!setup` |
| `!permissions` | Manage permissions | `!permissions <role> <command>` | `!permissions DJ play` |
| `!blacklist` | Manage blacklist | `!blacklist <add/remove> <user>` | `!blacklist add @User` |
| `!config` | Server configuration | `!config <setting> <value>` | `!config prefix !` |

### Bot Management

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `!restart` | Restart bot | `!restart` | `!restart` |
| `!update` | Update bot | `!update` | `!update` |
| `!maintenance` | Toggle maintenance mode | `!maintenance` | `!maintenance` |
| `!logs` | View bot logs | `!logs [lines]` | `!logs 50` |

## Command Syntax

### Notation

- `<required>`: Required argument
- `[optional]`: Optional argument
- `a|b`: Choose between options
- `...`: Multiple arguments allowed

### Examples

```
!play <title|URL> [position]
!search <query> [limit]
!playlist <create|delete|rename> <name>
```

## Command Categories

### By Permission Level

#### User Commands
- Basic playback controls
- Queue viewing
- Media search
- Personal settings

#### DJ Commands
- Queue management
- Playlist creation
- Voice channel controls
- Volume control

#### Admin Commands
- Bot configuration
- Permission management
- Server settings
- Maintenance commands

#### Owner Commands
- Bot restart
- Updates
- Global settings
- System maintenance

### By Function

#### Media Control
- Playback controls
- Volume adjustment
- Quality settings
- Subtitle management

#### Queue Management
- Queue manipulation
- Playlist operations
- Loop settings
- Shuffle controls

#### Voice Channel
- Channel joining/leaving
- Voice region settings
- Bitrate control
- Disconnect timer

#### Configuration
- Bot settings
- Server setup
- Permission management
- Maintenance tools

## Command Aliases

Many commands have aliases for convenience:

| Command | Aliases |
|---------|---------|
| `!play` | `!p`, `!stream` |
| `!queue` | `!q`, `!list` |
| `!skip` | `!s`, `!next` |
| `!pause` | `!stop`, `!halt` |
| `!resume` | `!continue`, `!start` |
| `!volume` | `!vol`, `!v` |
| `!search` | `!find`, `!lookup` |
| `!playlist` | `!pl`, `!list` |
| `!help` | `!h`, `!commands` |

## Command Cooldowns

Some commands have cooldowns to prevent abuse:

| Command | Cooldown |
|---------|----------|
| `!play` | 3 seconds |
| `!search` | 5 seconds |
| `!skip` | 2 seconds |
| `!playlist` | 10 seconds |
| `!update` | 300 seconds |

## Error Messages

Common error messages and their meanings:

| Error | Description | Solution |
|-------|-------------|----------|
| "Not in voice channel" | User must be in voice channel | Join a voice channel |
| "No media playing" | No active playback | Start playing media first |
| "Queue is empty" | Nothing in queue | Add media to queue |
| "Invalid permissions" | Missing required role | Request permission from admin |

## Support

For command support:
1. Use `!help <command>` for detailed help
2. Check command documentation
3. Join Discord support channel
4. Create GitHub issue 