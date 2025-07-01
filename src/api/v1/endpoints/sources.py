"""
Source API endpoints for WATCHKEEPER

This module provides API endpoints for source-related operations.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_api_key
from src.crud.crud_source import source
from src.models.source import SourceType
from src.schemas.source import (
    SourceCreate, 
    SourceUpdate, 
    SourceResponse, 
    SourceFilter,
    SourceCollectionStatus
)
from src.schemas.common import (
    PaginatedResponse, 
    MessageResponse, 
    PaginationParams
)


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[SourceResponse])
async def get_sources(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    pagination: PaginationParams = Depends(),
    source_type: Optional[SourceType] = None,
    language: Optional[str] = None,
    country: Optional[str] = None,
    min_reliability: Optional[float] = Query(None, ge=0, le=1),
    max_reliability: Optional[float] = Query(None, ge=0, le=1),
    is_active: Optional[bool] = None
) -> Any:
    """
    Get sources with optional filtering.
    """
    # Create filter object from query parameters
    filter_params = SourceFilter(
        source_type=source_type,
        language=language,
        country=country,
        min_reliability=min_reliability,
        max_reliability=max_reliability,
        is_active=is_active
    )
    
    # Get sources and total count
    sources_list = await source.get_multi_by_filter(
        db=db, 
        filter_params=filter_params, 
        pagination=pagination
    )
    total = await source.count_by_filter(db=db, filter_params=filter_params)
    
    # Return paginated response
    return PaginatedResponse(
        items=sources_list,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post("/", response_model=SourceResponse)
async def create_source(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    source_in: SourceCreate
) -> Any:
    """
    Create a new source.
    """
    # Check if source with same name already exists
    existing_source = await source.get_by_name(db=db, name=source_in.name)
    if existing_source:
        raise HTTPException(
            status_code=400,
            detail="Source with this name already exists"
        )
    
    # Check if source with same URL already exists
    existing_source = await source.get_by_url(db=db, url=source_in.url)
    if existing_source:
        raise HTTPException(
            status_code=400,
            detail="Source with this URL already exists"
        )
    
    # Create source
    return await source.create(db=db, obj_in=source_in)


@router.get("/active", response_model=PaginatedResponse[SourceResponse])
async def get_active_sources(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    pagination: PaginationParams = Depends()
) -> Any:
    """
    Get active sources.
    """
    # Get active sources and total count
    sources_list = await source.get_active_sources(db=db, pagination=pagination)
    total = await source.count_active_sources(db=db)
    
    # Return paginated response
    return PaginatedResponse(
        items=sources_list,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    source_id: int = Path(..., gt=0)
) -> Any:
    """
    Get a specific source by ID.
    """
    # Get source
    db_source = await source.get(db=db, id=source_id)
    if not db_source:
        raise HTTPException(
            status_code=404,
            detail="Source not found"
        )
    
    return db_source


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    source_id: int = Path(..., gt=0),
    source_in: SourceUpdate
) -> Any:
    """
    Update a source.
    """
    # Get source
    db_source = await source.get(db=db, id=source_id)
    if not db_source:
        raise HTTPException(
            status_code=404,
            detail="Source not found"
        )
    
    # If name is being updated, check for duplicates
    if source_in.name and source_in.name != db_source.name:
        existing_source = await source.get_by_name(db=db, name=source_in.name)
        if existing_source and existing_source.id != source_id:
            raise HTTPException(
                status_code=400,
                detail="Source with this name already exists"
            )
    
    # If URL is being updated, check for duplicates
    if source_in.url and source_in.url != db_source.url:
        existing_source = await source.get_by_url(db=db, url=source_in.url)
        if existing_source and existing_source.id != source_id:
            raise HTTPException(
                status_code=400,
                detail="Source with this URL already exists"
            )
    
    # Update source
    return await source.update(db=db, db_obj=db_source, obj_in=source_in)


@router.delete("/{source_id}", response_model=MessageResponse)
async def delete_source(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    source_id: int = Path(..., gt=0)
) -> Any:
    """
    Delete a source.
    """
    # Get source
    db_source = await source.get(db=db, id=source_id)
    if not db_source:
        raise HTTPException(
            status_code=404,
            detail="Source not found"
        )
    
    # Delete source
    await source.remove(db=db, id=source_id)
    
    return MessageResponse(message=f"Source with ID {source_id} deleted successfully")


@router.patch("/{source_id}/toggle-active", response_model=SourceResponse)
async def toggle_source_active_status(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    source_id: int = Path(..., gt=0),
    is_active: bool = Body(..., embed=True)
) -> Any:
    """
    Toggle the active status of a source.
    """
    # Toggle active status
    db_source = await source.toggle_active_status(
        db=db, 
        source_id=source_id, 
        is_active=is_active
    )
    
    if not db_source:
        raise HTTPException(
            status_code=404,
            detail="Source not found"
        )
    
    return db_source
