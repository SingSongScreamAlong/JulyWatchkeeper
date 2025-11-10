"""Alert and Notification Models"""

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, func, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    threat_level_threshold = Column(Float, default=7.0)
    missionary_relevance_threshold = Column(Float, default=7.0)
    region_filter = Column(ARRAY(String))
    country_filter = Column(ARRAY(String))
    keyword_filter = Column(ARRAY(String))
    notification_channels = Column(JSONB)  # {email: true, sms: false, push: true}
    escalation_rules = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    alerts = relationship("Alert", back_populates="alert_rule")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "threat_level_threshold": self.threat_level_threshold,
            "missionary_relevance_threshold": self.missionary_relevance_threshold,
            "region_filter": self.region_filter,
            "country_filter": self.country_filter,
            "keyword_filter": self.keyword_filter,
            "notification_channels": self.notification_channels,
            "escalation_rules": self.escalation_rules,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_rule_id = Column(Integer, ForeignKey('alert_rules.id'))
    intelligence_id = Column(Integer, ForeignKey('intelligence_items.id'))
    alert_type = Column(String(50))  # high_threat, critical, evacuation
    priority = Column(Integer, default=5)  # 1-10
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default='pending')  # pending, sent, failed, acknowledged
    sent_at = Column(DateTime)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(Integer)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    alert_rule = relationship("AlertRule", back_populates="alerts")
    intelligence = relationship("IntelligenceItem")

    def to_dict(self):
        return {
            "id": self.id,
            "alert_rule_id": self.alert_rule_id,
            "intelligence_id": self.intelligence_id,
            "alert_type": self.alert_type,
            "priority": self.priority,
            "title": self.title,
            "message": self.message,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class NotificationRecipient(Base):
    __tablename__ = "notification_recipients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    push_token = Column(Text)
    roles = Column(ARRAY(String))  # admin, field_staff, analyst
    regions = Column(ARRAY(String))
    notification_preferences = Column(JSONB)  # {email_enabled: true, sms_enabled: false}
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "roles": self.roles,
            "regions": self.regions,
            "notification_preferences": self.notification_preferences,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
