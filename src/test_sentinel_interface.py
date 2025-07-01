#!/usr/bin/env python3
"""
SENTINEL Interface Test Script
This script tests the integration between the SENTINEL mock interface and the WATCHKEEPER API.
It verifies API endpoints, WebSocket functionality, and data flow.
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta

import aiohttp
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("sentinel_test")

# Create FastAPI app
app = FastAPI(title="WATCHKEEPER API Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing only, in production specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections = []

# Sample data
intelligence_items = [
    {
        "id": str(uuid.uuid4()),
        "title": "Potential security threat in Berlin",
        "content": "Reports indicate increased suspicious activity near embassy district in Berlin. Local authorities have increased patrols in the area.",
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        "source": {
            "id": "news.dw",
            "name": "Deutsche Welle",
            "reliability": 0.85
        },
        "severity_assessment": {
            "score": 6,
            "confidence": 0.75
        },
        "mission_relevance": {
            "score": 7,
            "confidence": 0.8
        },
        "geo_data": {
            "coordinates": [
                {
                    "name": "Berlin Embassy District",
                    "latitude": 52.5163,
                    "longitude": 13.3779
                }
            ]
        },
        "language": "en"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Manifestation prévue à Paris",
        "content": "Une grande manifestation est prévue demain à Paris. Les autorités s'attendent à une participation massive.",
        "translated_content": "A large demonstration is planned for tomorrow in Paris. Authorities expect massive participation.",
        "original_language": "fr",
        "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
        "source": {
            "id": "news.lemonde",
            "name": "Le Monde",
            "reliability": 0.9
        },
        "severity_assessment": {
            "score": 4,
            "confidence": 0.8
        },
        "mission_relevance": {
            "score": 5,
            "confidence": 0.7
        },
        "geo_data": {
            "coordinates": [
                {
                    "name": "Paris",
                    "latitude": 48.8566,
                    "longitude": 2.3522
                }
            ]
        },
        "language": "fr",
        "ai_analysis": "This appears to be a planned demonstration that may disrupt transportation and create security concerns in central Paris."
    },
    {
        "id": str(uuid.uuid4()),
        "title": "High alert in Madrid after threat",
        "content": "Security forces in Madrid have raised alert levels following credible intelligence about a potential threat.",
        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        "source": {
            "id": "government.spain",
            "name": "Spanish Interior Ministry",
            "reliability": 0.95
        },
        "severity_assessment": {
            "score": 8,
            "confidence": 0.9
        },
        "mission_relevance": {
            "score": 9,
            "confidence": 0.85
        },
        "geo_data": {
            "coordinates": [
                {
                    "name": "Madrid",
                    "latitude": 40.4168,
                    "longitude": -3.7038
                }
            ]
        },
        "language": "en",
        "url": "https://interior.gob.es/alerts"
    }
]

# System status data
system_status = {
    "status": "operational",
    "uptime": 86400,  # 24 hours in seconds
    "version": "0.9.0",
    "collectors": {
        "active": 12,
        "total": 15
    },
    "processing": {
        "queue_size": 5,
        "processed_last_hour": 42,
        "processed_last_day": 1024
    },
    "accuracy": {
        "threat_level": 78,
        "threat_type": 72,
        "geographic": 85,
        "relevance": 76
    }
}

# Processing metrics
processing_metrics = [
    {"date": (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d"), "count": 950},
    {"date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"), "count": 1020},
    {"date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"), "count": 980},
    {"date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"), "count": 1100},
    {"date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"), "count": 1050},
    {"date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), "count": 1150},
    {"date": datetime.now().strftime("%Y-%m-%d"), "count": 500}
]

# API Routes

@app.get("/")
async def root():
    return {"message": "WATCHKEEPER API Test Server"}

@app.get("/api/intelligence/list")
async def get_intelligence_list():
    return intelligence_items

@app.get("/api/intelligence/{item_id}")
async def get_intelligence_item(item_id: str):
    for item in intelligence_items:
        if item["id"] == item_id:
            return item
    return JSONResponse(status_code=404, content={"message": "Item not found"})

class IntelligenceSubmission(BaseModel):
    title: str
    content: str
    source: str
    language: str = "en"
    coordinates: dict = None

@app.post("/api/intelligence/submit")
async def submit_intelligence(submission: IntelligenceSubmission):
    # Create new intelligence item
    new_item = {
        "id": str(uuid.uuid4()),
        "title": submission.title,
        "content": submission.content,
        "timestamp": datetime.now().isoformat(),
        "source": {
            "id": f"user.submission",
            "name": submission.source,
            "reliability": 0.7
        },
        "severity_assessment": {
            "score": 5,  # Default score
            "confidence": 0.6
        },
        "mission_relevance": {
            "score": 5,  # Default score
            "confidence": 0.6
        },
        "language": submission.language
    }
    
    # Add coordinates if provided
    if submission.coordinates:
        new_item["geo_data"] = {
            "coordinates": [submission.coordinates]
        }
    
    # Add to intelligence items
    intelligence_items.insert(0, new_item)
    
    # Broadcast to WebSocket clients
    await broadcast_intelligence_update(new_item)
    
    return {"message": "Intelligence submitted successfully", "id": new_item["id"]}

@app.get("/api/status")
async def get_status():
    return {
        "system": system_status,
        "processing_metrics": processing_metrics
    }

# WebSocket endpoint
@app.websocket("/ws/connect")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "status_update",
            "data": system_status
        })
        
        # Handle messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle ping
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                # Handle subscribe
                elif message.get("type") == "subscribe":
                    # In a real implementation, we would store subscriptions
                    # For this test, we just acknowledge
                    await websocket.send_json({
                        "type": "subscription_ack",
                        "topics": message.get("topics", [])
                    })
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

async def broadcast_intelligence_update(item):
    """Broadcast intelligence update to all connected clients"""
    if not active_connections:
        return
        
    for connection in active_connections:
        try:
            await connection.send_json({
                "type": "intelligence_update",
                "data": {
                    "item": item
                }
            })
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")

# Background task to simulate real-time updates
async def send_periodic_updates():
    """Send periodic updates to simulate real-time data"""
    while True:
        await asyncio.sleep(30)  # Send update every 30 seconds
        
        # Generate new intelligence item
        locations = [
            {"name": "London", "latitude": 51.5074, "longitude": -0.1278},
            {"name": "Rome", "latitude": 41.9028, "longitude": 12.4964},
            {"name": "Vienna", "latitude": 48.2082, "longitude": 16.3738},
            {"name": "Brussels", "latitude": 50.8503, "longitude": 4.3517}
        ]
        
        location = locations[int(time.time()) % len(locations)]
        
        new_item = {
            "id": str(uuid.uuid4()),
            "title": f"Situation update from {location['name']}",
            "content": f"This is an automated test update for {location['name']} generated at {datetime.now().isoformat()}",
            "timestamp": datetime.now().isoformat(),
            "source": {
                "id": "system.test",
                "name": "Test System",
                "reliability": 0.99
            },
            "severity_assessment": {
                "score": int(time.time() % 10),  # Random severity 0-9
                "confidence": 0.9
            },
            "mission_relevance": {
                "score": int((time.time() + 3) % 10),  # Random relevance 0-9
                "confidence": 0.9
            },
            "geo_data": {
                "coordinates": [location]
            },
            "language": "en"
        }
        
        # Add to intelligence items
        intelligence_items.insert(0, new_item)
        
        # Broadcast update
        await broadcast_intelligence_update(new_item)
        
        # Update system status
        system_status["processing"]["processed_last_hour"] += 1
        system_status["processing"]["processed_last_day"] += 1
        
        # Broadcast system status update
        for connection in active_connections:
            try:
                await connection.send_json({
                    "type": "status_update",
                    "data": system_status
                })
            except Exception as e:
                logger.error(f"Error broadcasting status update: {e}")

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    asyncio.create_task(send_periodic_updates())

# Mount static files for the SENTINEL mock interface
app.mount("/sentinel_mock", StaticFiles(directory="sentinel_mock"), name="sentinel_mock")

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
