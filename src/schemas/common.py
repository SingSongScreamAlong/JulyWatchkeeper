"""
Common Schemas for WATCHKEEPER

This module provides common Pydantic schemas used across the application.
"""

from typing import Generic, TypeVar, List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime

# Generic type for paginated responses
T = TypeVar('T')


class MessageResponse(BaseModel):
    """
    Standard message response schema.
    
    Attributes:
        message: Response message
        status: Response status (success, error, warning, info)
    """
    message: str
    status: str = "success"


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    
    Attributes:
        message: Error message
        status: Always "error"
        error_code: Optional error code
        details: Optional error details
    """
    message: str
    status: str = "error"
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.
    
    Attributes:
        page: Page number (1-indexed)
        page_size: Number of items per page
    """
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response schema.
    
    Attributes:
        items: List of items
        total: Total number of items
        page: Current page number
        page_size: Number of items per page
        pages: Total number of pages
    """
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class GeoPoint(BaseModel):
    """
    Geographic point schema.
    
    Attributes:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    """
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class TimeRange(BaseModel):
    """
    Time range schema.
    
    Attributes:
        start_time: Start time
        end_time: End time
    """
    start_time: datetime
    end_time: datetime
