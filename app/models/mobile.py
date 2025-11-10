"""Mobile and Offline Sync Models"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class MobileSyncQueue(Base):
    __tablename__ = "mobile_sync_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    device_id = Column(String(255))
    sync_type = Column(String(50))  # full, incremental, push
    data_type = Column(String(100))  # intelligence, incidents, alerts, contacts
    entity_id = Column(Integer)
    action = Column(String(50))  # create, update, delete
    payload = Column(JSONB)
    priority = Column(Integer, default=5)
    status = Column(String(50), default='pending')  # pending, synced, failed
    attempts = Column(Integer, default=0)
    error_message = Column(Text)
    synced_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "sync_type": self.sync_type,
            "data_type": self.data_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "attempts": self.attempts,
            "error_message": self.error_message,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
