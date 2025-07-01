"""
Redis cache for WATCHKEEPER API

This module provides Redis caching functionality for the WATCHKEEPER API.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable

# Make aioredis import optional
try:
    import aioredis
    REDIS_AVAILABLE = True
except (ImportError, TypeError):
    REDIS_AVAILABLE = False
    aioredis = None

from fastapi import Depends

from src.utils.logger import get_logger
from src.utils.config import get_config

# Initialize logger
logger = get_logger("watchkeeper.api.cache")

class RedisCache:
    """
    Redis cache for API responses and frequently accessed data
    """
    
    def __init__(self):
        """Initialize the Redis cache"""
        self.config = get_config().get("cache", {})
        self.redis_url = self.config.get("redis_url", "redis://localhost:6379/0")
        self.default_ttl = self.config.get("default_ttl", 3600)  # 1 hour default
        self.enabled = REDIS_AVAILABLE and self.config.get("enabled", True)
        
        if not REDIS_AVAILABLE and self.config.get("enabled", True):
            logger.warning("Redis is not available. Caching will be disabled.")
            self.enabled = False
        self.redis = None
        self.connected = False
    
    async def connect(self):
        """Connect to Redis server"""
        if self.connected or not self.enabled:
            return
            
        if not REDIS_AVAILABLE:
            logger.warning("Redis is not available. Skipping connection.")
            return
            
        try:
            self.redis = await aioredis.create_redis_pool(self.redis_url)
            self.connected = True
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.connected = False
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found
        """
        if not self.enabled or not self.connected:
            return None
        
        try:
            value = await self.redis.get(key)
            
            if value:
                return json.loads(value)
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting value from cache: {e}", exc_info=True)
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for default)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled or not self.connected:
            return False
        
        try:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
            
            # Convert value to JSON
            json_value = json.dumps(value)
            
            # Set value in Redis
            await self.redis.set(key, json_value, ex=ttl)
            
            return True
        
        except Exception as e:
            logger.error(f"Error setting value in cache: {e}", exc_info=True)
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled or not self.connected:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        
        except Exception as e:
            logger.error(f"Error deleting value from cache: {e}", exc_info=True)
            return False
    
    async def clear(self) -> bool:
        """
        Clear the cache
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled or not self.connected:
            return False
        
        try:
            await self.redis.flushdb()
            return True
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}", exc_info=True)
            return False
    
    async def get_or_set(self, key: str, value_func: Callable, ttl: Optional[int] = None) -> Any:
        """
        Get a value from the cache or set it if not found
        
        Args:
            key: Cache key
            value_func: Function to call to get the value if not in cache
            ttl: Time to live in seconds (None for default)
            
        Returns:
            Any: Cached or newly generated value
        """
        # Try to get from cache first
        cached_value = await self.get(key)
        
        if cached_value is not None:
            return cached_value
        
        # Not in cache, call the function to get the value
        value = await value_func()
        
        # Store in cache
        await self.set(key, value, ttl)
        
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern
        
        Args:
            pattern: Redis key pattern (e.g., "intelligence:*")
            
        Returns:
            int: Number of keys invalidated
        """
        if not self.connected:
            return 0
        
        try:
            # Find all keys matching the pattern
            keys = await self.redis.keys(pattern)
            
            if not keys:
                return 0
            
            # Delete all matching keys
            count = await self.redis.delete(*keys)
            
            logger.debug(f"Invalidated {count} keys matching pattern {pattern}")
            
            return count
        
        except Exception as e:
            logger.error(f"Error invalidating keys with pattern {pattern}: {e}", exc_info=True)
            return 0

# Create global cache instance
cache = RedisCache()

async def get_cache() -> RedisCache:
    """
    Get the Redis cache instance
    
    Returns:
        RedisCache: Redis cache instance
    """
    if not cache.connected:
        await cache.connect()
    
    return cache

# Cache decorator for API endpoints
def cached(key_prefix: str, ttl: Optional[int] = None):
    """
    Decorator for caching API endpoint responses
    
    Args:
        key_prefix: Prefix for cache keys
        ttl: Time to live in seconds (None for default)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = f"{key_prefix}:{json.dumps(args)}:{json.dumps(kwargs)}"
            
            # Get cache instance
            cache_instance = await get_cache()
            
            # Try to get from cache
            cached_result = await cache_instance.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Not in cache, call the function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_instance.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator
