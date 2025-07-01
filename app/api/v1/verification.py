from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ...database import get_db
from ...models import VerificationInfo, IntelligenceItem
from ...auth import get_current_active_user, User

router = APIRouter()

# Pydantic models
class VerificationInfoBase(BaseModel):
    source_verified: bool = True
    url_verified: bool = True
    timestamp: str
    verification_method: str
    verification_agent: str

class VerificationInfoCreate(VerificationInfoBase):
    pass

class VerificationInfoResponse(VerificationInfoBase):
    intelligence_id: int

    class Config:
        orm_mode = True

# Get all verification info
@router.get("/", response_model=List[VerificationInfoResponse], dependencies=[Depends(get_current_active_user)])
async def get_all_verification_info(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    verifications = db.query(VerificationInfo).offset(skip).limit(limit).all()
    return verifications

# Get verification info by intelligence ID
@router.get("/{intelligence_id}", response_model=VerificationInfoResponse, dependencies=[Depends(get_current_active_user)])
async def get_verification_info(intelligence_id: int, db: Session = Depends(get_db)):
    verification = db.query(VerificationInfo).filter(VerificationInfo.intelligence_id == intelligence_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification info not found")
    return verification

# Create verification info
@router.post("/", response_model=VerificationInfoResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_active_user)])
async def create_verification_info(verification: VerificationInfoCreate, intelligence_id: int, db: Session = Depends(get_db)):
    # Check if intelligence item exists
    intelligence = db.query(IntelligenceItem).filter(IntelligenceItem.id == intelligence_id).first()
    if not intelligence:
        raise HTTPException(status_code=404, detail="Intelligence item not found")
    
    # Check if verification already exists
    existing_verification = db.query(VerificationInfo).filter(VerificationInfo.intelligence_id == intelligence_id).first()
    if existing_verification:
        raise HTTPException(status_code=400, detail="Verification info already exists for this intelligence item")
    
    # Create new verification info
    db_verification = VerificationInfo(
        intelligence_id=intelligence_id,
        source_verified=verification.source_verified,
        url_verified=verification.url_verified,
        timestamp=verification.timestamp,
        verification_method=verification.verification_method,
        verification_agent=verification.verification_agent
    )
    db.add(db_verification)
    db.commit()
    db.refresh(db_verification)
    
    return db_verification

# Update verification info
@router.put("/{intelligence_id}", response_model=VerificationInfoResponse, dependencies=[Depends(get_current_active_user)])
async def update_verification_info(intelligence_id: int, verification: VerificationInfoCreate, db: Session = Depends(get_db)):
    # Get existing verification info
    db_verification = db.query(VerificationInfo).filter(VerificationInfo.intelligence_id == intelligence_id).first()
    if not db_verification:
        raise HTTPException(status_code=404, detail="Verification info not found")
    
    # Update fields
    db_verification.source_verified = verification.source_verified
    db_verification.url_verified = verification.url_verified
    db_verification.timestamp = verification.timestamp
    db_verification.verification_method = verification.verification_method
    db_verification.verification_agent = verification.verification_agent
    
    # Commit changes
    db.commit()
    db.refresh(db_verification)
    
    return db_verification

# Delete verification info
@router.delete("/{intelligence_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_active_user)])
async def delete_verification_info(intelligence_id: int, db: Session = Depends(get_db)):
    # Get existing verification info
    db_verification = db.query(VerificationInfo).filter(VerificationInfo.intelligence_id == intelligence_id).first()
    if not db_verification:
        raise HTTPException(status_code=404, detail="Verification info not found")
    
    # Delete verification info
    db.delete(db_verification)
    db.commit()
    
    return None

# Verify intelligence item
@router.post("/{intelligence_id}/verify", response_model=VerificationInfoResponse, dependencies=[Depends(get_current_active_user)])
async def verify_intelligence_item(intelligence_id: int, verification: VerificationInfoCreate, db: Session = Depends(get_db)):
    # Check if intelligence item exists
    intelligence = db.query(IntelligenceItem).filter(IntelligenceItem.id == intelligence_id).first()
    if not intelligence:
        raise HTTPException(status_code=404, detail="Intelligence item not found")
    
    # Check if verification already exists
    existing_verification = db.query(VerificationInfo).filter(VerificationInfo.intelligence_id == intelligence_id).first()
    
    if existing_verification:
        # Update existing verification
        existing_verification.source_verified = verification.source_verified
        existing_verification.url_verified = verification.url_verified
        existing_verification.timestamp = verification.timestamp
        existing_verification.verification_method = verification.verification_method
        existing_verification.verification_agent = verification.verification_agent
        db_verification = existing_verification
    else:
        # Create new verification
        db_verification = VerificationInfo(
            intelligence_id=intelligence_id,
            source_verified=verification.source_verified,
            url_verified=verification.url_verified,
            timestamp=verification.timestamp,
            verification_method=verification.verification_method,
            verification_agent=verification.verification_agent
        )
        db.add(db_verification)
    
    # Commit changes
    db.commit()
    db.refresh(db_verification)
    
    return db_verification
