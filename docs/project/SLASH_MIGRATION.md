# Slash Command Migration Tracking

## Overview

This document tracks the migration of bot commands to Discord's slash command system.

## Migration Status

### Overall Progress
- Total Commands: 35
- Migrated: 4 (11%)
- In Progress: 4 (11%)
- Not Started: 27 (77%)
- Deprecated: 0 (0%)

## Command Categories

### 1. Plex Media Commands (🟡 In Progress)

#### Media Playback
- [x] `/plex-play` - Play media
- [x] `/plex-search` - Search media
- [x] `/plex-status` - Show playback status
- [x] `/plex-libraries` - List libraries
- [ ] `/plex-queue` - Manage play queue
- [ ] `/plex-playlist` - Manage playlists

#### Media Control
- [x] Play/Pause (button)
- [x] Stop (button)
- [x] Seek (button)
- [ ] Volume control
- [ ] Quality control

### 2. OSRS Commands (🔴 Not Started)

#### Pet System
- [ ] `/osrs-pets list` - List all pets
- [ ] `/osrs-pets show` - Show pet details
- [ ] `/osrs-pets track` - Track pet progress
- [ ] `/osrs-pets stats` - Show pet statistics

#### Skills
- [ ] `/osrs-skills` - Show skill levels
- [ ] `/osrs-xp` - Show XP gains
- [ ] `/osrs-goals` - Set/show goals
- [ ] `/osrs-compare` - Compare stats

#### Economy
- [ ] `/osrs-price` - Check item prices
- [ ] `/osrs-ge` - Grand Exchange info
- [ ] `/osrs-profit` - Profit calculations
- [ ] `/osrs-alerts` - Price alerts

### 3. Pokemon Commands (🔴 Not Started)

#### Pokemon Info
- [ ] `/pokemon-info` - Pokemon details
- [ ] `/pokemon-move` - Move information
- [ ] `/pokemon-type` - Type effectiveness
- [ ] `/pokemon-ability` - Ability information

#### Team Building
- [ ] `/pokemon-team` - Team management
- [ ] `/pokemon-analyze` - Team analysis
- [ ] `/pokemon-coverage` - Type coverage
- [ ] `/pokemon-suggest` - Team suggestions

### 4. Admin Commands (🔴 Not Started)

#### Configuration
- [ ] `/admin-config` - View/edit config
- [ ] `/admin-perms` - Manage permissions
- [ ] `/admin-roles` - Role management
- [ ] `/admin-logs` - View logs

#### Maintenance
- [ ] `/admin-status` - System status
- [ ] `/admin-cache` - Cache management
- [ ] `/admin-backup` - Backup controls
- [ ] `/admin-update` - Update system

## Migration Notes

### 1. Command Structure Changes
- All commands use slash command format
- Subcommands for related functionality
- Options for command parameters
- Command group organization

### 2. Permission Changes
- Application command permissions
- Default permission requirements
- Role-based access control
- Channel-specific permissions

### 3. Response Changes
- Ephemeral responses where appropriate
- Deferred responses for long operations
- Interactive components (buttons, selects)
- Error handling improvements

### 4. Testing Requirements
- Command registration verification
- Permission testing
- Response format validation
- Component interaction testing

## Implementation Priorities

### Phase 1 (Current)
1. Complete Plex media commands
2. Add interaction components
3. Update permission system
4. Document new commands

### Phase 2 (Next)
1. Migrate OSRS commands
2. Add data visualization
3. Implement tracking features
4. Update documentation

### Phase 3 (Future)
1. Migrate Pokemon commands
2. Add team building features
3. Implement analysis tools
4. Complete documentation

### Phase 4 (Final)
1. Migrate admin commands
2. Add monitoring tools
3. Implement backup system
4. Finalize documentation

## Technical Considerations

### 1. Command Registration
```python
@tree.command(name="command-name", description="Command description")
@app_commands.describe(
    param1="Parameter description",
    param2="Parameter description"
)
async def command(interaction: discord.Interaction, param1: str, param2: int):
    # Implementation
    pass
```

### 2. Response Handling
```python
async def handle_command(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        # Long operation
        result = await do_something()
        await interaction.followup.send(result)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)
```

### 3. Component Integration
```python
class CommandView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="Action"))
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Validate interaction
        return True
```

## Migration Checklist

For each command:
- [ ] Create slash command structure
- [ ] Implement command logic
- [ ] Add permission checks
- [ ] Add response handling
- [ ] Implement components
- [ ] Add error handling
- [ ] Write tests
- [ ] Update documentation
- [ ] Test in development
- [ ] Deploy to production
- [ ] Verify functionality
- [ ] Update command list

## Resources

### Documentation
- [Discord.py Docs](https://discordpy.readthedocs.io/)
- [Discord API Docs](https://discord.com/developers/docs/)
- [Application Commands](https://discord.com/developers/docs/interactions/application-commands)

### Tools
- Discord Developer Portal
- Application Command Manager
- Permission Calculator
- Testing Framework 