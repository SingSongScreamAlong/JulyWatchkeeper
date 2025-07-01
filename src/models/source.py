"""
Source Model for WATCHKEEPER

This module defines the Source model for storing intelligence sources.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum

from src.core.database import Base


class SourceType(str, enum.Enum):
    """Enumeration of source types."""
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    GOVERNMENT = "government"
    NGO = "ngo"
    ACADEMIC = "academic"
    INTELLIGENCE = "intelligence"
    OTHER = "other"


class Source(Base):
    """
    Source model for storing intelligence sources.
    
    Attributes:
        id: Unique identifier for the source
        name: Name of the source
        url: URL of the source
        source_type: Type of the source
        reliability_score: Reliability score for the source (0-1)
        language: Language of the source
        country: Country of the source
        last_collected_at: Last collection date
        is_active: Whether the source is active
        collection_frequency: Collection frequency in seconds
        rate_limit: Rate limit for the source
        intelligence_items: Related intelligence items
    """
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    source_type = Column(Enum(SourceType), nullable=False, default=SourceType.NEWS)
    
    # Source assessment
    reliability_score = Column(Float, nullable=False, default=0.5)
    language = Column(String(10), nullable=False, default="en")
    country = Column(String(2), nullable=True)
    
    # Collection metadata
    last_collected_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    collection_frequency = Column(Integer, default=3600, nullable=False)  # in seconds
    rate_limit = Column(Integer, default=100, nullable=False)  # requests per hour
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    intelligence_items = relationship("Intelligence", back_populates="source")
    
    def __repr__(self):
        """String representation of the source."""
        return f"<Source(id={self.id}, name='{self.name}', type={self.source_type})>"
