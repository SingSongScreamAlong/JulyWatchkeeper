"""
Main API server for WATCHKEEPER

This module integrates all API components and provides a unified server.
"""

import os
import asyncio
import uvicorn
from fastapi import FastAPI

from src.api.api import app as api_app
from src.api.websocket import setup_websocket_routes
from src.api.cache import cache
from src.utils.logger import get_logger
from src.utils.config import get_config, load_config

# Initialize logger
logger = get_logger("watchkeeper.api.server")

# Create FastAPI app
app = FastAPI(
    title="WATCHKEEPER Intelligence Platform",
    description="API server for the WATCHKEEPER intelligence platform",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    logger.info("Starting WATCHKEEPER API server")
    
    # Connect to Redis cache
    await cache.connect()
    
    # Log startup information
    logger.info("WATCHKEEPER API server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Shutting down WATCHKEEPER API server")
    
    # Disconnect from Redis cache
    await cache.disconnect()

# Mount the API router
app.mount("/api", api_app)

# Set up WebSocket routes
setup_websocket_routes(app)

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the API server
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    # Load configuration
    config_path = os.environ.get("WATCHKEEPER_CONFIG", "config.yaml")
    load_config(config_path)
    
    # Get server configuration
    config = get_config()
    server_config = config.get("api", {}).get("server", {})
    
    # Override with configuration if provided
    host = server_config.get("host", host)
    port = server_config.get("port", port)
    
    # Log server information
    logger.info(f"Starting WATCHKEEPER API server on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=server_config.get("reload", False)
    )

if __name__ == "__main__":
    run_server()
