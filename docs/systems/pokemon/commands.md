# Pokemon Discord Commands

## Overview

This document lists all available Pokemon-related Discord commands, their usage, and examples. Commands are organized by category and include required permissions and cooldown information.

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

## Related Documentation
- [Pokemon API Documentation](./api.md)
- [Battle System](./battle-system.md)
- [Trading System](./trading-system.md)

## Changelog

### v1.0.0 - 2024-02-16
- Initial Pokemon commands
- Battle system commands
- Trading system commands
- Training & evolution commands

_Last Updated: February 2024_ 