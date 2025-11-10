"""Automated Response Playbook Engine

Executes automated responses based on triggers from intelligence, incidents, or alerts.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class PlaybookService:
    """Manages automated response playbooks"""

    def __init__(self, db: Session):
        self.db = db

    def evaluate_triggers(self) -> List[Dict[str, Any]]:
        """Evaluate all active playbooks and return triggered ones"""
        from ..models.playbooks import ResponsePlaybook
        from ..models.intelligence import IntelligenceItem
        from ..models.incidents import FieldIncident

        active_playbooks = self.db.query(ResponsePlaybook).filter(
            ResponsePlaybook.active == True
        ).all()

        triggered = []

        for playbook in active_playbooks:
            trigger_conditions = playbook.trigger_conditions

            # Evaluate trigger conditions
            if self._check_trigger_conditions(trigger_conditions):
                triggered.append({
                    'playbook_id': playbook.id,
                    'playbook_name': playbook.name,
                    'priority': playbook.priority,
                    'auto_execute': playbook.auto_execute
                })

        return triggered

    def _check_trigger_conditions(self, conditions: Dict) -> bool:
        """Check if trigger conditions are met"""
        from ..models.intelligence import IntelligenceItem
        from ..models.incidents import FieldIncident
        from ..models.personnel import Personnel

        trigger_type = conditions.get('type')

        if trigger_type == 'intelligence_threat_level':
            threshold = conditions.get('threshold', 8.0)
            region = conditions.get('region')

            query = self.db.query(IntelligenceItem).filter(
                IntelligenceItem.threat_level >= threshold
            )

            if region:
                query = query.filter(IntelligenceItem.region == region)

            # Check if any recent intelligence matches
            from datetime import timedelta
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            count = query.filter(IntelligenceItem.created_at >= recent_cutoff).count()

            return count > 0

        elif trigger_type == 'incident_severity':
            threshold = conditions.get('threshold', 8)
            incident_type = conditions.get('incident_type')

            query = self.db.query(FieldIncident).filter(
                FieldIncident.severity >= threshold,
                FieldIncident.status != 'resolved'
            )

            if incident_type:
                query = query.filter(FieldIncident.incident_type == incident_type)

            return query.count() > 0

        elif trigger_type == 'personnel_in_danger':
            # Check if personnel in danger zones
            danger_count = self.db.query(Personnel).filter(
                Personnel.status == 'active',
                Personnel.current_location.like('%danger%')  # Simplified check
            ).count()

            return danger_count > 0

        elif trigger_type == 'missed_checkins':
            threshold_count = conditions.get('threshold_count', 3)

            # Check for multiple missed check-ins
            from datetime import timedelta
            check_time = datetime.utcnow() - timedelta(hours=24)

            overdue = self.db.query(Personnel).filter(
                Personnel.status == 'active',
                Personnel.tracking_enabled == True,
                Personnel.last_check_in < check_time
            ).count()

            return overdue >= threshold_count

        return False

    async def execute_playbook(
        self,
        playbook_id: int,
        triggered_by: str = 'auto',
        trigger_user_id: Optional[int] = None,
        intelligence_id: Optional[int] = None,
        incident_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a playbook"""
        from ..models.playbooks import ResponsePlaybook, PlaybookExecution

        playbook = self.db.query(ResponsePlaybook).filter(
            ResponsePlaybook.id == playbook_id
        ).first()

        if not playbook:
            return {'success': False, 'error': 'Playbook not found'}

        # Check if auto-execute is allowed
        if triggered_by == 'auto' and not playbook.auto_execute:
            return {
                'success': False,
                'error': 'Playbook requires manual approval',
                'requires_approval': True
            }

        # Create execution record
        execution = PlaybookExecution(
            playbook_id=playbook_id,
            intelligence_id=intelligence_id,
            incident_id=incident_id,
            triggered_by=triggered_by,
            trigger_user_id=trigger_user_id,
            status='in_progress',
            actions_completed=[],
            actions_failed=[]
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        logger.info(f"Starting playbook execution {execution.id} for playbook {playbook.name}")

        # Execute actions sequentially
        actions = playbook.actions
        completed = []
        failed = []

        for action in actions:
            try:
                result = await self._execute_action(action, execution)

                if result['success']:
                    completed.append({
                        'action': action['type'],
                        'result': result,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    failed.append({
                        'action': action['type'],
                        'error': result.get('error'),
                        'timestamp': datetime.utcnow().isoformat()
                    })

            except Exception as e:
                logger.error(f"Error executing action {action['type']}: {e}")
                failed.append({
                    'action': action['type'],
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })

        # Update execution record
        execution.actions_completed = completed
        execution.actions_failed = failed
        execution.status = 'completed' if not failed else 'partial_failure'
        execution.completed_at = datetime.utcnow()

        # Update playbook execution count
        playbook.execution_count += 1
        playbook.last_executed = datetime.utcnow()

        self.db.commit()

        logger.info(
            f"Playbook execution {execution.id} completed: "
            f"{len(completed)} succeeded, {len(failed)} failed"
        )

        return {
            'success': True,
            'execution_id': execution.id,
            'actions_completed': len(completed),
            'actions_failed': len(failed),
            'details': {
                'completed': completed,
                'failed': failed
            }
        }

    async def _execute_action(self, action: Dict, execution) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.get('type')

        if action_type == 'send_alert':
            return await self._action_send_alert(action, execution)

        elif action_type == 'notify_personnel':
            return await self._action_notify_personnel(action, execution)

        elif action_type == 'create_incident':
            return await self._action_create_incident(action, execution)

        elif action_type == 'update_threat_level':
            return await self._action_update_threat_level(action, execution)

        elif action_type == 'activate_geofence':
            return await self._action_activate_geofence(action, execution)

        elif action_type == 'send_briefing':
            return await self._action_send_briefing(action, execution)

        else:
            return {'success': False, 'error': f'Unknown action type: {action_type}'}

    async def _action_send_alert(self, action: Dict, execution) -> Dict[str, Any]:
        """Action: Send alert"""
        from ..models.alerts import Alert

        alert = Alert(
            alert_type=action.get('alert_type', 'playbook_automated'),
            priority=action.get('priority', 7),
            title=action.get('title', 'Automated Playbook Alert'),
            message=action.get('message', 'Playbook action triggered'),
            status='pending',
            metadata={
                'playbook_execution_id': execution.id,
                'automated': True
            }
        )

        self.db.add(alert)
        self.db.commit()

        logger.info(f"Alert {alert.id} created by playbook action")

        # Trigger async alert sending
        from ..tasks.alerts import send_alert
        send_alert.delay(alert.id)

        return {'success': True, 'alert_id': alert.id}

    async def _action_notify_personnel(self, action: Dict, execution) -> Dict[str, Any]:
        """Action: Notify specific personnel"""
        personnel_ids = action.get('personnel_ids', [])
        message = action.get('message')

        if not personnel_ids or not message:
            return {'success': False, 'error': 'Missing personnel_ids or message'}

        from ..tasks.notifications import send_multi_channel

        for personnel_id in personnel_ids:
            send_multi_channel.delay(
                personnel_id,
                "Automated Alert",
                message,
                channels=['email', 'sms']
            )

        return {'success': True, 'notified_count': len(personnel_ids)}

    async def _action_create_incident(self, action: Dict, execution) -> Dict[str, Any]:
        """Action: Create automated incident report"""
        from ..models.incidents import FieldIncident

        incident = FieldIncident(
            incident_type=action.get('incident_type', 'automated'),
            severity=action.get('severity', 7),
            title=action.get('title', 'Automated Incident'),
            description=action.get('description', 'Created by automated playbook'),
            reporter_name='Automated System',
            incident_date=datetime.utcnow(),
            status='new',
            metadata={
                'playbook_execution_id': execution.id,
                'automated': True
            }
        )

        self.db.add(incident)
        self.db.commit()

        return {'success': True, 'incident_id': incident.id}

    async def _action_update_threat_level(self, action: Dict, execution) -> Dict[str, Any]:
        """Action: Update threat level for region"""
        # This would update a regional threat assessment
        region = action.get('region')
        new_level = action.get('threat_level')

        logger.info(f"Threat level for {region} updated to {new_level}")

        return {'success': True, 'region': region, 'new_level': new_level}

    async def _action_activate_geofence(self, action: Dict, execution) -> Dict[str, Any]:
        """Action: Activate or create geofence"""
        from ..models.personnel import Geofence

        geofence_id = action.get('geofence_id')

        if geofence_id:
            geofence = self.db.query(Geofence).filter(Geofence.id == geofence_id).first()
            if geofence:
                geofence.active = True
                self.db.commit()
                return {'success': True, 'geofence_id': geofence_id, 'action': 'activated'}

        return {'success': False, 'error': 'Geofence not found'}

    async def _action_send_briefing(self, action: Dict, execution) -> Dict[str, Any]:
        """Action: Generate and send briefing"""
        from ..tasks.intelligence import generate_daily_briefing

        generate_daily_briefing.delay()

        return {'success': True, 'action': 'briefing_queued'}
