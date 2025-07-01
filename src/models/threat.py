"""
Threat Model for WATCHKEEPER

This module defines the Threat model for storing intelligence threats.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
import enum

from src.core.database import Base


class ThreatCategory(str, enum.Enum):
    """Enumeration of threat categories."""
    SECURITY = "security"
    POLITICAL = "political"
    ECONOMIC = "economic"
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    TECHNOLOGICAL = "technological"
    OTHER = "other"


class ThreatStatus(str, enum.Enum):
    """Enumeration of threat statuses."""
    PENDING = "pending"
    ACTIVE = "active"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"


class Threat(Base):
    """
    Threat model for storing intelligence threats.
    
    Attributes:
        id: Unique identifier for the threat
        title: Title of the threat
        description: Brief description of the threat
        content: Detailed content of the threat
        location: Geographic location of the threat (latitude, longitude)
        severity: Severity level of the threat (1-10)
        category: Category of the threat
        status: Current status of the threat
        confidence_score: Confidence score for the threat (0-1)
        missionary_relevance: Relevance score for missionary operations (0-1)
        source_url: URL of the source
        source_name: Name of the source
        published_at: Publication date of the source
        created_at: Creation date of the threat
        updated_at: Last update date of the threat
        is_active: Whether the threat is active
        resolved_at: Date when the threat was resolved
        intelligence_items: Related intelligence items
    """
    __tablename__ = "threats"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    
    # Geographic location using PostGIS
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    
    # Threat assessment
    severity = Column(Integer, nullable=False, default=5)
    category = Column(Enum(ThreatCategory), nullable=False, default=ThreatCategory.OTHER)
    status = Column(Enum(ThreatStatus), nullable=False, default=ThreatStatus.PENDING)
    confidence_score = Column(Float, nullable=False, default=0.5)
    missionary_relevance = Column(Float, nullable=False, default=0.5)
    
    # Source information
    source_url = Column(String(500), nullable=True)
    source_name = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    intelligence_items = relationship("Intelligence", back_populates="threat")
    
    def __repr__(self):
        """String representation of the threat."""
        return f"<Threat(id={self.id}, title='{self.title}', status={self.status})>"
