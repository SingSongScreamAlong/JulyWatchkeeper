"""Alert and Notification Service for WATCHKEEPER

Handles email, SMS, and push notifications for critical intelligence alerts.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)

try:
    import aiohttp
    from twilio.rest import Client as TwilioClient
    import firebase_admin
    from firebase_admin import credentials, messaging
    TWILIO_AVAILABLE = True
    FIREBASE_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    FIREBASE_AVAILABLE = False
    logger.warning("Optional notification dependencies not installed (twilio, firebase-admin)")


class AlertService:
    """Manages alerts and notifications for intelligence items"""

    def __init__(self, db: Session, config: Dict[str, Any]):
        self.db = db
        self.config = config

        # Email configuration
        self.smtp_host = config.get('smtp_host', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_user = config.get('smtp_user')
        self.smtp_password = config.get('smtp_password')
        self.from_email = config.get('from_email', 'alerts@watchkeeper.org')

        # SMS configuration (Twilio)
        self.sms_enabled = config.get('sms_enabled', False) and TWILIO_AVAILABLE
        if self.sms_enabled:
            self.twilio_client = TwilioClient(
                config.get('twilio_account_sid'),
                config.get('twilio_auth_token')
            )
            self.twilio_phone = config.get('twilio_phone_number')

        # Push notification configuration (Firebase)
        self.push_enabled = config.get('push_enabled', False) and FIREBASE_AVAILABLE
        if self.push_enabled and not firebase_admin._apps:
            cred = credentials.Certificate(config.get('firebase_credentials_path'))
            firebase_admin.initialize_app(cred)

    async def evaluate_intelligence_for_alerts(self, intelligence_id: int) -> List[Dict[str, Any]]:
        """Evaluate if intelligence item triggers any alert rules"""
        from ..models.intelligence import IntelligenceItem
        from ..models.alerts import AlertRule, Alert

        # Get intelligence item
        intel = self.db.query(IntelligenceItem).filter(
            IntelligenceItem.id == intelligence_id
        ).first()

        if not intel:
            return []

        # Get active alert rules
        rules = self.db.query(AlertRule).filter(AlertRule.enabled == True).all()

        triggered_alerts = []

        for rule in rules:
            if self._matches_alert_rule(intel, rule):
                alert = await self._create_alert(intel, rule)
                triggered_alerts.append(alert)

        return triggered_alerts

    def _matches_alert_rule(self, intel, rule) -> bool:
        """Check if intelligence item matches alert rule criteria"""

        # Check threat level threshold
        if intel.threat_level < rule.threat_level_threshold:
            return False

        # Check missionary relevance threshold
        if intel.missionary_relevance < rule.missionary_relevance_threshold:
            return False

        # Check region filter
        if rule.region_filter:
            if not intel.region or intel.region not in rule.region_filter:
                return False

        # Check country filter
        if rule.country_filter:
            if not intel.country or intel.country not in rule.country_filter:
                return False

        # Check keyword filter
        if rule.keyword_filter:
            intel_text = f"{intel.title} {intel.content}".lower()
            if not any(keyword.lower() in intel_text for keyword in rule.keyword_filter):
                return False

        return True

    async def _create_alert(self, intel, rule) -> Dict[str, Any]:
        """Create alert record and send notifications"""
        from ..models.alerts import Alert, NotificationRecipient

        # Determine alert type and priority
        alert_type = self._determine_alert_type(intel)
        priority = self._calculate_priority(intel)

        # Create alert record
        alert = Alert(
            alert_rule_id=rule.id,
            intelligence_id=intel.id,
            alert_type=alert_type,
            priority=priority,
            title=f"ALERT: {intel.title}",
            message=self._generate_alert_message(intel, rule),
            status='pending',
            metadata={
                'threat_level': intel.threat_level,
                'missionary_relevance': intel.missionary_relevance,
                'region': intel.region,
                'country': intel.country
            }
        )

        self.db.add(alert)
        self.db.commit()

        # Get recipients based on alert rule
        recipients = await self._get_alert_recipients(rule, intel)

        # Send notifications
        await self._send_notifications(alert, recipients, rule)

        # Update alert status
        alert.status = 'sent'
        alert.sent_at = datetime.utcnow()
        self.db.commit()

        return {
            'alert_id': alert.id,
            'type': alert_type,
            'priority': priority,
            'recipients_count': len(recipients)
        }

    def _determine_alert_type(self, intel) -> str:
        """Determine alert type based on intelligence characteristics"""
        if intel.threat_level >= 9.0:
            return 'critical'
        elif intel.threat_level >= 8.0:
            return 'high_threat'
        elif intel.threat_level >= 7.0:
            return 'elevated'
        elif 'evacuat' in intel.content.lower():
            return 'evacuation'
        elif 'attack' in intel.content.lower() or 'violence' in intel.content.lower():
            return 'security_incident'
        else:
            return 'general'

    def _calculate_priority(self, intel) -> int:
        """Calculate alert priority (1-10)"""
        priority = int((intel.threat_level + intel.missionary_relevance) / 2)
        return max(1, min(10, priority))

    def _generate_alert_message(self, intel, rule) -> str:
        """Generate alert message content"""
        message = f"""
WATCHKEEPER INTELLIGENCE ALERT
Alert Rule: {rule.name}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

THREAT ASSESSMENT:
- Threat Level: {intel.threat_level}/10
- Missionary Relevance: {intel.missionary_relevance}/10
- Region: {intel.region or 'N/A'}
- Country: {intel.country or 'N/A'}
- Location: {intel.location or 'N/A'}

INTELLIGENCE SUMMARY:
{intel.title}

{intel.content[:500]}{'...' if len(intel.content) > 500 else ''}

SOURCE: {intel.source}
URL: {intel.url}

RECOMMENDED ACTIONS:
{self._generate_recommendations(intel)}

---
This is an automated alert from WATCHKEEPER Intelligence System.
For more details, log in to the dashboard.
"""
        return message

    def _generate_recommendations(self, intel) -> str:
        """Generate recommended actions based on threat level"""
        if intel.threat_level >= 9.0:
            return """
1. IMMEDIATE: Contact all personnel in affected region
2. IMMEDIATE: Activate evacuation protocols if necessary
3. IMMEDIATE: Notify embassy/consulate
4. Monitor situation continuously
5. Prepare emergency response team
"""
        elif intel.threat_level >= 8.0:
            return """
1. Contact personnel in affected region within 1 hour
2. Review safety protocols
3. Establish check-in schedule
4. Monitor local news sources
5. Prepare contingency plans
"""
        elif intel.threat_level >= 7.0:
            return """
1. Notify field supervisors
2. Increase monitoring frequency
3. Brief personnel on situation
4. Review security procedures
"""
        else:
            return """
1. Monitor situation development
2. Keep personnel informed
3. Review relevant safety protocols
"""

    async def _get_alert_recipients(self, rule, intel) -> List:
        """Get list of recipients for this alert"""
        from ..models.alerts import NotificationRecipient

        recipients = self.db.query(NotificationRecipient).filter(
            NotificationRecipient.active == True
        ).all()

        # Filter by regions if specified
        if intel.region:
            recipients = [r for r in recipients if not r.regions or intel.region in r.regions]

        # Filter by roles based on alert priority
        priority = self._calculate_priority(intel)
        if priority >= 9:
            # Critical alerts go to everyone
            pass
        elif priority >= 7:
            # High priority to field staff and admins
            recipients = [r for r in recipients if 'field_staff' in r.roles or 'admin' in r.roles]
        else:
            # Normal priority to analysts and admins
            recipients = [r for r in recipients if 'analyst' in r.roles or 'admin' in r.roles]

        return recipients

    async def _send_notifications(self, alert, recipients: List, rule):
        """Send notifications via configured channels"""
        channels = rule.notification_channels or {}

        tasks = []

        for recipient in recipients:
            prefs = recipient.notification_preferences or {}

            # Email
            if channels.get('email', True) and recipient.email:
                if prefs.get('email_enabled', True):
                    tasks.append(self._send_email(recipient.email, alert))

            # SMS
            if channels.get('sms', False) and recipient.phone and self.sms_enabled:
                if prefs.get('sms_enabled', False):
                    tasks.append(self._send_sms(recipient.phone, alert))

            # Push notification
            if channels.get('push', False) and recipient.push_token and self.push_enabled:
                if prefs.get('push_enabled', True):
                    tasks.append(self._send_push(recipient.push_token, alert))

        # Send all notifications concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Notification failed: {result}")

    async def _send_email(self, to_email: str, alert) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = alert.title
            msg['From'] = self.from_email
            msg['To'] = to_email

            # Plain text version
            text_part = MIMEText(alert.message, 'plain')
            msg.attach(text_part)

            # HTML version
            html_content = self._generate_html_email(alert)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def _send_sms(self, phone: str, alert) -> bool:
        """Send SMS notification"""
        if not self.sms_enabled:
            return False

        try:
            # Truncate message for SMS (160 chars recommended)
            sms_message = f"WATCHKEEPER ALERT [{alert.alert_type.upper()}]: {alert.title[:100]}"

            message = self.twilio_client.messages.create(
                body=sms_message,
                from_=self.twilio_phone,
                to=phone
            )

            logger.info(f"SMS sent to {phone}: {message.sid}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False

    async def _send_push(self, push_token: str, alert) -> bool:
        """Send push notification"""
        if not self.push_enabled:
            return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=alert.title,
                    body=alert.message[:200] + ('...' if len(alert.message) > 200 else '')
                ),
                data={
                    'alert_id': str(alert.id),
                    'alert_type': alert.alert_type,
                    'priority': str(alert.priority),
                    'intelligence_id': str(alert.intelligence_id)
                },
                token=push_token
            )

            response = messaging.send(message)
            logger.info(f"Push notification sent: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    def _generate_html_email(self, alert) -> str:
        """Generate HTML email content"""
        priority_color = {
            'critical': '#ff0000',
            'high_threat': '#ff6600',
            'elevated': '#ff9900',
            'security_incident': '#cc0000',
            'general': '#0066cc'
        }.get(alert.alert_type, '#666666')

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: {priority_color}; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .footer {{ padding: 10px; text-align: center; font-size: 12px; color: #666; }}
        .priority {{ display: inline-block; padding: 5px 10px; background-color: {priority_color}; color: white; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>WATCHKEEPER ALERT</h1>
            <p><span class="priority">{alert.alert_type.upper()}</span></p>
        </div>
        <div class="content">
            <h2>{alert.title}</h2>
            <pre style="white-space: pre-wrap;">{alert.message}</pre>
        </div>
        <div class="footer">
            <p>WATCHKEEPER Intelligence System | Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    async def send_test_alert(self, recipient_email: str) -> bool:
        """Send a test alert to verify system"""
        from ..models.alerts import Alert

        test_alert = Alert(
            alert_type='test',
            priority=5,
            title='WATCHKEEPER Test Alert',
            message=f"""
This is a test alert from WATCHKEEPER Intelligence System.

Sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

If you received this message, your notification system is working correctly.

---
WATCHKEEPER Intelligence System
            """,
            status='test'
        )

        return await self._send_email(recipient_email, test_alert)


class EscalationManager:
    """Manages alert escalation chains"""

    def __init__(self, db: Session):
        self.db = db

    async def check_escalations(self):
        """Check for alerts that need escalation"""
        from ..models.alerts import Alert

        # Get unacknowledged high-priority alerts older than threshold
        threshold_time = datetime.utcnow() - timedelta(minutes=30)

        alerts = self.db.query(Alert).filter(
            and_(
                Alert.status == 'sent',
                Alert.acknowledged_at.is_(None),
                Alert.priority >= 8,
                Alert.sent_at < threshold_time
            )
        ).all()

        for alert in alerts:
            await self._escalate_alert(alert)

    async def _escalate_alert(self, alert):
        """Escalate an unacknowledged alert"""
        # TODO: Implement escalation logic
        # - Notify supervisors
        # - Send to backup contacts
        # - Trigger emergency protocols
        logger.warning(f"Alert {alert.id} requires escalation")
