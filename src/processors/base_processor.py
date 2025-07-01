"""
Base Processor for WATCHKEEPER

This module defines the base class for all intelligence processors.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from src.utils.logger import get_logger

class BaseProcessor(ABC):
    """
    Base class for all intelligence processors
    
    This abstract class defines the interface that all processors must implement.
    It provides common functionality for processing intelligence items.
    """
    
    def __init__(self, processor_name: str):
        """
        Initialize the processor
        
        Args:
            processor_name: Name of the processor
        """
        self.processor_name = processor_name
        self.logger = get_logger(f"watchkeeper.processors.{processor_name}")
        self.running = False
        self.last_process_time = 0
    
    @abstractmethod
    async def process(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single intelligence item
        
        Args:
            item: Intelligence item to process
            
        Returns:
            Dict[str, Any]: Processed intelligence item with additional metadata
        """
        pass
    
    async def process_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of intelligence items
        
        Args:
            items: List of intelligence items to process
            
        Returns:
            List[Dict[str, Any]]: List of processed intelligence items
        """
        processed_items = []
        
        for item in items:
            try:
                processed_item = await self.process(item)
                processed_items.append(processed_item)
            except Exception as e:
                self.logger.error(f"Error processing item: {e}", exc_info=True)
        
        return processed_items
    
    async def process_continuously(self, queue: asyncio.Queue):
        """
        Continuously process intelligence items from a queue
        
        Args:
            queue: Queue of intelligence items to process
        """
        self.running = True
        self.logger.info(f"Starting continuous processing with {self.processor_name}")
        
        while self.running:
            try:
                # Get item from queue
                item = await queue.get()
                
                # Process item
                self.logger.debug(f"Processing item with {self.processor_name}")
                processed_item = await self.process(item)
                
                # Mark task as done
                queue.task_done()
                
                # Update last process time
                self.last_process_time = time.time()
                
                # TODO: Send processed item to next stage in pipeline
            
            except Exception as e:
                self.logger.error(f"Error in continuous processing: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before trying again
    
    async def stop(self):
        """Stop the processor"""
        self.logger.info(f"Stopping {self.processor_name} processor")
        self.running = False
