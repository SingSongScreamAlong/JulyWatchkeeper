# WATCHKEEPER Monitoring & Observability

Comprehensive monitoring infrastructure for production deployment.

## Stack Overview

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notification
- **Loki**: Log aggregation
- **Promtail**: Log collection
- **Node Exporter**: System metrics
- **PostgreSQL Exporter**: Database metrics
- **Redis Exporter**: Cache metrics

## Quick Start

### 1. Start Monitoring Stack

```bash
# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Check status
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 3. Configure Environment

Add to `.env`:

```env
# Grafana
GRAFANA_PASSWORD=your_secure_password

# Alertmanager - Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@watchkeeper.org
SMTP_PASSWORD=your_smtp_password

# Alertmanager - Slack
SLACK_WEBHOOK_CRITICAL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_WEBHOOK_SAFETY=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_WEBHOOK_INFRA=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_WEBHOOK_INTEL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Alertmanager - PagerDuty
PAGERDUTY_SERVICE_KEY=your_service_key
PAGERDUTY_SAFETY_KEY=your_safety_key
```

## Metrics Collected

### API Metrics
- `http_requests_total` - Total HTTP requests by endpoint and status
- `http_request_duration_seconds` - Request latency histogram

### Intelligence Metrics
- `intelligence_items_collected_total` - Items collected by source
- `intelligence_collection_failures_total` - Collection failures
- `intelligence_last_collected_timestamp` - Last successful collection

### Alert Metrics
- `alerts_created_total` - Alerts created by severity
- `alerts_unacknowledged` - Current unacknowledged alerts
- `alerts_acknowledged_total` - Acknowledged alerts

### Personnel Metrics
- `personnel_active_count` - Number of active personnel
- `personnel_missed_checkins` - Personnel who missed check-ins
- `personnel_in_danger_zones` - Personnel in danger zones
- `personnel_location_updates_total` - Location update events

### Incident Metrics
- `incidents_created_total` - Incidents created
- `incidents_open` - Open incidents by severity

### Database Metrics
- `database_queries_total` - Query count by operation
- `database_query_duration_seconds` - Query latency
- `database_connection_pool_size` - Connection pool size
- `pg_stat_activity_count` - Active connections

### Celery Metrics
- `celery_tasks_succeeded_total` - Successful tasks
- `celery_tasks_failed_total` - Failed tasks
- `celery_task_duration_seconds` - Task duration
- `celery_queue_length` - Queue backlog

### System Metrics
- `node_cpu_seconds_total` - CPU usage
- `node_memory_MemAvailable_bytes` - Available memory
- `node_filesystem_avail_bytes` - Available disk space

## Alert Rules

### Critical Alerts

**APIDown** - API service unavailable
- Trigger: API unreachable for 1 minute
- Action: Page on-call, check logs

**PersonnelInDangerZone** - Personnel in dangerous area
- Trigger: Any personnel enter danger zone
- Action: Immediate safety response

**MissedCheckins** - Personnel missed check-in
- Trigger: Any personnel miss scheduled check-in
- Action: Immediate contact attempt

**DatabaseDown** - Database unavailable
- Trigger: Database unreachable for 1 minute
- Action: Emergency database recovery

### Warning Alerts

**APIHighErrorRate** - High 5xx error rate
- Trigger: >5% error rate for 5 minutes
- Action: Investigate logs, check dependencies

**APIHighResponseTime** - Slow API responses
- Trigger: 95th percentile >2s for 5 minutes
- Action: Check database queries, optimize

**HighAlertVolume** - Unusual alert volume
- Trigger: >50 alerts per hour
- Action: Check intelligence sources

**CeleryTaskFailureRate** - Background task failures
- Trigger: >5 failures per hour
- Action: Check worker logs

**HighMemoryUsage** - System memory pressure
- Trigger: >85% memory usage for 5 minutes
- Action: Identify memory leaks

## Grafana Dashboards

### WATCHKEEPER Overview Dashboard

Main operational dashboard with:

1. **API Performance**
   - Request rate
   - Error rate
   - Response time (p95)

2. **Personnel Safety**
   - Active personnel count
   - Personnel in danger zones (red alert)
   - Missed check-ins

3. **Intelligence Collection**
   - Items collected (24h)
   - Collection by source (pie chart)
   - Collection failures

4. **Alerts**
   - Unacknowledged alerts
   - Alert severity distribution
   - Alert volume trend

5. **Infrastructure**
   - Database connections
   - Redis memory usage
   - Celery queue length
   - Task success rate

6. **System Resources**
   - CPU usage
   - Memory usage
   - Disk space

### Creating Custom Dashboards

1. Access Grafana at http://localhost:3001
2. Click "+" → "Dashboard"
3. Add panels with Prometheus queries
4. Save and share dashboard JSON

## Alert Routing

Alertmanager routes alerts to different teams:

### Critical Alerts
- **Destination**: critical@watchkeeper.org, Slack #critical-alerts, PagerDuty
- **Triggers**: APIDown, DatabaseDown, personnel safety
- **Response Time**: Immediate

### Personnel Safety Alerts
- **Destination**: safety@watchkeeper.org, leadership@watchkeeper.org, Slack #personnel-safety
- **Triggers**: MissedCheckins, PersonnelInDangerZone
- **Response Time**: Immediate (0-5 minutes)

### Infrastructure Alerts
- **Destination**: devops@watchkeeper.org, Slack #infrastructure
- **Triggers**: Service outages, high resource usage
- **Response Time**: 15 minutes

### Intelligence Team Alerts
- **Destination**: intel@watchkeeper.org, Slack #intelligence
- **Triggers**: Collection failures, no recent intelligence
- **Response Time**: 1 hour

## Log Aggregation

### Log Sources

All logs aggregated in Loki:

1. **API Logs**: `/app/logs/api/*.log`
2. **Celery Logs**: `/app/logs/celery/*.log`
3. **Intelligence Logs**: `/app/logs/intelligence/*.log`
4. **System Logs**: `/var/log/syslog`

### Querying Logs in Grafana

Example LogQL queries:

```logql
# All API errors
{job="watchkeeper_api"} |= "ERROR"

# Failed intelligence collection
{job="intelligence_collection"} | json | level="ERROR"

# Specific user actions
{job="watchkeeper_api"} | json | user_id="123"

# Slow requests
{job="watchkeeper_api"} | json | duration > 2000
```

### Log Retention

- Default: 31 days (744 hours)
- Critical logs: Archive to S3 for 1 year
- Configure in `monitoring/loki-config.yml`

## Performance Tuning

### Metrics Collection

Adjust scrape intervals in `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'watchkeeper_api'
    scrape_interval: 10s  # More frequent for critical services

  - job_name: 'node'
    scrape_interval: 30s  # Less frequent for system metrics
```

### Alert Sensitivity

Adjust thresholds in `monitoring/alerts.yml`:

```yaml
- alert: APIHighResponseTime
  expr: histogram_quantile(0.95, ...) > 2  # Adjust threshold
  for: 5m  # Adjust evaluation period
```

### Data Retention

Configure in `prometheus.yml`:

```yaml
command:
  - '--storage.tsdb.retention.time=30d'  # Keep 30 days
  - '--storage.tsdb.retention.size=50GB'  # Or 50GB max
```

## Integration with Application

### Add Metrics to New Endpoints

```python
from app.services.metrics_service import (
    http_requests_total,
    http_request_duration_seconds
)

@router.get("/my-endpoint")
async def my_endpoint():
    start_time = time.time()

    # Your logic here

    # Track metrics
    duration = time.time() - start_time
    http_request_duration_seconds.labels(
        method="GET",
        endpoint="/my-endpoint"
    ).observe(duration)

    return {"status": "ok"}
```

### Add Custom Metrics

```python
from prometheus_client import Counter, Gauge

# Define metric
my_custom_metric = Counter(
    'my_custom_metric_total',
    'Description of metric',
    ['label1', 'label2']
)

# Use metric
my_custom_metric.labels(
    label1='value1',
    label2='value2'
).inc()
```

## Production Recommendations

### High Availability

1. **Multiple Prometheus Instances**: Use Thanos for global view
2. **Grafana HA**: Run multiple Grafana instances with shared database
3. **Alertmanager Cluster**: Deploy 3+ Alertmanager instances

### Security

1. **Enable Authentication**: Configure Prometheus basic auth
2. **Network Isolation**: Use firewall rules for metrics endpoints
3. **TLS Encryption**: Enable HTTPS for all dashboards
4. **RBAC**: Configure Grafana team-based access control

### Backup

```bash
# Backup Prometheus data
docker run -v prometheus_data:/prometheus \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /prometheus

# Backup Grafana dashboards
curl -u admin:password http://localhost:3001/api/dashboards/db/watchkeeper-overview \
  > backup/dashboard-$(date +%Y%m%d).json
```

### Scaling

- **Prometheus Federation**: Aggregate metrics from multiple Prometheus servers
- **Loki Sharding**: Distribute logs across multiple Loki instances
- **Grafana Caching**: Enable query result caching

## Troubleshooting

### Prometheus Not Scraping

```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Check Prometheus logs
docker logs watchkeeper_prometheus
```

### Alerts Not Firing

```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules

# Check Alertmanager status
curl http://localhost:9093/api/v1/status
```

### Grafana Dashboard Empty

1. Check datasource connection in Grafana
2. Verify Prometheus has data: http://localhost:9090/graph
3. Check query syntax in panel editor

### High Resource Usage

```bash
# Check Prometheus disk usage
docker exec watchkeeper_prometheus du -sh /prometheus

# Check memory usage
docker stats watchkeeper_prometheus
```

## Monitoring Checklist

### Daily
- [ ] Check critical alerts in Alertmanager
- [ ] Review Grafana dashboard for anomalies
- [ ] Verify all intelligence sources collecting

### Weekly
- [ ] Review alert trends
- [ ] Check log disk usage
- [ ] Analyze slow query logs
- [ ] Review personnel safety metrics

### Monthly
- [ ] Backup Prometheus data
- [ ] Export Grafana dashboards
- [ ] Review and tune alert thresholds
- [ ] Capacity planning based on metrics

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Loki Documentation](https://grafana.com/docs/loki/)

## Support

For monitoring issues:
- **Email**: devops@watchkeeper.org
- **Slack**: #infrastructure
- **On-call**: PagerDuty escalation
