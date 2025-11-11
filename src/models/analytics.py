"""
Analytics Model for WATCHKEEPER

This module defines models for analytics and metrics tracking.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB

from src.core.database import Base


class AnalyticsMetric(Base):
    """
    Analytics metric model for tracking system metrics over time.

    Attributes:
        id: Unique identifier for the metric
        metric_name: Name of the metric (e.g., 'threat_count', 'processing_time')
        metric_category: Category of the metric (e.g., 'performance', 'usage', 'threat')
        value: Numeric value of the metric
        dimensions: JSON object with dimensional data (e.g., {'region': 'Europe', 'severity': 'high'})
        timestamp: When the metric was recorded
        metadata: Additional metadata
    """
    __tablename__ = "analytics_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Metric identification
    metric_name = Column(String(100), nullable=False, index=True)
    metric_category = Column(String(50), nullable=False, index=True)

    # Metric value
    value = Column(Float, nullable=False)

    # Dimensions for grouping/filtering
    dimensions = Column(JSONB, nullable=True)  # e.g., {"region": "Europe", "severity": "high"}

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Additional data
    metadata = Column(JSONB, nullable=True)

    # Create composite index for efficient querying
    __table_args__ = (
        Index('ix_metrics_name_timestamp', 'metric_name', 'timestamp'),
        Index('ix_metrics_category_timestamp', 'metric_category', 'timestamp'),
    )

    def __repr__(self):
        """String representation of the metric."""
        return f"<AnalyticsMetric(id={self.id}, name={self.metric_name}, value={self.value})>"


class SystemHealth(Base):
    """
    System health model for tracking overall system status.

    Attributes:
        id: Unique identifier
        component: System component name (e.g., 'database', 'celery', 'ollama')
        status: Status of the component ('healthy', 'degraded', 'down')
        response_time_ms: Response time in milliseconds
        error_rate: Error rate (0-1)
        metadata: Additional health data
        checked_at: When the health check was performed
    """
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)

    # Component identification
    component = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # healthy, degraded, down

    # Health metrics
    response_time_ms = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)  # 0.0 to 1.0

    # Additional data
    metadata = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        """String representation of the health check."""
        return f"<SystemHealth(id={self.id}, component={self.component}, status={self.status})>"
