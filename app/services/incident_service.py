"""Incident Reporting Service

Handles field incident reports from missionaries and staff.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)


class IncidentService:
    """Manages field incident reports"""

    def __init__(self, db: Session):
        self.db = db

    async def create_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new field incident report"""
        from ..models.incidents import FieldIncident

        incident = FieldIncident(
            incident_type=incident_data['incident_type'],
            severity=incident_data['severity'],
            title=incident_data['title'],
            description=incident_data['description'],
            location=incident_data.get('location'),
            latitude=incident_data.get('latitude'),
            longitude=incident_data.get('longitude'),
            country=incident_data.get('country'),
            region=incident_data.get('region'),
            reported_by=incident_data.get('reported_by'),
            reporter_name=incident_data.get('reporter_name'),
            reporter_contact=incident_data.get('reporter_contact'),
            incident_date=incident_data['incident_date'],
            attachments=incident_data.get('attachments', {}),
            witnesses=incident_data.get('witnesses', {}),
            metadata=incident_data.get('metadata', {})
        )

        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        # Check if incident triggers alerts
        if incident.severity >= 8:
            await self._trigger_incident_alert(incident)

        # Check for related intelligence
        await self._correlate_with_intelligence(incident)

        logger.info(f"Created incident {incident.id}: {incident.title}")

        return incident.to_dict()

    async def update_incident(self, incident_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing incident"""
        from ..models.incidents import FieldIncident

        incident = self.db.query(FieldIncident).filter(
            FieldIncident.id == incident_id
        ).first()

        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # Update fields
        for key, value in updates.items():
            if hasattr(incident, key):
                setattr(incident, key, value)

        incident.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(incident)

        return incident.to_dict()

    async def verify_incident(self, incident_id: int, verifier_id: int, notes: str) -> Dict[str, Any]:
        """Mark an incident as verified"""
        from ..models.incidents import FieldIncident

        incident = self.db.query(FieldIncident).filter(
            FieldIncident.id == incident_id
        ).first()

        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        incident.verified = True
        incident.verified_by = verifier_id
        incident.verification_notes = notes
        incident.status = 'verified'

        self.db.commit()
        self.db.refresh(incident)

        logger.info(f"Incident {incident_id} verified by user {verifier_id}")

        return incident.to_dict()

    async def get_incidents_by_region(self, region: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get incidents for a specific region"""
        from ..models.incidents import FieldIncident

        query = self.db.query(FieldIncident).filter(FieldIncident.region == region)

        if status:
            query = query.filter(FieldIncident.status == status)

        incidents = query.order_by(FieldIncident.incident_date.desc()).all()

        return [incident.to_dict() for incident in incidents]

    async def get_high_severity_incidents(self, min_severity: int = 7) -> List[Dict[str, Any]]:
        """Get high severity unresolved incidents"""
        from ..models.incidents import FieldIncident

        incidents = self.db.query(FieldIncident).filter(
            and_(
                FieldIncident.severity >= min_severity,
                FieldIncident.status.in_(['new', 'investigating'])
            )
        ).order_by(FieldIncident.severity.desc()).all()

        return [incident.to_dict() for incident in incidents]

    async def _trigger_incident_alert(self, incident):
        """Trigger alert for high-severity incident"""
        from .alert_service import AlertService
        from ..models.alerts import Alert

        # Create immediate alert for high-severity incident
        alert = Alert(
            intelligence_id=incident.related_intelligence_id,
            alert_type='field_incident',
            priority=incident.severity,
            title=f"FIELD INCIDENT: {incident.title}",
            message=f"""
HIGH-SEVERITY FIELD INCIDENT REPORT

Incident Type: {incident.incident_type}
Severity: {incident.severity}/10
Location: {incident.location or 'Unknown'}
Country: {incident.country or 'Unknown'}
Reported By: {incident.reporter_name or 'Anonymous'}
Incident Time: {incident.incident_date.strftime('%Y-%m-%d %H:%M:%S')}

DESCRIPTION:
{incident.description}

This incident requires immediate attention.
""",
            status='pending',
            metadata={
                'incident_id': incident.id,
                'incident_type': incident.incident_type,
                'severity': incident.severity
            }
        )

        self.db.add(alert)
        self.db.commit()

        logger.warning(f"High-severity incident alert created for incident {incident.id}")

    async def _correlate_with_intelligence(self, incident):
        """Try to correlate incident with existing intelligence"""
        from ..models.intelligence import IntelligenceItem

        # Search for intelligence items in the same region/country
        intelligence_items = self.db.query(IntelligenceItem).filter(
            or_(
                IntelligenceItem.country == incident.country,
                IntelligenceItem.region == incident.region
            )
        ).order_by(IntelligenceItem.collection_date.desc()).limit(10).all()

        # Simple correlation based on date proximity and keywords
        for intel in intelligence_items:
            # Check if dates are within 7 days
            if intel.collection_date:
                date_diff = abs((incident.incident_date - intel.collection_date).days)
                if date_diff <= 7:
                    # Check for keyword matches
                    incident_text = f"{incident.title} {incident.description}".lower()
                    intel_text = f"{intel.title} {intel.content}".lower()

                    common_words = set(incident_text.split()) & set(intel_text.split())
                    if len(common_words) > 5:
                        incident.related_intelligence_id = intel.id
                        self.db.commit()
                        logger.info(f"Correlated incident {incident.id} with intelligence {intel.id}")
                        break
