"""
Alert schemas for WATCHKEEPER API
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from src.models.alert import AlertSeverity, AlertStatus


class AlertBase(BaseModel):
    """Base alert schema."""
    title: str
    message: str
    severity: AlertSeverity


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    intelligence_id: Optional[int] = None
    threat_id: Optional[int] = None
    assigned_to_user_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    status: Optional[AlertStatus] = None
    assigned_to_user_id: Optional[int] = None
    resolution_notes: Optional[str] = None


class AlertResponse(AlertBase):
    """Schema for alert response."""
    id: int
    status: AlertStatus
    intelligence_id: Optional[int] = None
    threat_id: Optional[int] = None
    assigned_to_user_id: Optional[int] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True


class AlertFilter(BaseModel):
    """Schema for filtering alerts."""
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    assigned_to_user_id: Optional[int] = None
    intelligence_id: Optional[int] = None
    threat_id: Optional[int] = None
