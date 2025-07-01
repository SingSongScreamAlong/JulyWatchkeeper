"""
Intelligence Model for WATCHKEEPER

This module defines the Intelligence model for storing processed intelligence articles.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
import enum

from src.core.database import Base


class ProcessingStatus(str, enum.Enum):
    """Enumeration of processing statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Intelligence(Base):
    """
    Intelligence model for storing processed intelligence articles.
    
    Attributes:
        id: Unique identifier for the intelligence item
        raw_content: Raw content of the intelligence item
        processed_content: Processed content of the intelligence item
        threat_id: Foreign key to the related threat
        source_id: Foreign key to the related source
        ai_analysis_data: JSON data from AI analysis
        processing_status: Status of the processing
        error_message: Error message if processing failed
        processing_time: Time taken for processing in seconds
        confidence_score: Confidence score for the intelligence (0-1)
        threat: Related threat
        source: Related source
    """
    __tablename__ = "intelligence_items"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_content = Column(Text, nullable=False)
    processed_content = Column(Text, nullable=True)
    
    # Foreign keys
    threat_id = Column(Integer, ForeignKey("threats.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    
    # AI analysis
    ai_analysis_data = Column(JSONB, nullable=True)
    processing_status = Column(Enum(ProcessingStatus), nullable=False, default=ProcessingStatus.PENDING)
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds
    confidence_score = Column(Float, nullable=True)
    
    # Geolocation
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    threat = relationship("Threat", back_populates="intelligence_items")
    source = relationship("Source", back_populates="intelligence_items")
    
    def __repr__(self):
        """String representation of the intelligence item."""
        return f"<Intelligence(id={self.id}, status={self.processing_status})>"
