"""
Threat Schemas for WATCHKEEPER

This module provides Pydantic schemas for threat-related API requests and responses.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

from src.models.threat import ThreatCategory, ThreatStatus
from src.schemas.common import GeoPoint


class ThreatBase(BaseModel):
    """
    Base schema for threat data.
    
    Attributes:
        title: Title of the threat
        description: Brief description of the threat
        content: Detailed content of the threat
        location: Geographic location of the threat (latitude, longitude)
        severity: Severity level of the threat (1-10)
        category: Category of the threat
        confidence_score: Confidence score for the threat (0-1)
        missionary_relevance: Relevance score for missionary operations (0-1)
        source_url: URL of the source
        source_name: Name of the source
        published_at: Publication date of the source
    """
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10, max_length=500)
    content: str = Field(..., min_length=10)
    location: Optional[GeoPoint] = None
    severity: int = Field(5, ge=1, le=10)
    category: ThreatCategory = ThreatCategory.OTHER
    confidence_score: float = Field(0.5, ge=0, le=1)
    missionary_relevance: float = Field(0.5, ge=0, le=1)
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    published_at: Optional[datetime] = None


class ThreatCreate(ThreatBase):
    """
    Schema for creating a new threat.
    """
    pass


class ThreatUpdate(BaseModel):
    """
    Schema for updating an existing threat.
    
    All fields are optional to allow partial updates.
    """
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    content: Optional[str] = Field(None, min_length=10)
    location: Optional[GeoPoint] = None
    severity: Optional[int] = Field(None, ge=1, le=10)
    category: Optional[ThreatCategory] = None
    status: Optional[ThreatStatus] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    missionary_relevance: Optional[float] = Field(None, ge=0, le=1)
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    published_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    resolved_at: Optional[datetime] = None


class ThreatInDB(ThreatBase):
    """
    Schema for threat data as stored in the database.
    
    Adds database-specific fields to the base schema.
    """
    id: int
    status: ThreatStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ThreatResponse(ThreatInDB):
    """
    Schema for threat data in API responses.
    
    May include additional computed fields or related data.
    """
    pass


class ThreatFilter(BaseModel):
    """
    Schema for filtering threats in list endpoints.
    
    Attributes:
        status: Filter by status
        category: Filter by category
        min_severity: Minimum severity level
        max_severity: Maximum severity level
        min_confidence: Minimum confidence score
        max_confidence: Maximum confidence score
        min_missionary_relevance: Minimum missionary relevance score
        max_missionary_relevance: Maximum missionary relevance score
        is_active: Filter by active status
        created_after: Filter by creation date (after)
        created_before: Filter by creation date (before)
    """
    status: Optional[ThreatStatus] = None
    category: Optional[ThreatCategory] = None
    min_severity: Optional[int] = Field(None, ge=1, le=10)
    max_severity: Optional[int] = Field(None, ge=1, le=10)
    min_confidence: Optional[float] = Field(None, ge=0, le=1)
    max_confidence: Optional[float] = Field(None, ge=0, le=1)
    min_missionary_relevance: Optional[float] = Field(None, ge=0, le=1)
    max_missionary_relevance: Optional[float] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
