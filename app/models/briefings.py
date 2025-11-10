"""Intelligence Briefing Models"""

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, func, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class IntelligenceBriefing(Base):
    __tablename__ = "intelligence_briefings"

    id = Column(Integer, primary_key=True, index=True)
    briefing_type = Column(String(50))  # daily, weekly, incident, executive
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    full_content = Column(Text, nullable=False)
    format = Column(String(50))  # text, html, pdf, voice
    priority = Column(Integer, default=5)
    region_focus = Column(String(100))
    time_period_start = Column(DateTime)
    time_period_end = Column(DateTime)
    intelligence_items_included = Column(ARRAY(Integer))
    incidents_included = Column(ARRAY(Integer))
    key_threats = Column(JSONB)
    recommendations = Column(Text)
    generated_by = Column(String(100))  # auto, analyst_name
    reviewed_by = Column(Integer)
    published = Column(Boolean, default=False)
    publish_date = Column(DateTime)
    recipients = Column(ARRAY(Integer))
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "briefing_type": self.briefing_type,
            "title": self.title,
            "summary": self.summary,
            "full_content": self.full_content,
            "format": self.format,
            "priority": self.priority,
            "region_focus": self.region_focus,
            "time_period_start": self.time_period_start.isoformat() if self.time_period_start else None,
            "time_period_end": self.time_period_end.isoformat() if self.time_period_end else None,
            "intelligence_items_included": self.intelligence_items_included,
            "incidents_included": self.incidents_included,
            "key_threats": self.key_threats,
            "recommendations": self.recommendations,
            "generated_by": self.generated_by,
            "reviewed_by": self.reviewed_by,
            "published": self.published,
            "publish_date": self.publish_date.isoformat() if self.publish_date else None,
            "recipients": self.recipients,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
