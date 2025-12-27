"""
Rate Limiter for SEC EDGAR API
===============================

Re-export of the shared SEC EDGAR rate limiter with extended interface
for zero-dollar transaction acquisition module.

SEC Guidelines:
- Maximum 10 requests per second
- Identify requests with proper User-Agent
- Avoid excessive load during market hours

Reference:
- JLAW Zero-Dollar Transaction Forensic Specification v1.0
- Section 12.2: SEC EDGAR Acquisition Module
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Optional

# Import the shared rate limiter from existing SEC EDGAR integration
from src.integrations.sec_edgar import RateLimiter as BaseRateLimiter, get_shared_rate_limiter


class EdgarRateLimiter:
    """
    Rate limiter for SEC EDGAR API compliance (wraps base rate limiter).
    
    SEC Guidelines:
        - Maximum 10 requests per second
        - Identify requests with proper User-Agent
        - Avoid excessive load during market hours
    
    This class wraps the existing SEC EDGAR rate limiter with additional
    convenience methods for the zero-dollar acquisition module.
    """
    
    def __init__(self, max_requests_per_second: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_second: Maximum requests per second (default: 10)
        """
        # Get the shared base rate limiter (singleton)
        self._base_limiter = get_shared_rate_limiter()
        self.max_requests_per_second = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second
    
    async def acquire(self):
        """
        Acquire rate limit slot with proper spacing.
        
        Delegates to the base rate limiter which handles
        rate limiting and cooldown periods.
        """
        await self._base_limiter.acquire()
    
    @asynccontextmanager
    async def throttle(self):
        """
        Context manager for throttled requests.
        
        Usage:
            async with rate_limiter.throttle():
                response = await make_request()
        """
        await self.acquire()
        yield
    
    def activate_cooldown(self, reason: str = "Rate limit violation detected"):
        """Activate cooldown period after rate limit violation."""
        self._base_limiter.activate_cooldown(reason)
    
    def is_in_cooldown(self) -> bool:
        """Check if rate limiter is currently in cooldown period."""
        return self._base_limiter.is_in_cooldown()
    
    def get_stats(self):
        """Get current rate limiter statistics."""
        return self._base_limiter.get_stats()


# Export convenience function to get shared rate limiter
def get_edgar_rate_limiter() -> BaseRateLimiter:
    """
    Get the shared global rate limiter instance.
    
    Returns:
        Singleton RateLimiter instance
    """
    return get_shared_rate_limiter()

