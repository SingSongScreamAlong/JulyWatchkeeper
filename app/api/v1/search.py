"""Search API Endpoints

Advanced search across all WATCHKEEPER data using Elasticsearch.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from ...services.search_service import get_search_service
from ...core.auth import get_current_user
from ...models.user import User

router = APIRouter()


class SearchQuery(BaseModel):
    """Search query parameters"""
    query: str
    filters: Optional[dict] = None
    from_: int = 0
    size: int = 20


class SearchFilters(BaseModel):
    """Advanced search filters"""
    source: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    min_threat_level: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    near_location: Optional[dict] = None


@router.get("/search/intelligence")
async def search_intelligence(
    q: str = Query(..., description="Search query"),
    source: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    min_threat: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    from_: int = Query(0, alias="from"),
    size: int = Query(20, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Search intelligence items with advanced filters

    - **q**: Search query (searches title, content, keywords)
    - **source**: Filter by source name
    - **category**: Filter by category
    - **region**: Filter by region
    - **min_threat**: Minimum threat level (1-10)
    - **date_from**: Start date (ISO format)
    - **date_to**: End date (ISO format)
    - **from**: Pagination offset
    - **size**: Results per page (max 100)
    """
    search_service = get_search_service()

    filters = {}
    if source:
        filters['source'] = source
    if category:
        filters['category'] = category
    if region:
        filters['region'] = region
    if min_threat:
        filters['min_threat_level'] = min_threat
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to

    results = search_service.search_intelligence(
        query=q,
        filters=filters if filters else None,
        from_=from_,
        size=size
    )

    return results


@router.get("/search/all")
async def search_all(
    q: str = Query(..., description="Search query"),
    from_: int = Query(0, alias="from"),
    size: int = Query(20, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Search across all data types (intelligence, incidents, alerts, personnel)

    Returns results from all indices ranked by relevance.
    """
    search_service = get_search_service()

    results = search_service.search_all(
        query=q,
        from_=from_,
        size=size
    )

    return results


@router.get("/search/suggestions")
async def get_search_suggestions(
    prefix: str = Query(..., min_length=2),
    field: str = Query('title', regex='^(title|content)$'),
    current_user: User = Depends(get_current_user)
):
    """
    Get search suggestions based on prefix

    - **prefix**: Prefix to search for (minimum 2 characters)
    - **field**: Field to get suggestions from (title or content)
    """
    search_service = get_search_service()

    suggestions = search_service.get_suggestions(prefix, field)

    return {"suggestions": suggestions}


@router.get("/search/trending")
async def get_trending_terms(
    days: int = Query(7, ge=1, le=30),
    size: int = Query(10, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Get trending terms from recent intelligence

    - **days**: Number of days to analyze (1-30)
    - **size**: Number of terms to return (max 50)
    """
    search_service = get_search_service()

    terms = search_service.get_trending_terms(days, size)

    return {"trending_terms": terms, "period_days": days}


@router.get("/search/aggregations/{index_type}/{field}")
async def get_field_aggregations(
    index_type: str,
    field: str,
    size: int = Query(10, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Get aggregation counts for a field

    - **index_type**: Type of index (intelligence, incidents, alerts, personnel)
    - **field**: Field to aggregate (e.g., source, category, region)
    - **size**: Number of top values to return (max 50)
    """
    valid_indices = ['intelligence', 'incidents', 'alerts', 'personnel', 'briefings']

    if index_type not in valid_indices:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid index type. Must be one of: {', '.join(valid_indices)}"
        )

    search_service = get_search_service()

    aggregations = search_service.aggregate_by_field(index_type, field, size)

    return {
        "index_type": index_type,
        "field": field,
        "aggregations": aggregations
    }


@router.get("/search/geospatial")
async def search_by_location(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    distance: str = Query('50km', regex=r'^\d+(km|mi)$'),
    q: Optional[str] = None,
    from_: int = Query(0, alias="from"),
    size: int = Query(20, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Search intelligence items near a location

    - **lat**: Latitude (-90 to 90)
    - **lon**: Longitude (-180 to 180)
    - **distance**: Search radius (e.g., '50km', '30mi')
    - **q**: Optional text query
    - **from**: Pagination offset
    - **size**: Results per page (max 100)
    """
    search_service = get_search_service()

    filters = {
        'near_location': {
            'lat': lat,
            'lon': lon,
            'distance': distance
        }
    }

    results = search_service.search_intelligence(
        query=q or '',
        filters=filters,
        from_=from_,
        size=size
    )

    return results


@router.post("/search/advanced")
async def advanced_search(
    search_query: SearchQuery,
    current_user: User = Depends(get_current_user)
):
    """
    Advanced search with complex filters

    POST body example:
    ```json
    {
      "query": "security threat",
      "filters": {
        "source": "reuters",
        "min_threat_level": 7,
        "region": "Middle East",
        "date_from": "2024-01-01"
      },
      "from_": 0,
      "size": 20
    }
    ```
    """
    search_service = get_search_service()

    results = search_service.search_intelligence(
        query=search_query.query,
        filters=search_query.filters,
        from_=search_query.from_,
        size=search_query.size
    )

    return results


@router.post("/search/reindex")
async def trigger_reindex(
    index_type: str = Query(..., regex='^(intelligence|incidents|alerts|personnel|all)$'),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger re-indexing of data (admin only)

    - **index_type**: Type to reindex (intelligence, incidents, alerts, personnel, or all)

    Note: This can take time for large datasets.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # This would trigger a Celery task to reindex
    # For now, return acknowledgment
    return {
        "status": "reindex_triggered",
        "index_type": index_type,
        "message": f"Reindexing {index_type} in background"
    }


@router.get("/search/stats")
async def get_search_stats(
    current_user: User = Depends(get_current_user)
):
    """Get search index statistics"""
    search_service = get_search_service()

    stats = {}

    for index_name, index_id in search_service.indices.items():
        try:
            index_stats = search_service.es.count(index=index_id)
            stats[index_name] = {
                'document_count': index_stats['count']
            }
        except Exception as e:
            stats[index_name] = {'error': str(e)}

    return {"indices": stats}
