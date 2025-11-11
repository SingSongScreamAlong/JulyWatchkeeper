"""
Celery Application Configuration for WATCHKEEPER

This module configures Celery for background task processing.
"""

from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

# Create Celery app
celery_app = Celery(
    "watchkeeper",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    include=[
        "src.tasks.intelligence_tasks",
        "src.tasks.alert_tasks",
        "src.tasks.export_tasks",
        "src.tasks.analytics_tasks",
        "src.tasks.collection_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    # Collect intelligence every hour
    'collect-intelligence-hourly': {
        'task': 'src.tasks.collection_tasks.collect_intelligence',
        'schedule': crontab(minute=0),  # Every hour
    },
    # Process pending intelligence every 15 minutes
    'process-pending-intelligence': {
        'task': 'src.tasks.intelligence_tasks.process_pending_batch',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    # Clean up old exports daily at 2 AM
    'cleanup-old-exports': {
        'task': 'src.tasks.export_tasks.cleanup_old_exports',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # Generate daily metrics at midnight
    'generate-daily-metrics': {
        'task': 'src.tasks.analytics_tasks.generate_daily_metrics',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    # Check system health every 5 minutes
    'check-system-health': {
        'task': 'src.tasks.analytics_tasks.check_system_health',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    # Retry failed notifications every 30 minutes
    'retry-failed-notifications': {
        'task': 'src.tasks.alert_tasks.retry_failed_notifications',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
