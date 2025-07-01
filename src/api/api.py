"""
REST API for WATCHKEEPER

This module provides a FastAPI-based REST API for the WATCHKEEPER intelligence platform.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Query, Path, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.utils.logger import get_logger
from src.utils.config import load_config
from src.storage.sqlite_storage import SQLiteStorage
from src.collectors.collector_manager import CollectorManager
from src.processors.ai_processor import AIProcessor
from src.processors.geo_processor import GeoProcessor
from src.processors.severity_processor import SeverityProcessor
from src.processors.relevance_processor import RelevanceProcessor
from src.processors.language_processor import LanguageProcessor

# Initialize logger
logger = get_logger("watchkeeper.api")

# Create FastAPI app
app = FastAPI(
    title="WATCHKEEPER API",
    description="REST API for the WATCHKEEPER intelligence platform",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
storage = None
collector_manager = None
ai_processor = None
geo_processor = None
severity_processor = None
relevance_processor = None
language_processor = None

# Pydantic models for API requests and responses
class IntelligenceItem(BaseModel):
    """Intelligence item model"""
    title: str = Field(..., description="Title of the intelligence item")
    content: str = Field(..., description="Content of the intelligence item")
    source: Dict[str, Any] = Field(..., description="Source information")
    url: Optional[str] = Field(None, description="URL of the intelligence item")
    published_date: Optional[str] = Field(None, description="Publication date of the intelligence item")
    language: Optional[str] = Field("en", description="Language of the intelligence item")
    locations: Optional[List[str]] = Field(None, description="Locations mentioned in the intelligence item")
    tags: Optional[List[str]] = Field(None, description="Tags for the intelligence item")

class ProcessedIntelligence(BaseModel):
    """Processed intelligence model"""
    id: str = Field(..., description="ID of the intelligence item")
    title: str = Field(..., description="Title of the intelligence item")
    content: str = Field(..., description="Content of the intelligence item")
    source: Dict[str, Any] = Field(..., description="Source information")
    url: Optional[str] = Field(None, description="URL of the intelligence item")
    published_date: Optional[str] = Field(None, description="Publication date of the intelligence item")
    storage_time: str = Field(..., description="Time when the item was stored")
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="AI analysis of the intelligence item")
    geo_data: Optional[Dict[str, Any]] = Field(None, description="Geographic data extracted from the intelligence item")
    severity_assessment: Optional[Dict[str, Any]] = Field(None, description="Severity assessment of the intelligence item")
    relevance_assessment: Optional[Dict[str, Any]] = Field(None, description="Missionary relevance assessment")
    language_data: Optional[Dict[str, Any]] = Field(None, description="Language data and translations")

class SearchQuery(BaseModel):
    """Search query model"""
    query: str = Field(..., description="Search query string")
    limit: int = Field(10, description="Maximum number of results to return")
    source_type: Optional[str] = Field(None, description="Filter by source type")
    min_severity: Optional[int] = Field(None, description="Minimum severity score")
    min_relevance: Optional[int] = Field(None, description="Minimum relevance score")
    start_date: Optional[str] = Field(None, description="Start date for filtering (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for filtering (YYYY-MM-DD)")

class ApiResponse(BaseModel):
    """Generic API response model"""
    status: str = Field(..., description="Status of the request (success or error)")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global storage, collector_manager, ai_processor, geo_processor, severity_processor, relevance_processor, language_processor
    
    try:
        # Load configuration
        config = get_config()
        
        # Initialize storage
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "intelligence.db")
        storage = SQLiteStorage(db_path)
        
        # Initialize processors
        ai_processor = AIProcessor()
        geo_processor = GeoProcessor()
        severity_processor = SeverityProcessor()
        relevance_processor = RelevanceProcessor()
        language_processor = LanguageProcessor()
        
        # Initialize collector manager
        collector_manager = CollectorManager()
        
        logger.info("API components initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing API components: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Shutting down WATCHKEEPER API")

@app.get("/", response_model=ApiResponse)
async def root():
    """Root endpoint"""
    return {
        "status": "success",
        "message": "WATCHKEEPER API is running",
        "data": {
            "version": "0.1.0",
            "name": "WATCHKEEPER Intelligence Platform"
        }
    }

@app.post("/intelligence", response_model=ApiResponse)
async def submit_intelligence(item: IntelligenceItem, background_tasks: BackgroundTasks):
    """
    Submit a new intelligence item
    
    The item will be processed and stored in the background.
    """
    try:
        # Convert to dict
        item_dict = item.dict()
        
        # Add timestamp
        item_dict["submission_time"] = datetime.now().isoformat()
        
        # Schedule background processing
        background_tasks.add_task(process_and_store_item, item_dict)
        
        return {
            "status": "success",
            "message": "Intelligence item submitted for processing",
            "data": {
                "received": True,
                "processing": "background"
            }
        }
    
    except Exception as e:
        logger.error(f"Error submitting intelligence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/intelligence/{item_id}", response_model=ApiResponse)
async def get_intelligence(item_id: str = Path(..., description="ID of the intelligence item")):
    """
    Get a specific intelligence item by ID
    """
    try:
        item = await storage.get_item_by_id(item_id)
        
        if not item:
            raise HTTPException(status_code=404, detail=f"Intelligence item {item_id} not found")
        
        return {
            "status": "success",
            "message": f"Retrieved intelligence item {item_id}",
            "data": item
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting intelligence item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/intelligence", response_model=ApiResponse)
async def list_intelligence(
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Maximum number of items to return")
):
    """
    List intelligence items with optional filtering
    """
    try:
        items = []
        
        # Get items by source type or date
        if source_type:
            items = await storage.get_items_by_source(source_type, limit)
        elif date:
            items = await storage.get_items_by_date(date)
        else:
            # Get recent items
            items = await storage.get_recent_items(limit)
        
        return {
            "status": "success",
            "message": f"Retrieved {len(items)} intelligence items",
            "data": items
        }
    
    except Exception as e:
        logger.error(f"Error listing intelligence items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=ApiResponse)
async def search_intelligence(query: SearchQuery):
    """
    Search for intelligence items
    """
    try:
        # Use the search_items method from SQLiteStorage
        items = await storage.search_items(query.query, query.limit)
        
        # Filter by source type if specified
        if query.source_type:
            items = [item for item in items if query.source_type.lower() in item["source"].lower()]
        
        # Filter by date range if specified
        if query.start_date or query.end_date:
            filtered_items = []
            
            for item in items:
                item_date = None
                
                # Try to parse the timestamp
                try:
                    if "timestamp" in item and item["timestamp"]:
                        item_date = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")).date()
                except:
                    continue
                
                if not item_date:
                    continue
                
                # Check if the item date is within the specified range
                if query.start_date:
                    start_date = datetime.fromisoformat(query.start_date).date()
                    if item_date < start_date:
                        continue
                
                if query.end_date:
                    end_date = datetime.fromisoformat(query.end_date).date()
                    if item_date > end_date:
                        continue
                
                filtered_items.append(item)
            
            items = filtered_items
        
        # Filter by severity (threat_level) if specified
        if query.min_severity is not None:
            items = [item for item in items if "threat_level" in item and 
                     item["threat_level"] >= query.min_severity]
        
        # Filter by relevance (missionary_relevance) if specified
        if query.min_relevance is not None:
            items = [item for item in items if "missionary_relevance" in item and 
                     item["missionary_relevance"] >= query.min_relevance]
        
        # Limit the number of results
        items = items[:query.limit]
        
        return {
            "status": "success",
            "message": f"Found {len(items)} matching intelligence items",
            "data": items
        }
    
    except Exception as e:
        logger.error(f"Error searching intelligence items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process", response_model=ApiResponse)
async def process_intelligence(item: IntelligenceItem):
    """
    Process an intelligence item without storing it
    
    This is useful for testing or one-off processing.
    """
    try:
        # Convert to dict
        item_dict = item.dict()
        
        # Process the item
        processed_item = await process_item(item_dict)
        
        return {
            "status": "success",
            "message": "Intelligence item processed",
            "data": processed_item
        }
    
    except Exception as e:
        logger.error(f"Error processing intelligence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", response_model=ApiResponse)
async def system_status():
    """
    Get system status information
    """
    try:
        # Get storage statistics
        # This is a simplified implementation - in production, we would have more detailed stats
        storage_stats = {
            "directory": storage.base_dir,
        }
        
        # Get processor status
        processor_stats = {
            "ai_processor": {
                "model": ai_processor.model_name,
                "last_process_time": ai_processor.last_process_time
            },
            "geo_processor": {
                "api": geo_processor.geocoding_api,
                "last_process_time": geo_processor.last_process_time
            },
            "severity_processor": {
                "last_process_time": severity_processor.last_process_time
            },
            "relevance_processor": {
                "last_process_time": relevance_processor.last_process_time
            },
            "language_processor": {
                "supported_languages": language_processor.supported_languages,
                "last_process_time": language_processor.last_process_time
            }
        }
        
        return {
            "status": "success",
            "message": "System status retrieved",
            "data": {
                "storage": storage_stats,
                "processors": processor_stats,
                "uptime": "N/A",  # In production, we would track actual uptime
                "version": "0.1.0"
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an intelligence item through all processors
    
    Args:
        item: Intelligence item to process
        
    Returns:
        Dict[str, Any]: Processed intelligence item
    """
    # Process language first to ensure English content for other processors
    processed_item = await language_processor.process(item)
    
    # Process with AI
    processed_item = await ai_processor.process(processed_item)
    
    # Process geographic information
    processed_item = await geo_processor.process(processed_item)
    
    # Process severity
    processed_item = await severity_processor.process(processed_item)
    
    # Process missionary relevance
    processed_item = await relevance_processor.process(processed_item)
    
    return processed_item

async def process_and_store_item(item: Dict[str, Any]) -> str:
    """
    Process an intelligence item and store it
    
    Args:
        item: Intelligence item to process
        
    Returns:
        str: ID of the stored item
    """
    # Process the item
    processed_item = await process_item(item)
    
    # Store the processed item
    item_id = await storage.store_item(processed_item)
    
    logger.info(f"Processed and stored intelligence item {item_id}")
    
    return item_id
