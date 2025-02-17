# OSRS Discord Activity Server

A server-side implementation of Old School RuneScape that runs entirely on the backend and displays through Discord's activity feature. All game logic, calculations, and state management happen server-side, with Discord serving purely as the display and input interface.

## Architecture Overview

- **Server-Side Game Engine**:
  - Complete OSRS game logic implementation
  - State management and persistence
  - Real-time game calculations
  - Player session handling
  - Multiplayer coordination
  
- **Discord Integration**:
  - Activity iframe display
  - Text channel fallback mode
  - Command handling
  - Real-time state updates
  - Voice channel integration

## Display Methods

1. **Discord Activity Mode**:
   - Runs in Discord's built-in activity iframe
   - Real-time WebSocket updates
   - Visual game rendering
   - Integrated with voice channels

2. **Text Channel Fallback**:
   - ASCII-style representation
   - Command-based interaction
   - Full feature parity with visual mode
   - Works in any Discord channel

## Server Features

- **Game Logic**:
  - Exact OSRS formulas and mechanics
  - Complete combat system
  - All skills and training methods
  - Inventory and equipment management
  - NPC interactions
  - World map and navigation

- **Multiplayer**:
  - Synchronized game state
  - Player interactions
  - Trading system
  - Chat functionality
  - Party system

- **Data Management**:
  - Persistent player data
  - State synchronization
  - Session management
  - Secure data storage

## Server Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/osrs-discord-server.git
cd osrs-discord-server
```

2. Install dependencies:
```bash
npm install
```

3. Configure Discord Application:
   - Create application at https://discord.com/developers/applications
   - Enable Activity Feature
   - Configure Activity Settings
   - Set up OAuth2 credentials
   - Enable required gateway intents

4. Environment Configuration:
```env
# Discord Configuration
DISCORD_APP_ID=your_app_id
DISCORD_PUBLIC_KEY=your_public_key
DISCORD_BOT_TOKEN=your_bot_token

# Server Configuration
PORT=8080
WS_PORT=8081
NODE_ENV=development

# Database Configuration (if using)
DATABASE_URL=your_database_url
```

5. Start the server:
```bash
npm run dev
```

## Technical Implementation

### Server Architecture
- Node.js/TypeScript backend
- WebSocket server for real-time updates
- State management system
- Player session handling
- Discord API integration

### Game Engine
- OSRS mechanics implementation
- Combat calculations
- Skill systems
- World management
- NPC AI
- Pathfinding

### Discord Integration
- Activity API implementation
- Voice channel integration
- Command handling
- State synchronization
- Real-time updates

## Usage in Discord

1. Start an activity in a voice channel:
   ```
   /osrs start
   ```

2. Join the voice channel to access the activity

3. Game commands:
   ```
   /move <x> <y>     - Move to location
   /attack <target>   - Attack NPC/player
   /skill <action>    - Perform skill action
   /inventory        - Check inventory
   /stats           - View stats
   /help            - Show all commands
   ```

## Development

### Adding New Features
1. Implement server-side logic
2. Add state management
3. Create Discord command handlers
4. Update display system
5. Test multiplayer synchronization

### Testing
```bash
# Run server tests
npm test

# Run integration tests
npm run test:integration

# Test Discord integration
npm run test:discord
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement server-side changes
4. Test thoroughly
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OSRS Wiki for game mechanics data
- Discord for Activity API
- RuneLite for inspiration
- OSRS community for testing

## Support

For server issues or feature requests, please create an issue in the repository. 