from sqlalchemy import Column, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base

class VerificationInfo(Base):
    __tablename__ = "verification_info"

    intelligence_id = Column(Integer, ForeignKey("intelligence_items.id"), primary_key=True)
    source_verified = Column(Boolean, default=True)
    url_verified = Column(Boolean, default=True)
    timestamp = Column(Text, nullable=False)
    verification_method = Column(Text, nullable=False)
    verification_agent = Column(Text, nullable=False)
    
    # Relationships
    intelligence_item = relationship("IntelligenceItem", back_populates="verification_info")
    
    def to_dict(self):
        return {
            "intelligence_id": self.intelligence_id,
            "source_verified": self.source_verified,
            "url_verified": self.url_verified,
            "timestamp": self.timestamp,
            "verification_method": self.verification_method,
            "verification_agent": self.verification_agent
        }
