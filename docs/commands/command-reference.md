# Command Reference

> **Note for contributors:** Please follow the [Documentation Standards](../guides/documentation/standards.md) and use the [documentation templates](../templates/) when updating or adding commands to this reference.

## Table of Contents
1. [General Commands](#general-commands)
2. [Media Commands](#media-commands)
3. [Playback Controls](#playback-controls)
4. [Queue Management](#queue-management)
5. [Playlist Commands](#playlist-commands)
6. [Voice Channel Commands](#voice-channel-commands)
7. [Admin Commands](#admin-commands)
8. [OSRS Combat Commands](#osrs-combat-commands)
9. [OSRS Quest Commands](#osrs-quest-commands)
10. [OSRS Trading Commands](#osrs-trading-commands)
11. [OSRS Grand Exchange](#osrs-grand-exchange)
12. [OSRS Progression Commands](#osrs-progression-commands)
13. [Pokemon Commands](#pokemon-commands)

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

> **Note:** All admin commands are now available as both classic (prefix) and slash commands. Use `/config`, `/cmd`, `/welcome`, `/autorole`, `/backup`, `/restore` or their classic equivalents. For full details, see the admin documentation.

### Configuration
- `/config prefix <new_prefix>` or `!config prefix <new_prefix>` — Change the bot's prefix for this server

### Custom Commands
- `/cmd add <name> <response>` or `!cmd add <name> <response>` — Add a custom command
- `/cmd remove <name>` or `!cmd remove <name>` — Remove a custom command
- `/cmd list` or `!cmd list` — List all custom commands

### Welcome & Autorole
- `/welcome #channel <message>` or `!welcome #channel <message>` — Set up or view the welcome message
- `/autorole @role` or `!autorole @role` — Set up or view the autorole for new members

### Backup & Restore
- `/backup` or `!backup` — Create a backup of server settings
- `/restore` or `!restore` — Restore server settings from a backup (attach backup file in classic mode)

## OSRS Combat Commands

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `/fight` | Preview and start a fight with a monster | `/fight <monster_name>` | `/fight Goblin` |
| `/attack` | Attack the monster you are fighting | `/attack` | `/attack` |
| `/flee` | Attempt to flee from combat | `/flee` | `/flee` |

## OSRS Quest Commands

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `/quests` | View your quest list. | `/quests [filter] [page]` | `/quests in_progress 2` |
| `/quest_info` | Get information about a specific quest. | `/quest_info <quest_name>` | `/quest_info "Cook's Assistant"` |

## OSRS Trading Commands

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `/trade offer` | Offer an item to another player. | `/trade offer <recipient> <item_name> [quantity]` | `/trade offer @User "Tuna" 10` |
| `/trade accept` | Accept a trade offer. | `/trade accept <trade_id>` | `/trade accept 123` |
| `/trade decline` | Decline a trade offer. | `/trade decline <trade_id>` | `/trade decline 123` |
| `/trade cancel` | Cancel a trade offer you sent. | `/trade cancel <trade_id>` | `/trade cancel 123` |
| `/trade list` | List your pending trades. | `/trade list` | `/trade list` |

## OSRS Grand Exchange

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `/ge buy` | Place a buy offer. | `/ge buy <item> <quantity> <price>` | `/ge buy "Lobster" 100 250` |
| `/ge sell` | Place a sell offer. | `/ge sell <item> <quantity> <price>` | `/ge sell "Yew logs" 500 300` |
| `/ge status` | Check your offers. | `/ge status` | `/ge status` |
| `/ge cancel` | Cancel an offer. | `/ge cancel <offer_id>` | `/ge cancel 456` |
| `/ge price` | Check item price. | `/ge price <item>` | `/ge price "Cannonball"` |
| `/ge history` | View item price history. | `/ge history <item>` | `/ge history "Rune platebody"` |

## OSRS Progression Commands

| Command | Description | Usage | Example |
|---------|-------------|--------|---------|
| `/achievements` | View your achievements. | `/achievements [category] [page]` | `/achievements Combat 1` |
| `/collection_log` | View your collection log. | `/collection_log [category] [page]` | `/collection_log Bosses 2` |

## Pokemon Commands

> **Note:** All main Pokemon commands are now available as both classic (prefix) and slash commands. See [Pokemon System Commands](../systems/pokemon/commands.md) for full details and usage examples.

- `/pokemon catch <name>` or `!pokemon catch <name>` — Catch a wild Pokemon
- `/pokemon list` or `!pokemon list` — View your Pokemon collection
- `/pokemon info <name>` or `!pokemon info <name>` — View details about a specific Pokemon
- `/pokemon release <name>` or `!pokemon release <name>` — Release a Pokemon from your collection
- `/pokemon battle @user` or `!pokemon battle @user` — Challenge another trainer to a battle
- `/pokemon accept` or `!pokemon accept` — Accept a pending battle challenge
- `/pokemon move <name>` or `!pokemon move <name>` — Use a move in battle
- `/pokemon switch <name>` or `!pokemon switch <name>` — Switch your active Pokemon in battle
- `/pokemon train <name>` or `!pokemon train <name>` — Train your Pokemon
- `/pokemon evolve <name>` or `!pokemon evolve <name>` — Evolve your Pokemon if eligible
- `/pokemon stats <name>` or `!pokemon stats <name>` — View your Pokemon's training progress
- `/pokemon moves <name>` or `!pokemon moves <name>` — View or manage your Pokemon's moves

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