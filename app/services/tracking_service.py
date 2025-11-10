"""Personnel Tracking and Geofencing Service

Handles real-time location tracking, geofencing, and check-in management.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import math

logger = logging.getLogger(__name__)


class TrackingService:
    """Manages personnel location tracking and geofencing"""

    def __init__(self, db: Session):
        self.db = db

    async def update_location(self, personnel_id: int, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update personnel location and check geofences"""
        from ..models.personnel import Personnel, LocationHistory, GeofenceEvent

        # Get personnel record
        personnel = self.db.query(Personnel).filter(Personnel.id == personnel_id).first()

        if not personnel:
            raise ValueError(f"Personnel {personnel_id} not found")

        if not personnel.tracking_enabled:
            raise ValueError(f"Tracking not enabled for personnel {personnel_id}")

        # Create location history entry
        location_entry = LocationHistory(
            personnel_id=personnel_id,
            latitude=location_data['latitude'],
            longitude=location_data['longitude'],
            accuracy=location_data.get('accuracy'),
            location_name=location_data.get('location_name'),
            country=location_data.get('country'),
            activity_type=location_data.get('activity_type', 'auto_update'),
            notes=location_data.get('notes')
        )

        self.db.add(location_entry)

        # Update personnel current location
        personnel.current_latitude = location_data['latitude']
        personnel.current_longitude = location_data['longitude']
        personnel.current_location = location_data.get('location_name')
        personnel.current_country = location_data.get('country')
        personnel.last_check_in = datetime.utcnow()

        self.db.commit()
        self.db.refresh(location_entry)

        # Check geofences
        geofence_events = await self._check_geofences(personnel, location_entry)

        logger.info(f"Updated location for personnel {personnel_id}")

        return {
            "location_id": location_entry.id,
            "personnel_id": personnel_id,
            "latitude": location_entry.latitude,
            "longitude": location_entry.longitude,
            "geofence_events": geofence_events
        }

    async def _check_geofences(self, personnel, location_entry) -> List[Dict[str, Any]]:
        """Check if location entry crosses any geofences"""
        from ..models.personnel import Geofence, GeofenceEvent

        # Get active geofences
        geofences = self.db.query(Geofence).filter(Geofence.active == True).all()

        events = []

        for geofence in geofences:
            # Calculate distance from geofence center
            distance = self._calculate_distance(
                location_entry.latitude,
                location_entry.longitude,
                geofence.center_latitude,
                geofence.center_longitude
            )

            # Check if within geofence radius
            within_fence = distance <= geofence.radius_meters

            # Get previous location
            prev_location = self.db.query(LocationHistory).filter(
                and_(
                    LocationHistory.personnel_id == personnel.id,
                    LocationHistory.id < location_entry.id
                )
            ).order_by(LocationHistory.id.desc()).first()

            if prev_location:
                prev_distance = self._calculate_distance(
                    prev_location.latitude,
                    prev_location.longitude,
                    geofence.center_latitude,
                    geofence.center_longitude
                )
                was_within_fence = prev_distance <= geofence.radius_meters

                # Detect entry/exit
                if within_fence and not was_within_fence:
                    # Entered geofence
                    event = await self._create_geofence_event(
                        geofence, personnel, location_entry, 'entered'
                    )
                    events.append(event)

                elif not within_fence and was_within_fence:
                    # Exited geofence
                    event = await self._create_geofence_event(
                        geofence, personnel, location_entry, 'exited'
                    )
                    events.append(event)

        return events

    async def _create_geofence_event(self, geofence, personnel, location_entry, event_type: str) -> Dict[str, Any]:
        """Create a geofence event and trigger alerts if needed"""
        from ..models.personnel import GeofenceEvent
        from ..models.alerts import Alert

        event = GeofenceEvent(
            geofence_id=geofence.id,
            personnel_id=personnel.id,
            location_history_id=location_entry.id,
            event_type=event_type
        )

        # Check if alert should be triggered
        should_alert = (
            (event_type == 'entered' and geofence.alert_on_enter) or
            (event_type == 'exited' and geofence.alert_on_exit)
        )

        if should_alert:
            event.alert_triggered = True

            # Create alert
            alert = Alert(
                alert_type='geofence',
                priority=int(geofence.threat_level) if geofence.threat_level else 5,
                title=f"Geofence {event_type.upper()}: {personnel.name}",
                message=f"""
Personnel has {event_type} geofence: {geofence.name}

Personnel: {personnel.name}
Organization: {personnel.organization}
Geofence: {geofence.name} ({geofence.fence_type})
Threat Level: {geofence.threat_level}/10
Location: {location_entry.location_name or 'Unknown'}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

{geofence.description or ''}

Emergency Contact: {personnel.emergency_contact_name} - {personnel.emergency_contact_phone}
""",
                status='pending',
                metadata={
                    'personnel_id': personnel.id,
                    'geofence_id': geofence.id,
                    'event_type': event_type,
                    'location': {
                        'latitude': location_entry.latitude,
                        'longitude': location_entry.longitude
                    }
                }
            )

            self.db.add(alert)

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        logger.info(f"Geofence event: Personnel {personnel.id} {event_type} {geofence.name}")

        return event.to_dict()

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters (Haversine formula)"""
        R = 6371000  # Earth radius in meters

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c

        return distance

    async def create_geofence(self, geofence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new geofence"""
        from ..models.personnel import Geofence

        geofence = Geofence(
            name=geofence_data['name'],
            description=geofence_data.get('description'),
            fence_type=geofence_data['fence_type'],
            center_latitude=geofence_data['center_latitude'],
            center_longitude=geofence_data['center_longitude'],
            radius_meters=geofence_data['radius_meters'],
            polygon=geofence_data.get('polygon'),
            threat_level=geofence_data.get('threat_level'),
            alert_on_enter=geofence_data.get('alert_on_enter', True),
            alert_on_exit=geofence_data.get('alert_on_exit', False),
            metadata=geofence_data.get('metadata', {})
        )

        self.db.add(geofence)
        self.db.commit()
        self.db.refresh(geofence)

        logger.info(f"Created geofence {geofence.id}: {geofence.name}")

        return geofence.to_dict()

    async def check_missed_checkins(self) -> List[Dict[str, Any]]:
        """Check for personnel who missed check-ins"""
        from ..models.personnel import Personnel
        from ..models.alerts import Alert

        # Get active personnel with tracking enabled
        personnel_list = self.db.query(Personnel).filter(
            and_(
                Personnel.status == 'active',
                Personnel.tracking_enabled == True
            )
        ).all()

        missed_checkins = []

        for person in personnel_list:
            if person.last_check_in:
                hours_since_checkin = (datetime.utcnow() - person.last_check_in).total_seconds() / 3600

                if hours_since_checkin > person.check_in_frequency_hours:
                    # Missed check-in
                    missed_checkins.append({
                        'personnel_id': person.id,
                        'name': person.name,
                        'hours_overdue': hours_since_checkin - person.check_in_frequency_hours,
                        'last_check_in': person.last_check_in.isoformat()
                    })

                    # Create alert for significantly overdue check-ins
                    if hours_since_checkin > person.check_in_frequency_hours * 2:
                        alert = Alert(
                            alert_type='missed_checkin',
                            priority=8,
                            title=f"MISSED CHECK-IN: {person.name}",
                            message=f"""
Personnel has missed scheduled check-in.

Personnel: {person.name}
Organization: {person.organization}
Last Check-In: {person.last_check_in.strftime('%Y-%m-%d %H:%M:%S')} UTC
Hours Overdue: {hours_since_checkin - person.check_in_frequency_hours:.1f}

Last Known Location: {person.current_location or 'Unknown'}
Country: {person.current_country or 'Unknown'}

Emergency Contact: {person.emergency_contact_name} - {person.emergency_contact_phone}

IMMEDIATE ACTION REQUIRED
""",
                            status='pending',
                            metadata={
                                'personnel_id': person.id,
                                'hours_overdue': hours_since_checkin - person.check_in_frequency_hours
                            }
                        )

                        self.db.add(alert)
                        logger.warning(f"Missed check-in alert for personnel {person.id}")

        if missed_checkins:
            self.db.commit()

        return missed_checkins

    async def get_personnel_in_danger_zones(self) -> List[Dict[str, Any]]:
        """Get all personnel currently in danger zones"""
        from ..models.personnel import Personnel, Geofence

        danger_zones = self.db.query(Geofence).filter(
            and_(
                Geofence.active == True,
                Geofence.fence_type == 'danger_zone'
            )
        ).all()

        personnel_at_risk = []

        active_personnel = self.db.query(Personnel).filter(
            and_(
                Personnel.status == 'active',
                Personnel.current_latitude.isnot(None),
                Personnel.current_longitude.isnot(None)
            )
        ).all()

        for person in active_personnel:
            for zone in danger_zones:
                distance = self._calculate_distance(
                    person.current_latitude,
                    person.current_longitude,
                    zone.center_latitude,
                    zone.center_longitude
                )

                if distance <= zone.radius_meters:
                    personnel_at_risk.append({
                        'personnel': person.to_dict(),
                        'danger_zone': zone.to_dict(),
                        'distance_meters': distance
                    })

        return personnel_at_risk
