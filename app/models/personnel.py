"""Personnel and Tracking Models"""

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, func, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class Personnel(Base):
    __tablename__ = "personnel"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    role = Column(String(100))  # missionary, staff, volunteer
    organization = Column(String(255))
    current_location = Column(String(500))
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    current_country = Column(String(100))
    home_base = Column(String(255))
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(50))
    medical_info = Column(JSONB)
    status = Column(String(50), default='active')  # active, on_leave, inactive
    tracking_enabled = Column(Boolean, default=False)
    last_check_in = Column(DateTime)
    check_in_frequency_hours = Column(Integer, default=24)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    location_history = relationship("LocationHistory", back_populates="personnel")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "organization": self.organization,
            "current_location": self.current_location,
            "current_latitude": self.current_latitude,
            "current_longitude": self.current_longitude,
            "current_country": self.current_country,
            "home_base": self.home_base,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "status": self.status,
            "tracking_enabled": self.tracking_enabled,
            "last_check_in": self.last_check_in.isoformat() if self.last_check_in else None,
            "check_in_frequency_hours": self.check_in_frequency_hours
        }


class LocationHistory(Base):
    __tablename__ = "location_history"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey('personnel.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float)  # GPS accuracy in meters
    location_name = Column(String(500))
    country = Column(String(100))
    activity_type = Column(String(50))  # check_in, auto_update, manual
    notes = Column(Text)
    timestamp = Column(DateTime, default=func.now())

    # Relationships
    personnel = relationship("Personnel", back_populates="location_history")

    def to_dict(self):
        return {
            "id": self.id,
            "personnel_id": self.personnel_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "location_name": self.location_name,
            "country": self.country,
            "activity_type": self.activity_type,
            "notes": self.notes,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class Geofence(Base):
    __tablename__ = "geofences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    fence_type = Column(String(50))  # safe_zone, danger_zone, restricted
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=False)
    polygon = Column(JSONB)  # GeoJSON for complex shapes
    threat_level = Column(Float)
    alert_on_enter = Column(Boolean, default=True)
    alert_on_exit = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "fence_type": self.fence_type,
            "center_latitude": self.center_latitude,
            "center_longitude": self.center_longitude,
            "radius_meters": self.radius_meters,
            "polygon": self.polygon,
            "threat_level": self.threat_level,
            "alert_on_enter": self.alert_on_enter,
            "alert_on_exit": self.alert_on_exit,
            "active": self.active,
            "metadata": self.metadata
        }


class GeofenceEvent(Base):
    __tablename__ = "geofence_events"

    id = Column(Integer, primary_key=True, index=True)
    geofence_id = Column(Integer, ForeignKey('geofences.id'))
    personnel_id = Column(Integer, ForeignKey('personnel.id'))
    event_type = Column(String(50))  # entered, exited
    location_history_id = Column(Integer, ForeignKey('location_history.id'))
    alert_triggered = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "geofence_id": self.geofence_id,
            "personnel_id": self.personnel_id,
            "event_type": self.event_type,
            "location_history_id": self.location_history_id,
            "alert_triggered": self.alert_triggered,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class SafeContact(Base):
    __tablename__ = "safe_contacts"

    id = Column(Integer, primary_key=True, index=True)
    contact_type = Column(String(100))  # safe_house, legal_aid, medical, transportation, embassy
    name = Column(String(255), nullable=False)
    organization = Column(String(255))
    phone = Column(String(50))
    alternate_phone = Column(String(50))
    email = Column(String(255))
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    country = Column(String(100))
    city = Column(String(100))
    region = Column(String(100))
    services_offered = Column(ARRAY(String))
    availability_24_7 = Column(Boolean, default=False)
    requires_appointment = Column(Boolean, default=False)
    trust_level = Column(Integer, default=5)  # 1-10
    last_verified = Column(DateTime)
    verified_by = Column(Integer)
    notes = Column(Text)
    encrypted_details = Column(Text)  # for sensitive contact info
    access_code = Column(String(100))
    active = Column(Boolean, default=True)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "contact_type": self.contact_type,
            "name": self.name,
            "organization": self.organization,
            "phone": self.phone,
            "alternate_phone": self.alternate_phone,
            "email": self.email,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country": self.country,
            "city": self.city,
            "region": self.region,
            "services_offered": self.services_offered,
            "availability_24_7": self.availability_24_7,
            "requires_appointment": self.requires_appointment,
            "trust_level": self.trust_level,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "notes": self.notes,
            "access_code": self.access_code,
            "active": self.active
        }
