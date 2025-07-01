from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel

from ...database import get_db
from ...models import Tag, IntelligenceItem
from ...auth import get_current_active_user, User

router = APIRouter()

# Pydantic models
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int
    intelligence_count: int = 0

    class Config:
        orm_mode = True

# Get all tags
@router.get("/", response_model=List[TagResponse], dependencies=[Depends(get_current_active_user)])
async def get_tags(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    tags = db.query(Tag).offset(skip).limit(limit).all()
    return tags

# Get tag by ID
@router.get("/{tag_id}", response_model=TagResponse, dependencies=[Depends(get_current_active_user)])
async def get_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

# Create new tag
@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_active_user)])
async def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    # Check if tag already exists
    existing_tag = db.query(Tag).filter(Tag.name == tag.name).first()
    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    # Create new tag
    db_tag = Tag(name=tag.name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    return db_tag

# Update tag
@router.put("/{tag_id}", response_model=TagResponse, dependencies=[Depends(get_current_active_user)])
async def update_tag(tag_id: int, tag: TagCreate, db: Session = Depends(get_db)):
    # Get existing tag
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Check if new name already exists
    if tag.name != db_tag.name:
        existing_tag = db.query(Tag).filter(Tag.name == tag.name).first()
        if existing_tag:
            raise HTTPException(status_code=400, detail="Tag with this name already exists")
    
    # Update tag
    db_tag.name = tag.name
    db.commit()
    db.refresh(db_tag)
    
    return db_tag

# Delete tag
@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_active_user)])
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    # Get existing tag
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Delete tag
    db.delete(db_tag)
    db.commit()
    
    return None

# Get intelligence items by tag
@router.get("/{tag_id}/intelligence", response_model=List[dict], dependencies=[Depends(get_current_active_user)])
async def get_intelligence_by_tag(tag_id: int, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    # Check if tag exists
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Get intelligence items with this tag
    items = db.query(IntelligenceItem).join(IntelligenceItem.tags).filter(
        Tag.id == tag_id
    ).offset(skip).limit(limit).all()
    
    # Convert to dict for response
    return [item.to_dict() for item in items]

# Get tag statistics
@router.get("/stats/overview", dependencies=[Depends(get_current_active_user)])
async def get_tag_stats(db: Session = Depends(get_db)):
    # Total tags
    total_tags = db.query(func.count(Tag.id)).scalar()
    
    # Tags with most intelligence items
    popular_tags = db.query(
        Tag.name,
        func.count(IntelligenceItem.id).label("count")
    ).join(Tag.intelligence_items).group_by(Tag.name).order_by(func.count(IntelligenceItem.id).desc()).limit(10).all()
    
    return {
        "total_tags": total_tags,
        "popular_tags": {t[0]: t[1] for t in popular_tags}
    }
