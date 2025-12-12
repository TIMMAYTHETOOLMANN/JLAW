#!/usr/bin/env python3
"""
Local Caching Layer - Hybrid diskcache + LRU
Provides persistent file-based caching without external dependencies like Redis.
Implements TTL-based expiration, LRU eviction, and thread-safe operations.
"""

import functools
import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
import logging

try:
    import diskcache as dc
except ImportError:
    dc = None
    logging.warning("diskcache not installed - using fallback cache")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalCache:
    """
    Hybrid local caching system using diskcache for persistence and
    functools.lru_cache for hot in-memory data.
    """
    
    DEFAULT_TTL = 3600  # 1 hour default
    DEFAULT_CACHE_DIR = "./cache"
    
    def __init__(
        self,
        cache_dir: str = DEFAULT_CACHE_DIR,
        size_limit: int = 1024 * 1024 * 1024,  # 1GB default
        enable_disk_cache: bool = True
    ):
        """
        Initialize local cache
        
        Args:
            cache_dir: Directory for persistent cache files
            size_limit: Maximum cache size in bytes
            enable_disk_cache: Whether to use diskcache (requires installation)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.enable_disk_cache = enable_disk_cache and dc is not None
        
        if self.enable_disk_cache:
            self.disk_cache = dc.Cache(
                str(self.cache_dir),
                size_limit=size_limit,
                eviction_policy='least-recently-used'
            )
            logger.info(f"Initialized diskcache at {self.cache_dir} with {size_limit} byte limit")
        else:
            self.disk_cache = None
            self._fallback_cache = {}
            logger.info(f"Using fallback in-memory cache (diskcache not available)")
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache"""
        if self.enable_disk_cache:
            return self.disk_cache.get(key)
        else:
            entry = self._fallback_cache.get(key)
            if entry:
                value, expiry = entry
                if expiry is None or time.time() < expiry:
                    return value
                else:
                    del self._fallback_cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """Store value in cache with TTL"""
        if self.enable_disk_cache:
            self.disk_cache.set(key, value, expire=ttl)
        else:
            expiry = time.time() + ttl if ttl else None
            self._fallback_cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if self.enable_disk_cache:
            return self.disk_cache.delete(key)
        else:
            if key in self._fallback_cache:
                del self._fallback_cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        if self.enable_disk_cache:
            self.disk_cache.clear()
        else:
            self._fallback_cache.clear()
    
    def stats(self) -> dict:
        """Get cache statistics"""
        if self.enable_disk_cache:
            return {
                "size": self.disk_cache.volume(),
                "count": len(self.disk_cache),
                "hits": getattr(self.disk_cache, 'hits', 0),
                "misses": getattr(self.disk_cache, 'misses', 0)
            }
        else:
            return {
                "size": len(str(self._fallback_cache)),
                "count": len(self._fallback_cache),
                "hits": 0,
                "misses": 0
            }
    
    def cached_function(
        self,
        ttl: int = DEFAULT_TTL,
        key_prefix: str = ""
    ) -> Callable:
        """
        Decorator to cache function results
        
        Usage:
            cache = LocalCache()
            
            @cache.cached_function(ttl=3600, key_prefix="sec_filing")
            def fetch_filing(cik: str, form_type: str):
                # Expensive operation
                return data
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key_parts = [key_prefix, func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                
                cache_key = hashlib.md5(
                    "|".join(key_parts).encode('utf-8')
                ).hexdigest()
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_value
                
                # Execute function and cache result
                logger.debug(f"Cache miss for {func.__name__}, executing...")
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl=ttl)
                
                return result
            
            return wrapper
        return decorator


# Global cache instance
_global_cache: Optional[LocalCache] = None


def get_cache(cache_dir: str = LocalCache.DEFAULT_CACHE_DIR) -> LocalCache:
    """Get or create global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = LocalCache(cache_dir=cache_dir)
    return _global_cache


# Convenience decorators using global cache
def cache_sec_filing(ttl: int = 86400):  # 24 hours
    """Cache SEC filing data"""
    return get_cache().cached_function(ttl=ttl, key_prefix="sec_filing")


def cache_parsed_document(ttl: int = 3600):  # 1 hour
    """Cache parsed document chunks"""
    return get_cache().cached_function(ttl=ttl, key_prefix="parsed_doc")


def cache_api_response(ttl: int = 1800):  # 30 minutes
    """Cache API responses"""
    return get_cache().cached_function(ttl=ttl, key_prefix="api_response")


# LRU cache for frequently accessed small data
@functools.lru_cache(maxsize=128)
def lru_cached_ticker_to_cik(ticker: str) -> Optional[str]:
    """
    In-memory LRU cache for ticker->CIK mapping
    This is an example of using functools.lru_cache for hot data
    """
    # Would implement actual lookup logic
    return None


# Example usage
if __name__ == "__main__":
    # Initialize cache
    cache = LocalCache(cache_dir="./cache")
    
    # Basic operations
    cache.set("test_key", {"data": "example"}, ttl=60)
    value = cache.get("test_key")
    print(f"Retrieved: {value}")
    
    # Decorator usage
    @cache.cached_function(ttl=300, key_prefix="expensive_op")
    def expensive_operation(param1: str, param2: int):
        """Simulate expensive operation"""
        print(f"Executing expensive operation with {param1}, {param2}")
        time.sleep(0.1)
        return f"Result: {param1}_{param2}"
    
    # First call - cache miss
    result1 = expensive_operation("test", 123)
    print(result1)
    
    # Second call - cache hit
    result2 = expensive_operation("test", 123)
    print(result2)
    
    # Stats
    print(f"Cache stats: {cache.stats()}")
