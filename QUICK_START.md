# WATCHKEEPER v2.0 - Quick Start Guide

Get WATCHKEEPER running in **5 minutes**!

## Prerequisites

- Docker & Docker Compose installed
- 4GB RAM minimum
- 20GB disk space
- Internet connection

## Option 1: Automated Setup (Recommended)

### Run the Quick Start Script

```bash
# Clone repository (if not already)
git clone https://github.com/your-org/watchkeeper.git
cd watchkeeper

# Run automated setup
./scripts/quick_start.sh
```

This script will:
- ✅ Create .env with secure keys
- ✅ Start all Docker services
- ✅ Run database migrations
- ✅ Create admin user
- ✅ Initialize search indices
- ✅ Start monitoring stack

**Done!** Jump to [Access Your Applications](#access-your-applications)

---

## Option 2: Manual Setup

### Step 1: Configure Environment (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Generate secure keys
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python3 -c "import secrets; print('ENCRYPTION_MASTER_KEY=' + secrets.token_urlsafe(32))" >> .env
```

### Step 2: Start Services (2 minutes)

```bash
# Start core services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Verify all services are running
docker-compose ps
```

**Expected output:** All services should show "Up" or "healthy"

### Step 3: Initialize Database (1 minute)

```bash
# Run database migrations
docker-compose exec api alembic upgrade head

# Create admin user and seed data
docker-compose exec api python scripts/init_db.py --seed --init-search
```

**You'll see:**
```
✓ Created admin user: admin
  Email: admin@watchkeeper.org
  Password: Admin123!
  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!
```

### Step 4: Start Frontend (1 minute)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

---

## Access Your Applications

### 🎯 **Main Dashboard**
**URL:** http://localhost:3000

**Login:**
- Username: `admin`
- Password: `Admin123!`

⚠️ **Change this password immediately after first login!**

### 📊 **API Documentation**
**URL:** http://localhost:8000/docs

Interactive Swagger UI to test all endpoints

### 📈 **Grafana Monitoring**
**URL:** http://localhost:3001

**Login:**
- Username: `admin`
- Password: `admin123`

### 🔍 **Prometheus**
**URL:** http://localhost:9090

Raw metrics and query builder

### 🔎 **Elasticsearch**
**URL:** http://localhost:9200

Search engine health and statistics

---

## Verify Everything Works

### 1. Test API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Should return: {"status":"healthy"}
```

### 2. Test Login

Open http://localhost:3000 in your browser:
- Should see login page
- Enter admin/Admin123!
- Should redirect to dashboard

### 3. Test Dashboard

You should see:
- ✅ Stats cards showing metrics
- ✅ Intelligence feed (may be empty initially)
- ✅ Interactive map
- ✅ Alerts panel

### 4. Test Intelligence Collection

```bash
# Manually trigger collection
docker-compose exec celery_worker celery -A app.celery_app call app.tasks.intelligence.collect_all_sources

# Check logs
docker-compose logs celery_worker --tail=50
```

---

## Quick Tasks

### Change Admin Password

1. Login to dashboard (http://localhost:3000)
2. Click profile icon → Settings
3. Change password
4. Save

### Add a New Intelligence Source

Edit `config/comprehensive_sources.json`:

```json
{
  "id": 100,
  "name": "My Custom Source",
  "url": "https://example.com/feed.xml",
  "type": "rss",
  "category": "security",
  "reliability": 8,
  "enabled": true
}
```

Restart services:
```bash
docker-compose restart celery_worker
```

### Report an Incident

1. Go to http://localhost:3000/incidents/new
2. Fill in the form
3. Click "Use my current location" for GPS
4. Submit

### Search Intelligence

1. Go to http://localhost:3000/search
2. Enter search query (e.g., "security threat")
3. Use advanced filters if needed
4. Click Search

---

## Troubleshooting

### Services Won't Start

```bash
# Check what's running
docker-compose ps

# View logs for specific service
docker-compose logs api
docker-compose logs postgres
docker-compose logs elasticsearch

# Restart all services
docker-compose restart
```

### Database Connection Error

```bash
# Wait longer for PostgreSQL to initialize
sleep 60

# Check PostgreSQL is running
docker-compose exec postgres pg_isready
```

### Elasticsearch Not Ready

```bash
# Elasticsearch takes longer to start (60-90 seconds)
sleep 90

# Check Elasticsearch health
curl http://localhost:9200/_cluster/health
```

### Frontend Won't Build

```bash
cd frontend

# Clear node modules
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Try again
npm run dev
```

### Port Already in Use

If ports 3000, 8000, 5432, or 9200 are already in use:

Edit `docker-compose.yml` and change the port mappings:

```yaml
ports:
  - "8080:8000"  # Change 8000 to 8080
```

---

## Next Steps

### For Development

1. **Read the docs:**
   - `README.md` - Complete overview
   - `DEPLOYMENT_GUIDE.md` - Production deployment
   - `MONITORING.md` - Monitoring setup
   - `SEARCH.md` - Search functionality

2. **Configure intelligence sources:**
   - Edit `config/comprehensive_sources.json`
   - Add your preferred sources
   - Restart celery worker

3. **Set up alerts:**
   - Configure SMTP settings in `.env`
   - Create alert rules via API
   - Test alert delivery

### For Production

1. **Security hardening:**
   - Change all default passwords
   - Configure SSL/TLS
   - Set up firewall rules
   - Review security checklist in `DEPLOYMENT_GUIDE.md`

2. **Configure monitoring:**
   - Set up Slack/PagerDuty webhooks
   - Configure email alerts
   - Review Grafana dashboards

3. **Set up backups:**
   - Configure automated database backups
   - Set up Elasticsearch snapshots
   - Test restore procedures

---

## Getting Help

### Documentation
- `README.md` - Main documentation
- `SYSTEM_STATUS.md` - Feature status
- `DEPLOYMENT_GUIDE.md` - Production guide

### Testing
```bash
# Run integration tests
pytest tests/test_integration.py -v

# Test coverage
pytest --cov=app tests/
```

### Support
- **Issues:** GitHub Issues
- **Email:** support@watchkeeper.org
- **Documentation:** See `/docs` folder

---

## Success! You're Running WATCHKEEPER 🎉

You now have:
- ✅ Fully functional API
- ✅ Real-time dashboard
- ✅ 58 intelligence sources collecting automatically
- ✅ Elasticsearch search
- ✅ Monitoring with Grafana
- ✅ WebSocket real-time updates

**Next:** Start exploring the dashboard and customize for your needs!

**Remember:** Change the default admin password!

---

**WATCHKEEPER v2.0** - Protecting missionaries through intelligence and technology

*Last Updated: 2024-11-10*
