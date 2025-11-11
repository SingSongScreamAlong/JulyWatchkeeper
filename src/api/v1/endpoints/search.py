"""
Search endpoints for WATCHKEEPER API
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any

from src.core.database import get_db
from src.services.search_service import SearchService
from src.middleware.rbac import get_current_active_user

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
async def search_all(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, le=100, description="Results per type"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Search across all entity types."""
    results = await SearchService.search_all(db, q, limit_per_type=limit)

    return {
        "query": q,
        "results": {
            "intelligence": [{"id": i.id, "raw_content": i.raw_content[:200]} for i in results["intelligence"]],
            "threats": [{"id": t.id, "title": t.title, "severity": t.severity} for t in results["threats"]],
            "sources": [{"id": s.id, "name": s.name, "url": s.url} for s in results["sources"]]
        },
        "counts": {
            "intelligence": len(results["intelligence"]),
            "threats": len(results["threats"]),
            "sources": len(results["sources"])
        }
    }


@router.get("/intelligence")
async def search_intelligence(
    q: str = Query(..., min_length=2, description="Search query"),
    status: Optional[str] = None,
    source_id: Optional[int] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Search intelligence items with filters."""
    filters = {}
    if status:
        filters["status"] = status
    if source_id:
        filters["source_id"] = source_id
    if min_confidence:
        filters["min_confidence"] = min_confidence

    results = await SearchService.search_intelligence(db, q, filters, limit)

    return {
        "query": q,
        "filters": filters,
        "count": len(results),
        "results": [
            {
                "id": item.id,
                "raw_content": item.raw_content[:200] if item.raw_content else "",
                "source_id": item.source_id,
                "confidence_score": item.confidence_score,
                "created_at": item.created_at
            }
            for item in results
        ]
    }


@router.get("/threats")
async def search_threats(
    q: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = None,
    min_severity: Optional[int] = Query(None, ge=0, le=10),
    status: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Search threats with filters."""
    filters = {}
    if category:
        filters["category"] = category
    if min_severity:
        filters["min_severity"] = min_severity
    if status:
        filters["status"] = status

    results = await SearchService.search_threats(db, q, filters, limit)

    return {
        "query": q,
        "filters": filters,
        "count": len(results),
        "results": [
            {
                "id": threat.id,
                "title": threat.title,
                "severity": threat.severity,
                "category": threat.category.value if threat.category else None,
                "status": threat.status.value if threat.status else None,
                "created_at": threat.created_at
            }
            for threat in results
        ]
    }


@router.get("/advanced")
async def advanced_search(
    text: Optional[str] = None,
    location: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    status: Optional[str] = None,
    source_ids: Optional[str] = Query(None, description="Comma-separated source IDs"),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Advanced intelligence search with multiple criteria."""
    # Parse source_ids if provided
    source_id_list = None
    if source_ids:
        source_id_list = [int(sid) for sid in source_ids.split(",")]

    results = await SearchService.advanced_intelligence_search(
        db,
        text_query=text,
        location=location,
        date_from=date_from,
        date_to=date_to,
        min_confidence=min_confidence,
        status=status,
        source_ids=source_id_list,
        limit=limit
    )

    return {
        "filters": {
            "text": text,
            "location": location,
            "date_from": date_from,
            "date_to": date_to,
            "min_confidence": min_confidence,
            "status": status,
            "source_ids": source_id_list
        },
        "count": len(results),
        "results": [
            {
                "id": item.id,
                "raw_content": item.raw_content[:200] if item.raw_content else "",
                "source_id": item.source_id,
                "confidence_score": item.confidence_score,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "created_at": item.created_at
            }
            for item in results
        ]
    }
