# Deployment Setup Guide

## Infrastructure Requirements

### 1. Hardware Requirements
- **Minimum Specifications**
  - CPU: 4 cores
  - RAM: 8GB
  - Storage: 50GB SSD
  - Network: 100Mbps

- **Recommended Specifications**
  - CPU: 8 cores
  - RAM: 16GB
  - Storage: 100GB SSD
  - Network: 1Gbps

### 2. Software Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- Nginx 1.20+
- Let's Encrypt
- PostgreSQL 14+
- Redis 6+

## Production Environment

### 1. Base Configuration
```bash
# Create production directory
mkdir -p /opt/discord-app
cd /opt/discord-app

# Clone repository
git clone <repository-url> .

# Create environment file
cp .env.example .env.prod
```

### 2. Docker Compose Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
    networks:
      - app_network

  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app_network

  redis:
    image: redis:6
    volumes:
      - redis_data:/data
    networks:
      - app_network

  nginx:
    image: nginx:1.20
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - app_network

networks:
  app_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### 3. Nginx Configuration
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream app_servers {
        server app:8000;
    }

    server {
        listen 80;
        server_name example.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name example.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location / {
            proxy_pass http://app_servers;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## Deployment Process

### 1. Initial Deployment
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Apply database migrations
docker-compose -f docker-compose.prod.yml exec app python manage.py migrate

# Create admin user
docker-compose -f docker-compose.prod.yml exec app python manage.py createsuperuser
```

### 2. SSL Certificate Setup
```bash
# Install certbot
apt-get update
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d example.com

# Auto-renewal setup
certbot renew --dry-run
```

### 3. Monitoring Setup
```bash
# Install monitoring tools
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d

# Configure Prometheus
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'discord_app'
    static_configs:
      - targets: ['app:8000']
EOF

# Configure Grafana dashboards
# Import dashboard JSON files
```

## Backup Procedures

### 1. Database Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backup

# Backup PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_$DATE.sql

# Cleanup old backups
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
```

### 2. Application Backup
```bash
#!/bin/bash
# app_backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backup/app

# Backup application data
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    /opt/discord-app

# Cleanup old backups
find $BACKUP_DIR -name "app_*.tar.gz" -mtime +7 -delete
```

## Scaling Considerations

### 1. Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  app:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

### 2. Load Balancing
```nginx
# nginx.conf with load balancing
upstream app_servers {
    least_conn;  # Least connections algorithm
    server app_1:8000;
    server app_2:8000;
    server app_3:8000;
}
```

## Maintenance Procedures

### 1. Updates and Upgrades
```bash
# Pull latest changes
git pull origin main

# Build new images
docker-compose -f docker-compose.prod.yml build

# Graceful restart
docker-compose -f docker-compose.prod.yml up -d --no-deps --build app
```

### 2. Monitoring and Alerts
```yaml
# alertmanager.yml
route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1h
  receiver: 'discord-webhook'

receivers:
  - name: 'discord-webhook'
    webhook_configs:
      - url: 'https://discord.com/api/webhooks/...'
```

## Rollback Procedures

### 1. Application Rollback
```bash
# Revert to previous version
git checkout <previous-commit>

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --no-deps --build app
```

### 2. Database Rollback
```bash
# Restore from backup
gunzip -c /backup/db_<date>.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U $DB_USER $DB_NAME
```

## Security Considerations

### 1. Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

### 2. Security Headers
```nginx
# nginx security headers
add_header X-Frame-Options "SAMEORIGIN";
add_header X-XSS-Protection "1; mode=block";
add_header X-Content-Type-Options "nosniff";
add_header Strict-Transport-Security "max-age=31536000";
``` 