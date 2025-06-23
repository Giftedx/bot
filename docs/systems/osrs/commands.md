# OSRS Discord Commands

> **Note for contributors:** Please follow the [Documentation Standards](../../guides/documentation/standards.md) and use the [documentation templates](../../templates/) when updating or adding commands to this document.

## Metadata
- **Last Updated**: 2024-06-07
- **Version**: 1.0.0
- **Status**: Audited & Updated
- **Authors**: [Contributors]
- **Related Documents**: [Command Reference](../../commands/command-reference.md), [OSRS System README](./README.md)

## Overview

This document lists all available OSRS-related Discord commands, their usage, and examples. Commands are organized by category and include required permissions and cooldown information.

## Table of Contents
1. [Command Categories](#command-categories)
2. [Player Stats](#player-stats)
3. [Items & Prices](#items--prices)
4. [Combat](#combat)
5. [Skills](#skills)
6. [Achievements](#achievements)
7. [Utility](#utility)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [References](#references)
11. [Change Log](#change-log)

## Command Categories

- [Player Stats](#player-stats)
- [Items & Prices](#items--prices)
- [Combat](#combat)
- [Skills](#skills)
- [Achievements](#achievements)
- [Utility](#utility)

## Player Stats

### `/stats`
Display player's skill levels and experience.

**Usage**
```
/stats [username] [skill]
```

**Parameters**
- `username` (optional): OSRS username (defaults to linked account)
- `skill` (optional): Specific skill to look up

**Examples**
```
/stats
/stats Zezima
/stats Zezima woodcutting
```

**Response**
```
📊 Stats for Zezima:
Combat Level: 126
Total Level: 2277
Total XP: 200,000,000

Skills:
Attack: 99 (13,034,431 xp)
Strength: 99 (13,034,431 xp)
...
```

### `/hiscores`
Look up player's hiscores rankings.

**Usage**
```
/hiscores [username] [skill]
```

**Cooldown**: 30 seconds
**Required Permission**: None

## Items & Prices

### `/price`
Look up Grand Exchange prices.

**Usage**
```
/price <item> [quantity]
```

**Parameters**
- `item`: Item name or ID
- `quantity` (optional): Number of items (default: 1)

**Examples**
```
/price "Abyssal whip"
/price "Dragon bones" 1000
```

### `/ge`
Search Grand Exchange listings.

**Usage**
```
/ge search <query>
/ge watch <item>
/ge alerts <item> <price>
```

**Subcommands**
- `search`: Search for items
- `watch`: Track item prices
- `alerts`: Set price alerts

**Examples**
```
/ge search "dragon"
/ge watch "Abyssal whip"
/ge alerts "Dragon bones" >3000
```

## Combat

### `/combat`
Calculate combat-related statistics.

**Usage**
```
/combat calc [stats...]
/combat max-hit [weapon]
```

**Examples**
```
/combat calc attack:99 strength:99
/combat max-hit "Abyssal whip"
```

### `/gear`
Display or calculate gear setups.

**Usage**
```
/gear show [setup]
/gear dps <monster>
```

**Examples**
```
/gear show melee
/gear dps "Corporeal Beast"
```

## Skills

### `/xp`
Calculate experience-related information.

**Usage**
```
/xp calc <level> [current_xp]
/xp time <skill> <target_level>
```

**Examples**
```
/xp calc 99
/xp time woodcutting 99
```

### `/track`
Track skill progress.

**Usage**
```
/track <skill> <target_level>
/track list
/track remove <skill>
```

**Examples**
```
/track woodcutting 99
/track list
```

## Achievements

### `/achievements`
View achievement progress.

**Usage**
```
/achievements [category]
/achievements search <query>
```

**Examples**
```
/achievements quests
/achievements search "dragon slayer"
```

### `/diary`
View achievement diary progress.

**Usage**
```
/diary [area]
/diary requirements <area>
```

**Examples**
```
/diary varrock
/diary requirements karamja
```

## Utility

### `/wiki`
Search the OSRS Wiki.

**Usage**
```
/wiki <query>
```

**Examples**
```
/wiki "dragon slayer requirements"
```

### `/calc`
Various OSRS calculators.

**Usage**
```
/calc xp <skill> <start_level> <end_level>
/calc profit <item> <quantity>
```

**Examples**
```
/calc xp woodcutting 1 99
/calc profit "dragon bones" 1000
```

## Command Settings

### Global Settings

- **Default Cooldown**: 3 seconds
- **Error Handling**: Commands will provide feedback on errors
- **Permissions**: Most commands available to all users
- **Rate Limiting**: 100 commands per minute per user

### Admin Commands

Admin commands require the `MANAGE_SERVER` permission:

- `/osrs config`: Configure OSRS bot settings
- `/osrs reset`: Reset user data
- `/osrs blacklist`: Manage command blacklist

## Embed Formatting

Commands use consistent embed formatting:

```python
embed = discord.Embed(
    title="Command Title",
    description="Command description",
    color=discord.Color.blue()
)
embed.add_field(name="Field Name", value="Field Value")
embed.set_footer(text="Footer text")
```

## Error Messages

Common error messages and their meanings:

| Error | Description | Resolution |
|-------|-------------|------------|
| Player not found | Username doesn't exist | Check spelling |
| Invalid level | Level out of range (1-99) | Enter valid level |
| Rate limited | Too many requests | Wait and retry |
| API Error | OSRS API unavailable | Try again later |

## Examples

### Skill Tracking
```
User: /track woodcutting 99
Bot: 🎯 Now tracking Woodcutting
Current Level: 75
XP to 99: 11,834,431
Progress: 23%
```

### Price Check
```
User: /price "Abyssal whip"
Bot: 💰 Abyssal whip
Price: 2,500,000 gp
Trend: +2.3% (24h)
Volume: 1,234 traded
```

## Best Practices
- Use exact item and skill names for best results.
- Link your OSRS account for personalized stats and tracking.
- Use `/help` for command syntax and options.
- Check cooldowns to avoid rate limits.

## Troubleshooting
| Issue | Solution | Notes |
|-------|----------|-------|
| Command not found | Ensure you are using the correct prefix or slash command | Check bot permissions |
| Incorrect stats | Verify your OSRS username is linked and spelled correctly | Use `/link` if needed |
| Price not updating | Grand Exchange data may be delayed | Try again later |

## References
- [Documentation Standards](../../guides/documentation/standards.md)
- [Documentation Templates](../../templates/)
- [Command Reference](../../commands/command-reference.md)
- [OSRS System README](./README.md)

## Change Log
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-06-07 | 1.0.0 | Audited, updated formatting, added metadata, best practices, troubleshooting, references, and changelog sections | [AI/Contributors] |

## Related Documentation
- [OSRS API Documentation](./api.md)
- [Bot Configuration](../../configuration/bot.md)
- [Command Framework](../../features/commands/README.md) 