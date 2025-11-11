"""
Analytics schemas for WATCHKEEPER API
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class MetricResponse(BaseModel):
    """Schema for analytics metric response."""
    id: int
    metric_name: str
    metric_category: str
    value: float
    dimensions: Optional[Dict[str, Any]] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SystemHealthResponse(BaseModel):
    """Schema for system health response."""
    id: int
    component: str
    status: str
    response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    checked_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    """Schema for dashboard summary."""
    total_intelligence: int
    total_threats: int
    active_alerts: int
    processing_rate: float
    system_health: str


class MetricsQuery(BaseModel):
    """Schema for metrics query."""
    metric_name: Optional[str] = None
    metric_category: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
