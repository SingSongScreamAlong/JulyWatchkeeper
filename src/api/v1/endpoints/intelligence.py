"""Intelligence Endpoints for WATCHKEEPER API

This module provides endpoints for managing intelligence items.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_api_key
from src.crud import intelligence, source, threat, tag
from src.schemas.intelligence import (
    IntelligenceCreate,
    IntelligenceUpdate,
    IntelligenceResponse,
    IntelligenceFilter,
    IntelligenceProcessRequest,
    IntelligenceProcessResponse,
    IntelligenceBatchProcessRequest,
    IntelligenceBatchProcessResponse
)
from src.schemas.common import PaginatedResponse, PaginationParams, MessageResponse
from src.models.intelligence import ProcessingStatus
from src.api.websocket import broadcast_to_topic

router = APIRouter()


@router.post("/", response_model=IntelligenceResponse)
async def create_intelligence(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    intelligence_in: IntelligenceCreate
) -> Any:
    """
    Create a new intelligence item.
    """
    # Check if source exists
    db_source = await source.get(db=db, id=intelligence_in.source_id)
    if not db_source:
        raise HTTPException(
            status_code=404,
            detail=f"Source with ID {intelligence_in.source_id} not found"
        )
    
    # If threat_id is provided, check if threat exists
    if intelligence_in.threat_id is not None:
        db_threat = await threat.get(db=db, id=intelligence_in.threat_id)
        if not db_threat:
            raise HTTPException(
                status_code=404,
                detail=f"Threat with ID {intelligence_in.threat_id} not found"
            )
    
    # Create intelligence item
    db_intelligence = await intelligence.create(db=db, obj_in=intelligence_in)
    
    # Broadcast to WebSocket clients
    await broadcast_to_topic(
        topic="intelligence",
        message={
            "event": "intelligence_created",
            "data": {
                "id": db_intelligence.id,
                "title": db_intelligence.title,
                "source_id": db_intelligence.source_id
            }
        }
    )
    
    return db_intelligence


@router.get("/", response_model=PaginatedResponse[IntelligenceResponse])
async def get_intelligence_items(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    pagination: PaginationParams = Depends(),
    source_id: Optional[int] = Query(None, gt=0),
    threat_id: Optional[int] = Query(None, gt=0),
    tag_id: Optional[int] = Query(None, gt=0),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
) -> Any:
    """
    Get intelligence items with filtering and pagination.
    """
    # Create filter parameters
    filter_params = IntelligenceFilter(
        source_id=source_id,
        threat_id=threat_id,
        tag_id=tag_id,
        status=status,
        search=search
    )
    
    # Get intelligence items and total count
    items = await intelligence.get_by_filter(db=db, filter_params=filter_params, pagination=pagination)
    total = await intelligence.count_by_filter(db=db, filter_params=filter_params)
    
    # Calculate total pages
    pages = (total + pagination.page_size - 1) // pagination.page_size
    
    # Return paginated response
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages
    )


@router.get("/by-source/{source_id}", response_model=PaginatedResponse[IntelligenceResponse])
async def get_intelligence_by_source(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    pagination: PaginationParams = Depends(),
    source_id: int = Path(..., gt=0)
) -> Any:
    """
    Get intelligence items by source ID.
    """
    # Check if source exists
    db_source = await source.get(db=db, id=source_id)
    if not db_source:
        raise HTTPException(
            status_code=404,
            detail=f"Source with ID {source_id} not found"
        )
    
    # Get intelligence items by source and total count
    items = await intelligence.get_by_source_id(db=db, source_id=source_id, pagination=pagination)
    
    # Create filter for count
    filter_params = IntelligenceFilter(source_id=source_id)
    total = await intelligence.count_by_filter(db=db, filter_params=filter_params)
    
    # Calculate total pages
    pages = (total + pagination.page_size - 1) // pagination.page_size
    
    # Return paginated response
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages
    )


@router.get("/by-tag/{tag_id}", response_model=PaginatedResponse[IntelligenceResponse])
async def get_intelligence_by_tag(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    pagination: PaginationParams = Depends(),
    tag_id: int = Path(..., gt=0)
) -> Any:
    """
    Get intelligence items by tag ID.
    """
    # Check if tag exists
    db_tag = await tag.get(db=db, id=tag_id)
    if not db_tag:
        raise HTTPException(
            status_code=404,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Get intelligence items by tag and total count
    items = await intelligence.get_by_tag_id(db=db, tag_id=tag_id, pagination=pagination)
    
    # Create filter for count
    filter_params = IntelligenceFilter(tag_id=tag_id)
    total = await intelligence.count_by_filter(db=db, filter_params=filter_params)
    
    # Calculate total pages
    pages = (total + pagination.page_size - 1) // pagination.page_size
    
    # Return paginated response
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages
    )


@router.get("/by-threat/{threat_id}", response_model=PaginatedResponse[IntelligenceResponse])
async def get_intelligence_by_threat(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    pagination: PaginationParams = Depends(),
    threat_id: int = Path(..., gt=0)
) -> Any:
    """
    Get intelligence items by threat ID.
    """
    # Check if threat exists
    db_threat = await threat.get(db=db, id=threat_id)
    if not db_threat:
        raise HTTPException(
            status_code=404,
            detail=f"Threat with ID {threat_id} not found"
        )
    
    # Get intelligence items by threat and total count
    items = await intelligence.get_by_threat_id(db=db, threat_id=threat_id, pagination=pagination)
    
    # Create filter for count
    filter_params = IntelligenceFilter(threat_id=threat_id)
    total = await intelligence.count_by_filter(db=db, filter_params=filter_params)
    
    # Calculate total pages
    pages = (total + pagination.page_size - 1) // pagination.page_size
    
    # Return paginated response
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages
    )


@router.get("/{intelligence_id}", response_model=IntelligenceResponse)
async def get_intelligence(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    intelligence_id: int = Path(..., gt=0)
) -> Any:
    """
    Get a specific intelligence item by ID.
    """
    # Get intelligence item
    db_intelligence = await intelligence.get(db=db, id=intelligence_id)
    if not db_intelligence:
        raise HTTPException(
            status_code=404,
            detail="Intelligence item not found"
        )
    
    return db_intelligence


@router.put("/{intelligence_id}", response_model=IntelligenceResponse)
async def update_intelligence(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    intelligence_id: int = Path(..., gt=0),
    intelligence_in: IntelligenceUpdate
) -> Any:
    """
    Update an intelligence item.
    """
    # Get intelligence item
    db_intelligence = await intelligence.get(db=db, id=intelligence_id)
    if not db_intelligence:
        raise HTTPException(
            status_code=404,
            detail="Intelligence item not found"
        )
    
    # If threat_id is being updated, check if threat exists
    if intelligence_in.threat_id is not None and intelligence_in.threat_id != db_intelligence.threat_id:
        db_threat = await threat.get(db=db, id=intelligence_in.threat_id)
        if not db_threat:
            raise HTTPException(
                status_code=404,
                detail=f"Threat with ID {intelligence_in.threat_id} not found"
            )
    
    # Update intelligence item
    return await intelligence.update(db=db, db_obj=db_intelligence, obj_in=intelligence_in)


@router.delete("/{intelligence_id}", response_model=MessageResponse)
async def delete_intelligence(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    intelligence_id: int = Path(..., gt=0)
) -> Any:
    """
    Delete an intelligence item.
    """
    # Get intelligence item
    db_intelligence = await intelligence.get(db=db, id=intelligence_id)
    if not db_intelligence:
        raise HTTPException(
            status_code=404,
            detail="Intelligence item not found"
        )
    
    # Delete intelligence item
    await intelligence.remove(db=db, id=intelligence_id)
    
    return MessageResponse(message=f"Intelligence item with ID {intelligence_id} deleted successfully")


@router.post("/process", response_model=IntelligenceProcessResponse)
async def process_intelligence(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    background_tasks: BackgroundTasks,
    process_request: IntelligenceProcessRequest
) -> Any:
    """
    Process an intelligence item.
    
    This endpoint triggers the processing of an intelligence item.
    Processing is performed asynchronously in the background.
    """
    # Get intelligence item
    db_intelligence = await intelligence.get(db=db, id=process_request.intelligence_id)
    if not db_intelligence:
        raise HTTPException(
            status_code=404,
            detail="Intelligence item not found"
        )
    
    # Check if intelligence item is already processed
    if db_intelligence.processing_status != ProcessingStatus.PENDING:
        return IntelligenceProcessResponse(
            intelligence_id=process_request.intelligence_id,
            status=db_intelligence.processing_status,
            message=f"Intelligence item already has status: {db_intelligence.processing_status.value}"
        )
    
    # Update status to PROCESSING
    db_intelligence = await intelligence.update_processing_status(
        db=db,
        intelligence_id=process_request.intelligence_id,
        status=ProcessingStatus.PROCESSING
    )
    
    # TODO: Add background task to process intelligence
    # This would be implemented in a service module
    # background_tasks.add_task(
    #     process_intelligence_task,
    #     intelligence_id=process_request.intelligence_id,
    #     options=process_request.processing_options
    # )
    
    return IntelligenceProcessResponse(
        intelligence_id=process_request.intelligence_id,
        status=ProcessingStatus.PROCESSING,
        message="Intelligence processing started"
    )


@router.post("/batch-process", response_model=IntelligenceBatchProcessResponse)
async def batch_process_intelligence(
    *,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
    background_tasks: BackgroundTasks,
    batch_request: IntelligenceBatchProcessRequest
) -> Any:
    """
    Process multiple intelligence items in batch.
    
    This endpoint triggers the processing of multiple intelligence items.
    Processing is performed asynchronously in the background.
    """
    processed_count = 0
    failed_count = 0
    
    for intelligence_id in batch_request.intelligence_ids:
        # Get intelligence item
        db_intelligence = await intelligence.get(db=db, id=intelligence_id)
        if not db_intelligence:
            failed_count += 1
            continue
        
        # Check if intelligence item is already processed
        if db_intelligence.processing_status != ProcessingStatus.PENDING:
            failed_count += 1
            continue
        
        # Update status to PROCESSING
        await intelligence.update_processing_status(
            db=db,
            intelligence_id=intelligence_id,
            status=ProcessingStatus.PROCESSING
        )
        
        # TODO: Add background task to process intelligence
        # This would be implemented in a service module
        # background_tasks.add_task(
        #     process_intelligence_task,
        #     intelligence_id=intelligence_id,
        #     options=batch_request.processing_options
        # )
        
        processed_count += 1
    
    return IntelligenceBatchProcessResponse(
        processed_count=processed_count,
        failed_count=failed_count,
        status="processing",
        message=f"Batch processing started for {processed_count} intelligence items"
    )
