"""Mobile Offline Sync API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from ...database import get_db
from ...auth import get_current_active_user
from ...models.mobile import MobileSyncQueue

router = APIRouter()


class SyncRequest(BaseModel):
    device_id: str
    last_sync_timestamp: Optional[str] = None
    data_types: List[str] = ['intelligence', 'alerts', 'incidents', 'contacts']


class SyncData(BaseModel):
    data_type: str
    entity_id: int
    action: str  # create, update, delete
    payload: dict


@router.post("/sync/pull")
async def pull_sync_data(
    sync_request: SyncRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Pull updates from server for offline sync"""

    user_id = current_user.id if hasattr(current_user, 'id') else 0

    # Get pending sync items for this user
    query = db.query(MobileSyncQueue).filter(
        MobileSyncQueue.user_id == user_id,
        MobileSyncQueue.device_id == sync_request.device_id,
        MobileSyncQueue.status == 'pending'
    )

    # Filter by data types
    if sync_request.data_types:
        query = query.filter(MobileSyncQueue.data_type.in_(sync_request.data_types))

    # Filter by timestamp if provided
    if sync_request.last_sync_timestamp:
        last_sync = datetime.fromisoformat(sync_request.last_sync_timestamp)
        query = query.filter(MobileSyncQueue.created_at > last_sync)

    sync_items = query.order_by(MobileSyncQueue.priority.desc()).limit(100).all()

    # Mark as synced
    for item in sync_items:
        item.status = 'synced'
        item.synced_at = datetime.utcnow()

    db.commit()

    return {
        'success': True,
        'items': [item.to_dict() for item in sync_items],
        'total_items': len(sync_items),
        'sync_timestamp': datetime.utcnow().isoformat()
    }


@router.post("/sync/push")
async def push_sync_data(
    sync_data: List[SyncData],
    device_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Push updates from mobile device to server"""

    user_id = current_user.id if hasattr(current_user, 'id') else 0

    # Process each sync item
    processed = []
    errors = []

    for item in sync_data:
        try:
            # Route to appropriate handler based on data_type
            if item.data_type == 'incidents':
                from ...services.incident_service import IncidentService
                service = IncidentService(db)
                if item.action == 'create':
                    await service.create_incident(item.payload)
            # Add handlers for other data types...

            processed.append(item.data_type)

        except Exception as e:
            errors.append({'data_type': item.data_type, 'error': str(e)})

    return {
        'success': len(errors) == 0,
        'processed': len(processed),
        'errors': errors
    }


@router.get("/sync/status")
async def get_sync_status(
    device_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get sync status for device"""

    user_id = current_user.id if hasattr(current_user, 'id') else 0

    pending = db.query(MobileSyncQueue).filter(
        MobileSyncQueue.user_id == user_id,
        MobileSyncQueue.device_id == device_id,
        MobileSyncQueue.status == 'pending'
    ).count()

    return {
        'device_id': device_id,
        'pending_items': pending,
        'server_time': datetime.utcnow().isoformat()
    }
