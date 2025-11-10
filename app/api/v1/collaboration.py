"""Collaboration and Intelligence Sharing API"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets

from ...database import get_db
from ...auth import get_current_active_user
from ...models.collaboration import Organization, SharedIntelligence

router = APIRouter()


# Pydantic Models
class OrganizationCreate(BaseModel):
    name: str
    organization_type: str  # missionary, ngo, government
    trust_level: int = 5
    can_receive_intel: bool = False
    can_submit_intel: bool = False
    regions_of_interest: Optional[List[str]] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class ShareIntelligence(BaseModel):
    intelligence_id: int
    organization_id: int
    share_level: str = 'summary_only'  # summary_only, full, classified
    expiry_days: Optional[int] = None


# Organization Endpoints
@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Register a new partner organization"""

    # Generate API key
    api_key = secrets.token_urlsafe(32)

    organization = Organization(
        **org_data.dict(),
        api_key=api_key
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    result = organization.to_dict()
    result['api_key'] = api_key  # Only show API key on creation

    return result


@router.get("/organizations")
async def get_organizations(
    active_only: bool = True,
    organization_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all partner organizations"""

    query = db.query(Organization)

    if active_only:
        query = query.filter(Organization.active == True)

    if organization_type:
        query = query.filter(Organization.organization_type == organization_type)

    organizations = query.all()
    return [org.to_dict() for org in organizations]


@router.get("/organizations/{org_id}")
async def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get organization details"""

    org = db.query(Organization).filter(Organization.id == org_id).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return org.to_dict()


@router.put("/organizations/{org_id}")
async def update_organization(
    org_id: int,
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update organization"""

    org = db.query(Organization).filter(Organization.id == org_id).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    for key, value in org_data.dict(exclude_unset=True).items():
        setattr(org, key, value)

    org.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(org)

    return org.to_dict()


# Intelligence Sharing Endpoints
@router.post("/share", status_code=status.HTTP_201_CREATED)
async def share_intelligence(
    share_data: ShareIntelligence,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Share intelligence with a partner organization"""

    from ...models.intelligence import IntelligenceItem

    # Verify intelligence exists
    intel = db.query(IntelligenceItem).filter(
        IntelligenceItem.id == share_data.intelligence_id
    ).first()

    if not intel:
        raise HTTPException(status_code=404, detail="Intelligence item not found")

    # Verify organization exists and can receive
    org = db.query(Organization).filter(
        Organization.id == share_data.organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not org.can_receive_intel:
        raise HTTPException(
            status_code=403,
            detail="Organization is not authorized to receive intelligence"
        )

    # Calculate expiry date
    expiry_date = None
    if share_data.expiry_days:
        expiry_date = datetime.utcnow() + timedelta(days=share_data.expiry_days)

    # Create share record
    shared = SharedIntelligence(
        intelligence_id=share_data.intelligence_id,
        shared_with_org_id=share_data.organization_id,
        shared_by_user_id=current_user.id if hasattr(current_user, 'id') else None,
        share_level=share_data.share_level,
        expiry_date=expiry_date
    )

    db.add(shared)
    db.commit()
    db.refresh(shared)

    return shared.to_dict()


@router.get("/shared-with-me")
async def get_shared_intelligence(
    share_level: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get intelligence shared with the user's organization"""

    # TODO: Get user's organization from current_user
    # For now, return sample response

    query = db.query(SharedIntelligence)

    if active_only:
        query = query.filter(
            SharedIntelligence.revoked == False,
            (SharedIntelligence.expiry_date.is_(None)) |
            (SharedIntelligence.expiry_date > datetime.utcnow())
        )

    if share_level:
        query = query.filter(SharedIntelligence.share_level == share_level)

    shared_items = query.all()

    # Load full intelligence items
    results = []

    for shared in shared_items:
        from ...models.intelligence import IntelligenceItem

        intel = db.query(IntelligenceItem).filter(
            IntelligenceItem.id == shared.intelligence_id
        ).first()

        if intel:
            intel_dict = intel.to_dict()

            # Filter fields based on share level
            if shared.share_level == 'summary_only':
                intel_dict = {
                    'id': intel_dict['id'],
                    'title': intel_dict['title'],
                    'summary': intel_dict['summary'],
                    'threat_level': intel_dict['threat_level'],
                    'region': intel_dict['region'],
                    'country': intel_dict['country']
                }

            results.append({
                'intelligence': intel_dict,
                'share_info': shared.to_dict()
            })

        # Mark as accessed
        if not shared.accessed:
            shared.accessed = True
            shared.last_accessed = datetime.utcnow()
            shared.access_count = 1
        else:
            shared.access_count += 1
            shared.last_accessed = datetime.utcnow()

    db.commit()

    return results


@router.post("/share/{share_id}/revoke")
async def revoke_shared_intelligence(
    share_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Revoke shared intelligence"""

    shared = db.query(SharedIntelligence).filter(
        SharedIntelligence.id == share_id
    ).first()

    if not shared:
        raise HTTPException(status_code=404, detail="Share not found")

    shared.revoked = True
    shared.revoked_at = datetime.utcnow()

    db.commit()

    return {"message": "Intelligence share revoked", "share_id": share_id}


@router.get("/share/analytics")
async def get_sharing_analytics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get analytics on intelligence sharing"""

    total_orgs = db.query(Organization).filter(Organization.active == True).count()

    total_shares = db.query(SharedIntelligence).count()

    active_shares = db.query(SharedIntelligence).filter(
        SharedIntelligence.revoked == False,
        (SharedIntelligence.expiry_date.is_(None)) |
        (SharedIntelligence.expiry_date > datetime.utcnow())
    ).count()

    accessed_shares = db.query(SharedIntelligence).filter(
        SharedIntelligence.accessed == True
    ).count()

    # Get most active organizations
    from sqlalchemy import func

    most_active = db.query(
        SharedIntelligence.shared_with_org_id,
        func.count(SharedIntelligence.id).label('share_count')
    ).group_by(
        SharedIntelligence.shared_with_org_id
    ).order_by(
        func.count(SharedIntelligence.id).desc()
    ).limit(5).all()

    most_active_orgs = []

    for org_id, count in most_active:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if org:
            most_active_orgs.append({
                'organization': org.name,
                'shares_received': count
            })

    return {
        'total_organizations': total_orgs,
        'total_shares': total_shares,
        'active_shares': active_shares,
        'accessed_shares': accessed_shares,
        'access_rate': f"{(accessed_shares/total_shares*100):.1f}%" if total_shares > 0 else "0%",
        'most_active_organizations': most_active_orgs
    }
