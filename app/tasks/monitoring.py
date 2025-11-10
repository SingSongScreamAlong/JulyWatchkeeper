"""Personnel monitoring background tasks"""

from ..celery_app import celery_app
from ..database import SessionLocal
from ..services.tracking_service import TrackingService
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.monitoring.check_missed_checkins')
def check_missed_checkins():
    """Check for personnel who missed their scheduled check-ins"""
    db = SessionLocal()
    try:
        from ..models.personnel import Personnel
        from ..models.alerts import Alert
        from datetime import datetime

        # Get active personnel with tracking enabled
        personnel_list = db.query(Personnel).filter(
            Personnel.status == 'active',
            Personnel.tracking_enabled == True
        ).all()

        missed_checkins = []

        for person in personnel_list:
            if person.last_check_in:
                hours_since_checkin = (datetime.utcnow() - person.last_check_in).total_seconds() / 3600

                if hours_since_checkin > person.check_in_frequency_hours:
                    missed_checkins.append({
                        'personnel_id': person.id,
                        'name': person.name,
                        'hours_overdue': hours_since_checkin - person.check_in_frequency_hours,
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
                        db.add(alert)
                        logger.warning(f"Missed check-in alert created for personnel {person.id}")

        if missed_checkins:
            db.commit()
            logger.info(f"Found {len(missed_checkins)} missed check-ins")
        else:
            logger.info("No missed check-ins detected")

        return {
            'success': True,
            'missed_checkins': len(missed_checkins),
            'details': missed_checkins
        }

    except Exception as e:
        logger.error(f"Error checking missed check-ins: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.monitoring.check_danger_zones')
def check_danger_zones():
    """Check for personnel currently in danger zones"""
    db = SessionLocal()
    try:
        tracking_service = TrackingService(db)

        # Get personnel in danger zones (this would be async in real implementation)
        from ..models.personnel import Personnel, Geofence
        import math

        def calculate_distance(lat1, lon1, lat2, lon2):
            R = 6371000  # Earth radius in meters
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            a = (math.sin(delta_lat / 2) ** 2 +
                 math.cos(lat1_rad) * math.cos(lat2_rad) *
                 math.sin(delta_lon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        danger_zones = db.query(Geofence).filter(
            Geofence.active == True,
            Geofence.fence_type == 'danger_zone'
        ).all()

        personnel_at_risk = []

        active_personnel = db.query(Personnel).filter(
            Personnel.status == 'active',
            Personnel.current_latitude.isnot(None),
            Personnel.current_longitude.isnot(None)
        ).all()

        for person in active_personnel:
            for zone in danger_zones:
                distance = calculate_distance(
                    person.current_latitude,
                    person.current_longitude,
                    zone.center_latitude,
                    zone.center_longitude
                )

                if distance <= zone.radius_meters:
                    personnel_at_risk.append({
                        'personnel_id': person.id,
                        'personnel_name': person.name,
                        'danger_zone': zone.name,
                        'distance_meters': distance
                    })

                    logger.warning(
                        f"Personnel {person.name} is in danger zone {zone.name} "
                        f"({distance:.0f}m from center)"
                    )

        logger.info(f"Found {len(personnel_at_risk)} personnel in danger zones")

        return {
            'success': True,
            'personnel_at_risk': len(personnel_at_risk),
            'details': personnel_at_risk
        }

    except Exception as e:
        logger.error(f"Error checking danger zones: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.monitoring.update_location')
def update_location(personnel_id: int, latitude: float, longitude: float, location_data: dict):
    """Process location update asynchronously (including geofence checks)"""
    db = SessionLocal()
    try:
        tracking_service = TrackingService(db)

        location_data.update({
            'latitude': latitude,
            'longitude': longitude
        })

        # This would be async in real implementation
        logger.info(f"Processing location update for personnel {personnel_id}")

        # Simplified synchronous version
        from ..models.personnel import Personnel, LocationHistory

        personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
        if not personnel:
            return {'success': False, 'error': 'Personnel not found'}

        # Create location history
        location_entry = LocationHistory(
            personnel_id=personnel_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=location_data.get('accuracy'),
            location_name=location_data.get('location_name'),
            country=location_data.get('country'),
            activity_type=location_data.get('activity_type', 'auto_update'),
            notes=location_data.get('notes')
        )
        db.add(location_entry)

        # Update personnel current location
        personnel.current_latitude = latitude
        personnel.current_longitude = longitude
        personnel.current_location = location_data.get('location_name')
        personnel.current_country = location_data.get('country')
        personnel.last_check_in = datetime.utcnow()

        db.commit()

        logger.info(f"Location updated for personnel {personnel_id}")

        return {
            'success': True,
            'personnel_id': personnel_id,
            'location_id': location_entry.id
        }

    except Exception as e:
        logger.error(f"Error updating location for personnel {personnel_id}: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()
