"""
API Router for WATCHKEEPER v1

This module provides the main router for the v1 API.
"""

from fastapi import APIRouter

from src.api.v1.endpoints import (
    health,
    threats,
    sources,
    intelligence,
    auth,
    users,
    roles,
    alerts,
    exports,
    analytics,
    search,
    verification
)

# Create the main API router for v1
api_router = APIRouter()

# Include all endpoint routers
# Core endpoints
api_router.include_router(health.router)
api_router.include_router(intelligence.router)
api_router.include_router(threats.router)
api_router.include_router(sources.router)

# Authentication & User Management
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(roles.permission_router)

# Alert & Notification System
api_router.include_router(alerts.router)

# Export System
api_router.include_router(exports.router)

# Analytics & Metrics
api_router.include_router(analytics.router)

# Advanced Search
api_router.include_router(search.router)

# Verification & Consensus
api_router.include_router(verification.router)
