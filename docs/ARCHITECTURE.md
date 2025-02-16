# Discord Application Architecture

## Overview

The application has been migrated from a bot-based model to a full Discord application model, utilizing modern Discord features and best practices.

## Core Components

### 1. Application Client (`src/app/client.py`)
- Modern Discord application client
- Handles interactions and command routing
- Manages application lifecycle
- Implements proper error handling

### 2. Command Handlers (`src/app/commands/`)
- Modular command implementation
- Uses slash commands exclusively
- Proper interaction response handling
- Command groups by feature

### 3. Interaction Components (`src/app/interactions/`)
- Reusable UI components
- Button handlers
- Select menus
- Modal forms

### 4. Integrations (`src/integrations/`)
- External service integrations
- Plex media integration
- OSRS data integration
- Pokemon data integration

## Application Structure

```
src/
├── app/                    # Core application code
│   ├── __init__.py        # Application entry point
│   ├── client.py          # Discord app client
│   ├── commands/          # Command handlers
│   │   ├── __init__.py
│   │   ├── plex.py       # Plex media commands
│   │   ├── pokemon.py    # Pokemon commands
│   │   └── osrs.py       # OSRS commands
│   ├── interactions/      # Interaction handlers
│   │   ├── __init__.py
│   │   ├── components.py # UI components
│   │   └── modals.py    # Form modals
│   └── state.py          # Application state
├── integrations/          # External integrations
├── data/                  # Data management
└── utils/                # Utilities
```

## Migration Notes

### Discord Application Changes
1. Moved from bot model to application model
2. Implemented slash commands
3. Added proper interaction handling
4. Updated permission system
5. Improved error handling

### Plex Integration Changes
1. Updated for interaction model
2. Added media controls
3. Improved player UI
4. Better state management

## Configuration

Required environment variables:
```env
# Discord Application
DISCORD_APP_ID=your_app_id
DISCORD_PUBLIC_KEY=your_public_key
DISCORD_TOKEN=your_token

# Plex Configuration
PLEX_URL=your_plex_url
PLEX_TOKEN=your_plex_token
```

## Development Guidelines

1. Command Implementation
   - Use slash commands exclusively
   - Implement proper permission checks
   - Handle all interaction responses
   - Add command documentation

2. Component Development
   - Create reusable components
   - Implement proper timeout handling
   - Add accessibility features
   - Document component usage

3. Integration Development
   - Implement proper cleanup
   - Handle rate limits
   - Add error recovery
   - Document configuration

## Testing

1. Command Testing
   - Test all command paths
   - Verify permission handling
   - Check interaction responses
   - Validate error handling

2. Component Testing
   - Test component lifecycle
   - Verify interaction handling
   - Check timeout behavior
   - Validate state management

## Deployment

1. Discord Setup
   - Register application
   - Configure permissions
   - Set up slash commands
   - Verify intents

2. Environment Setup
   - Configure variables
   - Set up logging
   - Configure monitoring
   - Set up backups
``` 