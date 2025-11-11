"""
Analytics endpoints for WATCHKEEPER API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from datetime import datetime, timedelta

from src.core.database import get_db
from src.models.analytics import AnalyticsMetric, SystemHealth
from src.models.intelligence import Intelligence, ProcessingStatus
from src.models.threat import Threat
from src.models.alert import Alert, AlertStatus
from src.schemas.analytics import MetricResponse, SystemHealthResponse, DashboardSummary, MetricsQuery
from src.middleware.rbac import get_current_active_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get dashboard summary statistics."""
    # Total intelligence items
    result = await db.execute(select(func.count(Intelligence.id)))
    total_intelligence = result.scalar() or 0

    # Total threats
    result = await db.execute(select(func.count(Threat.id)))
    total_threats = result.scalar() or 0

    # Active alerts
    result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED, AlertStatus.IN_PROGRESS])
        )
    )
    active_alerts = result.scalar() or 0

    # Processing rate (items processed in last hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = await db.execute(
        select(func.count(Intelligence.id)).where(
            and_(
                Intelligence.processed_at >= one_hour_ago,
                Intelligence.processing_status == ProcessingStatus.COMPLETED
            )
        )
    )
    processing_rate = result.scalar() or 0

    # System health (latest check)
    result = await db.execute(
        select(SystemHealth)
        .where(SystemHealth.component == "database")
        .order_by(SystemHealth.checked_at.desc())
        .limit(1)
    )
    latest_health = result.scalar_one_or_none()
    system_health = latest_health.status if latest_health else "unknown"

    return DashboardSummary(
        total_intelligence=total_intelligence,
        total_threats=total_threats,
        active_alerts=active_alerts,
        processing_rate=processing_rate,
        system_health=system_health
    )


@router.post("/metrics", response_model=List[MetricResponse])
async def query_metrics(
    query: MetricsQuery,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Query analytics metrics."""
    stmt = select(AnalyticsMetric)

    # Apply filters
    if query.metric_name:
        stmt = stmt.where(AnalyticsMetric.metric_name == query.metric_name)
    if query.metric_category:
        stmt = stmt.where(AnalyticsMetric.metric_category == query.metric_category)
    if query.start_time:
        stmt = stmt.where(AnalyticsMetric.timestamp >= query.start_time)
    if query.end_time:
        stmt = stmt.where(AnalyticsMetric.timestamp <= query.end_time)

    stmt = stmt.order_by(AnalyticsMetric.timestamp.desc()).limit(query.limit)

    result = await db.execute(stmt)
    metrics = result.scalars().all()
    return metrics


@router.get("/health", response_model=List[SystemHealthResponse])
async def get_system_health(
    component: str = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get system health checks."""
    stmt = select(SystemHealth)

    if component:
        stmt = stmt.where(SystemHealth.component == component)

    stmt = stmt.order_by(SystemHealth.checked_at.desc()).limit(limit)

    result = await db.execute(stmt)
    health_checks = result.scalars().all()
    return health_checks


@router.get("/metrics/{metric_name}/latest", response_model=MetricResponse)
async def get_latest_metric(
    metric_name: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get the latest value of a specific metric."""
    result = await db.execute(
        select(AnalyticsMetric)
        .where(AnalyticsMetric.metric_name == metric_name)
        .order_by(AnalyticsMetric.timestamp.desc())
        .limit(1)
    )
    metric = result.scalar_one_or_none()

    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric '{metric_name}' not found"
        )

    return metric
