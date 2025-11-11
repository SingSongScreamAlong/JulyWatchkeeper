"""
Analytics Tasks

This module contains Celery tasks for analytics and metrics generation.
"""

from celery import Task
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

from src.core.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.models.analytics import AnalyticsMetric, SystemHealth
from src.models.intelligence import Intelligence, ProcessingStatus
from src.models.threat import Threat
from src.models.alert import Alert, AlertStatus
from sqlalchemy import select, func, and_
import logging
import psutil
import aiohttp

logger = logging.getLogger(__name__)


class AnalyticsTask(Task):
    """Base task for analytics processing."""

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 2}
    retry_backoff = True


@celery_app.task(base=AnalyticsTask, name="src.tasks.analytics_tasks.generate_daily_metrics")
def generate_daily_metrics() -> dict:
    """
    Generate daily analytics metrics.

    Returns:
        dict: Metrics generation result
    """
    logger.info("Generating daily metrics")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_generate_daily_metrics_async())
    return result


async def _generate_daily_metrics_async() -> dict:
    """Async daily metrics generation."""
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.utcnow()
            yesterday = now - timedelta(days=1)

            metrics_created = 0

            # Count intelligence items created today
            result = await session.execute(
                select(func.count(Intelligence.id)).where(
                    Intelligence.created_at >= yesterday
                )
            )
            intelligence_count = result.scalar() or 0

            metric = AnalyticsMetric(
                metric_name="intelligence_items_created",
                metric_category="usage",
                value=intelligence_count,
                dimensions={"period": "daily"},
                timestamp=now
            )
            session.add(metric)
            metrics_created += 1

            # Count processed intelligence items
            result = await session.execute(
                select(func.count(Intelligence.id)).where(
                    and_(
                        Intelligence.processed_at >= yesterday,
                        Intelligence.processing_status == ProcessingStatus.COMPLETED
                    )
                )
            )
            processed_count = result.scalar() or 0

            metric = AnalyticsMetric(
                metric_name="intelligence_items_processed",
                metric_category="performance",
                value=processed_count,
                dimensions={"period": "daily"},
                timestamp=now
            )
            session.add(metric)
            metrics_created += 1

            # Average processing time
            result = await session.execute(
                select(func.avg(Intelligence.processing_time)).where(
                    and_(
                        Intelligence.processed_at >= yesterday,
                        Intelligence.processing_status == ProcessingStatus.COMPLETED
                    )
                )
            )
            avg_processing_time = result.scalar() or 0

            metric = AnalyticsMetric(
                metric_name="avg_processing_time",
                metric_category="performance",
                value=avg_processing_time,
                dimensions={"period": "daily", "unit": "seconds"},
                timestamp=now
            )
            session.add(metric)
            metrics_created += 1

            # Count threats by severity
            result = await session.execute(
                select(Threat.severity, func.count(Threat.id))
                .where(Threat.created_at >= yesterday)
                .group_by(Threat.severity)
            )
            threats_by_severity = result.all()

            for severity, count in threats_by_severity:
                metric = AnalyticsMetric(
                    metric_name="threats_created",
                    metric_category="threat",
                    value=count,
                    dimensions={"period": "daily", "severity": str(severity)},
                    timestamp=now
                )
                session.add(metric)
                metrics_created += 1

            # Count alerts created
            result = await session.execute(
                select(func.count(Alert.id)).where(
                    Alert.created_at >= yesterday
                )
            )
            alerts_count = result.scalar() or 0

            metric = AnalyticsMetric(
                metric_name="alerts_created",
                metric_category="usage",
                value=alerts_count,
                dimensions={"period": "daily"},
                timestamp=now
            )
            session.add(metric)
            metrics_created += 1

            # Count resolved alerts
            result = await session.execute(
                select(func.count(Alert.id)).where(
                    and_(
                        Alert.resolved_at >= yesterday,
                        Alert.status == AlertStatus.RESOLVED
                    )
                )
            )
            resolved_count = result.scalar() or 0

            metric = AnalyticsMetric(
                metric_name="alerts_resolved",
                metric_category="usage",
                value=resolved_count,
                dimensions={"period": "daily"},
                timestamp=now
            )
            session.add(metric)
            metrics_created += 1

            await session.commit()

            logger.info(f"Generated {metrics_created} daily metrics")

            return {
                "status": "success",
                "metrics_created": metrics_created
            }

        except Exception as e:
            logger.error(f"Error generating daily metrics: {str(e)}")
            return {"status": "error", "message": str(e)}


@celery_app.task(base=AnalyticsTask, name="src.tasks.analytics_tasks.check_system_health")
def check_system_health() -> dict:
    """
    Check system health and record metrics.

    Returns:
        dict: Health check result
    """
    logger.info("Checking system health")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(_check_system_health_async())
    return result


async def _check_system_health_async() -> dict:
    """Async system health check."""
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.utcnow()
            checks_performed = 0

            # Check database
            try:
                start = datetime.utcnow()
                await session.execute(select(1))
                response_time = (datetime.utcnow() - start).total_seconds() * 1000

                health = SystemHealth(
                    component="database",
                    status="healthy" if response_time < 100 else "degraded",
                    response_time_ms=response_time,
                    error_rate=0.0,
                    checked_at=now
                )
                session.add(health)
                checks_performed += 1

            except Exception as e:
                health = SystemHealth(
                    component="database",
                    status="down",
                    error_rate=1.0,
                    error_message=str(e),
                    checked_at=now
                )
                session.add(health)
                checks_performed += 1

            # Check Redis (if configured)
            try:
                import redis
                import os
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                r = redis.from_url(redis_url, socket_connect_timeout=2)
                start = datetime.utcnow()
                r.ping()
                response_time = (datetime.utcnow() - start).total_seconds() * 1000

                health = SystemHealth(
                    component="redis",
                    status="healthy" if response_time < 50 else "degraded",
                    response_time_ms=response_time,
                    error_rate=0.0,
                    checked_at=now
                )
                session.add(health)
                checks_performed += 1

            except Exception as e:
                health = SystemHealth(
                    component="redis",
                    status="down",
                    error_rate=1.0,
                    error_message=str(e),
                    checked_at=now
                )
                session.add(health)
                checks_performed += 1

            # Check Ollama
            try:
                import os
                ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                async with aiohttp.ClientSession() as client:
                    start = datetime.utcnow()
                    async with client.get(f"{ollama_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        response_time = (datetime.utcnow() - start).total_seconds() * 1000
                        if resp.status == 200:
                            health = SystemHealth(
                                component="ollama",
                                status="healthy" if response_time < 1000 else "degraded",
                                response_time_ms=response_time,
                                error_rate=0.0,
                                checked_at=now
                            )
                        else:
                            health = SystemHealth(
                                component="ollama",
                                status="degraded",
                                response_time_ms=response_time,
                                error_rate=0.5,
                                error_message=f"HTTP {resp.status}",
                                checked_at=now
                            )
                        session.add(health)
                        checks_performed += 1

            except Exception as e:
                health = SystemHealth(
                    component="ollama",
                    status="down",
                    error_rate=1.0,
                    error_message=str(e),
                    checked_at=now
                )
                session.add(health)
                checks_performed += 1

            # System resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            health = SystemHealth(
                component="system_cpu",
                status="healthy" if cpu_percent < 80 else "degraded",
                response_time_ms=cpu_percent,
                metadata={"cpu_percent": cpu_percent},
                checked_at=now
            )
            session.add(health)
            checks_performed += 1

            health = SystemHealth(
                component="system_memory",
                status="healthy" if memory.percent < 85 else "degraded",
                response_time_ms=memory.percent,
                metadata={
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent": memory.percent
                },
                checked_at=now
            )
            session.add(health)
            checks_performed += 1

            await session.commit()

            logger.info(f"Performed {checks_performed} system health checks")

            return {
                "status": "success",
                "checks_performed": checks_performed
            }

        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return {"status": "error", "message": str(e)}
