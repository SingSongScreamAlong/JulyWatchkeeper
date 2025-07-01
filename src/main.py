#!/usr/bin/env python3
"""
WATCHKEEPER - FastAPI Application

This is the main FastAPI application for the WATCHKEEPER intelligence platform.
It provides API endpoints for intelligence collection, processing, and alerts.
"""

import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn
import psutil
import platform
from datetime import datetime

# Import API routers
from src.api.v1.api import api_router as api_v1_router

# Import WebSocket setup
from src.api.websocket import setup_websocket_routes

# Import core modules
from src.core.config import settings
from src.utils.logging import setup_logging, log
from src.core.security import get_api_key

# Create FastAPI app
app = FastAPI(
    title="WATCHKEEPER",
    description="AI-powered intelligence collection and processing engine for missionary operations",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
setup_logging()

# Include routers
app.include_router(api_v1_router, prefix="/api/v1", dependencies=[Depends(get_api_key)])

# Setup WebSocket routes
setup_websocket_routes(app)

# Custom docs endpoints (protected by API key)
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(api_key: str = Depends(get_api_key)):
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with basic information about the API."""
    return {
        "name": "WATCHKEEPER",
        "version": "1.0.0",
        "description": "AI-powered intelligence collection and processing engine",
        "status": "operational",
        "documentation": "/docs",
        "health": "/api/v1/health"
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Execute actions on application startup."""
    log.info("Starting WATCHKEEPER API server")
    log.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    log.info(f"Running on Mac mini: {platform.machine()} - {platform.processor()}")
    
    # Log system resources - optimized for Mac mini
    mem = psutil.virtual_memory()
    log.info(f"System memory: {mem.total / (1024 * 1024 * 1024):.2f} GB total, {mem.available / (1024 * 1024 * 1024):.2f} GB available")
    log.info(f"CPU cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")
    
    # Set resource limits appropriate for Mac mini
    # Adjust worker threads and connection pools based on available resources
    if mem.total < 8 * 1024 * 1024 * 1024:  # Less than 8GB RAM
        log.warning("Limited memory detected. Adjusting resource allocation for Mac mini.")
        # Resource adjustments would happen here in production

@app.on_event("shutdown")
async def shutdown_event():
    """Execute actions on application shutdown."""
    log.info("Shutting down WATCHKEEPER API server")

# Run the application directly when this file is executed
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=2,  # Reduced for Mac mini resources
    )
