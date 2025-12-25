"""
SEC EDGAR Rate Limiter with Cooldown Recovery
==============================================

Production-grade rate limiter implementing:
- Token bucket algorithm (9 requests/second - conservative buffer)
- Automatic 60-second cooldown upon 403 rate limit detection
- Singleton pattern for shared rate limiting across all clients
- Thread-safe async lock implementation
- Request statistics tracking for monitoring

SEC API Rate Limit: 10 requests/second maximum
JLAW Conservative Rate: 9 requests/second (111ms minimum interval)
"""

import asyncio
import time
import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RateLimiterStats:
    """Statistics for rate limiter monitoring."""
    total_requests: int = 0
    cooldown_activations: int = 0
    last_cooldown_time: Optional[datetime] = None
    last_request_time: Optional[datetime] = None
    
    def to_dict(self):
        return {
            "total_requests": self.total_requests,
            "cooldown_activations": self.cooldown_activations,
            "last_cooldown_time": self.last_cooldown_time.isoformat() if self.last_cooldown_time else None,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
        }


class RateLimiter:
    """
    Token bucket rate limiter for SEC EDGAR API with automatic cooldown recovery.
    
    SEC allows 10 requests/second maximum.
    We use 9 req/sec (111ms minimum interval) for safety buffer.
    
    This is a singleton instance shared across all SECEdgarClient instances
    to prevent concurrent rate violations.
    
    Features:
    - Automatic 60-second cooldown upon 403 rate limit detection
    - Request statistics tracking
    - Thread-safe async operations
    """
    
    MIN_INTERVAL = 1.0 / 9.0  # 111ms between requests (conservative)
    COOLDOWN_PERIOD = 60  # seconds after rate limit violation
    
    _instance = None
    
    def __new__(cls, requests_per_second: float = 9.0):
        """Ensure singleton pattern for rate limiter."""
        if cls._instance is None:
            cls._instance = super(RateLimiter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, requests_per_second: float = 9.0):
        """Initialize rate limiter (only once due to singleton)."""
        if getattr(self, '_initialized', False):
            return
        
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0
        self._lock = asyncio.Lock()
        self.stats = RateLimiterStats()
        self._cooldown_until = 0.0  # Timestamp when cooldown ends
        self._initialized = True
        
        logger.info(
            f"Initialized shared SEC rate limiter: {requests_per_second} req/sec "
            f"(min interval: {self.min_interval:.3f}s, cooldown: {self.COOLDOWN_PERIOD}s)"
        )
    
    async def acquire(self):
        """
        Wait until rate limit allows next request.
        
        Enforces minimum interval between requests and handles cooldown periods.
        """
        async with self._lock:
            now = time.time()
            
            # Check if we're in cooldown period
            if now < self._cooldown_until:
                cooldown_remaining = self._cooldown_until - now
                logger.warning(
                    f"Rate limiter in cooldown mode: {cooldown_remaining:.1f}s remaining "
                    f"(total: {self.COOLDOWN_PERIOD}s)"
                )
                await asyncio.sleep(cooldown_remaining)
                now = time.time()
            
            # Enforce minimum interval
            elapsed = now - self.last_request
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                await asyncio.sleep(sleep_time)
            
            self.last_request = time.time()
            self.stats.total_requests += 1
            self.stats.last_request_time = datetime.utcnow()
            
            if self.stats.total_requests % 100 == 0:
                logger.debug(f"Rate limiter: {self.stats.total_requests} requests processed")
    
    def activate_cooldown(self, reason: str = "Rate limit violation detected"):
        """
        Activate cooldown period after rate limit violation.
        
        Args:
            reason: Human-readable reason for cooldown
        """
        self._cooldown_until = time.time() + self.COOLDOWN_PERIOD
        self.stats.cooldown_activations += 1
        self.stats.last_cooldown_time = datetime.utcnow()
        
        logger.error(
            f"SEC API rate limiter cooldown activated: {reason}. "
            f"All requests blocked for {self.COOLDOWN_PERIOD} seconds. "
            f"(Activation #{self.stats.cooldown_activations})"
        )
    
    def is_in_cooldown(self) -> bool:
        """Check if rate limiter is currently in cooldown period."""
        return time.time() < self._cooldown_until
    
    def get_stats(self) -> RateLimiterStats:
        """Get current rate limiter statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset statistics (preserves cooldown state)."""
        cooldown_activations = self.stats.cooldown_activations
        last_cooldown = self.stats.last_cooldown_time
        self.stats = RateLimiterStats()
        self.stats.cooldown_activations = cooldown_activations
        self.stats.last_cooldown_time = last_cooldown


# Global singleton rate limiter instance shared across all clients
_SHARED_RATE_LIMITER = RateLimiter(requests_per_second=9.0)


def get_shared_rate_limiter() -> RateLimiter:
    """
    Get the shared global rate limiter instance.
    
    Returns:
        Singleton RateLimiter instance
    """
    return _SHARED_RATE_LIMITER
