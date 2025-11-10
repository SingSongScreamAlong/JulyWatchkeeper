"""Prometheus Metrics Service

Exposes application metrics for monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from typing import Callable
import time
import logging

logger = logging.getLogger(__name__)

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Intelligence Metrics
intelligence_items_collected_total = Counter(
    'intelligence_items_collected_total',
    'Total intelligence items collected',
    ['source', 'category']
)

intelligence_collection_failures_total = Counter(
    'intelligence_collection_failures_total',
    'Total intelligence collection failures',
    ['source', 'error_type']
)

intelligence_last_collected_timestamp = Gauge(
    'intelligence_last_collected_timestamp',
    'Timestamp of last successful intelligence collection',
    ['source']
)

intelligence_items_by_source_total = Counter(
    'intelligence_items_by_source_total',
    'Intelligence items by source',
    ['source']
)

# Alert Metrics
alerts_created_total = Counter(
    'alerts_created_total',
    'Total alerts created',
    ['severity', 'type']
)

alerts_acknowledged_total = Counter(
    'alerts_acknowledged_total',
    'Total alerts acknowledged',
    ['severity']
)

alerts_unacknowledged = Gauge(
    'alerts_unacknowledged',
    'Current number of unacknowledged alerts',
    ['severity']
)

alerts_by_severity_total = Counter(
    'alerts_by_severity_total',
    'Alerts by severity',
    ['severity']
)

# Personnel Metrics
personnel_active_count = Gauge(
    'personnel_active_count',
    'Number of active personnel'
)

personnel_missed_checkins = Gauge(
    'personnel_missed_checkins',
    'Number of personnel who missed check-ins'
)

personnel_in_danger_zones = Gauge(
    'personnel_in_danger_zones',
    'Number of personnel in danger zones'
)

personnel_location_updates_total = Counter(
    'personnel_location_updates_total',
    'Total personnel location updates'
)

# Incident Metrics
incidents_created_total = Counter(
    'incidents_created_total',
    'Total incidents created',
    ['severity', 'status']
)

incidents_open = Gauge(
    'incidents_open',
    'Number of open incidents',
    ['severity']
)

# Database Metrics
database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['operation', 'table']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

database_connection_pool_size = Gauge(
    'database_connection_pool_size',
    'Database connection pool size'
)

database_connection_pool_available = Gauge(
    'database_connection_pool_available',
    'Available database connections'
)

# Celery Metrics
celery_tasks_succeeded_total = Counter(
    'celery_tasks_succeeded_total',
    'Total Celery tasks succeeded',
    ['task']
)

celery_tasks_failed_total = Counter(
    'celery_tasks_failed_total',
    'Total Celery tasks failed',
    ['task', 'exception']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task']
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Celery queue length',
    ['queue']
)

# Cache Metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Authentication Metrics
auth_login_attempts_total = Counter(
    'auth_login_attempts_total',
    'Total login attempts',
    ['status']
)

auth_active_sessions = Gauge(
    'auth_active_sessions',
    'Number of active user sessions'
)

# WebSocket Metrics
websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

websocket_messages_sent_total = Counter(
    'websocket_messages_sent_total',
    'Total WebSocket messages sent',
    ['topic']
)

# Application Info
app_info = Info('watchkeeper_app', 'WATCHKEEPER application info')
app_info.info({
    'version': '2.0.0',
    'environment': 'production'
})


class MetricsMiddleware:
    """Middleware to collect HTTP metrics"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        method = scope['method']
        path = scope['path']

        # Skip metrics endpoint
        if path == '/metrics':
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                status_code = message['status']
                duration = time.time() - start_time

                # Record metrics
                http_requests_total.labels(
                    method=method,
                    endpoint=path,
                    status=status_code
                ).inc()

                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=path
                ).observe(duration)

            await send(message)

        await self.app(scope, receive, send_wrapper)


def track_intelligence_collection(source: str, category: str, items_count: int):
    """Track intelligence collection metrics"""
    intelligence_items_collected_total.labels(
        source=source,
        category=category
    ).inc(items_count)

    intelligence_items_by_source_total.labels(source=source).inc(items_count)
    intelligence_last_collected_timestamp.labels(source=source).set(time.time())


def track_intelligence_failure(source: str, error_type: str):
    """Track intelligence collection failures"""
    intelligence_collection_failures_total.labels(
        source=source,
        error_type=error_type
    ).inc()


def track_alert_created(severity: str, alert_type: str):
    """Track alert creation"""
    alerts_created_total.labels(severity=severity, type=alert_type).inc()
    alerts_by_severity_total.labels(severity=severity).inc()


def track_alert_acknowledged(severity: str):
    """Track alert acknowledgment"""
    alerts_acknowledged_total.labels(severity=severity).inc()


def update_personnel_metrics(active: int, missed_checkins: int, in_danger: int):
    """Update personnel metrics"""
    personnel_active_count.set(active)
    personnel_missed_checkins.set(missed_checkins)
    personnel_in_danger_zones.set(in_danger)


def track_location_update():
    """Track personnel location update"""
    personnel_location_updates_total.inc()


def track_incident_created(severity: str, status: str):
    """Track incident creation"""
    incidents_created_total.labels(severity=severity, status=status).inc()


def update_open_incidents(severity: str, count: int):
    """Update open incident count"""
    incidents_open.labels(severity=severity).set(count)


def track_database_query(operation: str, table: str, duration: float):
    """Track database query"""
    database_queries_total.labels(operation=operation, table=table).inc()
    database_query_duration_seconds.labels(operation=operation, table=table).observe(duration)


def update_connection_pool(size: int, available: int):
    """Update database connection pool metrics"""
    database_connection_pool_size.set(size)
    database_connection_pool_available.set(available)


def track_celery_task_success(task_name: str, duration: float):
    """Track successful Celery task"""
    celery_tasks_succeeded_total.labels(task=task_name).inc()
    celery_task_duration_seconds.labels(task=task_name).observe(duration)


def track_celery_task_failure(task_name: str, exception: str):
    """Track failed Celery task"""
    celery_tasks_failed_total.labels(task=task_name, exception=exception).inc()


def update_queue_length(queue_name: str, length: int):
    """Update Celery queue length"""
    celery_queue_length.labels(queue=queue_name).set(length)


def track_cache_hit(cache_type: str):
    """Track cache hit"""
    cache_hits_total.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str):
    """Track cache miss"""
    cache_misses_total.labels(cache_type=cache_type).inc()


def track_login_attempt(success: bool):
    """Track login attempt"""
    status = 'success' if success else 'failure'
    auth_login_attempts_total.labels(status=status).inc()


def update_active_sessions(count: int):
    """Update active session count"""
    auth_active_sessions.set(count)


def update_websocket_connections(count: int):
    """Update WebSocket connection count"""
    websocket_connections_active.set(count)


def track_websocket_message(topic: str):
    """Track WebSocket message sent"""
    websocket_messages_sent_total.labels(topic=topic).inc()


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    return generate_latest()
