"""
Unified SDK Manager for JLAW Forensic System
=============================================

Singleton manager that consolidates all OpenAI, Anthropic, and HTTP client
instantiations across the codebase, eliminating redundant SDK initializations
and enabling connection pooling.

Key Features:
- Single AsyncOpenAI client (primary) for async code
- Single OpenAI client (primary) for sync code
- Single AsyncOpenAI client (secondary for dual-OpenAI mode)
- Single OpenAI client (secondary) for sync code
- Single AsyncAnthropic client
- Shared aiohttp.ClientSession with connection pooling
- SEC EDGAR rate limiting (0.35s delay, semaphore for concurrent requests)
- Automatic retry logic with exponential backoff
- Graceful fallback handling (OpenRouter, secondary keys)

Usage:
    from src.forensics.sdk_manager import get_sdk_manager_sync
    
    sdk = get_sdk_manager_sync()
    
    # Use OpenAI client (sync or async)
    response = sdk.openai.chat.completions.create(...)
    response = await sdk.openai_async.chat.completions.create(...)
    
    # Use Anthropic client
    response = await sdk.anthropic.messages.create(...)
    
    # Make SEC requests with rate limiting
    response = await sdk.sec_request(url, user_agent)
    
    # Cleanup
    await sdk.close()
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager

import aiohttp

logger = logging.getLogger(__name__)

# Global singleton instance
_sdk_manager_instance: Optional['UnifiedSDKManager'] = None
_sdk_manager_lock = asyncio.Lock()


class UnifiedSDKManager:
    """
    Singleton SDK manager for all OpenAI, Anthropic, and HTTP clients.
    
    Ensures single client instantiation across the entire application,
    enabling connection pooling and centralized rate limiting.
    """
    
    def __init__(self):
        """Initialize SDK manager (should only be called once via get_sdk_manager())."""
        # Lazy-loaded clients (sync versions for backward compatibility)
        self._openai_client: Optional[Any] = None
        self._openai_secondary_client: Optional[Any] = None
        
        # Async versions for new async code
        self._openai_async_client: Optional[Any] = None
        self._openai_secondary_async_client: Optional[Any] = None
        self._anthropic_client: Optional[Any] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
        
        # Configuration (loaded lazily)
        self._config = None
        
        # SEC rate limiting
        self._sec_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent SEC requests
        self._last_sec_request_time = 0.0
        self._sec_rate_limit_delay = 0.35  # SEC allows 10 req/sec, use 0.35s for safety
        
        # Retry configuration
        self._max_retries = 3
        self._retry_backoff_base = 2  # Exponential backoff multiplier
        
        # Availability flags
        self._openai_available = False
        self._openai_secondary_available = False
        self._anthropic_available = False
        
        logger.info("✅ UnifiedSDKManager initialized (singleton)")
    
    def _load_config(self):
        """Lazy load configuration."""
        if self._config is None:
            from src.forensics.config_manager import get_config
            self._config = get_config().config
        return self._config
    
    @property
    def openai(self):
        """
        Get primary OpenAI sync client (lazy-loaded).
        For backward compatibility with sync code.
        
        Returns:
            OpenAI sync client or None if not available
        """
        if self._openai_client is None:
            try:
                from openai import OpenAI
                config = self._load_config()
                
                if config.openai.api_key:
                    self._openai_client = OpenAI(
                        api_key=config.openai.api_key,
                        max_retries=self._max_retries,
                        timeout=60.0
                    )
                    self._openai_available = True
                    logger.info(f"✅ Primary OpenAI sync client initialized (model: {config.openai.model})")
                else:
                    logger.warning("⚠️ OPENAI_API_KEY not set - OpenAI features disabled")
            except ImportError:
                logger.warning("⚠️ openai package not available - install with: pip install openai")
            except Exception as e:
                logger.error(f"❌ Failed to initialize primary OpenAI sync client: {e}")
        
        return self._openai_client
    
    @property
    def openai_async(self):
        """
        Get primary OpenAI async client (lazy-loaded).
        For new async code.
        
        Returns:
            AsyncOpenAI client or None if not available
        """
        if self._openai_async_client is None:
            try:
                from openai import AsyncOpenAI
                config = self._load_config()
                
                if config.openai.api_key:
                    self._openai_async_client = AsyncOpenAI(
                        api_key=config.openai.api_key,
                        max_retries=self._max_retries,
                        timeout=60.0
                    )
                    self._openai_available = True
                    logger.info(f"✅ Primary OpenAI async client initialized (model: {config.openai.model})")
                else:
                    logger.warning("⚠️ OPENAI_API_KEY not set - OpenAI features disabled")
            except ImportError:
                logger.warning("⚠️ openai package not available - install with: pip install openai")
            except Exception as e:
                logger.error(f"❌ Failed to initialize primary OpenAI async client: {e}")
        
        return self._openai_async_client
    
    @property
    def openai_secondary(self):
        """
        Get secondary OpenAI sync client (lazy-loaded).
        Used for dual-OpenAI mode when Anthropic is not available.
        
        Returns:
            OpenAI sync client or None if not available
        """
        if self._openai_secondary_client is None:
            try:
                from openai import OpenAI
                config = self._load_config()
                
                if config.openai.secondary_api_key:
                    self._openai_secondary_client = OpenAI(
                        api_key=config.openai.secondary_api_key,
                        max_retries=self._max_retries,
                        timeout=60.0
                    )
                    self._openai_secondary_available = True
                    logger.info("✅ Secondary OpenAI sync client initialized (dual-OpenAI mode)")
                else:
                    logger.debug("Secondary OpenAI key not configured")
            except ImportError:
                logger.warning("⚠️ openai package not available - install with: pip install openai")
            except Exception as e:
                logger.error(f"❌ Failed to initialize secondary OpenAI sync client: {e}")
        
        return self._openai_secondary_client
    
    @property
    def openai_secondary_async(self):
        """
        Get secondary OpenAI async client (lazy-loaded).
        Used for dual-OpenAI mode when Anthropic is not available.
        
        Returns:
            AsyncOpenAI client or None if not available
        """
        if self._openai_secondary_async_client is None:
            try:
                from openai import AsyncOpenAI
                config = self._load_config()
                
                if config.openai.secondary_api_key:
                    self._openai_secondary_async_client = AsyncOpenAI(
                        api_key=config.openai.secondary_api_key,
                        max_retries=self._max_retries,
                        timeout=60.0
                    )
                    self._openai_secondary_available = True
                    logger.info("✅ Secondary OpenAI async client initialized (dual-OpenAI mode)")
                else:
                    logger.debug("Secondary OpenAI key not configured")
            except ImportError:
                logger.warning("⚠️ openai package not available - install with: pip install openai")
            except Exception as e:
                logger.error(f"❌ Failed to initialize secondary OpenAI async client: {e}")
        
        return self._openai_secondary_async_client
    
    @property
    def anthropic(self):
        """
        Get Anthropic async client (lazy-loaded).
        
        Returns:
            AsyncAnthropic client or None if not available
        """
        if self._anthropic_client is None:
            try:
                from anthropic import AsyncAnthropic
                config = self._load_config()
                
                if config.anthropic.api_key:
                    self._anthropic_client = AsyncAnthropic(
                        api_key=config.anthropic.api_key,
                        max_retries=self._max_retries,
                        timeout=60.0
                    )
                    self._anthropic_available = True
                    logger.info(f"✅ Anthropic client initialized (model: {config.anthropic.model})")
                else:
                    logger.warning("⚠️ ANTHROPIC_API_KEY not set - Anthropic features disabled")
            except ImportError:
                logger.warning("⚠️ anthropic package not available - install with: pip install anthropic")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Anthropic client: {e}")
        
        return self._anthropic_client
    
    @property
    def http_session(self) -> aiohttp.ClientSession:
        """
        Get shared aiohttp ClientSession with connection pooling (lazy-loaded).
        
        Returns:
            Shared aiohttp.ClientSession
        """
        if self._http_session is None or self._http_session.closed:
            # Connection pooling configuration for optimal performance
            connector = aiohttp.TCPConnector(
                limit=100,  # Max 100 total connections
                limit_per_host=10,  # Max 10 connections per host
                ttl_dns_cache=300,  # DNS cache TTL (5 minutes)
                enable_cleanup_closed=True,
                force_close=False  # Enable connection reuse
            )
            
            timeout = aiohttp.ClientTimeout(
                total=60,  # Total timeout
                connect=10,  # Connection timeout
                sock_read=30  # Socket read timeout
            )
            
            self._http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                raise_for_status=False  # Don't raise on 4xx/5xx, handle manually
            )
            logger.info("✅ Shared HTTP session initialized with connection pooling")
        
        return self._http_session
    
    async def sec_request(
        self,
        url: str,
        user_agent: str,
        method: str = 'GET',
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Make SEC EDGAR request with automatic rate limiting and retry logic.
        
        Enforces SEC's rate limit of 10 requests/second (uses 0.35s delay for safety).
        Includes semaphore to prevent concurrent request overflow.
        
        Args:
            url: SEC EDGAR URL to fetch
            user_agent: SEC-compliant User-Agent string
            method: HTTP method (default: GET)
            **kwargs: Additional arguments for aiohttp request
        
        Returns:
            aiohttp.ClientResponse
        
        Raises:
            aiohttp.ClientError: On persistent failures after retries
        """
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = user_agent
        headers.setdefault('Accept', 'text/xml,application/xml,text/html,*/*')
        
        async with self._sec_semaphore:
            # Rate limiting: ensure 0.35s between requests
            now = time.time()
            time_since_last = now - self._last_sec_request_time
            if time_since_last < self._sec_rate_limit_delay:
                await asyncio.sleep(self._sec_rate_limit_delay - time_since_last)
            
            # Retry logic with exponential backoff
            for attempt in range(self._max_retries):
                try:
                    session = self.http_session
                    response = await session.request(method, url, headers=headers, **kwargs)
                    self._last_sec_request_time = time.time()
                    
                    # Handle rate limiting from SEC
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 5))
                        logger.warning(f"SEC rate limit hit, waiting {retry_after}s (attempt {attempt + 1}/{self._max_retries})")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Success or client error (don't retry 4xx except 429)
                    if response.status < 500:
                        return response
                    
                    # Server error - retry with exponential backoff
                    if attempt < self._max_retries - 1:
                        backoff = self._retry_backoff_base ** attempt
                        logger.warning(f"SEC request failed with {response.status}, retrying in {backoff}s (attempt {attempt + 1}/{self._max_retries})")
                        await asyncio.sleep(backoff)
                        continue
                    
                    # Last attempt failed
                    return response
                    
                except asyncio.TimeoutError:
                    if attempt < self._max_retries - 1:
                        backoff = self._retry_backoff_base ** attempt
                        logger.warning(f"SEC request timeout, retrying in {backoff}s (attempt {attempt + 1}/{self._max_retries})")
                        await asyncio.sleep(backoff)
                    else:
                        raise
                
                except Exception as e:
                    if attempt < self._max_retries - 1:
                        backoff = self._retry_backoff_base ** attempt
                        logger.warning(f"SEC request error: {e}, retrying in {backoff}s (attempt {attempt + 1}/{self._max_retries})")
                        await asyncio.sleep(backoff)
                    else:
                        raise
    
    def get_availability(self) -> Dict[str, bool]:
        """
        Get availability status of all SDK clients.
        
        Returns:
            Dict with availability flags for each client
        """
        # Trigger lazy loading to check availability
        _ = self.openai
        _ = self.openai_secondary
        _ = self.anthropic
        
        return {
            'openai': self._openai_available,
            'openai_secondary': self._openai_secondary_available,
            'anthropic': self._anthropic_available,
            'dual_agent': self._openai_available and (self._anthropic_available or self._openai_secondary_available)
        }
    
    async def close(self):
        """
        Close all SDK clients and cleanup resources.
        
        Should be called on application shutdown.
        """
        logger.info("Closing UnifiedSDKManager resources...")
        
        # Close HTTP session
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            logger.info("✅ HTTP session closed")
        
        # OpenAI sync clients don't need async cleanup
        if self._openai_client:
            try:
                self._openai_client.close()
                logger.info("✅ Primary OpenAI sync client closed")
            except Exception as e:
                logger.warning(f"Error closing primary OpenAI sync client: {e}")
        
        if self._openai_secondary_client:
            try:
                self._openai_secondary_client.close()
                logger.info("✅ Secondary OpenAI sync client closed")
            except Exception as e:
                logger.warning(f"Error closing secondary OpenAI sync client: {e}")
        
        # OpenAI async clients need async cleanup
        if self._openai_async_client:
            try:
                await self._openai_async_client.close()
                logger.info("✅ Primary OpenAI async client closed")
            except Exception as e:
                logger.warning(f"Error closing primary OpenAI async client: {e}")
        
        if self._openai_secondary_async_client:
            try:
                await self._openai_secondary_async_client.close()
                logger.info("✅ Secondary OpenAI async client closed")
            except Exception as e:
                logger.warning(f"Error closing secondary OpenAI async client: {e}")
        
        # Anthropic client cleanup
        if self._anthropic_client:
            try:
                await self._anthropic_client.close()
                logger.info("✅ Anthropic client closed")
            except Exception as e:
                logger.warning(f"Error closing Anthropic client: {e}")
        
        logger.info("✅ UnifiedSDKManager cleanup complete")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


async def get_sdk_manager() -> UnifiedSDKManager:
    """
    Get the singleton UnifiedSDKManager instance.
    
    Thread-safe singleton initialization.
    
    Returns:
        UnifiedSDKManager singleton instance
    
    Usage:
        sdk = await get_sdk_manager()
        response = await sdk.openai.chat.completions.create(...)
    """
    global _sdk_manager_instance
    
    if _sdk_manager_instance is None:
        async with _sdk_manager_lock:
            if _sdk_manager_instance is None:
                _sdk_manager_instance = UnifiedSDKManager()
    
    return _sdk_manager_instance


def get_sdk_manager_sync() -> UnifiedSDKManager:
    """
    Get the singleton UnifiedSDKManager instance (synchronous version).
    
    Use this for synchronous code that needs access to the SDK manager.
    The manager itself is thread-safe after initialization.
    
    Returns:
        UnifiedSDKManager singleton instance
    
    Usage:
        sdk = get_sdk_manager_sync()
        # Note: Still need to await async operations
        response = await sdk.openai.chat.completions.create(...)
    """
    global _sdk_manager_instance
    
    if _sdk_manager_instance is None:
        _sdk_manager_instance = UnifiedSDKManager()
    
    return _sdk_manager_instance


@asynccontextmanager
async def sdk_manager_context():
    """
    Context manager for UnifiedSDKManager with automatic cleanup.
    
    Usage:
        async with sdk_manager_context() as sdk:
            response = await sdk.openai.chat.completions.create(...)
    """
    sdk = await get_sdk_manager()
    try:
        yield sdk
    finally:
        await sdk.close()


# Convenience function for backward compatibility
def reset_sdk_manager():
    """
    Reset the SDK manager singleton (primarily for testing).
    
    ⚠️ WARNING: Only use in test scenarios. In production, the singleton
    should persist for the lifetime of the application.
    """
    global _sdk_manager_instance
    if _sdk_manager_instance:
        logger.warning("Resetting SDK manager singleton (test mode)")
    _sdk_manager_instance = None
