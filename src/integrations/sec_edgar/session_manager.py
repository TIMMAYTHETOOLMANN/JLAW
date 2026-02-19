"""
SEC EDGAR Session Manager with Connection Pooling
==================================================

Manages HTTP sessions with connection pooling, retry logic, and proper
resource cleanup for SEC EDGAR API requests.

Features:
- Connection pooling (10 connections, 20 max size)
- Exponential backoff retry strategy (5 retries, 2x backoff)
- Automatic retry on 429, 500, 502, 503, 504
- Proper User-Agent header management
- Session lifecycle management
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)


class SECSessionManager:
    """
    Manages HTTP sessions with connection pooling and retry logic.
    
    Features:
    - Connection pooling for efficient resource usage
    - Exponential backoff for transient failures
    - Automatic retry on 429 (rate limit), 5xx errors
    - Proper session cleanup
    """
    
    def __init__(self, user_agent: str):
        """
        Initialize session manager.
        
        Args:
            user_agent: User-Agent header for SEC compliance
        """
        self.user_agent = user_agent
        self.session: Optional[requests.Session] = None
        logger.debug("SEC Session Manager initialized")
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests.Session with connection pooling and retry strategy.
        
        Returns:
            Configured requests.Session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=5,  # Total number of retries
            backoff_factor=2,  # 1s, 2s, 4s, 8s, 16s
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["GET", "HEAD"],  # Only retry safe methods
            raise_on_status=False  # Don't raise exception on retry exhaustion
        )
        
        # Configure HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools to cache
            pool_maxsize=20  # Max connections in each pool
        )
        
        # Mount adapter for both HTTP and HTTPS
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Set default headers
        session.headers.update({
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Host": "www.sec.gov"
        })
        
        logger.debug(
            f"Created HTTP session with connection pooling "
            f"(pool_connections=10, pool_maxsize=20, retries=5)"
        )
        
        return session
    
    def get_session(self) -> requests.Session:
        """
        Get or create the HTTP session.
        
        Returns:
            requests.Session instance
        """
        if self.session is None:
            self.session = self._create_session()
        return self.session
    
    def close(self):
        """Close the session and release resources."""
        if self.session:
            self.session.close()
            self.session = None
            logger.debug("Closed HTTP session")
    
    def __enter__(self):
        """Context manager entry."""
        return self.get_session()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AsyncSECSessionManager:
    """
    Async version of session manager for aiohttp.
    
    Note: This is a placeholder for future async session management.
    Current implementation uses aiohttp.ClientSession directly in SECEdgarClient.
    """
    
    def __init__(self, user_agent: str):
        """Initialize async session manager."""
        self.user_agent = user_agent
        logger.debug("Async SEC Session Manager initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        import aiohttp
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Accept": "*/*",
                "Connection": "keep-alive",
                "Host": "www.sec.gov"
            },
            trust_env=True,
        )
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self, 'session') and self.session:
            await self.session.close()
