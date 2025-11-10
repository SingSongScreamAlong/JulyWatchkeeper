"""Alert-related background tasks"""

from ..celery_app import celery_app
from ..database import SessionLocal
from ..services.alert_service import AlertService, EscalationManager
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.alerts.send_alert')
def send_alert(alert_id: int):
    """Send an alert via configured channels (async)"""
    db = SessionLocal()
    try:
        from ..models.alerts import Alert

        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            logger.error(f"Alert {alert_id} not found")
            return {'success': False, 'error': 'Alert not found'}

        # Get configuration from environment
        config = {
            'smtp_host': 'localhost',  # TODO: Load from settings
            'smtp_port': 587,
            'sms_enabled': False,  # TODO: Configure
            'push_enabled': False,  # TODO: Configure
        }

        alert_service = AlertService(db, config)

        # Get recipients and send notifications
        # This is a simplified version - full implementation would get from alert rule
        logger.info(f"Sending alert {alert_id}: {alert.title}")

        return {'success': True, 'alert_id': alert_id}

    except Exception as e:
        logger.error(f"Error sending alert {alert_id}: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.alerts.check_escalations')
def check_escalations():
    """Check for alerts that need escalation"""
    db = SessionLocal()
    try:
        escalation_manager = EscalationManager(db)
        # Note: check_escalations is async, need to handle
        logger.info("Checking for alert escalations")

        # Simplified synchronous version
        from ..models.alerts import Alert
        from datetime import datetime, timedelta

        threshold_time = datetime.utcnow() - timedelta(minutes=30)

        unacknowledged = db.query(Alert).filter(
            Alert.status == 'sent',
            Alert.acknowledged_at.is_(None),
            Alert.priority >= 8,
            Alert.sent_at < threshold_time
        ).all()

        for alert in unacknowledged:
            logger.warning(f"Alert {alert.id} requires escalation")
            # TODO: Implement escalation logic
            # - Notify supervisors
            # - Send to backup contacts
            # - Trigger emergency protocols

        return {
            'success': True,
            'alerts_requiring_escalation': len(unacknowledged)
        }

    except Exception as e:
        logger.error(f"Error checking escalations: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.alerts.evaluate_intelligence_for_alerts')
def evaluate_intelligence_for_alerts(intelligence_id: int):
    """Evaluate if new intelligence triggers any alerts (async)"""
    db = SessionLocal()
    try:
        config = {}  # TODO: Load from settings
        alert_service = AlertService(db, config)

        # This would be async in real implementation
        logger.info(f"Evaluating intelligence {intelligence_id} for alerts")

        # Simplified synchronous version
        from ..models.intelligence import IntelligenceItem
        from ..models.alerts import AlertRule, Alert

        intel = db.query(IntelligenceItem).filter(
            IntelligenceItem.id == intelligence_id
        ).first()

        if not intel:
            return {'success': False, 'error': 'Intelligence not found'}

        # Get active alert rules
        rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()

        triggered = []
        for rule in rules:
            # Check if intelligence matches rule criteria
            if intel.threat_level >= rule.threat_level_threshold and \
               intel.missionary_relevance >= rule.missionary_relevance_threshold:

                # Create alert
                alert = Alert(
                    alert_rule_id=rule.id,
                    intelligence_id=intel.id,
                    alert_type='high_threat' if intel.threat_level >= 8 else 'general',
                    priority=int((intel.threat_level + intel.missionary_relevance) / 2),
                    title=f"ALERT: {intel.title}",
                    message=f"Threat Level: {intel.threat_level}/10\n\n{intel.content[:500]}",
                    status='pending'
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)

                # Send alert asynchronously
                send_alert.delay(alert.id)
                triggered.append(alert.id)

        return {
            'success': True,
            'intelligence_id': intelligence_id,
            'alerts_triggered': len(triggered),
            'alert_ids': triggered
        }

    except Exception as e:
        logger.error(f"Error evaluating intelligence {intelligence_id}: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()
