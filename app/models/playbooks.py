"""Response Playbook Models"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class ResponsePlaybook(Base):
    __tablename__ = "response_playbooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_conditions = Column(JSONB, nullable=False)
    priority = Column(Integer, default=5)
    actions = Column(JSONB, nullable=False)
    notification_template = Column(JSONB)
    escalation_chain = Column(JSONB)
    required_approvals = Column(ARRAY(String))
    auto_execute = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    execution_count = Column(Integer, default=0)
    last_executed = Column(DateTime)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    executions = relationship("PlaybookExecution", back_populates="playbook")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "trigger_conditions": self.trigger_conditions,
            "priority": self.priority,
            "actions": self.actions,
            "auto_execute": self.auto_execute,
            "active": self.active,
            "execution_count": self.execution_count,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PlaybookExecution(Base):
    __tablename__ = "playbook_executions"

    id = Column(Integer, primary_key=True, index=True)
    playbook_id = Column(Integer, ForeignKey('response_playbooks.id'))
    intelligence_id = Column(Integer, ForeignKey('intelligence_items.id'))
    incident_id = Column(Integer, ForeignKey('field_incidents.id'))
    triggered_by = Column(String(100))  # auto, manual, alert_rule
    trigger_user_id = Column(Integer)
    status = Column(String(50), default='pending')
    actions_completed = Column(JSONB)
    actions_failed = Column(JSONB)
    error_log = Column(Text)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    metadata = Column(JSONB)

    # Relationships
    playbook = relationship("ResponsePlaybook", back_populates="executions")

    def to_dict(self):
        return {
            "id": self.id,
            "playbook_id": self.playbook_id,
            "status": self.status,
            "triggered_by": self.triggered_by,
            "actions_completed": self.actions_completed,
            "actions_failed": self.actions_failed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
