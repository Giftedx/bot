# Command Migration Status

## Overview
This document tracks the migration of commands from the old bot model to the new Discord application slash command structure.

## Plex Commands (In Progress)

### Completed
- ✅ `plex-search` - Search media in Plex libraries
- ✅ `plex-recent` - Show recently added media
- ✅ `plex-stop` - Stop media playback

### In Progress
- 🟡 `plex-play` - Play media (needs testing)
- 🟡 `plex-pause` - Pause media (needs testing)
- 🟡 `plex-resume` - Resume media (needs testing)

### To Do
- 🔴 `plex-libraries` - List available libraries
- 🔴 `plex-queue` - Show play queue
- 🔴 `plex-next` - Skip to next item
- 🔴 `plex-previous` - Go to previous item

## OSRS Commands (Not Started)

### High Priority
- 🔴 `osrs-stats` - Show player stats
- 🔴 `osrs-price` - Check item prices
- 🔴 `osrs-ge` - Grand Exchange lookup

### Medium Priority
- 🔴 `osrs-quest` - Quest information
- 🔴 `osrs-hiscore` - Hiscore lookup
- 🔴 `osrs-wiki` - Wiki search

### Low Priority
- 🔴 `osrs-calc` - XP calculator
- 🔴 `osrs-map` - World map location
- 🔴 `osrs-drop` - Drop table lookup

## Pokemon Commands (Not Started)

### High Priority
- 🔴 `pokemon-info` - Pokemon information
- 🔴 `pokemon-move` - Move details
- 🔴 `pokemon-type` - Type effectiveness

### Medium Priority
- 🔴 `pokemon-ability` - Ability information
- 🔴 `pokemon-item` - Item details
- 🔴 `pokemon-nature` - Nature effects

### Low Priority
- 🔴 `pokemon-location` - Spawn locations
- 🔴 `pokemon-evolution` - Evolution chains
- 🔴 `pokemon-sprite` - Pokemon sprites

## Migration Notes

### Plex Commands
- Media control commands need proper error handling
- Progress bar component needs testing
- Library integration needs optimization
- Queue management needs implementation

### OSRS Commands
- API integration needs planning
- Rate limiting consideration required
- Cache implementation needed
- Error handling standardization required

### Pokemon Commands
- Data source selection needed
- Cache strategy required
- Image handling needs planning
- Rate limit considerations

## Testing Requirements

### Automated Tests
- Command registration
- Parameter validation
- Response formatting
- Error handling
- Rate limiting
- Cache behavior

### Manual Tests
- User interaction flow
- Response timing
- Media controls
- Visual elements
- Error messages
- Help text

## Next Steps

1. Complete Plex media control commands
2. Document completed commands
3. Begin OSRS command planning
4. Update progress tracking

## Status Key
- ✅ Completed and Tested
- 🟡 In Progress/Needs Testing
- 🔴 Not Started
- ⚫ Deprecated/Removed 