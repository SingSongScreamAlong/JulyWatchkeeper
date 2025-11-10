"""Collaboration and Intelligence Sharing Models"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    organization_type = Column(String(100))  # missionary, ngo, government
    trust_level = Column(Integer, default=5)  # 1-10
    api_key = Column(String(255), unique=True)
    can_receive_intel = Column(Boolean, default=False)
    can_submit_intel = Column(Boolean, default=False)
    regions_of_interest = Column(ARRAY(String))
    contact_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    active = Column(Boolean, default=True)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    shared_intelligence = relationship("SharedIntelligence", back_populates="organization")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "organization_type": self.organization_type,
            "trust_level": self.trust_level,
            "can_receive_intel": self.can_receive_intel,
            "can_submit_intel": self.can_submit_intel,
            "regions_of_interest": self.regions_of_interest,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SharedIntelligence(Base):
    __tablename__ = "shared_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    intelligence_id = Column(Integer, ForeignKey('intelligence_items.id'))
    shared_with_org_id = Column(Integer, ForeignKey('organizations.id'))
    shared_by_user_id = Column(Integer)
    share_level = Column(String(50))  # summary_only, full, classified
    expiry_date = Column(DateTime)
    accessed = Column(Boolean, default=False)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="shared_intelligence")

    def to_dict(self):
        return {
            "id": self.id,
            "intelligence_id": self.intelligence_id,
            "shared_with_org_id": self.shared_with_org_id,
            "share_level": self.share_level,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "accessed": self.accessed,
            "access_count": self.access_count,
            "revoked": self.revoked,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
