# Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Configuration](#configuration)
6. [Security](#security)
7. [Monitoring](#monitoring)
8. [Maintenance](#maintenance)

## Prerequisites

### System Requirements
- CPU: 2+ cores
- RAM: 2GB minimum
- Storage: 20GB minimum
- Network: 100Mbps minimum

### Software Requirements
- Python 3.8+
- Redis 6+
- Node.js 14+
- Nginx (recommended)
- SSL certificate
- Plex Media Server

### Accounts and Tokens
- Discord Bot Token
- Plex Token
- Domain Name (recommended)

## Deployment Options

### 1. Docker Deployment (Recommended)
- Containerized environment
- Easy scaling
- Consistent deployments
- Simple updates

### 2. Manual Deployment
- Full control
- Custom configuration
- Direct system access
- Lower resource overhead

## Docker Deployment

### Using Docker Compose

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     bot:
       build: .
       restart: unless-stopped
       environment:
         - DISCORD_TOKEN=${DISCORD_TOKEN}
         - PLEX_URL=${PLEX_URL}
         - PLEX_TOKEN=${PLEX_TOKEN}
         - REDIS_HOST=redis
       depends_on:
         - redis
   
     redis:
       image: redis:6-alpine
       restart: unless-stopped
       volumes:
         - redis_data:/data
   
     nginx:
       image: nginx:alpine
       restart: unless-stopped
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf:ro
         - ./ssl:/etc/nginx/ssl:ro
   
   volumes:
     redis_data:
   ```

2. **Create .env file**
   ```env
   DISCORD_TOKEN=your_discord_token
   PLEX_URL=https://your-plex-server:32400
   PLEX_TOKEN=your_plex_token
   REDIS_HOST=redis
   REDIS_PORT=6379
   ```

3. **Create Dockerfile**
   ```dockerfile
   FROM python:3.8-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD ["python", "-m", "src.bot"]
   ```

4. **Create nginx.conf**
   ```nginx
   events {
       worker_connections 1024;
   }
   
   http {
       upstream bot_api {
           server bot:8000;
       }
   
       server {
           listen 443 ssl;
           server_name your-domain.com;
   
           ssl_certificate /etc/nginx/ssl/cert.pem;
           ssl_certificate_key /etc/nginx/ssl/key.pem;
   
           location / {
               proxy_pass http://bot_api;
               proxy_set_header Upgrade $http_upgrade;
               proxy_set_header Connection "upgrade";
               proxy_set_header Host $host;
           }
       }
   }
   ```

5. **Deploy**
   ```bash
   docker-compose up -d
   ```

### Docker Management

1. **View Logs**
   ```bash
   docker-compose logs -f
   ```

2. **Update Services**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

3. **Scale Services**
   ```bash
   docker-compose up -d --scale bot=2
   ```

## Manual Deployment

### System Setup

1. **Update System**
   ```bash
   sudo apt update
   sudo apt upgrade
   ```

2. **Install Dependencies**
   ```bash
   sudo apt install python3.8 python3.8-venv redis-server nginx
   ```

3. **Create Service User**
   ```bash
   sudo useradd -r -s /bin/false discord-plex
   ```

### Application Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/discord-plex-player.git
   cd discord-plex-player
   ```

2. **Create Virtual Environment**
   ```bash
   python3.8 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create Systemd Service**
   ```ini
   # /etc/systemd/system/discord-plex.service
   [Unit]
   Description=Discord Plex Player
   After=network.target redis-server.service
   
   [Service]
   Type=simple
   User=discord-plex
   Group=discord-plex
   WorkingDirectory=/opt/discord-plex-player
   Environment=PATH=/opt/discord-plex-player/venv/bin
   ExecStart=/opt/discord-plex-player/venv/bin/python -m src.bot
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Configure Nginx**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
   
       ssl_certificate /etc/ssl/certs/your-cert.pem;
       ssl_certificate_key /etc/ssl/private/your-key.pem;
   
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

5. **Start Services**
   ```bash
   sudo systemctl enable redis-server
   sudo systemctl enable discord-plex
   sudo systemctl enable nginx
   
   sudo systemctl start redis-server
   sudo systemctl start discord-plex
   sudo systemctl start nginx
   ```

## Configuration

### Environment Variables

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_token
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret

# Plex Configuration
PLEX_URL=https://your-plex-server:32400
PLEX_TOKEN=your_plex_token
PLEX_CLIENT_ID=discord-plex-player
PLEX_DEVICE_NAME=Discord Bot

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# Web Configuration
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_DEBUG=false
WEB_SECRET_KEY=your_secret_key
CORS_ORIGINS=https://your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/discord-plex/bot.log
```

### SSL Configuration

1. **Generate Certificate (Let's Encrypt)**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

2. **Self-Signed Certificate**
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout /etc/ssl/private/selfsigned.key \
     -out /etc/ssl/certs/selfsigned.crt
   ```

## Security

### Firewall Configuration

1. **UFW (Uncomplicated Firewall)**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Fail2Ban**
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

### Security Best Practices

1. **File Permissions**
   ```bash
   sudo chown -R discord-plex:discord-plex /opt/discord-plex-player
   sudo chmod 600 /opt/discord-plex-player/.env
   ```

2. **Redis Security**
   ```bash
   # /etc/redis/redis.conf
   bind 127.0.0.1
   requirepass your_strong_password
   ```

3. **Regular Updates**
   ```bash
   sudo apt update
   sudo apt upgrade
   pip install --upgrade -r requirements.txt
   ```

## Monitoring

### System Monitoring

1. **Install Monitoring Tools**
   ```bash
   sudo apt install prometheus node-exporter
   ```

2. **Configure Prometheus**
   ```yaml
   # /etc/prometheus/prometheus.yml
   scrape_configs:
     - job_name: 'discord_plex'
       static_configs:
         - targets: ['localhost:8000']
   ```

3. **Enable Metrics**
   ```python
   from prometheus_client import Counter, Histogram
   
   requests_total = Counter('http_requests_total', 'Total requests')
   request_duration = Histogram('http_request_duration_seconds', 'Request duration')
   ```

### Log Monitoring

1. **Configure Logging**
   ```python
   import logging
   
   logging.basicConfig(
       filename='/var/log/discord-plex/bot.log',
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **Log Rotation**
   ```
   # /etc/logrotate.d/discord-plex
   /var/log/discord-plex/*.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
       create 0640 discord-plex discord-plex
   }
   ```

## Maintenance

### Backup Procedures

1. **Database Backup**
   ```bash
   # Backup Redis
   redis-cli save
   cp /var/lib/redis/dump.rdb /backup/redis/
   
   # Backup Configuration
   cp /opt/discord-plex-player/.env /backup/config/
   ```

2. **Automated Backup Script**
   ```bash
   #!/bin/bash
   
   BACKUP_DIR="/backup/discord-plex"
   DATE=$(date +%Y%m%d)
   
   # Create backup directory
   mkdir -p "$BACKUP_DIR/$DATE"
   
   # Backup Redis
   redis-cli save
   cp /var/lib/redis/dump.rdb "$BACKUP_DIR/$DATE/"
   
   # Backup Configuration
   cp /opt/discord-plex-player/.env "$BACKUP_DIR/$DATE/"
   
   # Compress backup
   cd "$BACKUP_DIR"
   tar czf "$DATE.tar.gz" "$DATE"
   rm -rf "$DATE"
   
   # Remove old backups (keep last 7 days)
   find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
   ```

### Update Procedures

1. **Update Application**
   ```bash
   cd /opt/discord-plex-player
   git pull
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart discord-plex
   ```

2. **Update System**
   ```bash
   sudo apt update
   sudo apt upgrade
   sudo systemctl restart redis-server
   sudo systemctl restart nginx
   ```

### Health Checks

1. **Service Status**
   ```bash
   sudo systemctl status discord-plex
   sudo systemctl status redis-server
   sudo systemctl status nginx
   ```

2. **Log Analysis**
   ```bash
   tail -f /var/log/discord-plex/bot.log
   ```

3. **Resource Usage**
   ```bash
   htop
   df -h
   free -m
   ```

## Troubleshooting

### Common Issues

1. **Bot Not Connecting**
   - Check Discord token
   - Verify network connectivity
   - Check bot permissions

2. **Media Playback Issues**
   - Verify Plex connection
   - Check media permissions
   - Monitor system resources

3. **High Resource Usage**
   - Check log files for errors
   - Monitor Redis memory usage
   - Review system metrics

### Debug Mode

1. **Enable Debug Logging**
   ```env
   LOG_LEVEL=DEBUG
   WEB_DEBUG=true
   ```

2. **View Debug Logs**
   ```bash
   tail -f /var/log/discord-plex/bot.log | grep DEBUG
   ```

## Support

For deployment support:
1. Check deployment documentation
2. Review error logs
3. Join Discord support channel
4. Create GitHub issue 