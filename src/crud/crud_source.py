"""
CRUD operations for Source model

This module provides CRUD operations specific to the Source model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.crud_base import CRUDBase
from src.models.source import Source, SourceType
from src.schemas.source import SourceCreate, SourceUpdate, SourceFilter
from src.schemas.common import PaginationParams


class CRUDSource(CRUDBase[Source, SourceCreate, SourceUpdate]):
    """
    CRUD operations for Source model.
    """
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Source]:
        """
        Get a source by name.
        
        Args:
            db: Database session
            name: Source name
            
        Returns:
            Source if found, None otherwise
        """
        query = select(Source).where(Source.name == name)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_url(self, db: AsyncSession, *, url: str) -> Optional[Source]:
        """
        Get a source by URL.
        
        Args:
            db: Database session
            url: Source URL
            
        Returns:
            Source if found, None otherwise
        """
        query = select(Source).where(Source.url == url)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_multi_by_filter(
        self,
        db: AsyncSession,
        *,
        filter_params: SourceFilter,
        pagination: PaginationParams
    ) -> List[Source]:
        """
        Get multiple sources by filter parameters.
        
        Args:
            db: Database session
            filter_params: Filter parameters
            pagination: Pagination parameters
            
        Returns:
            List of sources matching the filter
        """
        filters = self._build_filters(filter_params)
        return await self.get_multi(db=db, pagination=pagination, filters=filters)
    
    async def count_by_filter(
        self,
        db: AsyncSession,
        *,
        filter_params: SourceFilter
    ) -> int:
        """
        Count sources by filter parameters.
        
        Args:
            db: Database session
            filter_params: Filter parameters
            
        Returns:
            Count of sources matching the filter
        """
        filters = self._build_filters(filter_params)
        return await self.count(db=db, filters=filters)
    
    async def get_active_sources(
        self,
        db: AsyncSession,
        *,
        pagination: PaginationParams
    ) -> List[Source]:
        """
        Get active sources.
        
        Args:
            db: Database session
            pagination: Pagination parameters
            
        Returns:
            List of active sources
        """
        skip = (pagination.page - 1) * pagination.page_size
        query = select(Source).where(Source.is_active == True).offset(skip).limit(pagination.page_size)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count_active_sources(
        self,
        db: AsyncSession
    ) -> int:
        """
        Count active sources.
        
        Args:
            db: Database session
            
        Returns:
            Count of active sources
        """
        query = select(func.count()).select_from(Source).where(Source.is_active == True)
        result = await db.execute(query)
        return result.scalar_one()
    
    async def update_last_collected_at(
        self,
        db: AsyncSession,
        *,
        source_id: int,
        last_collected_at
    ) -> Optional[Source]:
        """
        Update the last_collected_at timestamp for a source.
        
        Args:
            db: Database session
            source_id: Source ID
            last_collected_at: Timestamp of last collection
            
        Returns:
            Updated source if found, None otherwise
        """
        source = await self.get(db, source_id)
        if not source:
            return None
            
        source.last_collected_at = last_collected_at
        db.add(source)
        await db.commit()
        await db.refresh(source)
        return source
    
    async def toggle_active_status(
        self,
        db: AsyncSession,
        *,
        source_id: int,
        is_active: bool
    ) -> Optional[Source]:
        """
        Toggle the active status of a source.
        
        Args:
            db: Database session
            source_id: Source ID
            is_active: New active status
            
        Returns:
            Updated source if found, None otherwise
        """
        source = await self.get(db, source_id)
        if not source:
            return None
            
        source.is_active = is_active
        db.add(source)
        await db.commit()
        await db.refresh(source)
        return source
    
    def _build_filters(self, filter_params: SourceFilter) -> List:
        """
        Build SQLAlchemy filter conditions from filter parameters.
        
        Args:
            filter_params: Filter parameters
            
        Returns:
            List of SQLAlchemy filter conditions
        """
        filters = []
        
        if filter_params.source_type:
            filters.append(Source.source_type == filter_params.source_type)
        
        if filter_params.language:
            filters.append(Source.language == filter_params.language)
        
        if filter_params.country:
            filters.append(Source.country == filter_params.country)
        
        if filter_params.min_reliability is not None:
            filters.append(Source.reliability_score >= filter_params.min_reliability)
        
        if filter_params.max_reliability is not None:
            filters.append(Source.reliability_score <= filter_params.max_reliability)
        
        if filter_params.is_active is not None:
            filters.append(Source.is_active == filter_params.is_active)
        
        return filters


source = CRUDSource(Source)
