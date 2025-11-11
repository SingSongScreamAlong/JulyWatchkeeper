"""
Export Tasks

This module contains Celery tasks for data export.
"""

from celery import Task
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio
import os
import csv
import json

from src.core.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.models.export import Export, ExportFormat, ExportStatus
from src.models.intelligence import Intelligence
from src.models.threat import Threat
from src.models.source import Source
from src.services.export_service import ExportService
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


class ExportTask(Task):
    """Base task for export processing with error handling."""

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 2}
    retry_backoff = True


@celery_app.task(base=ExportTask, name="src.tasks.export_tasks.generate_export")
def generate_export(export_id: int) -> dict:
    """
    Generate an export file.

    Args:
        export_id: ID of the export request

    Returns:
        dict: Export generation result
    """
    logger.info(f"Generating export {export_id}")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_generate_export_async(export_id))
    return result


async def _generate_export_async(export_id: int) -> dict:
    """Async export generation."""
    async with AsyncSessionLocal() as session:
        try:
            # Get export request
            result = await session.execute(
                select(Export).where(Export.id == export_id)
            )
            export = result.scalar_one_or_none()

            if not export:
                logger.error(f"Export {export_id} not found")
                return {"status": "error", "message": "Export not found"}

            # Update status to processing
            export.status = ExportStatus.PROCESSING
            await session.commit()

            # Initialize export service
            export_service = ExportService()

            # Generate export based on resource type and format
            if export.resource_type == "intelligence":
                file_path = await export_service.export_intelligence(
                    export_format=export.export_format,
                    filters=export.filters or {}
                )
            elif export.resource_type == "threats":
                file_path = await export_service.export_threats(
                    export_format=export.export_format,
                    filters=export.filters or {}
                )
            elif export.resource_type == "sources":
                file_path = await export_service.export_sources(
                    export_format=export.export_format,
                    filters=export.filters or {}
                )
            else:
                raise ValueError(f"Unknown resource type: {export.resource_type}")

            # Get file size
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

            # Update export record
            export.status = ExportStatus.COMPLETED
            export.file_path = file_path
            export.file_size = file_size
            export.completed_at = datetime.utcnow()
            export.expires_at = datetime.utcnow() + timedelta(days=7)  # Expire in 7 days

            await session.commit()

            logger.info(f"Successfully generated export {export_id} at {file_path}")

            return {
                "status": "success",
                "export_id": export_id,
                "file_path": file_path,
                "file_size": file_size
            }

        except Exception as e:
            logger.error(f"Error generating export {export_id}: {str(e)}")

            # Update status to failed
            if export:
                export.status = ExportStatus.FAILED
                export.error_message = str(e)
                await session.commit()

            return {"status": "error", "export_id": export_id, "message": str(e)}


@celery_app.task(name="src.tasks.export_tasks.cleanup_old_exports")
def cleanup_old_exports() -> dict:
    """
    Clean up expired export files.

    Returns:
        dict: Cleanup result
    """
    logger.info("Cleaning up old exports")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_cleanup_old_exports_async())
    return result


async def _cleanup_old_exports_async() -> dict:
    """Async cleanup of expired exports."""
    async with AsyncSessionLocal() as session:
        try:
            # Get expired exports
            result = await session.execute(
                select(Export).where(
                    Export.expires_at <= datetime.utcnow(),
                    Export.status == ExportStatus.COMPLETED
                )
            )
            expired_exports = result.scalars().all()

            deleted_count = 0
            freed_bytes = 0

            for export in expired_exports:
                try:
                    # Delete file if it exists
                    if export.file_path and os.path.exists(export.file_path):
                        freed_bytes += export.file_size or 0
                        os.remove(export.file_path)
                        logger.info(f"Deleted export file: {export.file_path}")

                    # Delete database record
                    await session.delete(export)
                    deleted_count += 1

                except Exception as e:
                    logger.error(f"Error deleting export {export.id}: {str(e)}")

            await session.commit()

            logger.info(f"Cleaned up {deleted_count} expired exports, freed {freed_bytes} bytes")

            return {
                "status": "success",
                "deleted_count": deleted_count,
                "freed_bytes": freed_bytes
            }

        except Exception as e:
            logger.error(f"Error cleaning up old exports: {str(e)}")
            return {"status": "error", "message": str(e)}
