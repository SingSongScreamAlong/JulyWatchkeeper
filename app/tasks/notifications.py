"""Notification sending tasks"""

from ..celery_app import celery_app
from ..database import SessionLocal
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.notifications.send_email')
def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """Send email notification asynchronously"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os

        smtp_host = os.getenv('SMTP_HOST', 'localhost')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', 'alerts@watchkeeper.org')

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        # Plain text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)

        # HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}")

        return {'success': True, 'recipient': to_email}

    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='app.tasks.notifications.send_sms')
def send_sms(phone: str, message: str):
    """Send SMS notification asynchronously"""
    try:
        import os
        from twilio.rest import Client

        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_phone = os.getenv('TWILIO_PHONE_NUMBER')

        if not all([account_sid, auth_token, from_phone]):
            return {'success': False, 'error': 'Twilio not configured'}

        client = Client(account_sid, auth_token)

        # Truncate message for SMS (160 chars)
        sms_message = message[:160]

        msg = client.messages.create(
            body=sms_message,
            from_=from_phone,
            to=phone
        )

        logger.info(f"SMS sent to {phone}: {msg.sid}")

        return {'success': True, 'recipient': phone, 'sid': msg.sid}

    except Exception as e:
        logger.error(f"Error sending SMS to {phone}: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='app.tasks.notifications.send_push')
def send_push(push_token: str, title: str, body: str, data: dict = None):
    """Send push notification asynchronously"""
    try:
        import firebase_admin
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body[:200]  # Truncate for push
            ),
            data=data or {},
            token=push_token
        )

        response = messaging.send(message)

        logger.info(f"Push notification sent: {response}")

        return {'success': True, 'response': response}

    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='app.tasks.notifications.send_multi_channel')
def send_multi_channel(recipient_id: int, title: str, message: str, channels: list = None):
    """Send notification via multiple channels"""
    db = SessionLocal()
    try:
        from ..models.alerts import NotificationRecipient

        recipient = db.query(NotificationRecipient).filter(
            NotificationRecipient.id == recipient_id
        ).first()

        if not recipient:
            return {'success': False, 'error': 'Recipient not found'}

        channels = channels or ['email', 'sms', 'push']
        prefs = recipient.notification_preferences or {}

        results = []

        # Send via each enabled channel
        if 'email' in channels and recipient.email and prefs.get('email_enabled', True):
            result = send_email.delay(recipient.email, title, message)
            results.append({'channel': 'email', 'status': 'sent'})

        if 'sms' in channels and recipient.phone and prefs.get('sms_enabled', False):
            result = send_sms.delay(recipient.phone, message)
            results.append({'channel': 'sms', 'status': 'sent'})

        if 'push' in channels and recipient.push_token and prefs.get('push_enabled', True):
            result = send_push.delay(recipient.push_token, title, message)
            results.append({'channel': 'push', 'status': 'sent'})

        return {
            'success': True,
            'recipient_id': recipient_id,
            'channels_sent': results
        }

    except Exception as e:
        logger.error(f"Error sending multi-channel notification: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()
