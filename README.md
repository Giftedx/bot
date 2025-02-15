# OSRS Discord Bot

A feature-rich Discord bot that brings Old School RuneScape gameplay elements to your Discord server.

## Features

### Character System
- Create and manage OSRS characters
- Level up skills through various activities
- Track character progress and stats
- Equipment and inventory management
- Bank system for item storage

### Combat System
- PvE and PvP combat mechanics
- Different combat styles (Accurate, Aggressive, Defensive, Controlled)
- Combat training with XP gains
- Equipment bonuses and combat calculations
- Combat level calculation

### Quest System
- Multiple quests with varying difficulty levels
- Quest requirements (skills, items, quest points)
- Quest rewards (XP, items, quest points)
- Track quest progress and completion status

### Trading System
- Player-to-player trading
- Trade offers with expiration
- Safe trading interface
- Trade history tracking

### World System
- Multiple game worlds
- Different world types (regular, PvP, skill total)
- World hopping functionality
- World-specific features and restrictions

### Bank System
- Store and manage items
- View bank contents by category
- Deposit and withdraw items
- Search bank contents

## Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Discord Bot Token

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/osrs-discord-bot.git
cd osrs-discord-bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
- Create a PostgreSQL database
- Copy `.env.example` to `.env`
- Update the database URL in `.env`

5. Configure the bot:
- Add your Discord bot token to `.env`
- Customize other settings in `config.yaml` if needed

6. Initialize the database:
```bash
python run.py --init-db
```

7. Start the bot:
```bash
python run.py
```

## Usage

### Basic Commands
- `!osrs create <name>` - Create a new character
- `!osrs stats` - View character stats
- `!osrs train <skill>` - Train a skill
- `!osrs inventory` - View inventory

### Combat Commands
- `!combat train <style>` - Train combat skills
- `!combat stats` - View combat stats
- `!combat styles` - View combat styles
- `!combat attack <player>` - Attack another player

### Quest Commands
- `!quest list` - List all quests
- `!quest info <quest>` - View quest details
- `!quest start <quest>` - Start a quest
- `!quest progress` - View quest progress

### Trading Commands
- `!trade offer <player> <item> <amount>` - Offer a trade
- `!trade accept <trade_id>` - Accept a trade
- `!trade decline <trade_id>` - Decline a trade
- `!trade cancel <trade_id>` - Cancel your trade offer
- `!trade list` - List your active trades

### Bank Commands
- `!osrs bank` - View bank commands
- `!osrs bank view` - View bank contents
- `!osrs bank deposit <item> [amount]` - Deposit items
- `!osrs bank withdraw <item> [amount]` - Withdraw items
- `!osrs bank search <query>` - Search bank items

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Old School RuneScape for inspiration
- Discord.py library
- PostgreSQL
- All contributors and users of the bot
