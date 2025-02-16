# Deployment Guide

## Overview

This guide covers the deployment process for the Discord application, including environment setup, monitoring, and maintenance.

## Prerequisites

### System Requirements
- Python 3.12+
- Redis 6.0+
- PostgreSQL 13+ (optional)
- FFmpeg
- Systemd (Linux) or Windows Service
- 2GB RAM minimum
- 10GB storage minimum

### Discord Setup
1. Discord Developer Portal
   - Create application
   - Enable required intents
   - Set up OAuth2
   - Configure slash commands

2. Required Permissions
   - application.commands
   - bot (for legacy support)
   - Relevant channel permissions

## Environment Setup

### 1. Production Environment
```bash
# Create production directory
mkdir -p /opt/discord-app
cd /opt/discord-app

# Clone repository
git clone <repository-url> .

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy and edit environment file
cp .env.example .env.production

# Edit production environment
nano .env.production
```

Required variables:
```env
# Discord Application
DISCORD_APP_ID=your_app_id
DISCORD_PUBLIC_KEY=your_public_key
DISCORD_TOKEN=your_token

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379

# Optional Services
PLEX_URL=your_plex_url
PLEX_TOKEN=your_plex_token
```

### 3. Database Setup
```bash
# PostgreSQL setup
sudo -u postgres createuser discord_app
sudo -u postgres createdb discord_app_prod

# Apply migrations
python scripts/db_migrate.py
```

### 4. Redis Setup
```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf

# Enable Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

## Service Setup

### Linux (Systemd)
1. Create service file:
```bash
sudo nano /etc/systemd/system/discord-app.service
```

2. Service configuration:
```ini
[Unit]
Description=Discord Application Service
After=network.target

[Service]
Type=simple
User=discord-app
Group=discord-app
WorkingDirectory=/opt/discord-app
Environment=PATH=/opt/discord-app/venv/bin
EnvironmentFile=/opt/discord-app/.env.production
ExecStart=/opt/discord-app/venv/bin/python -m src.app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Enable and start service:
```bash
sudo systemctl enable discord-app
sudo systemctl start discord-app
```

### Windows Service
1. Install NSSM:
```powershell
choco install nssm
```

2. Create service:
```powershell
nssm install DiscordApp "C:\Program Files\Python312\python.exe"
nssm set DiscordApp AppParameters "-m src.app"
nssm set DiscordApp AppDirectory "C:\Services\discord-app"
nssm set DiscordApp AppEnvironment "PATH=C:\Services\discord-app\venv\Scripts;%PATH%"
```

## Monitoring

### 1. Logging Setup
```bash
# Create log directory
mkdir -p /var/log/discord-app

# Configure logging
nano config/logging.conf
```

Logging configuration:
```python
{
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/discord-app/app.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "standard"
        }
    }
}
```

### 2. Monitoring Tools
1. Set up Prometheus:
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.30.3/prometheus-2.30.3.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*
```

2. Configure metrics:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'discord_app'
    static_configs:
      - targets: ['localhost:8000']
```

### 3. Alert Setup
1. Configure alerting:
```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

2. Alert rules:
```yaml
groups:
  - name: discord_app
    rules:
      - alert: HighErrorRate
        expr: rate(discord_app_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
```

## Backup Procedures

### 1. Database Backup
```bash
# Create backup script
nano scripts/backup_db.sh
```

Backup script:
```bash
#!/bin/bash
BACKUP_DIR="/backup/discord-app"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump discord_app_prod > "$BACKUP_DIR/db_backup_$DATE.sql"
```

### 2. Redis Backup
```bash
# Create Redis backup script
nano scripts/backup_redis.sh
```

Redis backup:
```bash
#!/bin/bash
BACKUP_DIR="/backup/discord-app"
DATE=$(date +%Y%m%d_%H%M%S)
redis-cli save
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"
```

### 3. Automated Backups
```bash
# Add to crontab
0 */6 * * * /opt/discord-app/scripts/backup_db.sh
0 */6 * * * /opt/discord-app/scripts/backup_redis.sh
```

## Maintenance

### 1. Updates
```bash
# Update application
cd /opt/discord-app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart discord-app
```

### 2. Database Maintenance
```bash
# Vacuum database
psql discord_app_prod -c "VACUUM ANALYZE;"

# Reindex
psql discord_app_prod -c "REINDEX DATABASE discord_app_prod;"
```

### 3. Cache Maintenance
```bash
# Clear Redis cache
redis-cli FLUSHALL

# Monitor Redis memory
redis-cli INFO memory
```

## Troubleshooting

### 1. Service Issues
```bash
# Check service status
sudo systemctl status discord-app

# View logs
journalctl -u discord-app -f

# Restart service
sudo systemctl restart discord-app
```

### 2. Database Issues
```bash
# Check connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Kill hanging connections
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'discord_app_prod';"
```

### 3. Cache Issues
```bash
# Check Redis status
redis-cli ping

# Monitor Redis
redis-cli monitor

# Clear specific cache
redis-cli DEL cache_key
```

## Security

### 1. File Permissions
```bash
# Set proper permissions
sudo chown -R discord-app:discord-app /opt/discord-app
sudo chmod -R 750 /opt/discord-app
sudo chmod 640 /opt/discord-app/.env.production
```

### 2. Firewall Rules
```bash
# Allow necessary ports
sudo ufw allow 443/tcp
sudo ufw allow 5432/tcp
sudo ufw allow 6379/tcp
```

### 3. SSL Setup
```bash
# Generate certificate
certbot certonly --standalone -d your-domain.com

# Configure SSL
nano config/nginx.conf
```

## Recovery Procedures

### 1. Database Recovery
```bash
# Restore from backup
psql discord_app_prod < backup_file.sql

# Verify data
psql -c "SELECT count(*) FROM users;"
```

### 2. Cache Recovery
```bash
# Stop Redis
sudo systemctl stop redis-server

# Restore Redis backup
cp redis_backup.rdb /var/lib/redis/dump.rdb

# Start Redis
sudo systemctl start redis-server
```

### 3. Application Recovery
```bash
# Rollback to last working version
git reset --hard last_working_commit
sudo systemctl restart discord-app
``` 