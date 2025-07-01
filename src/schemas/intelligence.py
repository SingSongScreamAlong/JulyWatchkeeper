"""
Intelligence Schemas for WATCHKEEPER

This module provides Pydantic schemas for intelligence-related API requests and responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from src.models.intelligence import ProcessingStatus


class IntelligenceBase(BaseModel):
    """
    Base schema for intelligence data.
    
    Attributes:
        raw_content: Raw content of the intelligence item
        source_id: Foreign key to the related source
    """
    raw_content: str = Field(..., min_length=10)
    source_id: int = Field(..., gt=0)


class IntelligenceCreate(IntelligenceBase):
    """
    Schema for creating a new intelligence item.
    """
    pass


class IntelligenceUpdate(BaseModel):
    """
    Schema for updating an existing intelligence item.
    
    All fields are optional to allow partial updates.
    """
    raw_content: Optional[str] = Field(None, min_length=10)
    processed_content: Optional[str] = None
    threat_id: Optional[int] = Field(None, gt=0)
    ai_analysis_data: Optional[Dict[str, Any]] = None
    processing_status: Optional[ProcessingStatus] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = Field(None, ge=0)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class IntelligenceInDB(IntelligenceBase):
    """
    Schema for intelligence data as stored in the database.
    
    Adds database-specific fields to the base schema.
    """
    id: int
    processed_content: Optional[str] = None
    threat_id: Optional[int] = None
    ai_analysis_data: Optional[Dict[str, Any]] = None
    processing_status: ProcessingStatus
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    confidence_score: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class IntelligenceResponse(IntelligenceInDB):
    """
    Schema for intelligence data in API responses.
    
    May include additional computed fields or related data.
    """
    pass


class IntelligenceFilter(BaseModel):
    """
    Schema for filtering intelligence items in list endpoints.
    
    Attributes:
        source_id: Filter by source ID
        threat_id: Filter by threat ID
        processing_status: Filter by processing status
        min_confidence: Minimum confidence score
        max_confidence: Maximum confidence score
        created_after: Filter by creation date (after)
        created_before: Filter by creation date (before)
    """
    source_id: Optional[int] = None
    threat_id: Optional[int] = None
    processing_status: Optional[ProcessingStatus] = None
    min_confidence: Optional[float] = Field(None, ge=0, le=1)
    max_confidence: Optional[float] = Field(None, ge=0, le=1)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class IntelligenceProcessRequest(BaseModel):
    """
    Schema for requesting intelligence processing.
    
    Attributes:
        intelligence_id: ID of the intelligence item to process
        processing_options: Optional processing options
    """
    intelligence_id: int = Field(..., gt=0)
    processing_options: Optional[Dict[str, Any]] = None


class IntelligenceProcessResponse(BaseModel):
    """
    Schema for intelligence processing response.
    
    Attributes:
        intelligence_id: ID of the processed intelligence item
        status: Processing status
        message: Status message
        processing_time: Time taken for processing in seconds
    """
    intelligence_id: int
    status: ProcessingStatus
    message: str
    processing_time: Optional[float] = None


class IntelligenceBatchProcessRequest(BaseModel):
    """
    Schema for requesting batch intelligence processing.
    
    Attributes:
        intelligence_ids: List of intelligence item IDs to process
        processing_options: Optional processing options
    """
    intelligence_ids: List[int] = Field(..., min_items=1)
    processing_options: Optional[Dict[str, Any]] = None


class IntelligenceBatchProcessResponse(BaseModel):
    """
    Schema for batch intelligence processing response.
    
    Attributes:
        processed_count: Number of items processed
        failed_count: Number of items that failed processing
        status: Overall batch processing status
        message: Status message
    """
    processed_count: int
    failed_count: int
    status: str
    message: str
