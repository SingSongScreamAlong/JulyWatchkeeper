"""
Threat API endpoints for WATCHKEEPER

This module provides API endpoints for threat-related operations.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_api_key
from src.crud.crud_threat import threat
from src.models.threat import ThreatStatus, ThreatCategory
from src.schemas.threat import (
    ThreatCreate, 
    ThreatUpdate, 
    ThreatResponse, 
    ThreatFilter
)
from src.schemas.common import (
    PaginatedResponse, 
    MessageResponse, 
    PaginationParams,
    GeoPoint
)


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ThreatResponse])
async def get_threats(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    pagination: PaginationParams = Depends(),
    status: Optional[ThreatStatus] = None,
    category: Optional[ThreatCategory] = None,
    min_severity: Optional[float] = Query(None, ge=0, le=1),
    max_severity: Optional[float] = Query(None, ge=0, le=1),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    max_confidence: Optional[float] = Query(None, ge=0, le=1),
    min_missionary_relevance: Optional[float] = Query(None, ge=0, le=1),
    max_missionary_relevance: Optional[float] = Query(None, ge=0, le=1),
    source_id: Optional[int] = None,
    search_query: Optional[str] = None
) -> Any:
    """
    Get threats with optional filtering.
    """
    # Create filter object from query parameters
    filter_params = ThreatFilter(
        status=status,
        category=category,
        min_severity=min_severity,
        max_severity=max_severity,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        min_missionary_relevance=min_missionary_relevance,
        max_missionary_relevance=max_missionary_relevance,
        source_id=source_id,
        search_query=search_query
    )
    
    # Get threats and total count
    threats = await threat.get_multi_by_filter(
        db=db, 
        filter_params=filter_params, 
        pagination=pagination
    )
    total = await threat.count_by_filter(db=db, filter_params=filter_params)
    
    # Return paginated response
    return PaginatedResponse(
        items=threats,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post("/", response_model=ThreatResponse)
async def create_threat(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    threat_in: ThreatCreate
) -> Any:
    """
    Create a new threat.
    """
    # Check if threat with same title already exists
    existing_threat = await threat.get_by_title(db=db, title=threat_in.title)
    if existing_threat:
        raise HTTPException(
            status_code=400,
            detail="Threat with this title already exists"
        )
    
    # Create threat
    return await threat.create(db=db, obj_in=threat_in)


@router.get("/{threat_id}", response_model=ThreatResponse)
async def get_threat(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    threat_id: int = Path(..., gt=0)
) -> Any:
    """
    Get a specific threat by ID.
    """
    # Get threat
    db_threat = await threat.get(db=db, id=threat_id)
    if not db_threat:
        raise HTTPException(
            status_code=404,
            detail="Threat not found"
        )
    
    return db_threat


@router.put("/{threat_id}", response_model=ThreatResponse)
async def update_threat(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    threat_id: int = Path(..., gt=0),
    threat_in: ThreatUpdate
) -> Any:
    """
    Update a threat.
    """
    # Get threat
    db_threat = await threat.get(db=db, id=threat_id)
    if not db_threat:
        raise HTTPException(
            status_code=404,
            detail="Threat not found"
        )
    
    # If title is being updated, check for duplicates
    if threat_in.title and threat_in.title != db_threat.title:
        existing_threat = await threat.get_by_title(db=db, title=threat_in.title)
        if existing_threat and existing_threat.id != threat_id:
            raise HTTPException(
                status_code=400,
                detail="Threat with this title already exists"
            )
    
    # Update threat
    return await threat.update(db=db, db_obj=db_threat, obj_in=threat_in)


@router.delete("/{threat_id}", response_model=MessageResponse)
async def delete_threat(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    threat_id: int = Path(..., gt=0)
) -> Any:
    """
    Delete a threat.
    """
    # Get threat
    db_threat = await threat.get(db=db, id=threat_id)
    if not db_threat:
        raise HTTPException(
            status_code=404,
            detail="Threat not found"
        )
    
    # Delete threat
    await threat.remove(db=db, id=threat_id)
    
    return MessageResponse(message=f"Threat with ID {threat_id} deleted successfully")


@router.get("/geo/proximity", response_model=PaginatedResponse[ThreatResponse])
async def get_threats_by_proximity(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    pagination: PaginationParams = Depends(),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    distance_meters: float = Query(..., gt=0),
    status: Optional[ThreatStatus] = None,
    category: Optional[ThreatCategory] = None,
    min_severity: Optional[float] = Query(None, ge=0, le=1),
    max_severity: Optional[float] = Query(None, ge=0, le=1)
) -> Any:
    """
    Get threats within a specified distance of a geographic point.
    """
    # Create location point and filter object
    location = GeoPoint(latitude=latitude, longitude=longitude)
    filter_params = ThreatFilter(
        status=status,
        category=category,
        min_severity=min_severity,
        max_severity=max_severity
    )
    
    # Get threats by proximity
    threats = await threat.get_by_geo_proximity(
        db=db,
        location=location,
        distance_meters=distance_meters,
        pagination=pagination,
        filter_params=filter_params
    )
    
    # Get total count
    total = await threat.count_by_geo_proximity(
        db=db,
        location=location,
        distance_meters=distance_meters,
        filter_params=filter_params
    )
    
    # Return paginated response
    return PaginatedResponse(
        items=threats,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )
