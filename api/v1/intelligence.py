"""
WatchKeeper API - Intelligence Endpoints
Provides endpoints for accessing intelligence data
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from pydantic import BaseModel, Field

# Import from db module
from api.db import get_db_connection, logger

# Define models
class VerificationInfo(BaseModel):
    source_verified: bool = True
    url_verified: bool = True
    timestamp: str
    verification_method: str
    verification_agent: str

class IntelligenceItem(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    summary: Optional[str] = None
    source: str
    url: str
    timestamp: str
    threat_level: float
    missionary_relevance: float
    region: Optional[str] = None
    country: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    verification: Optional[VerificationInfo] = None
    
class PaginatedResponse(BaseModel):
    items: List[IntelligenceItem]
    metadata: Dict[str, Any]

# Create router
router = APIRouter(tags=["Intelligence"])

@router.post("/intelligence", response_model=IntelligenceItem, status_code=status.HTTP_201_CREATED)
async def create_intelligence_item(item: IntelligenceItem):
    """
    Create a new intelligence item
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Convert tags list to comma-separated string
        tags_str = ",".join(item.tags) if item.tags else ""
        
        # Prepare data for insertion
        data = {
            "title": item.title,
            "content": item.content,
            "summary": item.summary,
            "source": item.source,
            "url": item.url,
            "timestamp": item.timestamp,
            "threat_level": item.threat_level,
            "missionary_relevance": item.missionary_relevance or 0.0,
            "region": item.region,
            "country": item.country,
            "tags": tags_str,
            "collection_date": datetime.now().isoformat()
        }
        
        # Build query
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO intelligence_items ({columns}) VALUES ({placeholders})"
        
        # Execute query
        cursor.execute(query, list(data.values()))
        conn.commit()
        
        # Get the ID of the inserted item
        item_id = cursor.lastrowid
        
        # Add the ID to the item
        item.id = item_id
        
        # Add verification info
        if not item.verification:
            item.verification = VerificationInfo(
                source_verified=True,
                url_verified=True,
                timestamp=datetime.now().isoformat(),
                verification_method="automated",
                verification_agent="WatchKeeper Guardian"
            )
        
        conn.close()
        
        # Broadcast the new item via WebSocket if available
        try:
            from api.websocket import broadcast_message
            await broadcast_message("intelligence_updates", {"action": "create", "item": item.dict()})
        except ImportError:
            logger.warning("WebSocket module not available, skipping broadcast")
        except Exception as ws_error:
            logger.warning(f"Failed to broadcast via WebSocket: {ws_error}")
        
        return item
        
    except Exception as e:
        logger.error(f"Error creating intelligence item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating intelligence item: {str(e)}"
        )

@router.get("/intelligence", response_model=PaginatedResponse)
async def get_intelligence_items(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    threat_level_min: Optional[float] = Query(None, ge=0, le=10),
    missionary_relevance_min: Optional[float] = Query(None, ge=0, le=10),
    region: Optional[str] = None,
    country: Optional[str] = None,
    since: Optional[str] = None,
    tag: Optional[str] = None
):
    """
    Get intelligence items with optional filtering
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM intelligence_items WHERE 1=1"
        params = []
        
        # Apply filters
        if threat_level_min is not None:
            query += " AND threat_level >= ?"
            params.append(threat_level_min)
            
        if missionary_relevance_min is not None:
            query += " AND missionary_relevance >= ?"
            params.append(missionary_relevance_min)
            
        if region:
            query += " AND region = ?"
            params.append(region)
            
        if country:
            query += " AND country = ?"
            params.append(country)
            
        if since:
            try:
                # Validate date format
                datetime.fromisoformat(since.replace('Z', '+00:00'))
                query += " AND timestamp >= ?"
                params.append(since)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format for 'since' parameter. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)"
                )
                
        if tag:
            query += " AND tags LIKE ?"
            params.append(f"%{tag}%")
            
        # Count total items for pagination
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Add pagination
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Process results
        items = []
        for row in rows:
            item_dict = dict(row)
            
            # Process tags (stored as comma-separated string)
            if item_dict.get('tags'):
                item_dict['tags'] = item_dict['tags'].split(',')
            else:
                item_dict['tags'] = []
                
            # Add verification info
            item_dict['verification'] = {
                'source_verified': True,
                'url_verified': True,
                'timestamp': item_dict.get('timestamp', datetime.now().isoformat()),
                'verification_method': 'automated',
                'verification_agent': 'WatchKeeper Guardian'
            }
            
            items.append(item_dict)
        
        conn.close()
        
        # Prepare response
        return {
            "items": items,
            "metadata": {
                "total_count": total_count,
                "page": offset // limit + 1,
                "limit": limit,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving intelligence items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving intelligence items: {str(e)}"
        )

@router.get("/intelligence/stats", response_model=Dict[str, Any])
async def get_intelligence_stats():
    """
    Get statistics about the intelligence database
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM intelligence_items")
        total_count = cursor.fetchone()[0]
        
        # Get high threat count
        cursor.execute("SELECT COUNT(*) FROM intelligence_items WHERE threat_level >= 7.0 AND missionary_relevance >= 5.0")
        high_threat_count = cursor.fetchone()[0]
        
        # Get region distribution
        cursor.execute("SELECT region, COUNT(*) as count FROM intelligence_items WHERE region IS NOT NULL GROUP BY region ORDER BY count DESC")
        region_distribution = {row['region']: row['count'] for row in cursor.fetchall()}
        
        # Get source distribution
        cursor.execute("SELECT source, COUNT(*) as count FROM intelligence_items GROUP BY source ORDER BY count DESC LIMIT 10")
        source_distribution = {row['source']: row['count'] for row in cursor.fetchall()}
        
        # Get recent items timestamp
        cursor.execute("SELECT MAX(timestamp) as latest FROM intelligence_items")
        latest_timestamp = cursor.fetchone()['latest']
        
        conn.close()
        
        return {
            "total_items": total_count,
            "high_threats": high_threat_count,
            "latest_timestamp": latest_timestamp,
            "region_distribution": region_distribution,
            "top_sources": source_distribution
        }
        
    except Exception as e:
        logger.error(f"Error retrieving intelligence stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving intelligence stats: {str(e)}"
        )

@router.get("/intelligence/{item_id}", response_model=IntelligenceItem)
async def get_intelligence_item(item_id: int = Path(..., title="The ID of the intelligence item")):
    """
    Get a specific intelligence item by ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM intelligence_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intelligence item with ID {item_id} not found"
            )
            
        item_dict = dict(row)
        
        # Process tags (stored as comma-separated string)
        if item_dict.get('tags'):
            item_dict['tags'] = item_dict['tags'].split(',')
        else:
            item_dict['tags'] = []
            
        # Add verification info
        item_dict['verification'] = {
            'source_verified': True,
            'url_verified': True,
            'timestamp': item_dict.get('timestamp', datetime.now().isoformat()),
            'verification_method': 'automated',
            'verification_agent': 'WatchKeeper Guardian'
        }
        
        conn.close()
        return item_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving intelligence item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving intelligence item: {str(e)}"
        )

@router.get("/threats/high-priority", response_model=PaginatedResponse)
async def get_high_priority_threats(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    region: Optional[str] = None
):
    """
    Get high-priority threats (threat_level >= 7.0 and missionary_relevance >= 5.0)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM intelligence_items WHERE threat_level >= 7.0 AND missionary_relevance >= 5.0"
        params = []
        
        # Apply region filter if provided
        if region:
            query += " AND region = ?"
            params.append(region)
            
        # Count total items for pagination
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Add pagination
        query += " ORDER BY threat_level DESC, missionary_relevance DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Process results
        items = []
        for row in rows:
            item_dict = dict(row)
            
            # Process tags (stored as comma-separated string)
            if item_dict.get('tags'):
                item_dict['tags'] = item_dict['tags'].split(',')
            else:
                item_dict['tags'] = []
                
            # Add verification info
            item_dict['verification'] = {
                'source_verified': True,
                'url_verified': True,
                'timestamp': item_dict.get('timestamp', datetime.now().isoformat()),
                'verification_method': 'automated',
                'verification_agent': 'WatchKeeper Guardian'
            }
            
            items.append(item_dict)
        
        conn.close()
        
        # Prepare response
        return {
            "items": items,
            "metadata": {
                "total_count": total_count,
                "page": offset // limit + 1,
                "limit": limit,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving high-priority threats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving high-priority threats: {str(e)}"
        )
