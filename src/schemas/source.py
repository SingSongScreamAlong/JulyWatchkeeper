"""
Source Schemas for WATCHKEEPER

This module provides Pydantic schemas for source-related API requests and responses.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, AnyUrl

from src.models.source import SourceType


class SourceBase(BaseModel):
    """
    Base schema for source data.
    
    Attributes:
        name: Name of the source
        url: URL of the source
        source_type: Type of the source
        reliability_score: Reliability score for the source (0-1)
        language: Language of the source
        country: Country of the source (ISO 2-letter code)
        collection_frequency: Collection frequency in seconds
        rate_limit: Rate limit for the source
    """
    name: str = Field(..., min_length=3, max_length=255)
    url: str = Field(..., min_length=5, max_length=500)
    source_type: SourceType = SourceType.NEWS
    reliability_score: float = Field(0.5, ge=0, le=1)
    language: str = Field("en", min_length=2, max_length=10)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    collection_frequency: int = Field(3600, ge=60, description="Collection frequency in seconds")
    rate_limit: int = Field(100, ge=1, description="Requests per hour")


class SourceCreate(SourceBase):
    """
    Schema for creating a new source.
    """
    pass


class SourceUpdate(BaseModel):
    """
    Schema for updating an existing source.
    
    All fields are optional to allow partial updates.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    url: Optional[str] = Field(None, min_length=5, max_length=500)
    source_type: Optional[SourceType] = None
    reliability_score: Optional[float] = Field(None, ge=0, le=1)
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    collection_frequency: Optional[int] = Field(None, ge=60)
    rate_limit: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class SourceInDB(SourceBase):
    """
    Schema for source data as stored in the database.
    
    Adds database-specific fields to the base schema.
    """
    id: int
    is_active: bool
    last_collected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class SourceResponse(SourceInDB):
    """
    Schema for source data in API responses.
    
    May include additional computed fields or related data.
    """
    pass


class SourceFilter(BaseModel):
    """
    Schema for filtering sources in list endpoints.
    
    Attributes:
        source_type: Filter by source type
        language: Filter by language
        country: Filter by country
        min_reliability: Minimum reliability score
        max_reliability: Maximum reliability score
        is_active: Filter by active status
    """
    source_type: Optional[SourceType] = None
    language: Optional[str] = None
    country: Optional[str] = None
    min_reliability: Optional[float] = Field(None, ge=0, le=1)
    max_reliability: Optional[float] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None


class SourceCollectionStatus(BaseModel):
    """
    Schema for source collection status.
    
    Attributes:
        source_id: Source ID
        name: Source name
        last_collected_at: Last collection time
        next_collection_at: Next scheduled collection time
        is_active: Whether the source is active
        collection_frequency: Collection frequency in seconds
    """
    source_id: int
    name: str
    last_collected_at: Optional[datetime] = None
    next_collection_at: Optional[datetime] = None
    is_active: bool
    collection_frequency: int
