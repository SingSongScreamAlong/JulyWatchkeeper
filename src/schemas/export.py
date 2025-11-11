"""
Export schemas for WATCHKEEPER API
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from src.models.export import ExportFormat, ExportStatus


class ExportCreate(BaseModel):
    """Schema for creating an export request."""
    export_format: ExportFormat
    resource_type: str  # 'intelligence', 'threats', 'sources', etc.
    filters: Optional[Dict[str, Any]] = None


class ExportResponse(BaseModel):
    """Schema for export response."""
    id: int
    user_id: Optional[int] = None
    export_format: ExportFormat
    status: ExportStatus
    resource_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    row_count: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
