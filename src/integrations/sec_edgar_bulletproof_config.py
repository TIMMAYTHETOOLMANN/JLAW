"""
SEC EDGAR Bulletproof Configuration (v4.1.0)
============================================

Production-grade SEC EDGAR API client with advanced reliability features.

Features:
---------
1. **Advanced Caching Layer**
   - File-based persistent cache (no external dependencies)
   - Configurable TTL by data type (submissions: 24h, filings: 1h, XBRL: 24h, etc.)
   - Stale cache fallback - uses expired cache if fetch fails
   - Automatic cleanup of expired entries

2. **Adaptive Rate Limiting**
   - Token bucket algorithm with dynamic adjustment
   - Automatically slows down on 429 responses (2x-4x slowdown)
   - Gradual recovery after successful requests
   - Burst handling with cooldown

3. **Circuit Breaker Protection**
   - Three states: CLOSED, OPEN, HALF_OPEN
   - Prevents cascading failures
   - Configurable threshold and timeout

4. **Comprehensive Configuration**
   - Multiple retry strategies (exponential, linear, fibonacci)
   - Detailed timeout configuration
   - Environment variable support
   - Graceful degradation options

5. **Enhanced Error Handling**
   - Configurable failure behavior (raise vs return None)
   - Detailed statistics tracking
   - Comprehensive logging

6. **Specialized Methods for JLAW Nodes**
   - Pre-built methods for all JLAW requirements

Author: JLAW Forensic System
Version: 4.1.0
License: MIT
"""

import asyncio
import aiohttp
import json
import logging
import time
import os
import hashlib
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class RetryStrategy(Enum):
    """Retry backoff strategies."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"


@dataclass
class BulletproofConfig:
    """Bulletproof SEC EDGAR client configuration."""
    
    # User Agent (REQUIRED by SEC)
    user_agent: str = "JLAW-ForensicAnalyzer/4.1.0 (contact@example.com)"
    
    # Rate Limiting
    rate_limit: float = 6.0  # requests per second (conservative)
    burst_size: int = 3      # allow brief bursts
    adaptive_slowdown: bool = True  # slow down on 429 errors
    slowdown_factor: float = 2.0    # multiply by this on 429
    max_slowdown: float = 4.0       # maximum slowdown multiplier
    recovery_rate: float = 0.1      # gradually speed up after success
    
    # Caching
    cache_enabled: bool = True
    cache_dir: str = ".jlaw_cache/sec_edgar"
    stale_cache_fallback: bool = True  # use expired cache if fetch fails
    cache_ttl_submissions: int = 86400  # 24 hours
    cache_ttl_filings: int = 3600       # 1 hour
    cache_ttl_xbrl: int = 86400         # 24 hours
    cache_ttl_tickers: int = 604800     # 7 days
    cache_ttl_documents: int = 2592000  # 30 days
    cache_cleanup_interval: int = 3600  # cleanup every hour
    
    # Circuit Breaker
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5  # failures before opening
    circuit_breaker_timeout: int = 60   # seconds before half-open
    circuit_breaker_success_threshold: int = 2  # successes to close
    
    # Retry Configuration
    max_retries: int = 5
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0
    
    # Timeouts
    timeout_connect: float = 10.0
    timeout_read: float = 30.0
    timeout_total: float = 120.0
    
    # Error Handling
    raise_on_final_failure: bool = False  # graceful degradation
    
    # Mock Mode
    mock_mode: bool = False
    
    @classmethod
    def from_env(cls) -> 'BulletproofConfig':
        """Load configuration from environment variables."""
        return cls(
            user_agent=os.getenv('SEC_USER_AGENT', cls.user_agent),
            rate_limit=float(os.getenv('SEC_RATE_LIMIT', str(cls.rate_limit))),
            cache_enabled=os.getenv('SEC_CACHE_ENABLED', 'true').lower() in ('true', '1', 'yes'),
            cache_dir=os.getenv('SEC_CACHE_DIR', cls.cache_dir),
            stale_cache_fallback=os.getenv('SEC_STALE_CACHE_FALLBACK', 'true').lower() in ('true', '1', 'yes'),
            circuit_breaker_enabled=os.getenv('SEC_CIRCUIT_BREAKER_ENABLED', 'true').lower() in ('true', '1', 'yes'),
            max_retries=int(os.getenv('SEC_MAX_RETRIES', str(cls.max_retries))),
            retry_strategy=RetryStrategy(os.getenv('SEC_RETRY_STRATEGY', 'exponential')),
            raise_on_final_failure=os.getenv('SEC_RAISE_ON_FINAL_FAILURE', 'false').lower() in ('true', '1', 'yes'),
            mock_mode=os.getenv('SEC_MOCK_MODE', 'false').lower() in ('true', '1', 'yes'),
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings."""
        warnings = []
        
        # Check user agent
        if 'example.com' in self.user_agent.lower():
            warnings.append("User-Agent contains 'example.com' - replace with real contact email")
        
        if '@' not in self.user_agent:
            warnings.append("User-Agent should include contact email address")
        
        # Check rate limit
        if self.rate_limit > 10.0:
            warnings.append(f"Rate limit {self.rate_limit} exceeds SEC maximum of 10 req/sec")
        
        if self.rate_limit > 9.0:
            warnings.append(f"Rate limit {self.rate_limit} is aggressive - consider 6-9 req/sec for reliability")
        
        return warnings


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    data: Any
    cached_at: float
    ttl: int
    data_type: str
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() > (self.cached_at + self.ttl)
    
    def age(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.cached_at


class CacheManager:
    """File-based cache manager with TTL support."""
    
    def __init__(self, config: BulletproofConfig):
        self.config = config
        self.cache_dir = Path(config.cache_dir)
        self.last_cleanup = time.time()
        
        # Create cache directory
        if config.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache directory: {self.cache_dir}")
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        # Use hash to avoid filesystem issues with special characters
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str, allow_stale: bool = False) -> Optional[Any]:
        """Get item from cache."""
        if not self.config.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                entry: CacheEntry = pickle.load(f)
            
            if entry.is_expired():
                if allow_stale and self.config.stale_cache_fallback:
                    logger.warning(f"Using stale cache for {key} (age: {entry.age():.0f}s)")
                    return entry.data
                return None
            
            logger.debug(f"Cache hit for {key} (age: {entry.age():.0f}s)")
            return entry.data
            
        except Exception as e:
            logger.warning(f"Cache read error for {key}: {e}")
            return None
    
    def set(self, key: str, data: Any, data_type: str = "default") -> None:
        """Set item in cache with appropriate TTL."""
        if not self.config.cache_enabled:
            return
        
        # Get TTL based on data type
        ttl_map = {
            "submissions": self.config.cache_ttl_submissions,
            "filings": self.config.cache_ttl_filings,
            "xbrl": self.config.cache_ttl_xbrl,
            "tickers": self.config.cache_ttl_tickers,
            "documents": self.config.cache_ttl_documents,
        }
        ttl = ttl_map.get(data_type, 3600)  # default 1 hour
        
        entry = CacheEntry(
            key=key,
            data=data,
            cached_at=time.time(),
            ttl=ttl,
            data_type=data_type
        )
        
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
            logger.debug(f"Cached {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
    
    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        if not self.config.cache_enabled:
            return
        
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                cache_path.unlink()
                logger.debug(f"Invalidated cache for {key}")
            except Exception as e:
                logger.warning(f"Cache invalidation error for {key}: {e}")
    
    def cleanup(self) -> int:
        """Remove expired cache entries. Returns count of removed entries."""
        if not self.config.cache_enabled:
            return 0
        
        # Check if cleanup is needed
        if time.time() - self.last_cleanup < self.config.cache_cleanup_interval:
            return 0
        
        self.last_cleanup = time.time()
        removed = 0
        
        try:
            for cache_path in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_path, 'rb') as f:
                        entry: CacheEntry = pickle.load(f)
                    
                    if entry.is_expired():
                        cache_path.unlink()
                        removed += 1
                except Exception:
                    # Remove corrupted cache files
                    cache_path.unlink()
                    removed += 1
            
            if removed > 0:
                logger.info(f"Cache cleanup: removed {removed} expired entries")
        
        except Exception as e:
            logger.warning(f"Cache cleanup error: {e}")
        
        return removed


class AdaptiveRateLimiter:
    """Token bucket rate limiter with adaptive slowdown."""
    
    def __init__(self, config: BulletproofConfig):
        self.config = config
        self.tokens = config.burst_size
        self.max_tokens = config.burst_size
        self.last_update = time.time()
        self.current_rate = config.rate_limit
        self.slowdown_multiplier = 1.0
        self._lock = asyncio.Lock()
        
        logger.info(f"Adaptive rate limiter initialized: {self.current_rate} req/sec")
    
    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time and current rate
            self.tokens = min(
                self.max_tokens,
                self.tokens + (elapsed * self.current_rate / self.slowdown_multiplier)
            )
            self.last_update = now
            
            # Wait if no tokens available
            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / (self.current_rate / self.slowdown_multiplier)
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
                self.last_update = time.time()
            else:
                self.tokens -= 1.0
    
    def on_rate_limit_error(self) -> None:
        """Handle 429 rate limit error - slow down."""
        if not self.config.adaptive_slowdown:
            return
        
        self.slowdown_multiplier = min(
            self.config.max_slowdown,
            self.slowdown_multiplier * self.config.slowdown_factor
        )
        
        effective_rate = self.current_rate / self.slowdown_multiplier
        logger.warning(
            f"Rate limit hit - slowing down to {effective_rate:.2f} req/sec "
            f"(multiplier: {self.slowdown_multiplier:.1f}x)"
        )
    
    def on_success(self) -> None:
        """Handle successful request - gradually speed up."""
        if not self.config.adaptive_slowdown or self.slowdown_multiplier <= 1.0:
            return
        
        self.slowdown_multiplier = max(
            1.0,
            self.slowdown_multiplier - self.config.recovery_rate
        )
        
        if self.slowdown_multiplier > 1.0:
            effective_rate = self.current_rate / self.slowdown_multiplier
            logger.debug(f"Recovering speed: {effective_rate:.2f} req/sec")


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""
    
    def __init__(self, config: BulletproofConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self._lock = asyncio.Lock()
        
        if config.circuit_breaker_enabled:
            logger.info("Circuit breaker enabled")
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if not self.config.circuit_breaker_enabled:
            return await func(*args, **kwargs)
        
        async with self._lock:
            # Check state
            if self.state == CircuitBreakerState.OPEN:
                # Check if timeout has elapsed
                if time.time() - self.last_failure_time >= self.config.circuit_breaker_timeout:
                    logger.info("Circuit breaker: OPEN -> HALF_OPEN (timeout elapsed)")
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN - rejecting request")
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self) -> None:
        """Handle successful request."""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.circuit_breaker_success_threshold:
                    logger.info("Circuit breaker: HALF_OPEN -> CLOSED (recovered)")
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    async def _on_failure(self) -> None:
        """Handle failed request."""
        async with self._lock:
            self.last_failure_time = time.time()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                logger.warning("Circuit breaker: HALF_OPEN -> OPEN (failure during recovery)")
                self.state = CircuitBreakerState.OPEN
                self.failure_count = 0
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count += 1
                if self.failure_count >= self.config.circuit_breaker_threshold:
                    logger.error(
                        f"Circuit breaker: CLOSED -> OPEN "
                        f"({self.failure_count} consecutive failures)"
                    )
                    self.state = CircuitBreakerState.OPEN


@dataclass
class Statistics:
    """Statistics tracking for SEC API calls."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    retries: int = 0
    rate_limit_errors: int = 0
    circuit_breaker_opens: int = 0
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops == 0:
            return 0.0
        return self.cache_hits / total_cache_ops
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            **asdict(self),
            "success_rate": self.success_rate(),
            "cache_hit_rate": self.cache_hit_rate()
        }


class BulletproofSECEdgarClient:
    """
    Bulletproof SEC EDGAR API Client (v4.1.0)
    
    Production-grade client with advanced reliability features:
    - Persistent caching with stale fallback
    - Adaptive rate limiting
    - Circuit breaker protection
    - Comprehensive error handling
    - Specialized methods for all JLAW nodes
    """
    
    BASE_URL = "https://data.sec.gov"
    ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
    
    def __init__(self, config: Optional[BulletproofConfig] = None):
        """
        Initialize bulletproof SEC EDGAR client.
        
        Args:
            config: BulletproofConfig instance (defaults to environment config)
        """
        self.config = config or BulletproofConfig.from_env()
        
        # Validate configuration
        warnings = self.config.validate()
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
        
        # Initialize components
        self.cache = CacheManager(self.config)
        self.rate_limiter = AdaptiveRateLimiter(self.config)
        self.circuit_breaker = CircuitBreaker(self.config)
        self.stats = Statistics()
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"BulletproofSECEdgarClient v4.1.0 initialized")
        logger.info(f"Mock mode: {self.config.mock_mode}")
        logger.info(f"Cache enabled: {self.config.cache_enabled}")
        logger.info(f"Circuit breaker: {self.config.circuit_breaker_enabled}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(
            connect=self.config.timeout_connect,
            sock_read=self.config.timeout_read,
            total=self.config.timeout_total
        )
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.config.user_agent},
            timeout=timeout,
            trust_env=True,
        )
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay based on strategy."""
        if self.config.retry_strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.retry_base_delay * (2 ** attempt)
        elif self.config.retry_strategy == RetryStrategy.LINEAR:
            delay = self.config.retry_base_delay * (attempt + 1)
        elif self.config.retry_strategy == RetryStrategy.FIBONACCI:
            # Fibonacci sequence: 1, 1, 2, 3, 5, 8, 13...
            fib = [1, 1]
            for i in range(2, attempt + 2):
                fib.append(fib[i-1] + fib[i-2])
            delay = self.config.retry_base_delay * fib[attempt]
        else:
            delay = self.config.retry_base_delay
        
        return min(delay, self.config.retry_max_delay)
    
    async def _fetch(self, url: str, cache_key: Optional[str] = None, 
                    data_type: str = "default") -> Optional[str]:
        """
        Fetch URL with full bulletproof features.
        
        Args:
            url: URL to fetch
            cache_key: Cache key (defaults to URL)
            data_type: Data type for cache TTL
            
        Returns:
            Response text or None if failed
        """
        cache_key = cache_key or url
        
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.stats.cache_hits += 1
            return cached
        
        self.stats.cache_misses += 1
        
        # Mock mode
        if self.config.mock_mode:
            return self._get_mock_response(url)
        
        # Retry loop
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                self.stats.total_requests += 1
                
                # Rate limiting
                await self.rate_limiter.acquire()
                
                # Circuit breaker
                async def fetch_impl():
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            text = await response.text()
                            self.stats.successful_requests += 1
                            self.rate_limiter.on_success()
                            
                            # Cache successful response
                            self.cache.set(cache_key, text, data_type)
                            
                            return text
                        elif response.status == 429:
                            # Rate limit error
                            self.stats.rate_limit_errors += 1
                            self.rate_limiter.on_rate_limit_error()
                            raise Exception(f"Rate limit error (429): {url}")
                        elif response.status == 404:
                            # Not found - don't retry
                            logger.info(f"Resource not found (404): {url}")
                            return None
                        else:
                            raise Exception(f"HTTP {response.status}: {url}")
                
                result = await self.circuit_breaker.call(fetch_impl)
                
                # Run cache cleanup periodically
                self.cache.cleanup()
                
                return result
                
            except Exception as e:
                last_exception = e
                self.stats.failed_requests += 1
                
                if attempt < self.config.max_retries - 1:
                    self.stats.retries += 1
                    delay = self._get_retry_delay(attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.config.max_retries} attempts: {e}")
        
        # All retries exhausted - try stale cache
        if self.config.stale_cache_fallback:
            stale = self.cache.get(cache_key, allow_stale=True)
            if stale is not None:
                logger.warning(f"Using stale cache as fallback for {url}")
                return stale
        
        # Final failure
        if self.config.raise_on_final_failure:
            raise last_exception
        
        return None
    
    async def _fetch_json(self, url: str, cache_key: Optional[str] = None,
                         data_type: str = "default") -> Optional[Dict]:
        """Fetch JSON from URL."""
        content = await self._fetch(url, cache_key, data_type)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {url}: {e}")
                return None
        return None
    
    def _get_mock_response(self, url: str) -> str:
        """Return mock data for testing."""
        if "submissions/CIK" in url:
            return json.dumps({
                "name": "Mock Company Inc.",
                "cik": "0001234567",
                "filings": {
                    "recent": {
                        "accessionNumber": ["0001234567-24-000001", "0001234567-24-000002"],
                        "form": ["10-K", "10-Q"],
                        "filingDate": ["2024-01-15", "2024-04-15"],
                        "reportDate": ["2023-12-31", "2024-03-31"],
                        "primaryDocument": ["mock-10k.htm", "mock-10q.htm"],
                        "fileNumber": ["001-12345", "001-12345"]
                    }
                }
            })
        elif "companyfacts/CIK" in url:
            return json.dumps({
                "entityName": "Mock Company Inc.",
                "cik": "0001234567",
                "facts": {
                    "us-gaap": {
                        "Revenues": {
                            "units": {
                                "USD": [
                                    {
                                        "val": 1000000,
                                        "fy": 2023,
                                        "fp": "FY",
                                        "form": "10-K",
                                        "filed": "2024-01-15",
                                        "end": "2023-12-31"
                                    }
                                ]
                            }
                        }
                    }
                }
            })
        elif "company_tickers.json" in url:
            return json.dumps({
                "0": {"ticker": "MOCK", "cik_str": "1234567", "title": "Mock Company Inc."}
            })
        else:
            return "<?xml version='1.0'?><document>Mock content</document>"
    
    # ========================================================================
    # Core SEC EDGAR Methods
    # ========================================================================
    
    async def get_company_submissions(self, cik: str) -> Optional[Dict]:
        """
        Get company filing history.
        
        Args:
            cik: Company CIK (with or without leading zeros)
            
        Returns:
            Full submissions JSON including all filings
        """
        cik_padded = cik.zfill(10)
        url = f"{self.BASE_URL}/submissions/CIK{cik_padded}.json"
        cache_key = f"submissions:{cik_padded}"
        return await self._fetch_json(url, cache_key, "submissions")
    
    async def get_xbrl_facts(self, cik: str) -> Optional[Dict]:
        """
        Get XBRL company facts.
        
        Args:
            cik: Company CIK
            
        Returns:
            Complete XBRL facts JSON
        """
        cik_padded = cik.zfill(10)
        url = f"{self.BASE_URL}/api/xbrl/companyfacts/CIK{cik_padded}.json"
        cache_key = f"xbrl:{cik_padded}"
        return await self._fetch_json(url, cache_key, "xbrl")
    
    async def get_ticker_cik_mapping(self) -> Optional[Dict[str, str]]:
        """
        Get ticker to CIK mapping from SEC.
        
        Returns:
            Dictionary mapping ticker symbols to CIKs
        """
        url = "https://www.sec.gov/files/company_tickers.json"
        data = await self._fetch_json(url, "ticker_mapping", "tickers")
        if not data:
            return None
        
        # Convert to simple ticker -> CIK mapping
        mapping = {}
        for entry in data.values():
            ticker = entry.get("ticker", "").upper()
            cik = str(entry.get("cik_str", ""))
            if ticker and cik:
                mapping[ticker] = cik
        
        return mapping
    
    async def cik_from_ticker(self, ticker: str) -> Optional[str]:
        """
        Get CIK from ticker symbol.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            
        Returns:
            CIK string or None if not found
        """
        mapping = await self.get_ticker_cik_mapping()
        if mapping:
            return mapping.get(ticker.upper())
        return None
    
    async def get_filings(
        self,
        cik: str,
        form_types: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get filtered list of filings for a company.
        
        Args:
            cik: Company CIK
            form_types: Filter to specific form types
            start_date: Filter to filings on/after this date
            end_date: Filter to filings on/before this date
            limit: Maximum number of filings to return
            
        Returns:
            List of filing dictionaries
        """
        submissions = await self.get_company_submissions(cik)
        if not submissions:
            return []
        
        filings = []
        recent = submissions.get("filings", {}).get("recent", {})
        
        accessions = recent.get("accessionNumber", [])
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        primary_docs = recent.get("primaryDocument", [])
        
        for i in range(len(accessions)):
            form = forms[i] if i < len(forms) else ""
            
            # Filter by form type
            if form_types and form not in form_types:
                continue
            
            # Parse filing date
            filing_date_str = filing_dates[i] if i < len(filing_dates) else ""
            try:
                filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d').date()
            except ValueError:
                continue
            
            # Filter by date range
            if start_date and filing_date < start_date:
                continue
            if end_date and filing_date > end_date:
                continue
            
            # Parse report date
            report_date = None
            report_date_str = report_dates[i] if i < len(report_dates) else ""
            if report_date_str:
                try:
                    report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            accession = accessions[i]
            primary_doc = primary_docs[i] if i < len(primary_docs) else ""
            
            filings.append({
                "accession_number": accession,
                "form_type": form,
                "filing_date": filing_date.isoformat(),
                "report_date": report_date.isoformat() if report_date else None,
                "primary_document": primary_doc,
                "cik": cik
            })
            
            # Check limit
            if limit and len(filings) >= limit:
                break
        
        return filings
    
    async def get_filing_content(self, cik: str, accession_number: str, 
                                 document: str) -> Optional[str]:
        """
        Get filing document content.
        
        Args:
            cik: Company CIK
            accession_number: Accession number
            document: Document filename
            
        Returns:
            Document content as string
        """
        cik_clean = cik.lstrip("0") or "0"
        accession_clean = accession_number.replace("-", "")
        url = f"{self.ARCHIVES_URL}/{cik_clean}/{accession_clean}/{document}"
        cache_key = f"document:{cik}:{accession_number}:{document}"
        return await self._fetch(url, cache_key, "documents")
    
    # ========================================================================
    # Specialized Methods for JLAW Nodes
    # ========================================================================
    
    async def get_form4_filings(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get Form 4 insider trading filings for a company.
        
        Node 10: Insider Trading Analysis
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for filings
            end_date: End date for filings
            
        Returns:
            List of Form 4 filings
        """
        cik = await self.cik_from_ticker(ticker)
        if not cik:
            logger.error(f"Could not find CIK for ticker {ticker}")
            return []
        
        return await self.get_filings(
            cik,
            form_types=["3", "4", "5"],
            start_date=start_date,
            end_date=end_date
        )
    
    async def get_10k_filings(
        self,
        ticker: str,
        years: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get 10-K annual report filings for a company.
        
        Node 7: Annual Reports Analysis
        
        Args:
            ticker: Stock ticker symbol
            years: Number of years to retrieve
            
        Returns:
            List of 10-K filings
        """
        cik = await self.cik_from_ticker(ticker)
        if not cik:
            logger.error(f"Could not find CIK for ticker {ticker}")
            return []
        
        return await self.get_filings(
            cik,
            form_types=["10-K", "10-K/A"],
            limit=years
        )
    
    async def get_10q_filings(
        self,
        ticker: str,
        quarters: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get 10-Q quarterly report filings for a company.
        
        Node 8: Quarterly Reports Analysis
        
        Args:
            ticker: Stock ticker symbol
            quarters: Number of quarters to retrieve
            
        Returns:
            List of 10-Q filings
        """
        cik = await self.cik_from_ticker(ticker)
        if not cik:
            logger.error(f"Could not find CIK for ticker {ticker}")
            return []
        
        return await self.get_filings(
            cik,
            form_types=["10-Q", "10-Q/A"],
            limit=quarters
        )
    
    async def get_def14a_filings(
        self,
        ticker: str,
        years: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get DEF 14A proxy statement filings for a company.
        
        Node 9: Proxy Statements / Executive Compensation Analysis
        
        Args:
            ticker: Stock ticker symbol
            years: Number of years to retrieve
            
        Returns:
            List of DEF 14A filings
        """
        cik = await self.cik_from_ticker(ticker)
        if not cik:
            logger.error(f"Could not find CIK for ticker {ticker}")
            return []
        
        return await self.get_filings(
            cik,
            form_types=["DEF 14A", "DEFA14A"],
            limit=years
        )
    
    async def get_8k_filings(
        self,
        ticker: str,
        days: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Get 8-K current report filings for a company.
        
        Node 11: Material Events Analysis
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back
            
        Returns:
            List of 8-K filings
        """
        cik = await self.cik_from_ticker(ticker)
        if not cik:
            logger.error(f"Could not find CIK for ticker {ticker}")
            return []
        
        start_date = date.today() - timedelta(days=days)
        
        return await self.get_filings(
            cik,
            form_types=["8-K", "8-K/A"],
            start_date=start_date
        )
    
    async def get_13d_filings(
        self,
        ticker: str,
        years: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get Schedule 13D/13G beneficial ownership filings for a company.
        
        Node 12: Beneficial Ownership Analysis
        
        Args:
            ticker: Stock ticker symbol
            years: Number of years to retrieve
            
        Returns:
            List of 13D/13G filings
        """
        cik = await self.cik_from_ticker(ticker)
        if not cik:
            logger.error(f"Could not find CIK for ticker {ticker}")
            return []
        
        start_date = date.today() - timedelta(days=years * 365)
        
        return await self.get_filings(
            cik,
            form_types=["SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"],
            start_date=start_date
        )
    
    async def get_13f_filings(
        self,
        ticker: str,
        quarters: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get 13F-HR institutional holdings filings for a company.
        
        Node 13: Institutional Holdings Analysis
        
        Args:
            ticker: Stock ticker symbol
            quarters: Number of quarters to retrieve
            
        Returns:
            List of 13F filings
        """
        cik = await self.cik_from_ticker(ticker)
        if not cik:
            logger.error(f"Could not find CIK for ticker {ticker}")
            return []
        
        return await self.get_filings(
            cik,
            form_types=["13F-HR", "13F-HR/A"],
            limit=quarters
        )
    
    # ========================================================================
    # Statistics & Utilities
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.stats.to_dict()
    
    def reset_statistics(self) -> None:
        """Reset statistics."""
        self.stats = Statistics()
    
    def get_circuit_breaker_state(self) -> str:
        """Get current circuit breaker state."""
        return self.circuit_breaker.state.value
    
    def get_effective_rate_limit(self) -> float:
        """Get current effective rate limit considering slowdown."""
        return self.rate_limiter.current_rate / self.rate_limiter.slowdown_multiplier
