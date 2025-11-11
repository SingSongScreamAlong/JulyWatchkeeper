"""
Alert management endpoints for WATCHKEEPER API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from src.core.database import get_db
from src.models.alert import Alert, AlertStatus
from src.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, AlertFilter
from src.middleware.rbac import get_current_active_user
from src.tasks.alert_tasks import send_alert_notifications

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = 0,
    limit: int = 100,
    severity: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List alerts with optional filtering."""
    query = select(Alert)

    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)

    query = query.offset(skip).limit(limit).order_by(Alert.created_at.desc())

    result = await db.execute(query)
    alerts = result.scalars().all()
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific alert."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return alert


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_in: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new alert manually."""
    alert = Alert(
        title=alert_in.title,
        message=alert_in.message,
        severity=alert_in.severity,
        intelligence_id=alert_in.intelligence_id,
        threat_id=alert_in.threat_id,
        assigned_to_user_id=alert_in.assigned_to_user_id,
        metadata=alert_in.metadata
    )

    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    # Send notifications asynchronously
    send_alert_notifications.delay(alert.id)

    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_in: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update an alert (e.g., acknowledge, resolve)."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    # Update fields
    if alert_in.status is not None:
        alert.status = alert_in.status

        # Set timestamps based on status
        from datetime import datetime
        if alert_in.status == AlertStatus.ACKNOWLEDGED and not alert.acknowledged_at:
            alert.acknowledged_at = datetime.utcnow()
        elif alert_in.status == AlertStatus.RESOLVED and not alert.resolved_at:
            alert.resolved_at = datetime.utcnow()

    if alert_in.assigned_to_user_id is not None:
        alert.assigned_to_user_id = alert_in.assigned_to_user_id

    if alert_in.resolution_notes is not None:
        alert.resolution_notes = alert_in.resolution_notes

    await db.commit()
    await db.refresh(alert)

    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete an alert."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    await db.delete(alert)
    await db.commit()
