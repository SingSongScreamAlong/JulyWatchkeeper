from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base
from .intelligence import intelligence_tags

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    
    # Relationships
    intelligence_items = relationship("IntelligenceItem", secondary=intelligence_tags, back_populates="tags")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "intelligence_count": len(self.intelligence_items) if self.intelligence_items else 0
        }
