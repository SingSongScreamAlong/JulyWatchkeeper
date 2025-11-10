"""Celery configuration for WATCHKEEPER background tasks

This module configures Celery for async task processing including:
- Alert sending (email, SMS, push)
- Intelligence collection scheduling
- Check-in monitoring
- Geofence calculations
"""

from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Celery
celery_app = Celery(
    'watchkeeper',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=[
        'app.tasks.alerts',
        'app.tasks.intelligence',
        'app.tasks.monitoring',
        'app.tasks.notifications'
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Check missed check-ins every 15 minutes
    'check-missed-checkins': {
        'task': 'app.tasks.monitoring.check_missed_checkins',
        'schedule': crontab(minute='*/15'),
    },

    # Collect intelligence every 30 minutes
    'collect-intelligence': {
        'task': 'app.tasks.intelligence.collect_all_sources',
        'schedule': crontab(minute='*/30'),
    },

    # Check for alert escalations every 10 minutes
    'check-escalations': {
        'task': 'app.tasks.alerts.check_escalations',
        'schedule': crontab(minute='*/10'),
    },

    # Generate daily intelligence briefing at 06:00 UTC
    'daily-briefing': {
        'task': 'app.tasks.intelligence.generate_daily_briefing',
        'schedule': crontab(hour=6, minute=0),
    },

    # Check personnel in danger zones every 5 minutes
    'danger-zone-check': {
        'task': 'app.tasks.monitoring.check_danger_zones',
        'schedule': crontab(minute='*/5'),
    },

    # Cleanup old data weekly (Sundays at 02:00 UTC)
    'weekly-cleanup': {
        'task': 'app.tasks.maintenance.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
}

# Task routing
celery_app.conf.task_routes = {
    'app.tasks.alerts.*': {'queue': 'alerts'},
    'app.tasks.intelligence.*': {'queue': 'intelligence'},
    'app.tasks.monitoring.*': {'queue': 'monitoring'},
    'app.tasks.notifications.*': {'queue': 'notifications'},
}
