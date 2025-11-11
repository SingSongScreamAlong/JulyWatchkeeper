"""
Notification Service for WATCHKEEPER

This service handles sending notifications via email, SMS, and webhooks.
"""

import os
import logging
from typing import Optional, Dict, Any
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications through various channels."""

    def __init__(self):
        """Initialize notification service with configuration from environment."""
        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        # Twilio configuration
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER", "")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> bool:
        """
        Send an email notification.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html: Optional HTML body

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("Email credentials not configured, skipping email notification")
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.smtp_from
            message["To"] = to

            # Add plain text and HTML parts
            message.attach(MIMEText(body, "plain"))
            if html:
                message.attach(MIMEText(html, "html"))

            # Create SSL context
            context = ssl.create_default_context()

            # Send email
            if self.smtp_use_tls:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(message)

            logger.info(f"Email sent successfully to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False

    async def send_sms(self, to: str, message: str) -> bool:
        """
        Send an SMS notification via Twilio.

        Args:
            to: Recipient phone number (E.164 format)
            message: SMS message text

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.warning("Twilio credentials not configured, skipping SMS notification")
            return False

        try:
            # Use Twilio API
            async with aiohttp.ClientSession() as session:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"

                data = {
                    "From": self.twilio_from_number,
                    "To": to,
                    "Body": message
                }

                auth = aiohttp.BasicAuth(self.twilio_account_sid, self.twilio_auth_token)

                async with session.post(url, data=data, auth=auth) as response:
                    if response.status in [200, 201]:
                        logger.info(f"SMS sent successfully to {to}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send SMS to {to}: {response.status} - {error_text}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {str(e)}")
            return False

    async def send_webhook(self, url: str, payload: Dict[str, Any]) -> bool:
        """
        Send a webhook notification.

        Args:
            url: Webhook URL
            payload: JSON payload to send

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201, 202, 204]:
                        logger.info(f"Webhook sent successfully to {url}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send webhook to {url}: {response.status} - {error_text}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send webhook to {url}: {str(e)}")
            return False

    async def send_in_app(self, user_id: int, title: str, message: str) -> bool:
        """
        Send an in-app notification (stored in database for UI to display).

        Args:
            user_id: ID of the user to notify
            title: Notification title
            message: Notification message

        Returns:
            bool: True if created successfully, False otherwise
        """
        # This would be implemented by creating a record in a notifications table
        # for now, we'll just log it
        logger.info(f"In-app notification for user {user_id}: {title}")
        return True
