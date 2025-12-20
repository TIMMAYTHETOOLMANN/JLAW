"""
Retry Handler with Exponential Backoff
======================================

Provides robust retry logic for:
- Failed node executions
- API call failures
- Transient errors

Features:
- Exponential backoff with jitter
- Configurable retry limits
- Exception filtering
- Async support
"""

import asyncio
import random
import logging
from typing import Callable, Any, Optional, List, Type, Union
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RetryExhausted(Exception):
    """All retry attempts exhausted."""
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_range: tuple = (0.5, 1.5)
    
    # Exceptions to retry on (empty = retry all)
    retryable_exceptions: List[Type[Exception]] = None
    
    # Exceptions to never retry
    non_retryable_exceptions: List[Type[Exception]] = None
    
    def __post_init__(self):
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [Exception]
        if self.non_retryable_exceptions is None:
            self.non_retryable_exceptions = [KeyboardInterrupt, SystemExit]


class RetryHandler:
    """
    Handles retry logic with exponential backoff.
    
    Usage:
        handler = RetryHandler(max_retries=3)
        
        # Async function
        result = await handler.execute_async(my_async_func, arg1, arg2)
        
        # Sync function
        result = handler.execute(my_sync_func, arg1, arg2)
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry with exponential backoff and optional jitter."""
        delay = self.config.initial_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            jitter_min, jitter_max = self.config.jitter_range
            delay *= random.uniform(jitter_min, jitter_max)
        
        return delay
    
    def _should_retry(self, exception: Exception) -> bool:
        """Determine if exception should trigger a retry."""
        # Never retry these
        for exc_type in self.config.non_retryable_exceptions:
            if isinstance(exception, exc_type):
                return False
        
        # Check if exception is retryable
        for exc_type in self.config.retryable_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        return False
    
    async def execute_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryExhausted: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if not self._should_retry(e):
                    self.logger.error(f"Non-retryable exception: {e}")
                    raise
                
                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"All {self.config.max_retries + 1} attempts failed for {func.__name__}"
                    )
        
        raise RetryExhausted(
            f"Function {func.__name__} failed after {self.config.max_retries + 1} attempts",
            last_exception
        )
    
    def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute sync function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryExhausted: If all retries fail
        """
        import time
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if not self._should_retry(e):
                    self.logger.error(f"Non-retryable exception: {e}")
                    raise
                
                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"All {self.config.max_retries + 1} attempts failed for {func.__name__}"
                    )
        
        raise RetryExhausted(
            f"Function {func.__name__} failed after {self.config.max_retries + 1} attempts",
            last_exception
        )


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    Decorator for adding retry logic to functions.
    
    Usage:
        @with_retry(max_retries=3, initial_delay=1.0)
        async def my_api_call():
            # ... may fail transiently ...
            pass
    """
    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        retryable_exceptions=retryable_exceptions or [Exception]
    )
    handler = RetryHandler(config)
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await handler.execute_async(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return handler.execute(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Pre-configured handlers for common use cases
API_RETRY_HANDLER = RetryHandler(RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
))

NODE_RETRY_HANDLER = RetryHandler(RetryConfig(
    max_retries=2,
    initial_delay=2.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
))

SEC_EDGAR_RETRY_HANDLER = RetryHandler(RetryConfig(
    max_retries=5,
    initial_delay=1.0,
    max_delay=120.0,
    exponential_base=2.0,
    jitter=True
))
