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


# File Upload Endpoints
@router.post("/{incident_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_incident_attachment(
    incident_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Upload attachments to an incident"""
    from ...models.incidents import FieldIncident
    from ...services.file_service import get_file_service

    # Verify incident exists
    incident = db.query(FieldIncident).filter(FieldIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    file_service = get_file_service()
    uploaded_files = []

    for file in files:
        # Upload file
        result = await file_service.upload_file(
            file.file,
            file.filename,
            uploaded_by=current_user.id if hasattr(current_user, 'id') else 0,
            related_entity='incident',
            related_id=incident_id
        )

        if result['success']:
            uploaded_files.append(result)
        else:
            # Clean up previously uploaded files if one fails
            for prev_file in uploaded_files:
                await file_service.delete_file(prev_file['file_path'])
            raise HTTPException(status_code=400, detail=result['error'])

    # Update incident with attachment info
    existing_attachments = incident.attachments or {}
    attachment_list = existing_attachments.get('files', [])

    for file_info in uploaded_files:
        attachment_list.append({
            'file_id': file_info['file_id'],
            'filename': file_info['original_filename'],
            'size': file_info['size_bytes'],
            'mime_type': file_info['mime_type'],
            'uploaded_at': file_info['uploaded_at'],
            'url': file_service.get_file_url(file_info['stored_filename'], file_info['category'])
        })

    existing_attachments['files'] = attachment_list
    incident.attachments = existing_attachments

    db.commit()

    return {
        'success': True,
        'incident_id': incident_id,
        'files_uploaded': len(uploaded_files),
        'files': attachment_list
    }


@router.get("/{incident_id}/attachments")
async def get_incident_attachments(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all attachments for an incident"""
    from ...models.incidents import FieldIncident

    incident = db.query(FieldIncident).filter(FieldIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    attachments = incident.attachments or {}
    return attachments.get('files', [])


@router.delete("/{incident_id}/attachments/{file_id}")
async def delete_incident_attachment(
    incident_id: int,
    file_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete an attachment from an incident"""
    from ...models.incidents import FieldIncident
    from ...services.file_service import get_file_service

    incident = db.query(FieldIncident).filter(FieldIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    attachments = incident.attachments or {}
    files = attachments.get('files', [])

    # Find and remove file from list
    file_to_delete = None
    new_files = []

    for file_info in files:
        if file_info['file_id'] == file_id:
            file_to_delete = file_info
        else:
            new_files.append(file_info)

    if not file_to_delete:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Delete file from storage
    file_service = get_file_service()
    # Note: We'd need to store the file_path in attachments to delete it
    # For now, just remove from incident

    attachments['files'] = new_files
    incident.attachments = attachments

    db.commit()

    return {
        'success': True,
        'message': 'Attachment deleted',
        'file_id': file_id
    }
