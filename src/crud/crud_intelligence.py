"""
CRUD operations for Intelligence model

This module provides CRUD operations specific to the Intelligence model.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.crud_base import CRUDBase
from src.models.intelligence import Intelligence, ProcessingStatus
from src.schemas.intelligence import IntelligenceCreate, IntelligenceUpdate, IntelligenceFilter
from src.schemas.common import PaginationParams, TimeRange


class CRUDIntelligence(CRUDBase[Intelligence, IntelligenceCreate, IntelligenceUpdate]):
    """
    CRUD operations for Intelligence model.
    """
    
    async def get_by_source_id(
        self,
        db: AsyncSession,
        *,
        source_id: int,
        pagination: PaginationParams
    ) -> List[Intelligence]:
        """
        Get intelligence items by source ID.
        
        Args:
            db: Database session
            source_id: Source ID
            pagination: Pagination parameters
            
        Returns:
            List of intelligence items for the specified source
        """
        skip = (pagination.page - 1) * pagination.page_size
        query = select(Intelligence).where(Intelligence.source_id == source_id).offset(skip).limit(pagination.page_size)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_threat_id(
        self,
        db: AsyncSession,
        *,
        threat_id: int,
        pagination: PaginationParams
    ) -> List[Intelligence]:
        """
        Get intelligence items by threat ID.
        
        Args:
            db: Database session
            threat_id: Threat ID
            pagination: Pagination parameters
            
        Returns:
            List of intelligence items for the specified threat
        """
        skip = (pagination.page - 1) * pagination.page_size
        query = select(Intelligence).where(Intelligence.threat_id == threat_id).offset(skip).limit(pagination.page_size)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_unprocessed(
        self,
        db: AsyncSession,
        *,
        pagination: PaginationParams
    ) -> List[Intelligence]:
        """
        Get unprocessed intelligence items.
        
        Args:
            db: Database session
            pagination: Pagination parameters
            
        Returns:
            List of unprocessed intelligence items
        """
        skip = (pagination.page - 1) * pagination.page_size
        query = select(Intelligence).where(Intelligence.processing_status == ProcessingStatus.PENDING).offset(skip).limit(pagination.page_size)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count_unprocessed(
        self,
        db: AsyncSession
    ) -> int:
        """
        Count unprocessed intelligence items.
        
        Args:
            db: Database session
            
        Returns:
            Count of unprocessed intelligence items
        """
        query = select(func.count()).select_from(Intelligence).where(Intelligence.processing_status == ProcessingStatus.PENDING)
        result = await db.execute(query)
        return result.scalar_one()
    
    async def get_multi_by_filter(
        self,
        db: AsyncSession,
        *,
        filter_params: IntelligenceFilter,
        pagination: PaginationParams
    ) -> List[Intelligence]:
        """
        Get multiple intelligence items by filter parameters.
        
        Args:
            db: Database session
            filter_params: Filter parameters
            pagination: Pagination parameters
            
        Returns:
            List of intelligence items matching the filter
        """
        filters = self._build_filters(filter_params)
        return await self.get_multi(db=db, pagination=pagination, filters=filters)
    
    async def count_by_filter(
        self,
        db: AsyncSession,
        *,
        filter_params: IntelligenceFilter
    ) -> int:
        """
        Count intelligence items by filter parameters.
        
        Args:
            db: Database session
            filter_params: Filter parameters
            
        Returns:
            Count of intelligence items matching the filter
        """
        filters = self._build_filters(filter_params)
        return await self.count(db=db, filters=filters)
    
    async def update_processing_status(
        self,
        db: AsyncSession,
        *,
        intelligence_id: int,
        status: ProcessingStatus,
        processed_content: Optional[str] = None,
        ai_analysis_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        processing_time: Optional[float] = None,
        confidence_score: Optional[float] = None,
        threat_id: Optional[int] = None
    ) -> Optional[Intelligence]:
        """
        Update the processing status and related fields of an intelligence item.
        
        Args:
            db: Database session
            intelligence_id: Intelligence ID
            status: New processing status
            processed_content: Optional processed content
            ai_analysis_data: Optional AI analysis data
            error_message: Optional error message
            processing_time: Optional processing time in seconds
            confidence_score: Optional confidence score
            threat_id: Optional threat ID
            
        Returns:
            Updated intelligence item if found, None otherwise
        """
        intelligence = await self.get(db, intelligence_id)
        if not intelligence:
            return None
            
        intelligence.processing_status = status
        intelligence.processed_at = datetime.utcnow()
        
        if processed_content is not None:
            intelligence.processed_content = processed_content
            
        if ai_analysis_data is not None:
            intelligence.ai_analysis_data = ai_analysis_data
            
        if error_message is not None:
            intelligence.error_message = error_message
            
        if processing_time is not None:
            intelligence.processing_time = processing_time
            
        if confidence_score is not None:
            intelligence.confidence_score = confidence_score
            
        if threat_id is not None:
            intelligence.threat_id = threat_id
            
        db.add(intelligence)
        await db.commit()
        await db.refresh(intelligence)
        return intelligence
    
    async def get_by_status(
        self,
        db: AsyncSession,
        *,
        status: ProcessingStatus,
        pagination: PaginationParams
    ) -> List[Intelligence]:
        """
        Get intelligence items by processing status.
        
        Args:
            db: Database session
            status: Processing status
            pagination: Pagination parameters
            
        Returns:
            List of intelligence items with the specified status
        """
        skip = (pagination.page - 1) * pagination.page_size
        query = select(Intelligence).where(Intelligence.processing_status == status).offset(skip).limit(pagination.page_size)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count_by_status(
        self,
        db: AsyncSession,
        *,
        status: ProcessingStatus
    ) -> int:
        """
        Count intelligence items by processing status.
        
        Args:
            db: Database session
            status: Processing status
            
        Returns:
            Count of intelligence items with the specified status
        """
        query = select(func.count()).select_from(Intelligence).where(Intelligence.processing_status == status)
        result = await db.execute(query)
        return result.scalar_one()
    
    def _build_filters(self, filter_params: IntelligenceFilter) -> List:
        """
        Build SQLAlchemy filter conditions from filter parameters.
        
        Args:
            filter_params: Filter parameters
            
        Returns:
            List of SQLAlchemy filter conditions
        """
        filters = []
        
        if filter_params.source_id:
            filters.append(Intelligence.source_id == filter_params.source_id)
        
        if filter_params.threat_id:
            filters.append(Intelligence.threat_id == filter_params.threat_id)
        
        if filter_params.processing_status:
            filters.append(Intelligence.processing_status == filter_params.processing_status)
        
        if filter_params.min_confidence is not None:
            filters.append(Intelligence.confidence_score >= filter_params.min_confidence)
        
        if filter_params.max_confidence is not None:
            filters.append(Intelligence.confidence_score <= filter_params.max_confidence)
        
        if filter_params.created_after:
            filters.append(Intelligence.created_at >= filter_params.created_after)
        
        if filter_params.created_before:
            filters.append(Intelligence.created_at <= filter_params.created_before)
        
        return filters


intelligence = CRUDIntelligence(Intelligence)
