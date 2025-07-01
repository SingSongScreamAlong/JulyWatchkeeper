"""
API Router for WATCHKEEPER v1

This module provides the main router for the v1 API.
"""

from fastapi import APIRouter

from src.api.v1.endpoints import health, threats, sources, intelligence

# Create the main API router for v1
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(threats.router, prefix="/threats", tags=["threats"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])
