"""
Collector Manager for WATCHKEEPER

This module manages all intelligence collectors and coordinates their operation.
"""

import asyncio
import logging
from typing import Dict, List, Any

from src.utils.logger import get_logger
from src.collectors.base_collector import BaseCollector
from src.collectors.news_collector import NewsCollector
from src.collectors.social_media_collector import SocialMediaCollector
from src.collectors.government_collector import GovernmentCollector

class CollectorManager:
    """
    Manages all intelligence collectors and coordinates their operation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the collector manager
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_logger("watchkeeper.collectors")
        self.collectors = []
        self._initialize_collectors()
        
    def _initialize_collectors(self):
        """Initialize all enabled collectors based on configuration"""
        collector_config = self.config.get("collectors", {})
        
        # Initialize news collectors if enabled
        if collector_config.get("news", {}).get("enabled", False):
            self.logger.info("Initializing news collectors")
            news_config = collector_config.get("news", {})
            for source in news_config.get("sources", []):
                self.collectors.append(NewsCollector(
                    source=source,
                    rate_limit=news_config.get("rate_limit", 60),
                    languages=news_config.get("languages", ["en"])
                ))
        
        # Initialize social media collectors if enabled
        if collector_config.get("social_media", {}).get("enabled", False):
            self.logger.info("Initializing social media collectors")
            social_config = collector_config.get("social_media", {})
            for source in social_config.get("sources", []):
                self.collectors.append(SocialMediaCollector(
                    source=source,
                    rate_limit=social_config.get("rate_limit", 30)
                ))
        
        # Initialize government collectors if enabled
        if collector_config.get("government", {}).get("enabled", False):
            self.logger.info("Initializing government collectors")
            gov_config = collector_config.get("government", {})
            for source in gov_config.get("sources", []):
                self.collectors.append(GovernmentCollector(
                    source=source,
                    rate_limit=gov_config.get("rate_limit", 10)
                ))
        
        self.logger.info(f"Initialized {len(self.collectors)} collectors")
    
    async def start(self):
        """Start all collectors"""
        self.logger.info("Starting all collectors")
        
        # Create tasks for all collectors
        collector_tasks = []
        for collector in self.collectors:
            collector_tasks.append(asyncio.create_task(collector.collect_continuously()))
        
        # Wait for all collector tasks to complete (they should run indefinitely)
        if collector_tasks:
            await asyncio.gather(*collector_tasks)
        else:
            self.logger.warning("No collectors were enabled. Collection system is idle.")
            # Keep the task alive
            while True:
                await asyncio.sleep(60)
    
    async def stop(self):
        """Stop all collectors"""
        self.logger.info("Stopping all collectors")
        for collector in self.collectors:
            await collector.stop()
