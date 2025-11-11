"""
Base Collector for WATCHKEEPER

This module defines the base class for all intelligence collectors.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from src.utils.logger import get_logger

class BaseCollector(ABC):
    """
    Base class for all intelligence collectors
    
    This abstract class defines the interface that all collectors must implement.
    It provides common functionality for rate limiting, error handling, and collection management.
    """
    
    def __init__(self, source: str, rate_limit: int = 60):
        """
        Initialize the collector
        
        Args:
            source: Name of the source
            rate_limit: Maximum number of requests per minute
        """
        self.source = source
        self.rate_limit = rate_limit
        self.logger = get_logger(f"watchkeeper.collectors.{source}")
        self.running = False
        self.last_request_time = 0
        self.reliability_score = 0.7  # Default reliability score (0.0 to 1.0)
    
    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect intelligence from the source
        
        Returns:
            List[Dict[str, Any]]: List of collected intelligence items
        """
        pass
    
    @abstractmethod
    def parse_content(self, content: Any) -> Dict[str, Any]:
        """
        Parse content from the source into a standardized format
        
        Args:
            content: Raw content from the source
            
        Returns:
            Dict[str, Any]: Parsed intelligence item
        """
        pass
    
    async def collect_continuously(self):
        """
        Continuously collect intelligence from the source with rate limiting
        """
        self.running = True
        self.logger.info(f"Starting continuous collection from {self.source}")
        
        while self.running:
            try:
                # Apply rate limiting
                await self._rate_limit()
                
                # Collect intelligence
                self.logger.debug(f"Collecting from {self.source}")
                items = await self.collect()
                
                if items:
                    self.logger.info(f"Collected {len(items)} items from {self.source}")
                    
                    # Process and store the collected items
                    for item in items:
                        # Add source metadata
                        item["source"] = {
                            "name": self.source,
                            "reliability_score": self.reliability_score,
                            "collection_time": time.time()
                        }

                        # Send to processing pipeline
                        await self._send_to_pipeline(item)
                else:
                    self.logger.debug(f"No new items from {self.source}")
                
                # Sleep before next collection
                await asyncio.sleep(60)  # Default to checking once per minute
            
            except Exception as e:
                self.logger.error(f"Error collecting from {self.source}: {e}", exc_info=True)
                # Exponential backoff on error
                await asyncio.sleep(60)
    
    async def stop(self):
        """Stop the collector"""
        self.logger.info(f"Stopping collection from {self.source}")
        self.running = False
    
    async def _rate_limit(self):
        """Apply rate limiting to avoid overloading the source"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Calculate time to wait based on rate limit
        min_interval = 60.0 / self.rate_limit  # seconds per request
        
        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            self.logger.debug(f"Rate limiting {self.source}, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def assess_relevance(self, content: Dict[str, Any]) -> float:
        """
        Assess the relevance of content to missionary operations

        Args:
            content: Parsed content

        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        # Default implementation - should be overridden by subclasses
        # This is a placeholder that gives medium relevance to everything
        return 0.5

    async def _send_to_pipeline(self, item: Dict[str, Any]):
        """
        Send collected item to the processing pipeline.

        Creates an Intelligence record in the database and queues it for processing.

        Args:
            item: Collected intelligence item with metadata
        """
        try:
            from src.core.database import AsyncSessionLocal
            from src.models.intelligence import Intelligence, ProcessingStatus
            from src.models.source import Source
            from sqlalchemy import select

            async with AsyncSessionLocal() as session:
                # Find or create source
                result = await session.execute(
                    select(Source).where(Source.name == self.source)
                )
                source = result.scalar_one_or_none()

                if not source:
                    # Create source if it doesn't exist
                    from src.models.source import SourceType
                    source = Source(
                        name=self.source,
                        url=item.get("url", ""),
                        source_type=SourceType.NEWS,  # Default
                        is_active=True,
                        reliability_score=self.reliability_score
                    )
                    session.add(source)
                    await session.commit()
                    await session.refresh(source)

                # Create intelligence item
                intelligence = Intelligence(
                    raw_content=item.get("content", ""),
                    source_id=source.id,
                    processing_status=ProcessingStatus.PENDING,
                    ai_analysis_data={"source_metadata": item.get("source", {})}
                )

                session.add(intelligence)
                await session.commit()
                await session.refresh(intelligence)

                self.logger.info(f"Created intelligence item {intelligence.id} from {self.source}")

                # Queue for processing using Celery
                try:
                    from src.tasks.intelligence_tasks import process_intelligence_item
                    process_intelligence_item.delay(intelligence.id)
                    self.logger.debug(f"Queued intelligence {intelligence.id} for processing")
                except Exception as e:
                    self.logger.warning(f"Failed to queue intelligence for processing: {e}")

        except Exception as e:
            self.logger.error(f"Error sending item to pipeline: {e}", exc_info=True)
