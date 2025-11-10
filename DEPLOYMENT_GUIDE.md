# WATCHKEEPER v2.0 - Complete Deployment Guide

Production-ready deployment guide for the WATCHKEEPER missionary intelligence and safety system.

## Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Production Deployment](#production-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

## System Overview

WATCHKEEPER v2.0 is a comprehensive intelligence collection and personnel safety system featuring:

**Core Components:**
- FastAPI REST API with WebSocket support
- PostgreSQL database
- Redis cache and message broker
- Elasticsearch for advanced search
- Celery background task processing
- React frontend dashboard

**Key Features:**
- Real-time intelligence collection from 58+ sources
- Automated alert system with escalation
- Personnel tracking and geofencing
- ML-based threat prediction
- Multi-language NLP processing
- End-to-end encryption for sensitive data
- Comprehensive monitoring with Prometheus & Grafana
- Organization collaboration platform

## Prerequisites

### Required Software

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git**
- **Node.js** 18+ (for frontend development)
- **Python** 3.11+ (for local development)

### System Requirements

**Minimum (Development):**
- 4 GB RAM
- 20 GB disk space
- 2 CPU cores

**Recommended (Production):**
- 16 GB RAM
- 100 GB SSD
- 4+ CPU cores
- 1 Gbps network

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/watchkeeper.git
cd watchkeeper
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Essential variables:**

```env
# Security
SECRET_KEY=your_very_long_random_secret_key_here_change_this
ENCRYPTION_MASTER_KEY=another_very_long_random_key_for_encryption

# Database
POSTGRES_USER=watchkeeper_user
POSTGRES_PASSWORD=strong_database_password
POSTGRES_DB=watchkeeper

# Redis
REDIS_URL=redis://redis:6379/0

# Email (for alerts)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@watchkeeper.org
SMTP_PASSWORD=your_email_password

# External APIs (optional)
OPENAI_API_KEY=sk-...  # For enhanced NLP
MAPBOX_TOKEN=pk...  # For advanced mapping
```

### 3. Start Services

```bash
# Start core services
docker-compose up -d postgres redis elasticsearch

# Wait for services to be healthy (30-60 seconds)
docker-compose ps

# Initialize database
docker-compose exec postgres psql -U watchkeeper_user -d watchkeeper -f /docker-entrypoint-initdb.d/init_db.sql

# Run migrations
docker-compose exec api alembic upgrade head

# Start all services
docker-compose up -d

# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d
```

### 4. Initialize Search Indices

```bash
# Initialize Elasticsearch indices
docker-compose exec api python -c "from app.tasks.search import initialize_indices; initialize_indices()"

# Index existing data
docker-compose exec api python -c "from app.tasks.search import reindex_all; reindex_all()"
```

### 5. Create Admin User

```bash
docker-compose exec api python -c "
from app.database import SessionLocal
from app.models.user import User
from app.core.auth import get_password_hash

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@watchkeeper.org',
    hashed_password=get_password_hash('ChangeThisPassword123!'),
    is_active=True,
    is_admin=True
)
db.add(admin)
db.commit()
print('Admin user created')
"
```

### 6. Access Applications

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Elasticsearch**: http://localhost:9200

## Production Deployment

### Security Hardening

#### 1. SSL/TLS Configuration

```bash
# Install Certbot
apt-get install certbot

# Generate certificates
certbot certonly --standalone -d watchkeeper.yourdomain.com

# Configure nginx reverse proxy
```

**nginx.conf example:**

```nginx
server {
    listen 443 ssl http2;
    server_name watchkeeper.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/watchkeeper.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/watchkeeper.yourdomain.com/privkey.pem;

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}
```

#### 2. Firewall Configuration

```bash
# Allow only necessary ports
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

#### 3. Database Security

```sql
-- Disable remote PostgreSQL access
# In postgresql.conf:
listen_addresses = 'localhost'

-- Use strong passwords
ALTER USER watchkeeper_user WITH PASSWORD 'very_strong_password';

-- Restrict permissions
REVOKE ALL ON DATABASE watchkeeper FROM PUBLIC;
GRANT CONNECT ON DATABASE watchkeeper TO watchkeeper_user;
```

### High Availability Setup

#### 1. Database Replication

```yaml
# docker-compose.ha.yml
services:
  postgres-primary:
    image: postgres:15-alpine
    environment:
      POSTGRES_REPLICATION_MODE: master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: repl_password

  postgres-replica1:
    image: postgres:15-alpine
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_MASTER_HOST: postgres-primary
```

#### 2. Load Balancing

```bash
# Install HAProxy
apt-get install haproxy

# Configure load balancing across multiple API instances
```

**haproxy.cfg:**

```
frontend watchkeeper_api
    bind *:8080
    default_backend api_servers

backend api_servers
    balance roundrobin
    server api1 localhost:8001 check
    server api2 localhost:8002 check
    server api3 localhost:8003 check
```

### Scaling

#### Scale API Workers

```bash
# Scale to 3 API instances
docker-compose up -d --scale api=3
```

#### Scale Celery Workers

```bash
# Scale to 5 Celery workers
docker-compose up -d --scale celery_worker=5
```

#### Elasticsearch Cluster

```yaml
# Add ES nodes
elasticsearch-node2:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  environment:
    - discovery.seed_hosts=elasticsearch,elasticsearch-node2
    - cluster.initial_master_nodes=elasticsearch,elasticsearch-node2

elasticsearch-node3:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  environment:
    - discovery.seed_hosts=elasticsearch,elasticsearch-node2,elasticsearch-node3
    - cluster.initial_master_nodes=elasticsearch,elasticsearch-node2,elasticsearch-node3
```

## Configuration

### Intelligence Sources

Edit `config/comprehensive_sources.json` to add/modify sources:

```json
{
  "sources": [
    {
      "id": 100,
      "name": "Custom RSS Feed",
      "url": "https://example.com/rss",
      "type": "rss",
      "category": "custom",
      "reliability": 8,
      "update_frequency": 1800,
      "enabled": true,
      "priority": "high"
    }
  ]
}
```

### Alert Rules

Configure in database or via API:

```python
# Create alert rule
POST /api/v1/alerts/rules
{
  "name": "High Threat Intelligence",
  "condition": "threat_level >= 8",
  "severity": "critical",
  "target_groups": ["field_personnel", "leadership"],
  "notification_channels": ["email", "sms", "push"]
}
```

### Geofences

```python
# Create danger zone
POST /api/v1/geofences
{
  "name": "Kabul Red Zone",
  "fence_type": "danger_zone",
  "geometry_type": "circle",
  "coordinates": [[34.5553, 69.2075]],
  "radius": 5000,
  "threat_level": 9,
  "active": true
}
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Database
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping

# Elasticsearch
curl http://localhost:9200/_cluster/health
```

### Key Metrics to Monitor

1. **API Performance**
   - Request rate: < 1000 req/min (normal)
   - Response time: < 200ms (p95)
   - Error rate: < 1%

2. **Personnel Safety**
   - Personnel in danger zones: 0 (alert if > 0)
   - Missed check-ins: 0 (critical alert)
   - Active personnel: Monitor trends

3. **Intelligence Collection**
   - Collection rate: ~1 item/minute
   - Failure rate: < 5%
   - Source availability: > 90%

4. **System Resources**
   - CPU usage: < 70%
   - Memory usage: < 80%
   - Disk usage: < 85%

### Alerts

Configure Alertmanager for critical notifications:

```bash
# Test email alerts
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {"alertname": "test", "severity": "critical"},
    "annotations": {"description": "Test alert"}
  }]'
```

## Backup & Recovery

### Database Backup

```bash
# Automated daily backup
cat > /etc/cron.daily/watchkeeper-backup << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
docker-compose exec -T postgres pg_dump -U watchkeeper_user watchkeeper | \
  gzip > /backups/watchkeeper-db-$DATE.sql.gz

# Retain 30 days
find /backups -name "watchkeeper-db-*.sql.gz" -mtime +30 -delete
EOF

chmod +x /etc/cron.daily/watchkeeper-backup
```

### Elasticsearch Backup

```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/watchkeeper_backups" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/backups/elasticsearch"
    }
  }'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/watchkeeper_backups/snapshot_$(date +%Y%m%d)"
```

### Recovery

```bash
# Restore database
gunzip < /backups/watchkeeper-db-20241110.sql.gz | \
  docker-compose exec -T postgres psql -U watchkeeper_user watchkeeper

# Restore Elasticsearch
curl -X POST "localhost:9200/_snapshot/watchkeeper_backups/snapshot_20241110/_restore"
```

## Troubleshooting

### Common Issues

#### API Won't Start

```bash
# Check logs
docker-compose logs api

# Common causes:
# 1. Database not ready - wait 30 seconds
# 2. Port conflict - change API_PORT in .env
# 3. Missing environment variables - check .env
```

#### Intelligence Not Collecting

```bash
# Check Celery workers
docker-compose logs celery_worker

# Manually trigger collection
docker-compose exec api python -c "
from app.tasks.intelligence import collect_all_sources
collect_all_sources()
"

# Check source configuration
cat config/comprehensive_sources.json | grep enabled
```

#### Elasticsearch Issues

```bash
# Check ES health
curl http://localhost:9200/_cluster/health?pretty

# Common fixes:
# Increase memory
# Edit docker-compose.yml:
#   ES_JAVA_OPTS=-Xms1g -Xmx1g

# Clear corrupted indices
curl -X DELETE "localhost:9200/watchkeeper_*"

# Reinitialize
docker-compose exec api python -c "
from app.tasks.search import initialize_indices, reindex_all
initialize_indices()
reindex_all()
"
```

#### High Memory Usage

```bash
# Check container stats
docker stats

# Identify culprit and restart
docker-compose restart elasticsearch

# Permanent fix: increase resources
# Edit docker-compose.yml deploy.resources.limits
```

### Log Locations

```bash
# API logs
docker-compose logs -f api

# Celery logs
docker-compose logs -f celery_worker

# PostgreSQL logs
docker-compose logs -f postgres

# Application logs (mounted volume)
tail -f logs/api/api.log
tail -f logs/celery/celery.log
```

### Support

For issues not covered here:

1. Check documentation:
   - `ENHANCED_FEATURES.md` - Feature details
   - `MONITORING.md` - Monitoring setup
   - `SEARCH.md` - Search functionality

2. Contact support:
   - Email: support@watchkeeper.org
   - Slack: #watchkeeper-support

3. Report bugs:
   - GitHub Issues: https://github.com/your-org/watchkeeper/issues

## Maintenance

### Regular Tasks

**Daily:**
- [ ] Check critical alerts
- [ ] Verify intelligence collection
- [ ] Review personnel safety status

**Weekly:**
- [ ] Review Grafana dashboards
- [ ] Check disk space
- [ ] Verify backups

**Monthly:**
- [ ] Update dependencies
- [ ] Review and tune alert thresholds
- [ ] Capacity planning
- [ ] Security audit

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build

# Apply database migrations
docker-compose exec api alembic upgrade head

# Restart services
docker-compose up -d
```

## Performance Tuning

### Database Optimization

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM intelligence_items WHERE threat_level >= 8;

-- Add indices for common queries
CREATE INDEX idx_intelligence_threat ON intelligence_items(threat_level);
CREATE INDEX idx_intelligence_region ON intelligence_items(region);
CREATE INDEX idx_intelligence_date ON intelligence_items(created_at DESC);

-- Vacuum database
VACUUM ANALYZE;
```

### Redis Optimization

```bash
# Increase max memory
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### API Optimization

```python
# Enable response caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

---

**WATCHKEEPER v2.0** - Protecting missionaries through intelligence and technology

Last Updated: 2024-11-10
Version: 2.0.0
