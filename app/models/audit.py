"""Audit Log Model"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

from ..database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    username = Column(String(255))
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(Integer)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    request_method = Column(String(10))
    request_path = Column(String(500))
    status_code = Column(Integer)
    changes = Column(JSONB)
    metadata = Column(JSONB)
    timestamp = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "request_method": self.request_method,
            "request_path": self.request_path,
            "status_code": self.status_code,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
