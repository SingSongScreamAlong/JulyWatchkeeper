"""Personnel and Tracking API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ...database import get_db
from ...auth import get_current_active_user
from ...services.tracking_service import TrackingService

router = APIRouter()


# Pydantic Models
class PersonnelCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None
    home_base: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_info: Optional[dict] = None
    tracking_enabled: bool = False
    check_in_frequency_hours: int = 24


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    location_name: Optional[str] = None
    country: Optional[str] = None
    activity_type: Optional[str] = 'auto_update'
    notes: Optional[str] = None


class GeofenceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fence_type: str  # safe_zone, danger_zone, restricted
    center_latitude: float
    center_longitude: float
    radius_meters: float
    polygon: Optional[dict] = None
    threat_level: Optional[float] = None
    alert_on_enter: bool = True
    alert_on_exit: bool = False
    metadata: Optional[dict] = None


class SafeContactCreate(BaseModel):
    contact_type: str  # safe_house, legal_aid, medical, transportation, embassy
    name: str
    organization: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    services_offered: Optional[List[str]] = None
    availability_24_7: bool = False
    requires_appointment: bool = False
    trust_level: int = 5
    notes: Optional[str] = None
    access_code: Optional[str] = None


# Personnel Endpoints
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_personnel(
    personnel_data: PersonnelCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new personnel record"""
    from ...models.personnel import Personnel

    personnel = Personnel(**personnel_data.dict())
    db.add(personnel)
    db.commit()
    db.refresh(personnel)
    return personnel.to_dict()


@router.get("/")
async def get_personnel(
    status: Optional[str] = None,
    organization: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all personnel"""
    from ...models.personnel import Personnel

    query = db.query(Personnel)

    if status:
        query = query.filter(Personnel.status == status)

    if organization:
        query = query.filter(Personnel.organization == organization)

    personnel = query.all()
    return [p.to_dict() for p in personnel]


@router.get("/{personnel_id}")
async def get_personnel_detail(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get detailed personnel information"""
    from ...models.personnel import Personnel

    personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
    if not personnel:
        raise HTTPException(status_code=404, detail="Personnel not found")

    return personnel.to_dict()


# Location Tracking Endpoints
@router.post("/{personnel_id}/location")
async def update_personnel_location(
    personnel_id: int,
    location_data: LocationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update personnel location"""
    tracking_service = TrackingService(db)
    result = await tracking_service.update_location(personnel_id, location_data.dict())
    return result


@router.get("/{personnel_id}/location-history")
async def get_location_history(
    personnel_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get location history for personnel"""
    from ...models.personnel import LocationHistory

    history = db.query(LocationHistory).filter(
        LocationHistory.personnel_id == personnel_id
    ).order_by(LocationHistory.timestamp.desc()).limit(limit).all()

    return [h.to_dict() for h in history]


@router.get("/check-ins/missed")
async def check_missed_checkins(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Check for personnel who missed check-ins"""
    tracking_service = TrackingService(db)
    missed = await tracking_service.check_missed_checkins()
    return missed


@router.get("/danger-zones/current")
async def get_personnel_in_danger_zones(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get personnel currently in danger zones"""
    tracking_service = TrackingService(db)
    at_risk = await tracking_service.get_personnel_in_danger_zones()
    return at_risk


# Geofence Endpoints
@router.post("/geofences", status_code=status.HTTP_201_CREATED)
async def create_geofence(
    geofence_data: GeofenceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new geofence"""
    tracking_service = TrackingService(db)
    geofence = await tracking_service.create_geofence(geofence_data.dict())
    return geofence


@router.get("/geofences")
async def get_geofences(
    fence_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all geofences"""
    from ...models.personnel import Geofence

    query = db.query(Geofence)

    if active_only:
        query = query.filter(Geofence.active == True)

    if fence_type:
        query = query.filter(Geofence.fence_type == fence_type)

    geofences = query.all()
    return [g.to_dict() for g in geofences]


# Safe Contacts Endpoints
@router.post("/safe-contacts", status_code=status.HTTP_201_CREATED)
async def create_safe_contact(
    contact_data: SafeContactCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new safe contact"""
    from ...models.personnel import SafeContact

    contact = SafeContact(**contact_data.dict())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact.to_dict()


@router.get("/safe-contacts")
async def get_safe_contacts(
    country: Optional[str] = None,
    contact_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get safe contacts"""
    from ...models.personnel import SafeContact

    query = db.query(SafeContact)

    if active_only:
        query = query.filter(SafeContact.active == True)

    if country:
        query = query.filter(SafeContact.country == country)

    if contact_type:
        query = query.filter(SafeContact.contact_type == contact_type)

    contacts = query.all()
    return [c.to_dict() for c in contacts]


@router.get("/safe-contacts/nearby")
async def get_nearby_safe_contacts(
    latitude: float,
    longitude: float,
    radius_km: float = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get safe contacts near a location"""
    from ...models.personnel import SafeContact
    import math

    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    contacts = db.query(SafeContact).filter(
        SafeContact.active == True,
        SafeContact.latitude.isnot(None),
        SafeContact.longitude.isnot(None)
    ).all()

    nearby_contacts = []
    for contact in contacts:
        distance = calculate_distance(
            latitude, longitude,
            contact.latitude, contact.longitude
        )
        if distance <= radius_km:
            contact_dict = contact.to_dict()
            contact_dict['distance_km'] = round(distance, 2)
            nearby_contacts.append(contact_dict)

    # Sort by distance
    nearby_contacts.sort(key=lambda x: x['distance_km'])

    return nearby_contacts
