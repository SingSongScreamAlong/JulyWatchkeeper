"""Incident Reporting API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ...database import get_db
from ...auth import get_current_active_user
from ...services.incident_service import IncidentService

router = APIRouter()


# Pydantic Models
class IncidentCreate(BaseModel):
    incident_type: str  # threat, safety, medical, security
    severity: int  # 1-10
    title: str
    description: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None
    region: Optional[str] = None
    reported_by: Optional[int] = None
    reporter_name: Optional[str] = None
    reporter_contact: Optional[str] = None
    incident_date: datetime
    attachments: Optional[dict] = None
    witnesses: Optional[dict] = None
    metadata: Optional[dict] = None


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    actions_taken: Optional[str] = None
    follow_up_required: Optional[bool] = None
    metadata: Optional[dict] = None


class IncidentVerify(BaseModel):
    verifier_id: int
    notes: str


# Endpoints
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new field incident report"""
    incident_service = IncidentService(db)
    incident = await incident_service.create_incident(incident_data.dict())
    return incident


@router.get("/")
async def get_incidents(
    status: Optional[str] = None,
    region: Optional[str] = None,
    min_severity: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get incidents with optional filters"""
    from ...models.incidents import FieldIncident

    query = db.query(FieldIncident)

    if status:
        query = query.filter(FieldIncident.status == status)

    if region:
        query = query.filter(FieldIncident.region == region)

    if min_severity:
        query = query.filter(FieldIncident.severity >= min_severity)

    incidents = query.order_by(FieldIncident.incident_date.desc()).limit(limit).all()
    return [incident.to_dict() for incident in incidents]


@router.get("/high-severity")
async def get_high_severity_incidents(
    min_severity: int = 7,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get high severity unresolved incidents"""
    incident_service = IncidentService(db)
    incidents = await incident_service.get_high_severity_incidents(min_severity)
    return incidents


@router.get("/{incident_id}")
async def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific incident by ID"""
    from ...models.incidents import FieldIncident

    incident = db.query(FieldIncident).filter(FieldIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return incident.to_dict()


@router.put("/{incident_id}")
async def update_incident(
    incident_id: int,
    incident_data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update an incident"""
    incident_service = IncidentService(db)
    incident = await incident_service.update_incident(
        incident_id,
        incident_data.dict(exclude_unset=True)
    )
    return incident


@router.post("/{incident_id}/verify")
async def verify_incident(
    incident_id: int,
    verify_data: IncidentVerify,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Verify an incident report"""
    incident_service = IncidentService(db)
    incident = await incident_service.verify_incident(
        incident_id,
        verify_data.verifier_id,
        verify_data.notes
    )
    return incident


@router.get("/region/{region}")
async def get_incidents_by_region(
    region: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all incidents for a specific region"""
    incident_service = IncidentService(db)
    incidents = await incident_service.get_incidents_by_region(region, status)
    return incidents
