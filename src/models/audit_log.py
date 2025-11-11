"""
Audit Log Model for WATCHKEEPER

This module defines the AuditLog model for tracking all system actions.
"""

from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.orm import relationship

from src.core.database import Base


class AuditAction(str, enum.Enum):
    """Enumeration of audit actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    PROCESS = "process"
    ALERT = "alert"


class AuditLog(Base):
    """
    Audit log model for tracking all system actions.

    Attributes:
        id: Unique identifier for the audit log entry
        user_id: ID of the user who performed the action
        action: Type of action performed
        resource_type: Type of resource affected (e.g., 'intelligence', 'threat', 'user')
        resource_id: ID of the affected resource
        changes: JSON object with before/after values for updates
        ip_address: IP address from which the action was performed
        user_agent: User agent string
        status: Status of the action (success/failure)
        error_message: Error message if action failed
        created_at: When the action was performed
        user: User who performed the action
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='SET NULL'), nullable=True, index=True)

    # Action details
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True, index=True)

    # Change tracking
    changes = Column(JSONB, nullable=True)  # For UPDATE actions: {"field": {"old": "value", "new": "value"}}

    # Request metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="success")  # success, failure
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        """String representation of the audit log entry."""
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action}, resource={self.resource_type})>"
