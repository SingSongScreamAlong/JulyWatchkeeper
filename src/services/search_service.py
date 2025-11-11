"""
Advanced Search Service for WATCHKEEPER

This service provides full-text search capabilities using PostgreSQL's full-text search.
For production, this could be extended to use Elasticsearch.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import select, or_, and_, text, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.models.intelligence import Intelligence
from src.models.threat import Threat
from src.models.source import Source

logger = logging.getLogger(__name__)


class SearchService:
    """Service for advanced search across WATCHKEEPER data."""

    @staticmethod
    async def search_intelligence(
        db: AsyncSession,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Intelligence]:
        """
        Search intelligence items using full-text search.

        Args:
            db: Database session
            query: Search query string
            filters: Optional filters (status, source_id, etc.)
            limit: Maximum results to return

        Returns:
            List of matching intelligence items
        """
        # Build base query with full-text search
        # Using PostgreSQL's to_tsvector and to_tsquery for full-text search
        stmt = select(Intelligence).where(
            or_(
                Intelligence.raw_content.ilike(f"%{query}%"),
                Intelligence.processed_content.ilike(f"%{query}%")
            )
        )

        # Apply filters if provided
        if filters:
            if "status" in filters:
                stmt = stmt.where(Intelligence.processing_status == filters["status"])
            if "source_id" in filters:
                stmt = stmt.where(Intelligence.source_id == filters["source_id"])
            if "threat_id" in filters:
                stmt = stmt.where(Intelligence.threat_id == filters["threat_id"])
            if "min_confidence" in filters:
                stmt = stmt.where(Intelligence.confidence_score >= filters["min_confidence"])

        stmt = stmt.limit(limit).order_by(Intelligence.created_at.desc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def search_threats(
        db: AsyncSession,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Threat]:
        """
        Search threats using full-text search.

        Args:
            db: Database session
            query: Search query string
            filters: Optional filters (category, severity, etc.)
            limit: Maximum results to return

        Returns:
            List of matching threats
        """
        stmt = select(Threat).where(
            or_(
                Threat.title.ilike(f"%{query}%"),
                Threat.description.ilike(f"%{query}%")
            )
        )

        if filters:
            if "category" in filters:
                stmt = stmt.where(Threat.category == filters["category"])
            if "min_severity" in filters:
                stmt = stmt.where(Threat.severity >= filters["min_severity"])
            if "status" in filters:
                stmt = stmt.where(Threat.status == filters["status"])

        stmt = stmt.limit(limit).order_by(Threat.created_at.desc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def search_all(
        db: AsyncSession,
        query: str,
        limit_per_type: int = 50
    ) -> Dict[str, List]:
        """
        Search across all entity types.

        Args:
            db: Database session
            query: Search query string
            limit_per_type: Maximum results per entity type

        Returns:
            Dict with results for each entity type
        """
        results = {}

        # Search intelligence
        intelligence_results = await SearchService.search_intelligence(
            db, query, limit=limit_per_type
        )
        results["intelligence"] = intelligence_results

        # Search threats
        threat_results = await SearchService.search_threats(
            db, query, limit=limit_per_type
        )
        results["threats"] = threat_results

        # Search sources
        stmt = select(Source).where(
            or_(
                Source.name.ilike(f"%{query}%"),
                Source.url.ilike(f"%{query}%")
            )
        ).limit(limit_per_type)

        result = await db.execute(stmt)
        results["sources"] = list(result.scalars().all())

        return results

    @staticmethod
    async def advanced_intelligence_search(
        db: AsyncSession,
        text_query: Optional[str] = None,
        location: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_confidence: Optional[float] = None,
        status: Optional[str] = None,
        source_ids: Optional[List[int]] = None,
        limit: int = 100
    ) -> List[Intelligence]:
        """
        Advanced search with multiple criteria.

        Args:
            db: Database session
            text_query: Text to search for
            location: Location filter
            date_from: Start date filter
            date_to: End date filter
            min_confidence: Minimum confidence score
            status: Processing status filter
            source_ids: List of source IDs to filter by
            limit: Maximum results

        Returns:
            List of matching intelligence items
        """
        stmt = select(Intelligence)
        conditions = []

        if text_query:
            conditions.append(
                or_(
                    Intelligence.raw_content.ilike(f"%{text_query}%"),
                    Intelligence.processed_content.ilike(f"%{text_query}%")
                )
            )

        if location:
            # Search in AI analysis data for location
            conditions.append(
                Intelligence.ai_analysis_data.contains({"location": location})
            )

        if date_from:
            from datetime import datetime
            date_obj = datetime.fromisoformat(date_from)
            conditions.append(Intelligence.created_at >= date_obj)

        if date_to:
            from datetime import datetime
            date_obj = datetime.fromisoformat(date_to)
            conditions.append(Intelligence.created_at <= date_obj)

        if min_confidence is not None:
            conditions.append(Intelligence.confidence_score >= min_confidence)

        if status:
            conditions.append(Intelligence.processing_status == status)

        if source_ids:
            conditions.append(Intelligence.source_id.in_(source_ids))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.limit(limit).order_by(Intelligence.created_at.desc())

        result = await db.execute(stmt)
        return list(result.scalars().all())
