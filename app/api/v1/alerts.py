"""Alert and Notification API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ...database import get_db
from ...auth import get_current_active_user
from ...services.alert_service import AlertService
from ...models.alerts import AlertRule, Alert, NotificationRecipient

router = APIRouter()


# Pydantic Models
class AlertRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    enabled: bool = True
    threat_level_threshold: float = 7.0
    missionary_relevance_threshold: float = 7.0
    region_filter: Optional[List[str]] = None
    country_filter: Optional[List[str]] = None
    keyword_filter: Optional[List[str]] = None
    notification_channels: Optional[dict] = None
    escalation_rules: Optional[dict] = None


class AlertAcknowledge(BaseModel):
    acknowledged_by: int
    notes: Optional[str] = None


class NotificationRecipientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    push_token: Optional[str] = None
    roles: List[str]
    regions: Optional[List[str]] = None
    notification_preferences: Optional[dict] = None


# Alert Rule Endpoints
@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new alert rule"""
    rule = AlertRule(**rule_data.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule.to_dict()


@router.get("/rules")
async def get_alert_rules(
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all alert rules"""
    query = db.query(AlertRule)
    if enabled_only:
        query = query.filter(AlertRule.enabled == True)
    rules = query.all()
    return [rule.to_dict() for rule in rules]


@router.put("/rules/{rule_id}")
async def update_alert_rule(
    rule_id: int,
    rule_data: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update an alert rule"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    for key, value in rule_data.dict(exclude_unset=True).items():
        setattr(rule, key, value)

    db.commit()
    db.refresh(rule)
    return rule.to_dict()


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete an alert rule"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    db.delete(rule)
    db.commit()
    return {"message": "Alert rule deleted"}


# Alert Endpoints
@router.get("/")
async def get_alerts(
    status: Optional[str] = None,
    priority_min: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get alerts"""
    query = db.query(Alert)

    if status:
        query = query.filter(Alert.status == status)

    if priority_min:
        query = query.filter(Alert.priority >= priority_min)

    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return [alert.to_dict() for alert in alerts]


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    ack_data: AlertAcknowledge,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = 'acknowledged'
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = ack_data.acknowledged_by

    db.commit()
    db.refresh(alert)
    return alert.to_dict()


# Notification Recipients
@router.post("/recipients", status_code=status.HTTP_201_CREATED)
async def create_recipient(
    recipient_data: NotificationRecipientCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new notification recipient"""
    recipient = NotificationRecipient(**recipient_data.dict())
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    return recipient.to_dict()


@router.get("/recipients")
async def get_recipients(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all notification recipients"""
    query = db.query(NotificationRecipient)
    if active_only:
        query = query.filter(NotificationRecipient.active == True)
    recipients = query.all()
    return [r.to_dict() for r in recipients]


@router.post("/test")
async def send_test_alert(
    recipient_email: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Send a test alert to verify the notification system"""
    alert_service = AlertService(db, {})  # TODO: Load config from settings
    result = await alert_service.send_test_alert(recipient_email)
    return {"success": result, "recipient": recipient_email}
