"""
JSON Storage for WATCHKEEPER

This module provides a simple JSON-based storage system for intelligence items.
"""

import os
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.utils.logger import get_logger

class JsonStorage:
    """
    JSON-based storage system for intelligence items
    
    This class provides methods to store and retrieve intelligence items in JSON format.
    Items are stored in a directory structure organized by date and source type.
    """
    
    def __init__(self, base_dir: str):
        """
        Initialize the JSON storage
        
        Args:
            base_dir: Base directory for storing JSON files
        """
        self.base_dir = Path(base_dir)
        self.logger = get_logger("watchkeeper.storage.json")
        
        # Create base directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create lock for thread safety
        self._lock = asyncio.Lock()
    
    async def store_item(self, item: Dict[str, Any]) -> str:
        """
        Store an intelligence item
        
        Args:
            item: Intelligence item to store
            
        Returns:
            str: ID of the stored item
        """
        try:
            # Generate a unique ID if not present
            if "id" not in item:
                item["id"] = f"{int(time.time())}_{hash(str(item))}"
            
            # Add storage timestamp
            item["storage_time"] = datetime.now().isoformat()
            
            # Determine directory path based on source and date
            source_type = item.get("source", {}).get("name", "unknown").split(".")[0]
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            dir_path = self.base_dir / source_type / date_str
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"{item['id']}.json"
            file_path = dir_path / filename
            
            # Write to file with lock to prevent race conditions
            async with self._lock:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(item, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"Stored item {item['id']} to {file_path}")
            return item["id"]
        
        except Exception as e:
            self.logger.error(f"Error storing item: {e}", exc_info=True)
            raise
    
    async def store_items(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        Store multiple intelligence items
        
        Args:
            items: List of intelligence items to store
            
        Returns:
            List[str]: List of IDs of the stored items
        """
        item_ids = []
        for item in items:
            try:
                item_id = await self.store_item(item)
                item_ids.append(item_id)
            except Exception as e:
                self.logger.error(f"Error storing item in batch: {e}")
        
        return item_ids
    
    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an intelligence item by ID
        
        Args:
            item_id: ID of the item to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The retrieved item, or None if not found
        """
        try:
            # Search for the item in the directory structure
            for source_dir in self.base_dir.iterdir():
                if not source_dir.is_dir():
                    continue
                
                for date_dir in source_dir.iterdir():
                    if not date_dir.is_dir():
                        continue
                    
                    file_path = date_dir / f"{item_id}.json"
                    if file_path.exists():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
            
            self.logger.warning(f"Item {item_id} not found")
            return None
        
        except Exception as e:
            self.logger.error(f"Error retrieving item {item_id}: {e}", exc_info=True)
            return None
    
    async def get_items_by_date(self, date_str: str, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve intelligence items by date
        
        Args:
            date_str: Date string in format YYYY-MM-DD
            source_type: Optional source type filter
            
        Returns:
            List[Dict[str, Any]]: List of retrieved items
        """
        items = []
        
        try:
            # Determine directories to search
            if source_type:
                source_dirs = [self.base_dir / source_type]
            else:
                source_dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]
            
            # Search for items in each source directory
            for source_dir in source_dirs:
                date_dir = source_dir / date_str
                if not date_dir.exists() or not date_dir.is_dir():
                    continue
                
                # Load each JSON file in the date directory
                for file_path in date_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            item = json.load(f)
                            items.append(item)
                    except Exception as e:
                        self.logger.error(f"Error loading {file_path}: {e}")
            
            return items
        
        except Exception as e:
            self.logger.error(f"Error retrieving items for date {date_str}: {e}", exc_info=True)
            return []
    
    async def get_items_by_source(self, source_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve intelligence items by source type
        
        Args:
            source_type: Source type filter
            limit: Maximum number of items to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of retrieved items
        """
        items = []
        
        try:
            source_dir = self.base_dir / source_type
            if not source_dir.exists() or not source_dir.is_dir():
                return []
            
            # Get all date directories, sorted by date (newest first)
            date_dirs = sorted([d for d in source_dir.iterdir() if d.is_dir()], reverse=True)
            
            # Load items from each date directory until limit is reached
            for date_dir in date_dirs:
                if len(items) >= limit:
                    break
                
                # Load each JSON file in the date directory
                for file_path in date_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            item = json.load(f)
                            items.append(item)
                            
                            if len(items) >= limit:
                                break
                    except Exception as e:
                        self.logger.error(f"Error loading {file_path}: {e}")
            
            return items
        
        except Exception as e:
            self.logger.error(f"Error retrieving items for source {source_type}: {e}", exc_info=True)
            return []
    
    async def search_items(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for intelligence items containing the query string
        
        Args:
            query: Query string to search for
            limit: Maximum number of items to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of matching items
        """
        items = []
        query = query.lower()
        
        try:
            # Recursively search all JSON files
            for file_path in self._find_json_files(self.base_dir):
                if len(items) >= limit:
                    break
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        item = json.load(f)
                        
                        # Check if query is in title or content
                        title = item.get("title", "").lower()
                        content = item.get("content", "").lower()
                        
                        if query in title or query in content:
                            items.append(item)
                except Exception as e:
                    self.logger.error(f"Error searching {file_path}: {e}")
            
            return items
        
        except Exception as e:
            self.logger.error(f"Error searching for query '{query}': {e}", exc_info=True)
            return []
    
    def _find_json_files(self, directory: Path) -> List[Path]:
        """
        Recursively find all JSON files in a directory
        
        Args:
            directory: Directory to search
            
        Returns:
            List[Path]: List of JSON file paths
        """
        json_files = []
        
        for path in directory.iterdir():
            if path.is_file() and path.suffix == '.json':
                json_files.append(path)
            elif path.is_dir():
                json_files.extend(self._find_json_files(path))
        
        return json_files
