"""
SQLite Storage for WATCHKEEPER API

This module provides a storage adapter for the WATCHKEEPER API to read from the SQLite database.
"""

import os
import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.utils.logger import get_logger

class SQLiteStorage:
    """SQLite storage adapter for WATCHKEEPER API"""
    
    def __init__(self, db_path: str = 'data/intelligence.db'):
        """Initialize the SQLite storage adapter"""
        self.db_path = db_path
        self.logger = get_logger("watchkeeper.storage.sqlite")
        
        # Ensure the database exists
        if not os.path.exists(self.db_path):
            self.logger.warning(f"Database file not found at {self.db_path}")
            
    async def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an intelligence item by ID
        
        Args:
            item_id: ID of the item to retrieve
            
        Returns:
            Dict[str, Any] or None: The intelligence item if found, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM intelligence_items WHERE id = ?
            ''', (item_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Create a dictionary from the row
            item = dict(zip(column_names, row))
            
            # Parse JSON fields
            if 'keywords' in item and item['keywords']:
                item['keywords'] = json.loads(item['keywords'])
            else:
                item['keywords'] = []
                
            if 'investigation_data' in item and item['investigation_data']:
                item['investigation_data'] = json.loads(item['investigation_data'])
            else:
                item['investigation_data'] = {}
                
            # Format timestamp
            if 'timestamp' in item and item['timestamp']:
                try:
                    dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                    item['timestamp'] = dt.isoformat()
                except:
                    pass
                    
            conn.close()
            return item
            
        except Exception as e:
            self.logger.error(f"Error getting item by ID: {e}", exc_info=True)
            return None
            
    async def get_items_by_source(self, source_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get intelligence items by source type
        
        Args:
            source_type: Type of source to filter by
            limit: Maximum number of items to return
            
        Returns:
            List[Dict[str, Any]]: List of intelligence items
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM intelligence_items 
                WHERE source LIKE ? 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f"%{source_type}%", limit))
            
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Create a list of dictionaries from the rows
            items = []
            for row in rows:
                item = dict(zip(column_names, row))
                
                # Parse JSON fields
                if 'keywords' in item and item['keywords']:
                    item['keywords'] = json.loads(item['keywords'])
                else:
                    item['keywords'] = []
                    
                if 'investigation_data' in item and item['investigation_data']:
                    item['investigation_data'] = json.loads(item['investigation_data'])
                else:
                    item['investigation_data'] = {}
                    
                # Format timestamp
                if 'timestamp' in item and item['timestamp']:
                    try:
                        dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                        item['timestamp'] = dt.isoformat()
                    except:
                        pass
                        
                items.append(item)
                
            conn.close()
            return items
            
        except Exception as e:
            self.logger.error(f"Error getting items by source: {e}", exc_info=True)
            return []
            
    async def get_items_by_date(self, date_str: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get intelligence items by date
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            limit: Maximum number of items to return
            
        Returns:
            List[Dict[str, Any]]: List of intelligence items
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM intelligence_items 
                WHERE date(timestamp) = date(?)
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (date_str, limit))
            
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Create a list of dictionaries from the rows
            items = []
            for row in rows:
                item = dict(zip(column_names, row))
                
                # Parse JSON fields
                if 'keywords' in item and item['keywords']:
                    item['keywords'] = json.loads(item['keywords'])
                else:
                    item['keywords'] = []
                    
                if 'investigation_data' in item and item['investigation_data']:
                    item['investigation_data'] = json.loads(item['investigation_data'])
                else:
                    item['investigation_data'] = {}
                    
                # Format timestamp
                if 'timestamp' in item and item['timestamp']:
                    try:
                        dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                        item['timestamp'] = dt.isoformat()
                    except:
                        pass
                        
                items.append(item)
                
            conn.close()
            return items
            
        except Exception as e:
            self.logger.error(f"Error getting items by date: {e}", exc_info=True)
            return []
            
    async def get_recent_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent intelligence items
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List[Dict[str, Any]]: List of intelligence items
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM intelligence_items 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Create a list of dictionaries from the rows
            items = []
            for row in rows:
                item = dict(zip(column_names, row))
                
                # Parse JSON fields
                if 'keywords' in item and item['keywords']:
                    item['keywords'] = json.loads(item['keywords'])
                else:
                    item['keywords'] = []
                    
                if 'investigation_data' in item and item['investigation_data']:
                    item['investigation_data'] = json.loads(item['investigation_data'])
                else:
                    item['investigation_data'] = {}
                    
                # Format timestamp
                if 'timestamp' in item and item['timestamp']:
                    try:
                        dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                        item['timestamp'] = dt.isoformat()
                    except:
                        pass
                        
                items.append(item)
                
            conn.close()
            return items
            
        except Exception as e:
            self.logger.error(f"Error getting recent items: {e}", exc_info=True)
            return []
            
    async def get_high_threat_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get high threat intelligence items
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List[Dict[str, Any]]: List of intelligence items
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM intelligence_items 
                WHERE threat_level >= 7.0 AND missionary_relevance >= 5.0
                ORDER BY threat_level DESC, missionary_relevance DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Create a list of dictionaries from the rows
            items = []
            for row in rows:
                item = dict(zip(column_names, row))
                
                # Parse JSON fields
                if 'keywords' in item and item['keywords']:
                    item['keywords'] = json.loads(item['keywords'])
                else:
                    item['keywords'] = []
                    
                if 'investigation_data' in item and item['investigation_data']:
                    item['investigation_data'] = json.loads(item['investigation_data'])
                else:
                    item['investigation_data'] = {}
                    
                # Format timestamp
                if 'timestamp' in item and item['timestamp']:
                    try:
                        dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                        item['timestamp'] = dt.isoformat()
                    except:
                        pass
                        
                items.append(item)
                
            conn.close()
            return items
            
        except Exception as e:
            self.logger.error(f"Error getting high threat items: {e}", exc_info=True)
            return []
            
    async def search_items(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for intelligence items
        
        Args:
            query: Search query
            limit: Maximum number of items to return
            
        Returns:
            List[Dict[str, Any]]: List of intelligence items
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Use LIKE for simple text search
            search_term = f"%{query}%"
            
            cursor.execute('''
                SELECT * FROM intelligence_items 
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (search_term, search_term, limit))
            
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Create a list of dictionaries from the rows
            items = []
            for row in rows:
                item = dict(zip(column_names, row))
                
                # Parse JSON fields
                if 'keywords' in item and item['keywords']:
                    item['keywords'] = json.loads(item['keywords'])
                else:
                    item['keywords'] = []
                    
                if 'investigation_data' in item and item['investigation_data']:
                    item['investigation_data'] = json.loads(item['investigation_data'])
                else:
                    item['investigation_data'] = {}
                    
                # Format timestamp
                if 'timestamp' in item and item['timestamp']:
                    try:
                        dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                        item['timestamp'] = dt.isoformat()
                    except:
                        pass
                        
                items.append(item)
                
            conn.close()
            return items
            
        except Exception as e:
            self.logger.error(f"Error searching items: {e}", exc_info=True)
            return []
