"""
Alert and Notification Tasks

This module contains Celery tasks for alert creation and notification delivery.
"""

from celery import Task
from datetime import datetime
from typing import List, Optional
import asyncio
import os

from src.core.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.models.alert import Alert, Notification, AlertSeverity, AlertStatus, NotificationType, NotificationStatus
from src.models.intelligence import Intelligence
from src.models.threat import Threat
from src.services.notification_service import NotificationService
from sqlalchemy import select, and_
import logging

logger = logging.getLogger(__name__)


class AlertTask(Task):
    """Base task for alert processing with error handling."""

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True


@celery_app.task(base=AlertTask, name="src.tasks.alert_tasks.check_and_create_alert")
def check_and_create_alert(intelligence_id: int) -> Optional[dict]:
    """
    Check if an intelligence item should trigger an alert and create it if needed.

    Args:
        intelligence_id: ID of the intelligence item to check

    Returns:
        dict: Alert creation result or None if no alert needed
    """
    logger.info(f"Checking if intelligence {intelligence_id} should trigger alert")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_check_and_create_alert_async(intelligence_id))
    return result


async def _check_and_create_alert_async(intelligence_id: int) -> Optional[dict]:
    """Async alert checking and creation."""
    async with AsyncSessionLocal() as session:
        try:
            # Get intelligence item with related threat
            result = await session.execute(
                select(Intelligence).where(Intelligence.id == intelligence_id)
            )
            item = result.scalar_one_or_none()

            if not item:
                logger.warning(f"Intelligence item {intelligence_id} not found")
                return None

            # Get thresholds from environment
            high_threshold = float(os.getenv("HIGH_THREAT_THRESHOLD", "8.0"))
            critical_threshold = float(os.getenv("CRITICAL_THREAT_THRESHOLD", "9.0"))

            # Determine if alert is needed based on AI analysis
            should_alert = False
            severity = AlertSeverity.LOW

            # Check AI analysis for threat indicators
            if item.ai_analysis_data:
                threat_level = item.ai_analysis_data.get("threat_level", 0)

                if threat_level >= critical_threshold:
                    should_alert = True
                    severity = AlertSeverity.CRITICAL
                elif threat_level >= high_threshold:
                    should_alert = True
                    severity = AlertSeverity.HIGH
                elif threat_level >= 6.0:
                    should_alert = True
                    severity = AlertSeverity.MEDIUM

            # Also check related threat severity
            if item.threat_id:
                result = await session.execute(
                    select(Threat).where(Threat.id == item.threat_id)
                )
                threat = result.scalar_one_or_none()
                if threat and threat.severity >= 8:
                    should_alert = True
                    if threat.severity >= critical_threshold:
                        severity = AlertSeverity.CRITICAL
                    else:
                        severity = AlertSeverity.HIGH

            if not should_alert:
                logger.info(f"Intelligence {intelligence_id} does not require alert")
                return None

            # Create alert
            title = f"High Priority Intelligence: {item.ai_analysis_data.get('summary', 'New Threat Detected')[:100]}"
            message = f"""
New intelligence item detected requiring attention:

Summary: {item.ai_analysis_data.get('summary', 'N/A')}
Threat Level: {item.ai_analysis_data.get('threat_level', 'N/A')}
Location: {item.ai_analysis_data.get('location', 'Unknown')}
Source: ID {item.source_id}

Please review this intelligence item immediately.
            """.strip()

            alert = Alert(
                title=title,
                message=message,
                severity=severity,
                status=AlertStatus.NEW,
                intelligence_id=intelligence_id,
                threat_id=item.threat_id,
                metadata={
                    "ai_analysis": item.ai_analysis_data,
                    "confidence_score": item.confidence_score
                }
            )

            session.add(alert)
            await session.commit()
            await session.refresh(alert)

            logger.info(f"Created alert {alert.id} for intelligence {intelligence_id}")

            # Send notifications
            await send_alert_notifications.delay(alert.id)

            return {
                "status": "success",
                "alert_id": alert.id,
                "severity": severity.value
            }

        except Exception as e:
            logger.error(f"Error checking/creating alert for intelligence {intelligence_id}: {str(e)}")
            raise


@celery_app.task(base=AlertTask, name="src.tasks.alert_tasks.send_alert_notifications")
def send_alert_notifications(alert_id: int) -> dict:
    """
    Send notifications for an alert.

    Args:
        alert_id: ID of the alert to send notifications for

    Returns:
        dict: Notification sending result
    """
    logger.info(f"Sending notifications for alert {alert_id}")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_send_alert_notifications_async(alert_id))
    return result


async def _send_alert_notifications_async(alert_id: int) -> dict:
    """Async notification sending."""
    async with AsyncSessionLocal() as session:
        try:
            # Get alert
            result = await session.execute(
                select(Alert).where(Alert.id == alert_id)
            )
            alert = result.scalar_one_or_none()

            if not alert:
                logger.error(f"Alert {alert_id} not found")
                return {"status": "error", "message": "Alert not found"}

            notification_service = NotificationService()
            sent_count = 0
            failed_count = 0

            # Get recipients from environment
            import json
            email_recipients = json.loads(os.getenv("ALERT_EMAIL_RECIPIENTS", "[]"))
            sms_recipients = json.loads(os.getenv("ALERT_SMS_RECIPIENTS", "[]"))
            webhook_urls = json.loads(os.getenv("ALERT_WEBHOOK_URLS", "[]"))

            # Send email notifications
            for email in email_recipients:
                try:
                    notification = Notification(
                        alert_id=alert_id,
                        notification_type=NotificationType.EMAIL,
                        recipient=email,
                        status=NotificationStatus.PENDING
                    )
                    session.add(notification)
                    await session.commit()
                    await session.refresh(notification)

                    success = await notification_service.send_email(
                        to=email,
                        subject=f"[WATCHKEEPER Alert] {alert.title}",
                        body=alert.message
                    )

                    if success:
                        notification.status = NotificationStatus.SENT
                        notification.sent_at = datetime.utcnow()
                        sent_count += 1
                    else:
                        notification.status = NotificationStatus.FAILED
                        failed_count += 1

                    await session.commit()

                except Exception as e:
                    logger.error(f"Error sending email to {email}: {str(e)}")
                    failed_count += 1

            # Send SMS notifications (only for critical alerts)
            if alert.severity == AlertSeverity.CRITICAL:
                for phone in sms_recipients:
                    try:
                        notification = Notification(
                            alert_id=alert_id,
                            notification_type=NotificationType.SMS,
                            recipient=phone,
                            status=NotificationStatus.PENDING
                        )
                        session.add(notification)
                        await session.commit()
                        await session.refresh(notification)

                        success = await notification_service.send_sms(
                            to=phone,
                            message=f"WATCHKEEPER CRITICAL ALERT: {alert.title[:100]}"
                        )

                        if success:
                            notification.status = NotificationStatus.SENT
                            notification.sent_at = datetime.utcnow()
                            sent_count += 1
                        else:
                            notification.status = NotificationStatus.FAILED
                            failed_count += 1

                        await session.commit()

                    except Exception as e:
                        logger.error(f"Error sending SMS to {phone}: {str(e)}")
                        failed_count += 1

            # Send webhook notifications
            for webhook_url in webhook_urls:
                try:
                    notification = Notification(
                        alert_id=alert_id,
                        notification_type=NotificationType.WEBHOOK,
                        recipient=webhook_url,
                        status=NotificationStatus.PENDING
                    )
                    session.add(notification)
                    await session.commit()
                    await session.refresh(notification)

                    success = await notification_service.send_webhook(
                        url=webhook_url,
                        payload={
                            "alert_id": alert.id,
                            "title": alert.title,
                            "message": alert.message,
                            "severity": alert.severity.value,
                            "created_at": alert.created_at.isoformat()
                        }
                    )

                    if success:
                        notification.status = NotificationStatus.SENT
                        notification.sent_at = datetime.utcnow()
                        sent_count += 1
                    else:
                        notification.status = NotificationStatus.FAILED
                        failed_count += 1

                    await session.commit()

                except Exception as e:
                    logger.error(f"Error sending webhook to {webhook_url}: {str(e)}")
                    failed_count += 1

            logger.info(f"Sent {sent_count} notifications for alert {alert_id}, {failed_count} failed")

            return {
                "status": "success",
                "alert_id": alert_id,
                "sent_count": sent_count,
                "failed_count": failed_count
            }

        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert_id}: {str(e)}")
            raise


@celery_app.task(name="src.tasks.alert_tasks.retry_failed_notifications")
def retry_failed_notifications(max_retries: int = 3) -> dict:
    """
    Retry failed notifications.

    Args:
        max_retries: Maximum number of retries per notification

    Returns:
        dict: Retry result
    """
    logger.info("Retrying failed notifications")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_retry_failed_notifications_async(max_retries))
    return result


async def _retry_failed_notifications_async(max_retries: int) -> dict:
    """Async retry of failed notifications."""
    async with AsyncSessionLocal() as session:
        try:
            # Get failed notifications that haven't exceeded retry limit
            result = await session.execute(
                select(Notification)
                .where(
                    and_(
                        Notification.status == NotificationStatus.FAILED,
                        Notification.retry_count < max_retries
                    )
                )
            )
            failed_notifications = result.scalars().all()

            if not failed_notifications:
                logger.info("No failed notifications to retry")
                return {"status": "success", "retried_count": 0}

            notification_service = NotificationService()
            retried_count = 0

            for notification in failed_notifications:
                try:
                    success = False

                    if notification.notification_type == NotificationType.EMAIL:
                        # Get alert for context
                        alert_result = await session.execute(
                            select(Alert).where(Alert.id == notification.alert_id)
                        )
                        alert = alert_result.scalar_one_or_none()
                        if alert:
                            success = await notification_service.send_email(
                                to=notification.recipient,
                                subject=f"[WATCHKEEPER Alert] {alert.title}",
                                body=alert.message
                            )

                    elif notification.notification_type == NotificationType.SMS:
                        alert_result = await session.execute(
                            select(Alert).where(Alert.id == notification.alert_id)
                        )
                        alert = alert_result.scalar_one_or_none()
                        if alert:
                            success = await notification_service.send_sms(
                                to=notification.recipient,
                                message=f"WATCHKEEPER ALERT: {alert.title[:100]}"
                            )

                    elif notification.notification_type == NotificationType.WEBHOOK:
                        alert_result = await session.execute(
                            select(Alert).where(Alert.id == notification.alert_id)
                        )
                        alert = alert_result.scalar_one_or_none()
                        if alert:
                            success = await notification_service.send_webhook(
                                url=notification.recipient,
                                payload={
                                    "alert_id": alert.id,
                                    "title": alert.title,
                                    "message": alert.message,
                                    "severity": alert.severity.value,
                                    "created_at": alert.created_at.isoformat()
                                }
                            )

                    notification.retry_count += 1

                    if success:
                        notification.status = NotificationStatus.SENT
                        notification.sent_at = datetime.utcnow()
                        retried_count += 1
                        logger.info(f"Successfully retried notification {notification.id}")

                    await session.commit()

                except Exception as e:
                    logger.error(f"Error retrying notification {notification.id}: {str(e)}")
                    notification.retry_count += 1
                    await session.commit()

            logger.info(f"Retried {retried_count} failed notifications")

            return {
                "status": "success",
                "retried_count": retried_count,
                "total_failed": len(failed_notifications)
            }

        except Exception as e:
            logger.error(f"Error retrying failed notifications: {str(e)}")
            return {"status": "error", "message": str(e)}
