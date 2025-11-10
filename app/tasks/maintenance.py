"""Maintenance and cleanup tasks"""

from ..celery_app import celery_app
from ..database import SessionLocal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.maintenance.cleanup_old_data')
def cleanup_old_data():
    """Cleanup old data based on retention policies"""
    db = SessionLocal()
    try:
        logger.info("Starting weekly data cleanup")

        # Cleanup old alerts (keep for 90 days)
        from ..models.alerts import Alert
        alert_threshold = datetime.utcnow() - timedelta(days=90)

        old_alerts = db.query(Alert).filter(
            Alert.created_at < alert_threshold,
            Alert.status.in_(['acknowledged', 'resolved'])
        ).delete()

        # Cleanup old location history (keep for 180 days)
        from ..models.personnel import LocationHistory
        location_threshold = datetime.utcnow() - timedelta(days=180)

        old_locations = db.query(LocationHistory).filter(
            LocationHistory.timestamp < location_threshold
        ).delete()

        # Cleanup old sync queue (keep for 30 days)
        from ..models.mobile import MobileSyncQueue
        sync_threshold = datetime.utcnow() - timedelta(days=30)

        old_sync = db.query(MobileSyncQueue).filter(
            MobileSyncQueue.created_at < sync_threshold,
            MobileSyncQueue.status == 'synced'
        ).delete()

        db.commit()

        logger.info(
            f"Cleanup complete: {old_alerts} alerts, {old_locations} locations, "
            f"{old_sync} sync items"
        )

        return {
            'success': True,
            'alerts_deleted': old_alerts,
            'locations_deleted': old_locations,
            'sync_items_deleted': old_sync
        }

    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.maintenance.optimize_database')
def optimize_database():
    """Optimize database performance"""
    db = SessionLocal()
    try:
        logger.info("Optimizing database")

        # Run VACUUM ANALYZE on PostgreSQL
        db.execute("VACUUM ANALYZE")

        logger.info("Database optimization complete")

        return {'success': True}

    except Exception as e:
        logger.error(f"Error optimizing database: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.maintenance.backup_database')
def backup_database():
    """Backup database to configured location"""
    try:
        import os
        import subprocess
        from datetime import datetime

        db_url = os.getenv('DATABASE_URL', '')
        backup_dir = os.getenv('BACKUP_DIR', '/backups')

        if not db_url:
            return {'success': False, 'error': 'DATABASE_URL not configured'}

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{backup_dir}/watchkeeper_backup_{timestamp}.sql"

        # Extract database connection details
        # Format: postgresql://user:password@host:port/database
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)

        if not match:
            return {'success': False, 'error': 'Invalid DATABASE_URL format'}

        user, password, host, port, database = match.groups()

        # Set password environment variable for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = password

        # Run pg_dump
        subprocess.run([
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', database,
            '-f', backup_file
        ], env=env, check=True)

        logger.info(f"Database backup created: {backup_file}")

        return {
            'success': True,
            'backup_file': backup_file,
            'timestamp': timestamp
        }

    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        return {'success': False, 'error': str(e)}
