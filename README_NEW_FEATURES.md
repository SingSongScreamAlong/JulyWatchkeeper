# WATCHKEEPER - New Features Documentation

This document describes all the new systems and features added to WATCHKEEPER.

## Table of Contents

1. [Background Task Processing](#background-task-processing)
2. [Alert & Notification System](#alert--notification-system)
3. [User Management & RBAC](#user-management--rbac)
4. [Audit Logging](#audit-logging)
5. [Rate Limiting](#rate-limiting)
6. [Export System](#export-system)
7. [Advanced Search](#advanced-search)
8. [Analytics Dashboard](#analytics-dashboard)
9. [Source Verification](#source-verification)
10. [Pipeline Integration](#pipeline-integration)

---

## Background Task Processing

### Overview
WATCHKEEPER now uses **Celery** with **Redis** for asynchronous background task processing. This enables scalable, distributed processing of intelligence items.

### Key Features
- **Automatic processing**: Intelligence items are automatically queued for processing when collected
- **Batch processing**: Pending items are processed in batches every 15 minutes
- **Retry logic**: Failed tasks are automatically retried with exponential backoff
- **Scheduled jobs**: Daily metrics, health checks, and maintenance tasks run automatically

### Task Types

#### Intelligence Processing (`src/tasks/intelligence_tasks.py`)
- `process_intelligence_item`: Process a single intelligence item through the full pipeline
- `process_pending_batch`: Batch process pending intelligence items
- `reprocess_failed`: Retry failed intelligence items

#### Alert Tasks (`src/tasks/alert_tasks.py`)
- `check_and_create_alert`: Check if an intelligence item should trigger an alert
- `send_alert_notifications`: Send notifications for an alert via email/SMS/webhook
- `retry_failed_notifications`: Retry failed notification deliveries

#### Export Tasks (`src/tasks/export_tasks.py`)
- `generate_export`: Generate export files (PDF, Excel, CSV, JSON)
- `cleanup_old_exports`: Remove expired export files

#### Analytics Tasks (`src/tasks/analytics_tasks.py`)
- `generate_daily_metrics`: Generate daily analytics metrics
- `check_system_health`: Monitor system component health

#### Collection Tasks (`src/tasks/collection_tasks.py`)
- `collect_intelligence`: Run intelligence collection from all active sources
- `collect_from_source`: Collect from a specific source

### Starting Workers

```bash
# Start Celery worker and beat scheduler
./scripts/start_workers.sh

# Or manually:
celery -A src.core.celery_app worker --loglevel=info
celery -A src.core.celery_app beat --loglevel=info
```

### Scheduled Tasks
- **Hourly**: Intelligence collection
- **Every 15 minutes**: Process pending intelligence
- **Every 5 minutes**: System health checks
- **Every 30 minutes**: Retry failed notifications
- **Daily at midnight**: Generate analytics metrics
- **Daily at 2 AM**: Clean up old exports

---

## Alert & Notification System

### Overview
Automated alerting system that triggers notifications based on threat levels and intelligence analysis.

### Alert Triggers
- Critical threat level (≥9.0): Email + SMS
- High threat level (≥8.0): Email only
- Medium threat level (≥6.0): Email only

### Notification Channels
1. **Email** (SMTP)
2. **SMS** (Twilio)
3. **Webhooks** (HTTP POST)

### API Endpoints

```
GET    /api/v1/alerts              # List alerts
GET    /api/v1/alerts/{id}         # Get specific alert
POST   /api/v1/alerts              # Create alert manually
PUT    /api/v1/alerts/{id}         # Update alert (acknowledge/resolve)
DELETE /api/v1/alerts/{id}         # Delete alert
```

### Configuration

```bash
# Email settings (.env)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=watchkeeper@example.com

# Twilio SMS settings
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Alert thresholds
HIGH_THREAT_THRESHOLD=8.0
CRITICAL_THREAT_THRESHOLD=9.0

# Recipients
ALERT_EMAIL_RECIPIENTS=["admin@example.com"]
ALERT_SMS_RECIPIENTS=["+1234567890"]
ALERT_WEBHOOK_URLS=["https://your-webhook.com/alerts"]
```

---

## User Management & RBAC

### Overview
Complete user management system with role-based access control (RBAC).

### Default Roles

1. **Admin**
   - Full system access
   - User and role management
   - All permissions

2. **Analyst**
   - Read/write intelligence and threats
   - Create and update alerts
   - Export data
   - View analytics

3. **Viewer**
   - Read-only access to intelligence and threats
   - View analytics

4. **Operator**
   - Manage sources
   - View intelligence
   - Update alerts

### API Endpoints

#### Authentication
```
POST /api/v1/auth/login          # Login with username/password
```

#### Users
```
GET    /api/v1/users              # List users (admin only)
GET    /api/v1/users/me           # Get current user info
GET    /api/v1/users/{id}         # Get specific user
POST   /api/v1/users              # Create user (admin only)
PUT    /api/v1/users/{id}         # Update user
DELETE /api/v1/users/{id}         # Delete user (admin only)
POST   /api/v1/users/{id}/roles/{role_id}    # Add role to user
DELETE /api/v1/users/{id}/roles/{role_id}    # Remove role from user
```

#### Roles & Permissions
```
GET    /api/v1/roles              # List roles
GET    /api/v1/roles/{id}         # Get specific role
POST   /api/v1/roles              # Create role
PUT    /api/v1/roles/{id}         # Update role
DELETE /api/v1/roles/{id}         # Delete role
POST   /api/v1/roles/{id}/permissions/{perm_id}   # Add permission
DELETE /api/v1/roles/{id}/permissions/{perm_id}   # Remove permission

GET    /api/v1/permissions        # List permissions
POST   /api/v1/permissions        # Create permission
```

### Using Authentication

```python
# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# Use token in subsequent requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/intelligence",
    headers=headers
)
```

---

## Audit Logging

### Overview
Comprehensive audit logging tracks all system actions for compliance and debugging.

### Logged Actions
- CREATE: Resource creation
- UPDATE: Resource modification
- DELETE: Resource deletion
- LOGIN/LOGOUT: Authentication events
- EXPORT: Data exports
- PROCESS: Intelligence processing

### Audit Log Fields
- User ID and IP address
- Action type and resource
- Before/after values (for updates)
- Timestamp
- Status (success/failure)
- Error messages

### Database Table
All audit logs are stored in the `audit_logs` table with automatic retention management.

### Querying Audit Logs

```python
from src.models.audit_log import AuditLog, AuditAction

# Get all user actions
logs = db.query(AuditLog).filter(
    AuditLog.user_id == user_id
).all()

# Get all failed actions
failed = db.query(AuditLog).filter(
    AuditLog.status == "failure"
).all()
```

---

## Rate Limiting

### Overview
API rate limiting using **SlowAPI** with Redis backend.

### Default Limits
- 60 requests per minute (configurable)
- Per-API-key or per-IP tracking
- Automatic rate limit header injection

### Configuration

```bash
RATE_LIMIT_PER_MINUTE=60
REDIS_URL=redis://localhost:6379/0
```

### Custom Limits

```python
from src.middleware.rate_limit import limiter

@router.get("/intensive-operation")
@limiter.limit("10/minute")  # Custom limit
async def intensive_operation():
    ...
```

---

## Export System

### Overview
Export intelligence, threats, and sources to multiple formats.

### Supported Formats
- **PDF**: Formatted reports with tables
- **Excel**: Spreadsheets with formatting
- **CSV**: Comma-separated values
- **JSON**: Structured data

### API Endpoints

```
GET    /api/v1/exports            # List exports
GET    /api/v1/exports/{id}       # Get export status
POST   /api/v1/exports            # Create export (async)
GET    /api/v1/exports/{id}/download  # Download completed export
DELETE /api/v1/exports/{id}       # Delete export
```

### Example Usage

```python
# Request export
response = requests.post(
    "http://localhost:8000/api/v1/exports",
    json={
        "export_format": "excel",
        "resource_type": "intelligence",
        "filters": {"status": "completed"}
    },
    headers=headers
)
export_id = response.json()["id"]

# Check status
response = requests.get(
    f"http://localhost:8000/api/v1/exports/{export_id}",
    headers=headers
)

# Download when ready
if response.json()["status"] == "completed":
    file = requests.get(
        f"http://localhost:8000/api/v1/exports/{export_id}/download",
        headers=headers
    )
```

---

## Advanced Search

### Overview
Full-text search across intelligence, threats, and sources.

### Search Capabilities
- Text search with ILIKE patterns
- Multi-field search
- Filter by multiple criteria
- Location-based search
- Date range filtering
- Confidence score filtering

### API Endpoints

```
GET /api/v1/search                # Search all entity types
GET /api/v1/search/intelligence   # Search intelligence with filters
GET /api/v1/search/threats        # Search threats with filters
GET /api/v1/search/advanced       # Advanced multi-criteria search
```

### Example Queries

```python
# Simple search
requests.get(
    "http://localhost:8000/api/v1/search?q=earthquake",
    headers=headers
)

# Advanced search
requests.get(
    "http://localhost:8000/api/v1/search/advanced",
    params={
        "text": "security threat",
        "location": "Europe",
        "date_from": "2025-01-01",
        "min_confidence": 0.7
    },
    headers=headers
)
```

---

## Analytics Dashboard

### Overview
Real-time analytics and system metrics.

### Available Metrics
- Intelligence items created/processed
- Average processing time
- Threat counts by severity
- Alert statistics
- System health metrics

### API Endpoints

```
GET /api/v1/analytics/dashboard           # Dashboard summary
POST /api/v1/analytics/metrics            # Query metrics
GET /api/v1/analytics/health              # System health
GET /api/v1/analytics/metrics/{name}/latest  # Latest metric value
```

### Dashboard Summary Response

```json
{
  "total_intelligence": 1234,
  "total_threats": 56,
  "active_alerts": 8,
  "processing_rate": 15.5,
  "system_health": "healthy"
}
```

---

## Source Verification

### Overview
Multi-source verification and consensus analysis.

### Features
- **Source reliability scoring**: Calculated from historical performance
- **Consensus detection**: Find corroborating reports from multiple sources
- **Threat verification**: Verify threats using multiple intelligence sources
- **Automatic reliability updates**: Periodic recalculation of source scores

### API Endpoints

```
GET /api/v1/verification/source/{id}/reliability    # Get source reliability
GET /api/v1/verification/intelligence/{id}/consensus  # Find consensus
GET /api/v1/verification/threat/{id}/verify          # Verify threat
POST /api/v1/verification/sources/update-reliability  # Update all scores
```

### Consensus Example

```json
{
  "intelligence_id": 123,
  "confirming_sources": 3,
  "similar_items": [
    {
      "intelligence_id": 124,
      "source_id": 2,
      "similarity": 0.85,
      "created_at": "2025-01-15T10:30:00"
    }
  ],
  "average_similarity": 0.82,
  "consensus_strength": 0.88,
  "verified": true
}
```

---

## Pipeline Integration

### Overview
Collectors now automatically feed into the processing pipeline.

### Flow
1. **Collection**: Collectors gather intelligence from sources
2. **Storage**: Intelligence items are stored in the database with `PENDING` status
3. **Queuing**: Items are automatically queued for processing via Celery
4. **Processing**: Background workers process items through the pipeline:
   - Language detection & translation
   - AI analysis (summarization, classification)
   - Geographic extraction
   - Severity scoring
   - Relevance assessment
5. **Alert Check**: High-priority items trigger alerts
6. **Notification**: Alerts are sent to configured recipients

### Processor Pipeline

```
Intelligence Item (PENDING)
    ↓
Language Processor
    ↓
AI Processor (Ollama)
    ↓
Geo Processor
    ↓
Severity Processor
    ↓
Relevance Processor
    ↓
Intelligence Item (COMPLETED)
    ↓
Alert Check
    ↓
Notifications
```

---

## Database Setup

### Initialize Database

```bash
# Run initialization script
python scripts/init_database.py
```

This will:
1. Create all database tables
2. Create default permissions
3. Create default roles (admin, analyst, viewer, operator)
4. Create admin user (username: admin, password: admin123)

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/watchkeeper

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Admin user (for initialization)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@watchkeeper.local
```

---

## Quick Start Guide

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start Redis

```bash
redis-server
```

### 4. Initialize Database

```bash
python scripts/init_database.py
```

### 5. Start Workers

```bash
./scripts/start_workers.sh
```

### 6. Start API

```bash
uvicorn src.main:app --reload
```

### 7. Login and Test

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=admin123"

# Use the returned token in subsequent requests
```

---

## Security Notes

1. **Change default admin password immediately**
2. Use strong passwords for all users
3. Enable HTTPS in production
4. Rotate API keys regularly
5. Review audit logs regularly
6. Keep dependencies updated
7. Configure firewall rules
8. Use environment variables for secrets (never commit .env)

---

## Troubleshooting

### Celery workers not processing tasks
- Check Redis is running: `redis-cli ping`
- Check worker logs: `celery -A src.core.celery_app inspect active`
- Restart workers: `pkill celery && ./scripts/start_workers.sh`

### Database connection errors
- Verify DATABASE_URL in .env
- Check PostgreSQL is running
- Verify database exists: `psql -l`

### Authentication failures
- Verify JWT SECRET_KEY is set
- Check token expiration (default 30 minutes)
- Verify user exists and is active

### Rate limiting issues
- Check Redis connection
- Verify REDIS_URL in .env
- Check rate limit configuration

---

## Support

For issues or questions:
1. Check logs in the application
2. Review audit logs for failed operations
3. Check system health: `GET /api/v1/analytics/health`
4. Review Celery task logs

---

## Future Enhancements

Planned features:
- Elasticsearch integration for better search
- WebSocket notifications for real-time updates
- ML-based threat prediction
- Advanced correlation analysis
- Multi-tenancy support
- SSO/SAML authentication
