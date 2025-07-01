from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ...database import get_db
from ...models import IntelligenceItem, Tag, VerificationInfo
from ...auth import get_current_active_user, User

router = APIRouter()

# Pydantic models for request/response
class TagModel(BaseModel):
    id: Optional[int] = None
    name: str

class VerificationInfoModel(BaseModel):
    source_verified: bool = True
    url_verified: bool = True
    timestamp: str
    verification_method: str
    verification_agent: str

class IntelligenceItemBase(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    source: str
    source_id: int
    raw_content: str
    url: str
    collection_date: str
    publication_date: Optional[str] = None
    threat_level: float
    missionary_relevance: float
    region: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    keywords: Optional[str] = None
    sentiment: Optional[float] = None
    confidence: Optional[float] = None

class IntelligenceItemCreate(IntelligenceItemBase):
    tags: List[str] = []
    verification_info: Optional[VerificationInfoModel] = None

class IntelligenceItemResponse(IntelligenceItemBase):
    id: int
    created_at: datetime
    tags: List[str] = []
    verification_info: Optional[VerificationInfoModel] = None

    class Config:
        orm_mode = True

# Get all intelligence items with filtering options
@router.get("/", response_model=List[IntelligenceItemResponse], dependencies=[Depends(get_current_active_user)])
async def get_intelligence_items(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    region: Optional[str] = None,
    country: Optional[str] = None,
    min_threat: Optional[float] = None,
    min_relevance: Optional[float] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None
):
    query = db.query(IntelligenceItem)
    
    # Apply filters
    if region:
        query = query.filter(IntelligenceItem.region == region)
    if country:
        query = query.filter(IntelligenceItem.country == country)
    if min_threat is not None:
        query = query.filter(IntelligenceItem.threat_level >= min_threat)
    if min_relevance is not None:
        query = query.filter(IntelligenceItem.missionary_relevance >= min_relevance)
    if tag:
        query = query.join(IntelligenceItem.tags).filter(Tag.name == tag)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                IntelligenceItem.title.ilike(search_term),
                IntelligenceItem.content.ilike(search_term),
                IntelligenceItem.summary.ilike(search_term),
                IntelligenceItem.location.ilike(search_term),
                IntelligenceItem.country.ilike(search_term),
                IntelligenceItem.region.ilike(search_term)
            )
        )
    
    # Apply pagination
    items = query.order_by(IntelligenceItem.created_at.desc()).offset(skip).limit(limit).all()
    
    return items

# Get intelligence item by ID
@router.get("/{item_id}", response_model=IntelligenceItemResponse, dependencies=[Depends(get_current_active_user)])
async def get_intelligence_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(IntelligenceItem).filter(IntelligenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Intelligence item not found")
    return item

# Create new intelligence item
@router.post("/", response_model=IntelligenceItemResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_active_user)])
async def create_intelligence_item(item: IntelligenceItemCreate, db: Session = Depends(get_db)):
    # Create new intelligence item
    db_item = IntelligenceItem(
        title=item.title,
        content=item.content,
        summary=item.summary,
        source=item.source,
        source_id=item.source_id,
        raw_content=item.raw_content,
        url=item.url,
        collection_date=item.collection_date,
        publication_date=item.publication_date,
        threat_level=item.threat_level,
        missionary_relevance=item.missionary_relevance,
        region=item.region,
        country=item.country,
        location=item.location,
        latitude=item.latitude,
        longitude=item.longitude,
        keywords=item.keywords,
        sentiment=item.sentiment,
        confidence=item.confidence
    )
    
    # Add tags
    if item.tags:
        for tag_name in item.tags:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            db_item.tags.append(tag)
    
    # Add to database
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Add verification info if provided
    if item.verification_info:
        verification = VerificationInfo(
            intelligence_id=db_item.id,
            source_verified=item.verification_info.source_verified,
            url_verified=item.verification_info.url_verified,
            timestamp=item.verification_info.timestamp,
            verification_method=item.verification_info.verification_method,
            verification_agent=item.verification_info.verification_agent
        )
        db.add(verification)
        db.commit()
        db.refresh(db_item)
    
    return db_item

# Update intelligence item
@router.put("/{item_id}", response_model=IntelligenceItemResponse, dependencies=[Depends(get_current_active_user)])
async def update_intelligence_item(item_id: int, item: IntelligenceItemCreate, db: Session = Depends(get_db)):
    # Get existing item
    db_item = db.query(IntelligenceItem).filter(IntelligenceItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Intelligence item not found")
    
    # Update fields
    for field, value in item.dict(exclude={"tags", "verification_info"}).items():
        setattr(db_item, field, value)
    
    # Update tags
    if item.tags is not None:
        # Remove existing tags
        db_item.tags.clear()
        
        # Add new tags
        for tag_name in item.tags:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            db_item.tags.append(tag)
    
    # Update verification info
    if item.verification_info:
        verification = db.query(VerificationInfo).filter(VerificationInfo.intelligence_id == item_id).first()
        if verification:
            for field, value in item.verification_info.dict().items():
                setattr(verification, field, value)
        else:
            verification = VerificationInfo(
                intelligence_id=db_item.id,
                source_verified=item.verification_info.source_verified,
                url_verified=item.verification_info.url_verified,
                timestamp=item.verification_info.timestamp,
                verification_method=item.verification_info.verification_method,
                verification_agent=item.verification_info.verification_agent
            )
            db.add(verification)
    
    # Commit changes
    db.commit()
    db.refresh(db_item)
    
    return db_item

# Delete intelligence item
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_active_user)])
async def delete_intelligence_item(item_id: int, db: Session = Depends(get_db)):
    # Get existing item
    db_item = db.query(IntelligenceItem).filter(IntelligenceItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Intelligence item not found")
    
    # Delete item
    db.delete(db_item)
    db.commit()
    
    return None

# Get intelligence statistics
@router.get("/stats/overview", dependencies=[Depends(get_current_active_user)])
async def get_intelligence_stats(db: Session = Depends(get_db)):
    # Total items
    total_items = db.query(func.count(IntelligenceItem.id)).scalar()
    
    # Average threat level
    avg_threat = db.query(func.avg(IntelligenceItem.threat_level)).scalar() or 0
    
    # Average missionary relevance
    avg_relevance = db.query(func.avg(IntelligenceItem.missionary_relevance)).scalar() or 0
    
    # Items by region
    regions = db.query(
        IntelligenceItem.region, 
        func.count(IntelligenceItem.id).label("count")
    ).group_by(IntelligenceItem.region).all()
    
    # Items by country
    countries = db.query(
        IntelligenceItem.country, 
        func.count(IntelligenceItem.id).label("count")
    ).group_by(IntelligenceItem.country).all()
    
    # High threat items (threat level >= 7)
    high_threat_count = db.query(func.count(IntelligenceItem.id)).filter(
        IntelligenceItem.threat_level >= 7
    ).scalar()
    
    # High relevance items (missionary relevance >= 7)
    high_relevance_count = db.query(func.count(IntelligenceItem.id)).filter(
        IntelligenceItem.missionary_relevance >= 7
    ).scalar()
    
    return {
        "total_items": total_items,
        "avg_threat_level": float(avg_threat),
        "avg_missionary_relevance": float(avg_relevance),
        "regions": {r[0] or "Unknown": r[1] for r in regions},
        "countries": {c[0] or "Unknown": c[1] for c in countries},
        "high_threat_count": high_threat_count,
        "high_relevance_count": high_relevance_count
    }
