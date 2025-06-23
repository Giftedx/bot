# Pokemon System Commands

> **Note:** All main Pokemon commands are now available as both classic (prefix) and slash commands. You can use `/pokemon <subcommand>` or `!pokemon <subcommand>` interchangeably. Slash commands provide autocomplete, validation, and improved UX.

## Command List

### Collection Management
- `/pokemon catch <name>` or `!pokemon catch <name>` — Catch a wild Pokemon
- `/pokemon list` or `!pokemon list` — View your Pokemon collection
- `/pokemon info <name>` or `!pokemon info <name>` — View details about a specific Pokemon
- `/pokemon release <name>` or `!pokemon release <name>` — Release a Pokemon from your collection

### Battle System
- `/pokemon battle @user` or `!pokemon battle @user` — Challenge another trainer to a battle
- `/pokemon accept` or `!pokemon accept` — Accept a pending battle challenge
- `/pokemon move <name>` or `!pokemon move <name>` — Use a move in battle
- `/pokemon switch <name>` or `!pokemon switch <name>` — Switch your active Pokemon in battle

### Training & Evolution
- `/pokemon train <name>` or `!pokemon train <name>` — Train your Pokemon
- `/pokemon evolve <name>` or `!pokemon evolve <name>` — Evolve your Pokemon if eligible
- `/pokemon stats <name>` or `!pokemon stats <name>` — View your Pokemon's training progress
- `/pokemon moves <name>` or `!pokemon moves <name>` — View or manage your Pokemon's moves

## Usage Examples
- `/pokemon catch Pikachu` — Try to catch a wild Pikachu
- `/pokemon battle @Ash` — Challenge Ash to a battle
- `/pokemon train Bulbasaur` — Train your Bulbasaur
- `/pokemon info Eevee` — View details about your Eevee

## Tips
- Use slash commands for autocomplete and easier parameter selection.
- All commands support both classic and slash syntax for maximum compatibility.
- For more details on each command, use `/help pokemon <subcommand>` or `!help pokemon <subcommand>`.

## Metadata
- **Last Updated**: 2024-06-07
- **Version**: 1.0.0
- **Status**: Audited & Updated
- **Authors**: [Contributors]
- **Related Documents**: [Command Reference](../../commands/command-reference.md), [Pokemon System README](./README.md)

## Table of Contents
1. [Command Categories](#command-categories)
2. [Pokemon Management](#pokemon-management)
3. [Battle System](#battle-system)
4. [Training & Evolution](#training--evolution)
5. [Trading System](#trading-system)
6. [Items & Inventory](#items--inventory)
7. [Pokedex](#pokedex)
8. [Command Settings](#command-settings)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [References](#references)
12. [Change Log](#change-log)

## Command Categories

- [Pokemon Management](#pokemon-management)
- [Battle System](#battle-system)
- [Training & Evolution](#training--evolution)
- [Trading System](#trading-system)
- [Items & Inventory](#items--inventory)
- [Pokedex](#pokedex)

## Pokemon Management

### `/pokemon`
Display your Pokemon team and storage.

**Usage**
```
/pokemon [box] [page]
```

**Parameters**
- `box` (optional): Box number to view (1-8)
- `page` (optional): Page number for box view

**Examples**
```
/pokemon
/pokemon 2
/pokemon 1 2
```

**Response**
```
📦 Box 1 - Page 1/3
1. Pikachu Lv.25 ⚡ 
   HP: 45/45 | Moves: Thunder Shock, Quick Attack
2. Charmander Lv.15 🔥
   HP: 39/39 | Moves: Scratch, Ember
...
```

### `/team`
Manage your active Pokemon team.

**Usage**
```
/team view
/team set <positions>
/team swap <pos1> <pos2>
```

**Examples**
```
/team view
/team set 1,2,3,4,5,6
/team swap 1 2
```

## Battle System

### `/battle`
Start or manage Pokemon battles.

**Usage**
```
/battle challenge <@user>
/battle accept
/battle move <move>
/battle switch <position>
```

**Examples**
```
/battle challenge @User
/battle move "Thunder Shock"
/battle switch 2
```

### `/wild`
Encounter and catch wild Pokemon.

**Usage**
```
/wild search [area]
/wild catch <pokemon>
/wild run
```

**Examples**
```
/wild search "Viridian Forest"
/wild catch Pikachu
/wild run
```

## Training & Evolution

### `/train`
Train your Pokemon.

**Usage**
```
/train <pokemon> [method]
/train stats
/train moves
```

**Examples**
```
/train Pikachu
/train Pikachu "Thunder Shock"
/train stats
```

### `/evolve`
Evolve your Pokemon.

**Usage**
```
/evolve <pokemon> [item]
```

**Examples**
```
/evolve Pikachu
/evolve Eevee "Fire Stone"
```

## Trading System

### `/trade`
Trade Pokemon with other trainers.

**Usage**
```
/trade offer <@user> <pokemon>
/trade accept
/trade decline
/trade view
```

**Examples**
```
/trade offer @User Pikachu
/trade accept
/trade view
```

## Items & Inventory

### `/inventory`
Manage your items.

**Usage**
```
/inventory [page]
/inventory use <item> <pokemon>
/inventory give <item> <@user>
```

**Examples**
```
/inventory
/inventory use "Rare Candy" Pikachu
/inventory give "Potion" @User
```

## Pokedex

### `/pokedex`
View Pokedex information.

**Usage**
```
/pokedex <pokemon>
/pokedex search <query>
/pokedex caught
```

**Examples**
```
/pokedex Pikachu
/pokedex search "electric"
/pokedex caught
```

## Command Settings

### Global Settings

- **Default Cooldown**: 3 seconds
- **Battle Cooldown**: 30 seconds
- **Catch Cooldown**: 5 minutes
- **Trade Cooldown**: 1 minute

### Admin Commands

Admin commands require the `MANAGE_SERVER` permission:

- `/pokemon config`: Configure Pokemon bot settings
- `/pokemon spawn`: Manage Pokemon spawns
- `/pokemon reset`: Reset user data

## Embed Formatting

Commands use consistent embed formatting:

```python
embed = discord.Embed(
    title="Pokemon Status",
    description="Current Pokemon information",
    color=discord.Color.yellow()
)
embed.add_field(name="Stats", value="HP: 45/45")
embed.set_thumbnail(url="pokemon_image_url")
```

## Error Messages

Common error messages and their meanings:

| Error | Description | Resolution |
|-------|-------------|------------|
| Pokemon not found | Pokemon doesn't exist | Check spelling/ownership |
| Invalid move | Move not learned | Check move list |
| Trade error | Trade invalid | Verify trade details |
| Battle error | Battle issue | Check battle status |

## Examples

### Battle System
```
User: /battle challenge @User
Bot: 🎮 Battle Challenge
Trainer1: @User1
Trainer2: @User2
Format: Singles
Waiting for acceptance...
```

### Trading System
```
User: /trade offer @User Pikachu
Bot: 💱 Trade Offer
Offering: Pikachu Lv.25
To: @User
Status: Pending
Expires in: 5:00
```

## Best Practices
- Use exact Pokemon and item names for best results.
- Link your account for personalized tracking and trading.
- Use `/help` for command syntax and options.
- Check cooldowns to avoid rate limits.

## Troubleshooting
| Issue | Solution | Notes |
|-------|----------|-------|
| Command not found | Ensure you are using the correct prefix or slash command | Check bot permissions |
| Incorrect Pokemon data | Verify your account is linked and spelled correctly | Use `/link` if needed |
| Trade not working | Ensure both users are online and have available slots | Check trade cooldown |

## References
- [Documentation Standards](../../guides/documentation/standards.md)
- [Documentation Templates](../../templates/)
- [Command Reference](../../commands/command-reference.md)
- [Pokemon System README](./README.md)

## Change Log
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-06-07 | 1.0.0 | Audited, updated formatting, added metadata, best practices, troubleshooting, references, and changelog sections | [AI/Contributors] |

## Related Documentation
- [Pokemon API Documentation](./api.md)
- [Battle System](./battle-system.md)
- [Trading System](./trading-system.md) 