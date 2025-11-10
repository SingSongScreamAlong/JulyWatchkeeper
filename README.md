# WATCHKEEPER v2.0

**Advanced Missionary Intelligence & Personnel Safety System**

WATCHKEEPER is a production-ready intelligence collection and personnel safety platform designed specifically for missionary organizations operating in high-risk environments. The system provides real-time threat intelligence, automated alerts, personnel tracking, and comprehensive safety features.

---

## 🚀 What's New in v2.0

### Phase 1: Critical Infrastructure
- ✅ **Real-time Alert System** with escalation and multi-channel notifications
- ✅ **Field Incident Reporting** with multimedia support and geolocation
- ✅ **Personnel Tracking** with check-in monitoring and location history
- ✅ **Geofencing** with danger zones and automatic alerts
- ✅ **Safe Contact Management** with encrypted storage
- ✅ **Celery Background Workers** for automated task processing
- ✅ **WebSocket Real-time Updates** for live dashboard updates
- ✅ **58 Intelligence Sources** (expanded from 10)
- ✅ **Mobile Offline Sync** for field operations

### Phase 2: Security & Reliability
- ✅ **End-to-End Encryption** for sensitive personnel data
- ✅ **Audit Logging** for compliance and security
- ✅ **Rate Limiting** for API protection
- ✅ **Comprehensive Test Suite** with 95%+ coverage

### Phase 3: Enhanced Intelligence
- ✅ **Automated Playbook Engine** for incident response
- ✅ **Travel Route Safety Analysis** with threat mapping
- ✅ **ML Threat Prediction** using scikit-learn
- ✅ **Multi-Language NLP** supporting 10 languages
- ✅ **Sentiment Analysis** and entity extraction

### Phase 4: Scale & Collaboration
- ✅ **Elasticsearch Integration** for advanced search
- ✅ **Organization Collaboration Platform** for intelligence sharing
- ✅ **React Dashboard** with real-time updates
- ✅ **Monitoring Stack** (Prometheus, Grafana, Loki, Alertmanager)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Documentation](#-documentation)
- [Screenshots](#-screenshots)
- [Technology Stack](#-technology-stack)
- [Development](#-development)
- [Production Deployment](#-production-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Features

### Intelligence Collection
- **58+ Global Sources**: Government advisories, news agencies, NGO reports, security feeds
- **Automated Collection**: Scheduled polling every 15-30 minutes
- **Multi-Language Support**: Automatic translation from 10 languages to English
- **Threat Scoring**: ML-based threat level assessment (1-10 scale)
- **Geolocation**: Automatic location extraction and mapping
- **Sentiment Analysis**: Emotional tone detection for context

### Alert System
- **Real-Time Alerts**: WebSocket-powered instant notifications
- **Smart Routing**: Rule-based alert distribution to specific personnel/groups
- **Escalation**: Automatic escalation for unacknowledged critical alerts
- **Multi-Channel**: Email, SMS, push notifications, in-app alerts
- **Alert History**: Full audit trail of all alerts and responses

### Personnel Safety
- **Location Tracking**: Real-time GPS tracking of field personnel
- **Check-in Monitoring**: Automatic detection of missed check-ins
- **Geofencing**: Danger zone alerts when personnel enter high-risk areas
- **Safe Contacts**: Encrypted emergency contact information
- **Travel Planning**: Route safety analysis before deployment

### Incident Management
- **Field Reporting**: Mobile-friendly incident submission with photos
- **Severity Classification**: Automatic categorization and prioritization
- **Status Tracking**: Investigation workflow from report to resolution
- **Geospatial Analysis**: Map-based incident visualization
- **Related Intelligence**: Automatic linking to relevant intelligence items

### Advanced Features
- **ML Threat Prediction**: Forecast regional threat escalation 7-30 days ahead
- **Automated Playbooks**: Pre-configured response workflows for incidents
- **Collaboration Platform**: Secure intelligence sharing between organizations
- **Advanced Search**: Elasticsearch-powered full-text search with filters
- **Trending Analysis**: Identify emerging threats from intelligence patterns
- **Cultural Context**: Regional and cultural insights for intelligence

### Monitoring & Observability
- **Real-Time Dashboards**: Grafana visualization of key metrics
- **Alert Management**: Prometheus alerting with intelligent routing
- **Log Aggregation**: Centralized logging with Loki
- **Performance Metrics**: API, database, and worker performance tracking
- **Health Checks**: Automated system health monitoring

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  Dashboard · Intelligence Feed · Alerts · Map · Search       │
└─────────────────┬───────────────────────────────────────────┘
                  │ WebSocket + REST API
┌─────────────────┴───────────────────────────────────────────┐
│                  API Layer (FastAPI)                         │
│  Authentication · Rate Limiting · Validation · Metrics       │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬──────────────┬─────────────┐
    │             │              │              │             │
┌───▼───┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
│Postgres│   │  Redis  │   │Elastic  │   │ Celery  │   │Monitoring│
│Database│   │ Cache   │   │ Search  │   │ Workers │   │ Stack   │
└────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
                                              │
                    ┌─────────────────────────┴─────────┐
                    │                                   │
              ┌─────▼─────┐                      ┌─────▼─────┐
              │Intelligence│                      │   Alert   │
              │ Collection │                      │Processing │
              └───────────┘                      └───────────┘
```

### Components

**API Server (FastAPI)**
- REST endpoints for CRUD operations
- WebSocket server for real-time updates
- JWT authentication
- Request validation with Pydantic
- Automatic API documentation

**Database (PostgreSQL)**
- 18+ tables for comprehensive data model
- Full-text search capabilities
- Geospatial extensions (PostGIS)
- JSONB for flexible metadata

**Cache & Broker (Redis)**
- API response caching
- Celery message broker
- Rate limiting storage
- Session management

**Search (Elasticsearch)**
- Full-text search across all content
- Faceted search and aggregations
- Geospatial queries
- Real-time indexing

**Background Workers (Celery)**
- Intelligence collection (every 30 min)
- Alert processing and sending
- Personnel check-in monitoring
- ML model training
- Search index updates

**Monitoring (Prometheus + Grafana)**
- 50+ custom metrics
- Pre-built dashboards
- Alert rules for critical conditions
- Log aggregation with Loki

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB RAM minimum
- 20GB disk space

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/watchkeeper.git
cd watchkeeper

# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

### 2. Start Services

```bash
# Start core services
docker-compose up -d

# Wait 30 seconds for initialization

# Check health
docker-compose ps
```

### 3. Create Admin User

```bash
docker-compose exec api python scripts/create_admin.py
```

### 4. Access Applications

- **API**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Grafana**: http://localhost:3001 (admin/admin123)

**Default credentials:**
- Username: `admin`
- Password: (set during admin creation)

### 5. Initialize Search & Collection

```bash
# Initialize Elasticsearch indices
docker-compose exec api python -c "from app.tasks.search import initialize_indices; initialize_indices()"

# Start intelligence collection
docker-compose exec celery_worker celery -A app.celery_app inspect active
```

---

## 📚 Documentation

### Core Documentation
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)** - All features explained
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Development progress

### Component Documentation
- **[MONITORING.md](MONITORING.md)** - Monitoring & observability setup
- **[SEARCH.md](SEARCH.md)** - Elasticsearch search guide
- **[frontend/README.md](frontend/README.md)** - Frontend development

### API Documentation
- Interactive API docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

---

## 📸 Screenshots

### Dashboard Overview
Real-time intelligence feed with active alerts and threat map

### Threat Map
Interactive map showing intelligence locations, incidents, and personnel

### Alert Management
Real-time alerts with one-click acknowledgment

### Intelligence Search
Advanced search with filters, highlighting, and relevance scoring

### Analytics
Threat prediction charts and regional statistics

---

## 🛠 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL ORM
- **Celery** - Distributed task queue
- **Redis** - Cache and message broker
- **Elasticsearch** - Search engine
- **PostgreSQL** - Primary database

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **React Query** - Server state management
- **Recharts** - Data visualization
- **Leaflet** - Interactive maps
- **Socket.IO** - WebSocket client

### Machine Learning
- **scikit-learn** - Threat prediction models
- **langdetect** - Language detection
- **TextBlob** - Sentiment analysis
- **googletrans** - Translation

### Monitoring
- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **Loki** - Log aggregation
- **Alertmanager** - Alert routing

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Orchestration
- **Nginx** - Reverse proxy (production)
- **Certbot** - SSL certificates

---

## 💻 Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8 app/
black app/
mypy app/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding Intelligence Sources

Edit `config/comprehensive_sources.json`:

```json
{
  "id": 100,
  "name": "Custom Source",
  "url": "https://example.com/feed.xml",
  "type": "rss",
  "category": "security",
  "reliability": 8,
  "enabled": true
}
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific module
pytest app/tests/test_intelligence.py

# Integration tests
pytest app/tests/integration/
```

---

## 🚢 Production Deployment

### System Requirements
- **CPU**: 4+ cores
- **RAM**: 16GB+
- **Disk**: 100GB SSD
- **Network**: 1Gbps
- **OS**: Ubuntu 22.04 LTS or similar

### Deployment Steps

1. **Server Setup**
```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt-get install docker-compose-plugin
```

2. **Clone & Configure**
```bash
git clone https://github.com/your-org/watchkeeper.git
cd watchkeeper

# Configure production settings
cp .env.example .env
nano .env  # Set production values
```

3. **SSL Setup**
```bash
# Install Certbot
apt-get install certbot

# Generate certificate
certbot certonly --standalone -d watchkeeper.yourdomain.com
```

4. **Deploy**
```bash
# Start services
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Initialize
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/create_admin.py
```

5. **Configure Monitoring**
```bash
# Access Grafana
# http://your-server:3001

# Import dashboards
# monitoring/grafana/dashboards/*.json
```

### Security Checklist
- [ ] Change all default passwords
- [ ] Configure firewall (ufw)
- [ ] Enable SSL/TLS
- [ ] Set strong SECRET_KEY
- [ ] Configure backup strategy
- [ ] Enable audit logging
- [ ] Set up intrusion detection
- [ ] Configure rate limiting

### Scaling

**Horizontal Scaling:**
```bash
# Scale API workers
docker-compose up -d --scale api=3

# Scale Celery workers
docker-compose up -d --scale celery_worker=5
```

**Database Replication:**
```bash
# Configure PostgreSQL streaming replication
# See DEPLOYMENT_GUIDE.md for details
```

**Load Balancing:**
```bash
# Configure HAProxy or Nginx upstream
# See DEPLOYMENT_GUIDE.md for configuration
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write/update tests
5. Run linting and tests
6. Commit with clear messages (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Standards
- Follow PEP 8 for Python code
- Use type hints
- Write docstrings for functions/classes
- Maintain test coverage above 90%
- Update documentation

### Reporting Issues
- Use GitHub Issues
- Provide clear description
- Include steps to reproduce
- Add relevant logs/screenshots
- Specify environment details

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built for missionary organizations worldwide
- Inspired by the need for better field safety
- Powered by open-source technologies

---

## 📞 Support

- **Documentation**: See `/docs` folder
- **Issues**: GitHub Issues
- **Email**: support@watchkeeper.org
- **Website**: https://watchkeeper.org

---

## 🗺 Roadmap

### Completed (v2.0)
- ✅ Real-time intelligence collection
- ✅ Personnel tracking and geofencing
- ✅ ML-based threat prediction
- ✅ Advanced search with Elasticsearch
- ✅ Comprehensive monitoring

### Planned (v2.1)
- 📱 Native mobile apps (iOS/Android)
- 🤖 AI-powered threat analysis
- 📊 Advanced analytics dashboard
- 🌐 Multi-tenancy support
- 🔐 Two-factor authentication

### Future (v3.0)
- 🛰 Satellite imagery integration
- 🗣 Voice alert system
- 📱 Offline-first mobile app
- 🤝 Enhanced collaboration features
- 🧠 Deep learning threat models

---

**WATCHKEEPER v2.0** - Protecting missionaries through intelligence and technology

*Last Updated: 2024-11-10*
*Version: 2.0.0*
