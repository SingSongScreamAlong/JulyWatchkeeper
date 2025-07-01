from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Table, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base

# Junction table for intelligence items and tags
intelligence_tags = Table(
    'intelligence_tags',
    Base.metadata,
    Column('intelligence_id', Integer, ForeignKey('intelligence_items.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class IntelligenceItem(Base):
    __tablename__ = "intelligence_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    source = Column(Text, nullable=False)
    source_id = Column(Integer, nullable=False)
    raw_content = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    collection_date = Column(Text, nullable=False)
    publication_date = Column(Text)
    threat_level = Column(Float, nullable=False)
    missionary_relevance = Column(Float, nullable=False)
    region = Column(Text)
    country = Column(Text)
    location = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    keywords = Column(Text)
    sentiment = Column(Float)
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    tags = relationship("Tag", secondary=intelligence_tags, back_populates="intelligence_items")
    verification_info = relationship("VerificationInfo", back_populates="intelligence_item", uselist=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "source": self.source,
            "source_id": self.source_id,
            "url": self.url,
            "collection_date": self.collection_date,
            "publication_date": self.publication_date,
            "threat_level": self.threat_level,
            "missionary_relevance": self.missionary_relevance,
            "region": self.region,
            "country": self.country,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "sentiment": self.sentiment,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": [tag.name for tag in self.tags] if self.tags else [],
            "verification": self.verification_info.to_dict() if self.verification_info else None
        }
