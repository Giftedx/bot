# Installation Guide

## Prerequisites

### Required Software
- Python 3.8 or higher
- Node.js 14+ and npm
- Redis server
- PostgreSQL database
- Discord account and bot token
- Plex Media Server and token

### System Requirements
- CPU: 2+ cores recommended
- RAM: 4GB minimum, 8GB recommended
- Storage: 1GB for application, more depending on cache settings
- Network: Stable internet connection

## Installation Methods

### 1. Quick Install (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/discord-plex-player.git
cd discord-plex-player

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
cd src/frontend && npm install
```

### 2. Manual Installation

#### Backend Setup
1. Install Python dependencies:
```bash
pip install discord.py>=2.0.0
pip install Flask>=2.0.0
pip install plexapi>=4.0.0
# ... (see requirements.txt for full list)
```

2. Install Redis:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Download from https://redis.io/download
```

3. Install PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql

# macOS
brew install postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

#### Frontend Setup
1. Install Node.js dependencies:
```bash
cd src/frontend
npm install
```

## Configuration

### 1. Environment Variables
Copy `.env.template` to `.env` and configure:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_token
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret

# Plex Configuration
PLEX_URL=http://your-plex-server:32400
PLEX_TOKEN=your_plex_token

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 2. Discord Bot Setup
1. Create application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create bot and get token
3. Enable required intents:
   - Message Content Intent
   - Server Members Intent
   - Voice State Intent

### 3. Plex Setup
1. Get Plex token from your account
2. Configure Plex Media Server settings
3. Ensure remote access is enabled if needed

## Post-Installation

### 1. Database Setup
```bash
# Create database
createdb discord_plex_player

# Run migrations
python manage.py db upgrade
```

### 2. Start Services
```bash
# Start Redis
redis-server

# Start PostgreSQL (if not running)
sudo service postgresql start  # Linux
brew services start postgresql # macOS

# Start backend
python src/bot.py

# Start frontend development server
cd src/frontend && npm start
```

### 3. Verify Installation
1. Check bot comes online in Discord
2. Verify web interface loads
3. Test basic commands
4. Check database connection
5. Verify Redis connection

## Common Issues

### 1. Dependencies
- Issue: `pip install` fails
- Solution: Update pip (`pip install --upgrade pip`)

### 2. Database
- Issue: Cannot connect to PostgreSQL
- Solution: Check service is running and credentials are correct

### 3. Discord
- Issue: Bot doesn't come online
- Solution: Verify token and intents

### 4. Plex
- Issue: Cannot connect to Plex server
- Solution: Check URL and token, verify server is accessible

## Security Notes

1. Token Security
- Never commit `.env` file
- Rotate tokens regularly
- Use secure token storage

2. Database Security
- Use strong passwords
- Limit database access
- Regular backups

3. Network Security
- Configure firewalls
- Use HTTPS for web interface
- Implement rate limiting

## Next Steps

1. Read [Quick Start Guide](../getting-started/quickstart.md)
2. Configure [Environment](../getting-started/environment.md)
3. Review [Security Model](../architecture/security.md)
4. Set up [Monitoring](../deployment/monitoring.md)

## Support

If you encounter issues:
1. Check [Troubleshooting Guide](../troubleshooting/common-issues.md)
2. Search [GitHub Issues](https://github.com/yourusername/discord-plex-player/issues)
3. Join our [Discord Support Server](https://discord.gg/your-invite)
4. Create a new issue if problem persists 