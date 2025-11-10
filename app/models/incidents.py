"""Incident Models"""

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class FieldIncident(Base):
    __tablename__ = "field_incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String(100), nullable=False)  # threat, safety, medical, security
    severity = Column(Integer, nullable=False)  # 1-10
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    country = Column(String(100))
    region = Column(String(100))
    reported_by = Column(Integer)  # user_id
    reporter_name = Column(String(255))
    reporter_contact = Column(String(255))
    incident_date = Column(DateTime, nullable=False)
    reported_date = Column(DateTime, default=func.now())
    status = Column(String(50), default='new')  # new, investigating, resolved, false_report
    verified = Column(Boolean, default=False)
    verified_by = Column(Integer)
    verification_notes = Column(Text)
    related_intelligence_id = Column(Integer, ForeignKey('intelligence_items.id'))
    attachments = Column(JSONB)  # photos, documents
    witnesses = Column(JSONB)
    actions_taken = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    related_intelligence = relationship("IntelligenceItem")

    def to_dict(self):
        return {
            "id": self.id,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country": self.country,
            "region": self.region,
            "reported_by": self.reported_by,
            "reporter_name": self.reporter_name,
            "reporter_contact": self.reporter_contact,
            "incident_date": self.incident_date.isoformat() if self.incident_date else None,
            "reported_date": self.reported_date.isoformat() if self.reported_date else None,
            "status": self.status,
            "verified": self.verified,
            "verified_by": self.verified_by,
            "verification_notes": self.verification_notes,
            "related_intelligence_id": self.related_intelligence_id,
            "attachments": self.attachments,
            "witnesses": self.witnesses,
            "actions_taken": self.actions_taken,
            "follow_up_required": self.follow_up_required,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
