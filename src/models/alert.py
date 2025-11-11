"""
Alert and Notification Models for WATCHKEEPER

This module defines Alert and Notification models for the alerting system.
"""

from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship

from src.core.database import Base


class AlertSeverity(str, enum.Enum):
    """Enumeration of alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """Enumeration of alert statuses."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class NotificationType(str, enum.Enum):
    """Enumeration of notification types."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationStatus(str, enum.Enum):
    """Enumeration of notification statuses."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class Alert(Base):
    """
    Alert model for threat alerts.

    Attributes:
        id: Unique identifier for the alert
        title: Title of the alert
        message: Detailed message
        severity: Severity level of the alert
        status: Current status of the alert
        intelligence_id: Related intelligence item
        threat_id: Related threat
        assigned_to_user_id: User assigned to handle the alert
        created_at: When the alert was created
        acknowledged_at: When the alert was acknowledged
        resolved_at: When the alert was resolved
        metadata: Additional metadata in JSON format
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)

    # Severity and status
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.NEW, index=True)

    # Related entities
    intelligence_id = Column(Integer, ForeignKey("intelligence_items.id", ondelete='CASCADE'), nullable=True, index=True)
    threat_id = Column(Integer, ForeignKey("threats.id", ondelete='CASCADE'), nullable=True, index=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete='SET NULL'), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Additional data
    metadata = Column(JSONB, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    intelligence = relationship("Intelligence")
    threat = relationship("Threat")
    assigned_to_user = relationship("User", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of the alert."""
        return f"<Alert(id={self.id}, severity={self.severity}, status={self.status})>"


class Notification(Base):
    """
    Notification model for tracking sent notifications.

    Attributes:
        id: Unique identifier for the notification
        alert_id: Related alert
        notification_type: Type of notification (email, SMS, webhook)
        recipient: Email address, phone number, or webhook URL
        status: Status of the notification
        sent_at: When the notification was sent
        delivered_at: When the notification was confirmed delivered
        error_message: Error message if notification failed
        metadata: Additional metadata (e.g., message ID from provider)
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete='CASCADE'), nullable=False, index=True)

    # Notification details
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)
    recipient = Column(String(500), nullable=False)

    # Status
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Additional data
    metadata = Column(JSONB, nullable=True)  # e.g., provider message ID, response data

    # Relationships
    alert = relationship("Alert", back_populates="notifications")

    def __repr__(self):
        """String representation of the notification."""
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status})>"
