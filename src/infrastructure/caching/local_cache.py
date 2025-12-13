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
from typing import Any, Optional, Callable, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
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


@dataclass
class CacheEntry:
    """Individual cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float]
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def access(self) -> None:
        """Record access"""
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass  
class CacheStatistics:
    """Cache performance metrics"""
    total_entries: int
    total_size_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    hit_rate: float = 0.0
    
    def __post_init__(self):
        """Calculate hit rate"""
        total_requests = self.hit_count + self.miss_count
        if total_requests > 0:
            self.hit_rate = self.hit_count / total_requests


class SECEdgarCache:
    """
    Specialized cache for SEC EDGAR filings with appropriate TTLs.
    
    Cache TTLs:
    - Filing data: 24h (filings don't change once published)
    - Company info: 1 week (company metadata changes infrequently)
    - XBRL facts: 24h (financial data is immutable)
    """
    
    # TTL Constants (seconds)
    FILING_DATA_TTL = 86400        # 24 hours
    COMPANY_INFO_TTL = 604800      # 1 week
    XBRL_FACTS_TTL = 86400         # 24 hours
    FORM4_TTL = 43200              # 12 hours (insider trades)
    
    def __init__(self, cache_dir: str = "./cache/sec_edgar"):
        """Initialize SEC EDGAR cache"""
        self.cache = LocalCache(cache_dir=cache_dir)
        logger.info(f"Initialized SEC EDGAR cache at {cache_dir}")
    
    def get_filing(self, cik: str, form_type: str, filing_date: str) -> Optional[Dict]:
        """Get cached filing data"""
        key = f"filing:{cik}:{form_type}:{filing_date}"
        return self.cache.get(key)
    
    def set_filing(self, cik: str, form_type: str, filing_date: str, data: Dict) -> None:
        """Cache filing data"""
        key = f"filing:{cik}:{form_type}:{filing_date}"
        self.cache.set(key, data, ttl=self.FILING_DATA_TTL)
    
    def get_company_info(self, cik: str) -> Optional[Dict]:
        """Get cached company information"""
        key = f"company:{cik}"
        return self.cache.get(key)
    
    def set_company_info(self, cik: str, data: Dict) -> None:
        """Cache company information"""
        key = f"company:{cik}"
        self.cache.set(key, data, ttl=self.COMPANY_INFO_TTL)
    
    def get_xbrl_facts(self, cik: str, fiscal_year: int) -> Optional[Dict]:
        """Get cached XBRL financial facts"""
        key = f"xbrl:{cik}:{fiscal_year}"
        return self.cache.get(key)
    
    def set_xbrl_facts(self, cik: str, fiscal_year: int, data: Dict) -> None:
        """Cache XBRL financial facts"""
        key = f"xbrl:{cik}:{fiscal_year}"
        self.cache.set(key, data, ttl=self.XBRL_FACTS_TTL)
    
    def get_form4_transactions(self, cik: str, start_date: str, end_date: str) -> Optional[List]:
        """Get cached Form 4 transactions"""
        key = f"form4:{cik}:{start_date}:{end_date}"
        return self.cache.get(key)
    
    def set_form4_transactions(self, cik: str, start_date: str, end_date: str, data: List) -> None:
        """Cache Form 4 transactions"""
        key = f"form4:{cik}:{start_date}:{end_date}"
        self.cache.set(key, data, ttl=self.FORM4_TTL)
    
    def clear_company(self, cik: str) -> None:
        """Clear all cached data for a company"""
        # Pattern-based deletion (if supported by cache backend)
        if hasattr(self.cache, 'clear_pattern'):
            self.cache.clear_pattern(f"*:{cik}:*")
        else:
            logger.warning("Pattern-based cache clearing not supported")


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Function decorator for caching results
    
    Usage:
        @cached(ttl=3600, key_prefix="expensive")
        def expensive_function(arg1, arg2):
            return result
    """
    cache = get_cache()
    return cache.cached_function(ttl=ttl, key_prefix=key_prefix)


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
    
    # SEC EDGAR Cache demo
    print("\n--- SEC EDGAR Cache Demo ---")
    sec_cache = SECEdgarCache()
    
    # Cache a filing
    sec_cache.set_filing(
        cik="0000320193",
        form_type="10-K",
        filing_date="2024-03-15",
        data={"revenue": 1000000, "net_income": 100000}
    )
    
    # Retrieve filing
    filing = sec_cache.get_filing("0000320193", "10-K", "2024-03-15")
    print(f"Cached filing: {filing}")
