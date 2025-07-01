"""
Health Check Endpoint for WATCHKEEPER

This module provides health check endpoints for monitoring the application status.
"""

import platform
import time
from datetime import datetime
import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.config import settings
from src.utils.logging import logger

router = APIRouter()


@router.get("/", summary="Health Check")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        dict: Basic health status with timestamp
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/system", summary="System Health")
async def system_health():
    """
    System health check with resource usage information.
    
    Returns:
        dict: System health information including CPU, memory, and disk usage
    """
    # Get system information
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get process information
    process = psutil.Process()
    process_memory = process.memory_info()
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": cpu_percent,
            "memory_total_mb": memory.total / (1024 * 1024),
            "memory_available_mb": memory.available / (1024 * 1024),
            "memory_percent": memory.percent,
            "disk_total_gb": disk.total / (1024 * 1024 * 1024),
            "disk_free_gb": disk.free / (1024 * 1024 * 1024),
            "disk_percent": disk.percent
        },
        "process": {
            "memory_rss_mb": process_memory.rss / (1024 * 1024),
            "memory_vms_mb": process_memory.vms / (1024 * 1024),
            "threads": process.num_threads(),
            "uptime_seconds": time.time() - process.create_time()
        },
        "config": {
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "workers": settings.WORKERS
        }
    }


@router.get("/db", summary="Database Health")
async def db_health(db: AsyncSession = Depends(get_db)):
    """
    Database health check.
    
    Args:
        db: Database session
    
    Returns:
        dict: Database connection status
    """
    start_time = time.time()
    try:
        # Execute a simple query to check database connection
        query = "SELECT 1"
        await db.execute(query)
        
        # Calculate query execution time
        execution_time = time.time() - start_time
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "connected": True,
                "execution_time_ms": round(execution_time * 1000, 2)
            }
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "connected": False,
                "error": str(e)
            }
        }
