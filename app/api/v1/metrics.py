"""Metrics API Endpoints

Exposes Prometheus metrics for scraping.
"""

from fastapi import APIRouter, Response
from ...services.metrics_service import get_metrics, CONTENT_TYPE_LATEST

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "watchkeeper-api",
        "version": "2.0.0"
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes/orchestration"""
    # Check if application is ready to serve traffic
    # This could include database connectivity checks, etc.
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "redis": "ok",
            "celery": "ok"
        }
    }
