"""
CRUD operations for Threat model

This module provides CRUD operations specific to the Threat model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin

from src.crud.crud_base import CRUDBase
from src.models.threat import Threat, ThreatStatus, ThreatCategory
from src.schemas.threat import ThreatCreate, ThreatUpdate, ThreatFilter
from src.schemas.common import GeoPoint, TimeRange, PaginationParams


class CRUDThreat(CRUDBase[Threat, ThreatCreate, ThreatUpdate]):
    """
    CRUD operations for Threat model.
    """
    
    async def get_by_title(self, db: AsyncSession, *, title: str) -> Optional[Threat]:
        """
        Get a threat by title.
        
        Args:
            db: Database session
            title: Threat title
            
        Returns:
            Threat if found, None otherwise
        """
        query = select(Threat).where(Threat.title == title)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_multi_by_filter(
        self,
        db: AsyncSession,
        *,
        filter_params: ThreatFilter,
        pagination: PaginationParams
    ) -> List[Threat]:
        """
        Get multiple threats by filter parameters.
        
        Args:
            db: Database session
            filter_params: Filter parameters
            pagination: Pagination parameters
            
        Returns:
            List of threats matching the filter
        """
        filters = self._build_filters(filter_params)
        return await self.get_multi(db=db, pagination=pagination, filters=filters)
    
    async def count_by_filter(
        self,
        db: AsyncSession,
        *,
        filter_params: ThreatFilter
    ) -> int:
        """
        Count threats by filter parameters.
        
        Args:
            db: Database session
            filter_params: Filter parameters
            
        Returns:
            Count of threats matching the filter
        """
        filters = self._build_filters(filter_params)
        return await self.count(db=db, filters=filters)
    
    async def get_by_geo_proximity(
        self,
        db: AsyncSession,
        *,
        location: GeoPoint,
        distance_meters: float,
        pagination: PaginationParams,
        filter_params: Optional[ThreatFilter] = None
    ) -> List[Threat]:
        """
        Get threats within a certain distance of a geographic point.
        
        Args:
            db: Database session
            location: Geographic point
            distance_meters: Distance in meters
            pagination: Pagination parameters
            filter_params: Optional additional filter parameters
            
        Returns:
            List of threats within the specified distance
        """
        skip = (pagination.page - 1) * pagination.page_size
        
        # Create a WKT point from the coordinates
        point = f'SRID=4326;POINT({location.longitude} {location.latitude})'
        
        # Build the base query with proximity filter
        query = select(Threat).where(
            ST_DWithin(
                Threat.location.cast(Geography),
                point.cast(Geography),
                distance_meters
            )
        )
        
        # Add additional filters if provided
        if filter_params:
            filters = self._build_filters(filter_params)
            if filters:
                query = query.where(and_(*filters))
        
        # Add pagination
        query = query.offset(skip).limit(pagination.page_size)
        
        # Execute query
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count_by_geo_proximity(
        self,
        db: AsyncSession,
        *,
        location: GeoPoint,
        distance_meters: float,
        filter_params: Optional[ThreatFilter] = None
    ) -> int:
        """
        Count threats within a certain distance of a geographic point.
        
        Args:
            db: Database session
            location: Geographic point
            distance_meters: Distance in meters
            filter_params: Optional additional filter parameters
            
        Returns:
            Count of threats within the specified distance
        """
        # Create a WKT point from the coordinates
        point = f'SRID=4326;POINT({location.longitude} {location.latitude})'
        
        # Build the base query with proximity filter
        query = select(func.count()).select_from(Threat).where(
            ST_DWithin(
                Threat.location.cast(Geography),
                point.cast(Geography),
                distance_meters
            )
        )
        
        # Add additional filters if provided
        if filter_params:
            filters = self._build_filters(filter_params)
            if filters:
                query = query.where(and_(*filters))
        
        # Execute query
        result = await db.execute(query)
        return result.scalar_one()
    
    def _build_filters(self, filter_params: ThreatFilter) -> List:
        """
        Build SQLAlchemy filter conditions from filter parameters.
        
        Args:
            filter_params: Filter parameters
            
        Returns:
            List of SQLAlchemy filter conditions
        """
        filters = []
        
        if filter_params.status:
            filters.append(Threat.status == filter_params.status)
        
        if filter_params.category:
            filters.append(Threat.category == filter_params.category)
        
        if filter_params.min_severity is not None:
            filters.append(Threat.severity >= filter_params.min_severity)
        
        if filter_params.max_severity is not None:
            filters.append(Threat.severity <= filter_params.max_severity)
        
        if filter_params.min_confidence is not None:
            filters.append(Threat.confidence >= filter_params.min_confidence)
        
        if filter_params.max_confidence is not None:
            filters.append(Threat.confidence <= filter_params.max_confidence)
        
        if filter_params.min_missionary_relevance is not None:
            filters.append(Threat.missionary_relevance >= filter_params.min_missionary_relevance)
        
        if filter_params.max_missionary_relevance is not None:
            filters.append(Threat.missionary_relevance <= filter_params.max_missionary_relevance)
        
        if filter_params.source_id:
            filters.append(Threat.source_id == filter_params.source_id)
        
        if filter_params.time_range:
            if filter_params.time_range.start:
                filters.append(Threat.created_at >= filter_params.time_range.start)
            if filter_params.time_range.end:
                filters.append(Threat.created_at <= filter_params.time_range.end)
        
        if filter_params.search_query:
            search = f"%{filter_params.search_query}%"
            filters.append(
                or_(
                    Threat.title.ilike(search),
                    Threat.description.ilike(search),
                    Threat.content.ilike(search)
                )
            )
        
        return filters


threat = CRUDThreat(Threat)
