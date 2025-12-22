"""
Circuit Breaker Pattern for Fault-Tolerant Execution
====================================================

Implements the Circuit Breaker pattern for handling transient failures in
distributed systems and external service calls.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failure threshold exceeded, requests fail fast
- HALF_OPEN: Testing if service recovered, limited requests allowed

Usage:
    breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=Exception
    )
    
    result = await breaker.call(some_async_function, *args, **kwargs)
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Type, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"      # Failures exceeded threshold, failing fast
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    last_success_time: Optional[datetime]
    state_changed_at: datetime
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    
    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "state_changed_at": self.state_changed_at.isoformat(),
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes
        }


class CircuitBreaker:
    """
    Circuit Breaker for fault-tolerant async execution.
    
    Implements the Circuit Breaker pattern with three states:
    - CLOSED: Normal operation (default)
    - OPEN: Failure threshold exceeded, failing fast
    - HALF_OPEN: Testing if service recovered
    
    Features:
    - Automatic state transitions based on failure threshold
    - Recovery timeout before testing service
    - Success threshold for transitioning from HALF_OPEN to CLOSED
    - Configurable exception types to monitor
    - Comprehensive metrics tracking
    
    Example:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        
        try:
            result = await breaker.call(external_api_call, arg1, arg2)
        except CircuitBreakerOpenError:
            # Circuit is open, service unavailable
            result = use_fallback()
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        expected_exception: Type[Exception] = Exception,
        name: Optional[str] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery (HALF_OPEN)
            success_threshold: Number of successes in HALF_OPEN to close circuit
            expected_exception: Exception type to monitor (default: Exception)
            name: Optional name for logging/identification
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception
        self.name = name or "CircuitBreaker"
        
        # State management
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._last_success_time: Optional[datetime] = None
        self._state_changed_at = datetime.utcnow()
        
        # Metrics
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        
        # Thread safety
        self._lock = asyncio.Lock()
        
        logger.info(f"{self.name} initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def metrics(self) -> CircuitBreakerMetrics:
        """Get current metrics."""
        return CircuitBreakerMetrics(
            state=self._state,
            failure_count=self._failure_count,
            success_count=self._success_count,
            last_failure_time=self._last_failure_time,
            last_success_time=self._last_success_time,
            state_changed_at=self._state_changed_at,
            total_calls=self._total_calls,
            total_failures=self._total_failures,
            total_successes=self._total_successes
        )
    
    async def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Exception: Original exception from function if circuit allows
        """
        async with self._lock:
            self._total_calls += 1
            
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    logger.warning(f"{self.name}: Circuit OPEN, failing fast")
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Last failure: {self._last_failure_time}"
                    )
        
        # Execute function (outside lock to allow concurrent calls in CLOSED state)
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        
        except self.expected_exception as e:
            await self._on_failure(e)
            raise
    
    async def _on_success(self):
        """Handle successful function execution."""
        async with self._lock:
            self._success_count += 1
            self._total_successes += 1
            self._last_success_time = datetime.utcnow()
            
            if self._state == CircuitState.HALF_OPEN:
                # Check if we've had enough successes to close circuit
                if self._success_count >= self.success_threshold:
                    self._transition_to_closed()
                    logger.info(f"{self.name}: Service recovered, circuit CLOSED")
            
            # Reset failure count on success in CLOSED state
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0
    
    async def _on_failure(self, exception: Exception):
        """Handle failed function execution."""
        async with self._lock:
            self._failure_count += 1
            self._total_failures += 1
            self._last_failure_time = datetime.utcnow()
            
            logger.warning(
                f"{self.name}: Failure #{self._failure_count} - {exception.__class__.__name__}: {exception}"
            )
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN immediately opens circuit
                self._transition_to_open()
                logger.error(f"{self.name}: Recovery failed, circuit reopened")
            
            elif self._state == CircuitState.CLOSED:
                # Check if we've exceeded failure threshold
                if self._failure_count >= self.failure_threshold:
                    self._transition_to_open()
                    logger.error(
                        f"{self.name}: Failure threshold ({self.failure_threshold}) exceeded, "
                        f"circuit OPEN for {self.recovery_timeout}s"
                    )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if not self._last_failure_time:
            return True
        
        time_since_failure = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout
    
    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        self._state = CircuitState.OPEN
        self._state_changed_at = datetime.utcnow()
        self._success_count = 0
    
    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state."""
        self._state = CircuitState.HALF_OPEN
        self._state_changed_at = datetime.utcnow()
        self._failure_count = 0
        self._success_count = 0
        logger.info(f"{self.name}: Testing recovery, circuit HALF_OPEN")
    
    def _transition_to_closed(self):
        """Transition circuit to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._state_changed_at = datetime.utcnow()
        self._failure_count = 0
        self._success_count = 0
    
    async def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        async with self._lock:
            self._transition_to_closed()
            logger.info(f"{self.name}: Manually reset to CLOSED")
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CircuitBreaker(name='{self.name}', state={self._state.value}, "
            f"failures={self._failure_count}/{self.failure_threshold})"
        )


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    
    Provides centralized management of circuit breakers for different
    services or operations.
    
    Example:
        registry = CircuitBreakerRegistry()
        
        # Register circuit breakers
        registry.register("sec_api", failure_threshold=5, recovery_timeout=60)
        registry.register("polygon_api", failure_threshold=3, recovery_timeout=30)
        
        # Use circuit breakers
        breaker = registry.get("sec_api")
        result = await breaker.call(fetch_sec_data, cik)
    """
    
    def __init__(self):
        """Initialize registry."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def register(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        expected_exception: Type[Exception] = Exception
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker.
        
        Args:
            name: Unique name for circuit breaker
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before testing recovery
            success_threshold: Successes needed to close from HALF_OPEN
            expected_exception: Exception type to monitor
            
        Returns:
            Registered CircuitBreaker instance
        """
        async with self._lock:
            if name in self._breakers:
                logger.warning(f"Circuit breaker '{name}' already registered, returning existing")
                return self._breakers[name]
            
            breaker = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
                expected_exception=expected_exception,
                name=name
            )
            self._breakers[name] = breaker
            
            logger.info(f"Registered circuit breaker: {name}")
            return breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)
    
    def get_all_metrics(self) -> dict[str, CircuitBreakerMetrics]:
        """Get metrics for all registered circuit breakers."""
        return {
            name: breaker.metrics
            for name, breaker in self._breakers.items()
        }
    
    async def reset_all(self):
        """Reset all circuit breakers to CLOSED state."""
        for breaker in self._breakers.values():
            await breaker.reset()
        logger.info(f"Reset {len(self._breakers)} circuit breakers")


__all__ = [
    'CircuitBreaker',
    'CircuitBreakerRegistry',
    'CircuitState',
    'CircuitBreakerOpenError',
    'CircuitBreakerMetrics'
]
