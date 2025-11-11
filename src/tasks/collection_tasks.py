"""
Collection Tasks

This module contains Celery tasks for intelligence collection.
"""

from celery import Task
from datetime import datetime
from typing import Dict, Any
import asyncio

from src.core.celery_app import celery_app
from src.collectors.collector_manager import CollectorManager
import logging

logger = logging.getLogger(__name__)


class CollectionTask(Task):
    """Base task for collection processing."""

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 2}
    retry_backoff = True


@celery_app.task(base=CollectionTask, name="src.tasks.collection_tasks.collect_intelligence")
def collect_intelligence() -> dict:
    """
    Run intelligence collection from all active sources.

    Returns:
        dict: Collection result
    """
    logger.info("Starting intelligence collection")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_collect_intelligence_async())
    return result


async def _collect_intelligence_async() -> dict:
    """Async intelligence collection."""
    try:
        # Initialize collector manager
        collector_manager = CollectorManager()

        # Run collection
        results = await collector_manager.collect_all()

        total_collected = sum(r.get("items_collected", 0) for r in results.values())
        total_errors = sum(r.get("errors", 0) for r in results.values())

        logger.info(f"Collection complete: {total_collected} items collected, {total_errors} errors")

        return {
            "status": "success",
            "total_collected": total_collected,
            "total_errors": total_errors,
            "collectors": results
        }

    except Exception as e:
        logger.error(f"Error during intelligence collection: {str(e)}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=CollectionTask, name="src.tasks.collection_tasks.collect_from_source")
def collect_from_source(source_id: int) -> dict:
    """
    Collect intelligence from a specific source.

    Args:
        source_id: ID of the source to collect from

    Returns:
        dict: Collection result
    """
    logger.info(f"Collecting from source {source_id}")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_collect_from_source_async(source_id))
    return result


async def _collect_from_source_async(source_id: int) -> dict:
    """Async collection from specific source."""
    try:
        from src.core.database import AsyncSessionLocal
        from src.models.source import Source
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            # Get source
            result = await session.execute(
                select(Source).where(Source.id == source_id)
            )
            source = result.scalar_one_or_none()

            if not source:
                logger.error(f"Source {source_id} not found")
                return {"status": "error", "message": "Source not found"}

            if not source.is_active:
                logger.warning(f"Source {source_id} is not active")
                return {"status": "skipped", "message": "Source not active"}

            # Initialize appropriate collector based on source type
            collector_manager = CollectorManager()

            # Collect from this source
            items_collected = await collector_manager.collect_from_source(source)

            logger.info(f"Collected {items_collected} items from source {source_id}")

            return {
                "status": "success",
                "source_id": source_id,
                "items_collected": items_collected
            }

    except Exception as e:
        logger.error(f"Error collecting from source {source_id}: {str(e)}")
        return {"status": "error", "source_id": source_id, "message": str(e)}
