"""
Intelligence Processing Tasks

This module contains Celery tasks for processing intelligence items.
"""

from celery import Task
from datetime import datetime
from typing import Optional
import asyncio

from src.core.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.models.intelligence import Intelligence, ProcessingStatus
from src.processors.ai_processor import AIProcessor
from src.processors.severity_processor import SeverityProcessor
from src.processors.relevance_processor import RelevanceProcessor
from src.processors.geo_processor import GeoProcessor
from src.processors.language_processor import LanguageProcessor
from src.tasks.alert_tasks import check_and_create_alert
from sqlalchemy import select, update
import logging

logger = logging.getLogger(__name__)


class IntelligenceTask(Task):
    """Base task for intelligence processing with error handling."""

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True


@celery_app.task(base=IntelligenceTask, name="src.tasks.intelligence_tasks.process_intelligence_item")
def process_intelligence_item(intelligence_id: int) -> dict:
    """
    Process a single intelligence item through the full pipeline.

    Args:
        intelligence_id: ID of the intelligence item to process

    Returns:
        dict: Processing result with status and metadata
    """
    logger.info(f"Processing intelligence item {intelligence_id}")

    # Run async processing in event loop
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If loop is already running, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_process_intelligence_async(intelligence_id))
    return result


async def _process_intelligence_async(intelligence_id: int) -> dict:
    """Async processing of intelligence item."""
    async with AsyncSessionLocal() as session:
        try:
            # Get intelligence item
            result = await session.execute(
                select(Intelligence).where(Intelligence.id == intelligence_id)
            )
            item = result.scalar_one_or_none()

            if not item:
                logger.error(f"Intelligence item {intelligence_id} not found")
                return {"status": "error", "message": "Item not found"}

            # Update status to processing
            item.processing_status = ProcessingStatus.PROCESSING
            await session.commit()

            start_time = datetime.utcnow()

            # Initialize processors
            ai_processor = AIProcessor()
            severity_processor = SeverityProcessor()
            relevance_processor = RelevanceProcessor()
            geo_processor = GeoProcessor()
            language_processor = LanguageProcessor()

            # Process through pipeline
            # 1. Language detection and translation if needed
            processed_item = await language_processor.process(item)

            # 2. AI analysis (summarization, classification, etc.)
            processed_item = await ai_processor.process(processed_item)

            # 3. Geographic extraction
            processed_item = await geo_processor.process(processed_item)

            # 4. Severity scoring
            processed_item = await severity_processor.process(processed_item)

            # 5. Relevance assessment
            processed_item = await relevance_processor.process(processed_item)

            # Update processing metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            item.processing_time = processing_time
            item.processing_status = ProcessingStatus.COMPLETED
            item.processed_at = datetime.utcnow()

            await session.commit()

            logger.info(f"Successfully processed intelligence item {intelligence_id} in {processing_time:.2f}s")

            # Check if alert should be created
            await check_and_create_alert.delay(intelligence_id)

            return {
                "status": "success",
                "intelligence_id": intelligence_id,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"Error processing intelligence item {intelligence_id}: {str(e)}")

            # Update status to failed
            await session.execute(
                update(Intelligence)
                .where(Intelligence.id == intelligence_id)
                .values(
                    processing_status=ProcessingStatus.FAILED,
                    error_message=str(e)
                )
            )
            await session.commit()

            return {
                "status": "error",
                "intelligence_id": intelligence_id,
                "message": str(e)
            }


@celery_app.task(name="src.tasks.intelligence_tasks.process_pending_batch")
def process_pending_batch(batch_size: int = 10) -> dict:
    """
    Process a batch of pending intelligence items.

    Args:
        batch_size: Number of items to process in this batch

    Returns:
        dict: Batch processing result
    """
    logger.info(f"Processing batch of {batch_size} pending intelligence items")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_process_pending_batch_async(batch_size))
    return result


async def _process_pending_batch_async(batch_size: int) -> dict:
    """Async batch processing of pending items."""
    async with AsyncSessionLocal() as session:
        try:
            # Get pending items
            result = await session.execute(
                select(Intelligence)
                .where(Intelligence.processing_status == ProcessingStatus.PENDING)
                .limit(batch_size)
            )
            pending_items = result.scalars().all()

            if not pending_items:
                logger.info("No pending intelligence items to process")
                return {"status": "success", "processed_count": 0}

            # Queue each item for processing
            for item in pending_items:
                process_intelligence_item.delay(item.id)

            logger.info(f"Queued {len(pending_items)} items for processing")

            return {
                "status": "success",
                "queued_count": len(pending_items)
            }

        except Exception as e:
            logger.error(f"Error processing pending batch: {str(e)}")
            return {"status": "error", "message": str(e)}


@celery_app.task(name="src.tasks.intelligence_tasks.reprocess_failed")
def reprocess_failed(hours_ago: int = 24) -> dict:
    """
    Reprocess intelligence items that failed in the last N hours.

    Args:
        hours_ago: Look back this many hours for failed items

    Returns:
        dict: Reprocessing result
    """
    logger.info(f"Reprocessing failed items from last {hours_ago} hours")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_reprocess_failed_async(hours_ago))
    return result


async def _reprocess_failed_async(hours_ago: int) -> dict:
    """Async reprocessing of failed items."""
    async with AsyncSessionLocal() as session:
        try:
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_ago)

            # Get failed items
            result = await session.execute(
                select(Intelligence)
                .where(
                    Intelligence.processing_status == ProcessingStatus.FAILED,
                    Intelligence.updated_at >= cutoff_time
                )
            )
            failed_items = result.scalars().all()

            if not failed_items:
                logger.info(f"No failed items in last {hours_ago} hours")
                return {"status": "success", "reprocessed_count": 0}

            # Reset status to pending and queue for processing
            for item in failed_items:
                item.processing_status = ProcessingStatus.PENDING
                item.error_message = None
                await session.commit()
                process_intelligence_item.delay(item.id)

            logger.info(f"Queued {len(failed_items)} failed items for reprocessing")

            return {
                "status": "success",
                "reprocessed_count": len(failed_items)
            }

        except Exception as e:
            logger.error(f"Error reprocessing failed items: {str(e)}")
            return {"status": "error", "message": str(e)}
