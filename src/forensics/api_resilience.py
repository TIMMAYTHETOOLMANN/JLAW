"""
Production-grade API resilience with circuit breakers and retry logic.
Implements zero-tolerance failure handling for forensic operations.
"""

import asyncio
import time
import random
import hashlib
import hmac
import json
from typing import Dict, Any, Optional, Callable, List, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from collections import deque
import logging
import uuid

from src.forensics.core.integrity_manager import IntegrityError, ForensicHashChain, IntegrityLevel

T = TypeVar('T')

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery

class FailureType(Enum):
    """Failure classification for handling strategy."""
    TRANSIENT = "TRANSIENT"  # Retry with backoff
    PERMANENT = "PERMANENT"  # Fail fast
    RATE_LIMIT = "RATE_LIMIT"  # Special backoff
    INTEGRITY = "INTEGRITY"  # Hard failure, halt system

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: float = 0.5  # 50% failure rate
    recovery_timeout: int = 30  # Seconds in OPEN state
    expected_exception_types: List[type] = field(default_factory=lambda: [
        ConnectionError, TimeoutError, asyncio.TimeoutError
    ])
    window_size: int = 10  # Rolling window for failure rate
    half_open_max_calls: int = 3  # Test calls in HALF_OPEN

@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 0.5  # Base delay in seconds
    max_delay: float = 32.0  # Maximum backoff
    exponential_base: float = 2.0
    jitter: float = 1.0  # ±1 second jitter

class CircuitBreaker(Generic[T]):
    """
    Circuit breaker pattern preventing cascade failures.
    Monitors failure rates and temporarily blocks calls.
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig = CircuitBreakerConfig(),
        fallback: Optional[Callable[[], T]] = None
    ):
        self.name = name
        self.config = config
        self.fallback = fallback
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self.call_history = deque(maxlen=config.window_size)
        self._lock = asyncio.Lock()
        self.state_changes: List[Dict[str, Any]] = []

        # Forensic tracking
        self.hash_chain = ForensicHashChain(f"circuit_{name}")

    async def call(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result or fallback value
            
        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Original exception: If CLOSED and function fails
        """
        async with self._lock:
            current_state = await self._get_state()

            if current_state == CircuitState.OPEN:
                # Log state for forensics
                await self._log_call_attempt("REJECTED", current_state)

                if self.fallback:
                    return self.fallback()
                raise CircuitBreakerOpenError(
                    f"Circuit breaker {self.name} is OPEN"
                )

            if current_state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    # Exceeded test calls, evaluate
                    await self._evaluate_half_open()
                    return await self.call(func, *args, **kwargs)
                self.half_open_calls += 1

        # Execute the function
        try:
            start_time = time.monotonic()
            result = await func(*args, **kwargs)
            duration = time.monotonic() - start_time

            async with self._lock:
                await self._record_success(duration)

            return result

        except Exception as e:
            async with self._lock:
                await self._record_failure(e)
            raise

    async def _get_state(self) -> CircuitState:
        """Determine current circuit state."""
        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                time_since_failure = (
                    datetime.now(timezone.utc) - self.last_failure_time
                ).total_seconds()

                if time_since_failure > self.config.recovery_timeout:
                    await self._transition_state(CircuitState.HALF_OPEN)

        return self.state

    async def _record_success(self, duration: float):
        """Record successful call."""
        self.success_count += 1
        self.call_history.append(True)

        await self._log_call_attempt("SUCCESS", self.state, duration)

        if self.state == CircuitState.HALF_OPEN:
            # Check if we can close the circuit
            success_rate = sum(self.call_history) / len(self.call_history)
            if success_rate > (1 - self.config.failure_threshold):
                await self._transition_state(CircuitState.CLOSED)

    async def _record_failure(self, exception: Exception):
        """Record failed call."""
        self.failure_count += 1
        self.call_history.append(False)
        self.last_failure_time = datetime.now(timezone.utc)

        await self._log_call_attempt("FAILURE", self.state, error=str(exception))

        # Check if we should open the circuit
        if len(self.call_history) >= self.config.window_size:
            failure_rate = 1 - (sum(self.call_history) / len(self.call_history))

            if failure_rate >= self.config.failure_threshold:
                await self._transition_state(CircuitState.OPEN)

    async def _evaluate_half_open(self):
        """Evaluate HALF_OPEN state after test calls."""
        success_rate = sum(self.call_history[-self.half_open_calls:]) / self.half_open_calls

        if success_rate > 0.5:
            await self._transition_state(CircuitState.CLOSED)
        else:
            await self._transition_state(CircuitState.OPEN)

        self.half_open_calls = 0

    async def _transition_state(self, new_state: CircuitState):
        """Transition to new state with logging."""
        old_state = self.state
        self.state = new_state

        transition = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_state": old_state.value,
            "to_state": new_state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count
        }

        self.state_changes.append(transition)

        # Add to forensic chain
        await self.hash_chain.add_evidence(
            transition,
            IntegrityLevel.HIGH
        )

        # Alert on critical transitions
        if new_state == CircuitState.OPEN:
            await self._alert_circuit_open()

    async def _log_call_attempt(
        self,
        result: str,
        state: CircuitState,
        duration: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Log call attempt for forensics."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "circuit": self.name,
            "state": state.value,
            "result": result,
            "duration_ms": duration * 1000 if duration else None,
            "error": error
        }

        await self.hash_chain.add_evidence(
            log_entry,
            IntegrityLevel.MEDIUM
        )

    async def _alert_circuit_open(self):
        """Alert when circuit opens."""
        # In production, this would send to monitoring system
        logging.critical(
            f"Circuit breaker {self.name} OPENED - "
            f"Failure rate: {self.failure_count}/{self.failure_count + self.success_count}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        total_calls = self.failure_count + self.success_count

        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_rate": self.failure_count / total_calls if total_calls > 0 else 0,
            "total_calls": total_calls,
            "state_changes": len(self.state_changes),
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }

class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open."""
    pass

class ExponentialBackoff:
    """
    Exponential backoff with jitter for retry logic.
    Implements AWS best practices for API resilience.
    """

    def __init__(self, config: RetryConfig = RetryConfig()):
        self.config = config
        self.attempt = 0

    def next_delay(self) -> float:
        """Calculate next delay with jitter."""
        if self.attempt >= self.config.max_attempts:
            raise MaxRetriesExceededError(
                f"Maximum retries ({self.config.max_attempts}) exceeded"
            )

        # Calculate base delay
        delay = min(
            self.config.max_delay,
            self.config.base_delay * (self.config.exponential_base ** self.attempt)
        )

        # Add jitter
        jitter = random.uniform(-self.config.jitter, self.config.jitter)
        delay = max(0, delay + jitter)

        self.attempt += 1
        return delay

    def reset(self):
        """Reset backoff counter."""
        self.attempt = 0

class MaxRetriesExceededError(Exception):
    """Maximum retry attempts exceeded."""
    pass

class ResilientAPIClient:
    """
    Resilient API client with comprehensive failure handling.
    Combines circuit breaker, retry logic, and forensic tracking.
    """

    def __init__(
        self,
        name: str,
        circuit_config: CircuitBreakerConfig = CircuitBreakerConfig(),
        retry_config: RetryConfig = RetryConfig()
    ):
        self.name = name
        self.circuit_breaker = CircuitBreaker(name, circuit_config)
        self.retry_config = retry_config
        self.request_id_header = "X-Request-ID"
        self.idempotency_header = "X-Idempotency-Key"
        self.signature_header = "X-Signature"
        self.timestamp_header = "X-Timestamp"

        # Forensic tracking
        self.hash_chain = ForensicHashChain(f"api_{name}")
        self.request_log: List[Dict[str, Any]] = []

    async def execute_with_resilience(
        self,
        func: Callable[..., T],
        *args,
        failure_classifier: Optional[Callable[[Exception], FailureType]] = None,
        **kwargs
    ) -> T:
        """
        Execute function with full resilience patterns.
        
        Args:
            func: Async function to execute
            failure_classifier: Function to classify exceptions
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            IntegrityError: On integrity violations (hard failure)
            Original exception: After all retries exhausted
        """
        backoff = ExponentialBackoff(self.retry_config)
        request_id = str(uuid.uuid4())

        # Add forensic tracking
        await self._log_request_start(request_id, func.__name__)

        last_exception = None

        for attempt in range(self.retry_config.max_attempts):
            try:
                # Execute through circuit breaker
                result = await self.circuit_breaker.call(
                    self._execute_with_headers,
                    func,
                    request_id,
                    *args,
                    **kwargs
                )

                # Success - log and return
                await self._log_request_success(request_id, attempt + 1)
                return result

            except Exception as e:
                # Classify failure
                failure_type = self._classify_failure(e, failure_classifier)

                # Handle based on type
                if failure_type == FailureType.INTEGRITY:
                    # Hard failure - halt system
                    await self._handle_integrity_failure(request_id, e)
                    raise IntegrityError(f"Integrity violation: {e}")

                elif failure_type == FailureType.PERMANENT:
                    # Don't retry permanent failures
                    await self._log_request_failure(request_id, attempt + 1, e, "PERMANENT")
                    raise

                elif failure_type == FailureType.RATE_LIMIT:
                    # Special handling for rate limits
                    delay = await self._handle_rate_limit(e)
                    await asyncio.sleep(delay)

                else:  # TRANSIENT
                    # Retry with backoff
                    if attempt < self.retry_config.max_attempts - 1:
                        delay = backoff.next_delay()
                        await self._log_retry_attempt(request_id, attempt + 1, delay)
                        await asyncio.sleep(delay)

                last_exception = e

        # All retries exhausted
        await self._log_request_failure(
            request_id,
            self.retry_config.max_attempts,
            last_exception,
            "EXHAUSTED"
        )

        raise last_exception or Exception("All retries exhausted")

    async def _execute_with_headers(
        self,
        func: Callable,
        request_id: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with required headers."""
        # Only add headers if the function/request actually uses them
        # Check if this is an HTTP request that needs headers
        if "headers" in kwargs or any(k in kwargs for k in ['url', 'method', 'session']):
            # Add headers to kwargs if it's an HTTP request
            if "headers" in kwargs:
                headers = kwargs["headers"]
            else:
                headers = {}
                kwargs["headers"] = headers

            # Add required headers
            headers[self.request_id_header] = request_id
            headers[self.timestamp_header] = datetime.now(timezone.utc).isoformat()

            # Add idempotency key for non-GET requests
            if kwargs.get("method", "GET").upper() != "GET":
                idempotency_key = self._generate_idempotency_key(func.__name__, args, kwargs)
                headers[self.idempotency_header] = idempotency_key

            # Add signature if configured
            if hasattr(self, "signing_key"):
                signature = self._generate_signature(request_id, headers)
                headers[self.signature_header] = signature

        return await func(*args, **kwargs)

    def _classify_failure(
        self,
        exception: Exception,
        classifier: Optional[Callable[[Exception], FailureType]]
    ) -> FailureType:
        """Classify exception type for handling strategy."""
        if classifier:
            return classifier(exception)

        # Default classification
        if isinstance(exception, IntegrityError):
            return FailureType.INTEGRITY

        if isinstance(exception, (ValueError, TypeError, KeyError)):
            return FailureType.PERMANENT

        if "429" in str(exception) or "rate" in str(exception).lower():
            return FailureType.RATE_LIMIT

        if isinstance(exception, (ConnectionError, TimeoutError, OSError)):
            return FailureType.TRANSIENT

        # HTTP status codes
        if hasattr(exception, "status"):
            status = exception.status
            if 400 <= status < 500:
                if status == 429:
                    return FailureType.RATE_LIMIT
                return FailureType.PERMANENT
            elif status >= 500:
                return FailureType.TRANSIENT

        # Default to transient
        return FailureType.TRANSIENT

    async def _handle_rate_limit(self, exception: Exception) -> float:
        """Handle rate limit with appropriate delay."""
        # Try to extract Retry-After header
        if hasattr(exception, "headers"):
            retry_after = exception.headers.get("Retry-After", "30")
            try:
                return float(retry_after)
            except ValueError:
                pass

        # Default aggressive backoff for rate limits
        return 30.0

    async def _handle_integrity_failure(self, request_id: str, exception: Exception):
        """Handle integrity failure with immediate halt."""
        failure_data = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "exception": str(exception),
            "type": "INTEGRITY_VIOLATION",
            "action": "SYSTEM_HALT"
        }

        # Add to forensic chain with CRITICAL level
        await self.hash_chain.add_evidence(
            failure_data,
            IntegrityLevel.CRITICAL
        )

        # In production, trigger immediate alerts
        logging.critical(f"INTEGRITY VIOLATION - System halt required: {exception}")

    def _generate_idempotency_key(
        self,
        func_name: str,
        args: tuple,
        kwargs: dict
    ) -> str:
        """Generate idempotency key for request."""
        # Create canonical representation
        canonical = {
            "function": func_name,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items()))
        }

        # Generate SHA-256 hash
        canonical_str = json.dumps(canonical, sort_keys=True)
        return hashlib.sha256(canonical_str.encode()).hexdigest()

    def _generate_signature(self, request_id: str, headers: Dict) -> str:
        """Generate HMAC-SHA256 signature for request."""
        # Create canonical string
        canonical_parts = [
            request_id,
            headers.get(self.timestamp_header, ""),
            headers.get(self.idempotency_header, "")
        ]

        canonical = "|".join(canonical_parts)

        # Generate HMAC
        signature = hmac.new(
            self.signing_key.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def _log_request_start(self, request_id: str, func_name: str):
        """Log request initiation."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "function": func_name,
            "event": "REQUEST_START"
        }

        self.request_log.append(log_entry)
        await self.hash_chain.add_evidence(log_entry, IntegrityLevel.MEDIUM)

    async def _log_request_success(self, request_id: str, attempts: int):
        """Log successful request."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "REQUEST_SUCCESS",
            "attempts": attempts
        }

        self.request_log.append(log_entry)
        await self.hash_chain.add_evidence(log_entry, IntegrityLevel.MEDIUM)

    async def _log_request_failure(
        self,
        request_id: str,
        attempts: int,
        exception: Exception,
        reason: str
    ):
        """Log request failure."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "REQUEST_FAILURE",
            "attempts": attempts,
            "exception": str(exception),
            "reason": reason
        }

        self.request_log.append(log_entry)
        await self.hash_chain.add_evidence(log_entry, IntegrityLevel.HIGH)

    async def _log_retry_attempt(self, request_id: str, attempt: int, delay: float):
        """Log retry attempt."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "RETRY_ATTEMPT",
            "attempt": attempt,
            "delay_seconds": delay
        }

        self.request_log.append(log_entry)
        await self.hash_chain.add_evidence(log_entry, IntegrityLevel.MEDIUM)

class TokenBucket:
    """
    Token bucket rate limiter for API request throttling.
    
    Implements the token bucket algorithm as specified in the
    Forensic Document Analysis System Technical Guide.
    
    The token bucket algorithm allows for burst traffic while
    maintaining an average rate limit. Tokens are added at a
    constant rate (refillRate) up to a maximum capacity.
    
    Usage:
        # Conservative SEC rate limiter (7 req/sec)
        sec_limiter = TokenBucket(capacity=10, refill_rate=7)
        
        # Before each request:
        if await sec_limiter.take():
            # Make request
            pass
    
    SEC EDGAR Guidelines:
        - Official limit: 10 requests/second
        - Production recommendation: 5-7 req/sec for bulk downloads
    """

    def __init__(
        self,
        capacity: int = 10,
        refill_rate: float = 7.0,
        name: str = "default"
    ):
        """
        Initialize token bucket rate limiter.
        
        Args:
            capacity: Maximum number of tokens (burst capacity)
            refill_rate: Tokens added per second (sustained rate)
            name: Identifier for logging/forensics
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.name = name
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

        # Metrics for forensic tracking
        self.metrics = {
            "requests_allowed": 0,
            "requests_throttled": 0,
            "total_wait_time": 0.0,
            "peak_wait_time": 0.0
        }

        logging.debug(
            f"TokenBucket '{name}' initialized: capacity={capacity}, rate={refill_rate}/sec"
        )

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time and refill rate
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    async def take(self, tokens: int = 1) -> bool:
        """
        Attempt to take tokens from bucket, waiting if necessary.
        
        This method will wait if insufficient tokens are available,
        blocking until the required tokens can be obtained.
        
        Args:
            tokens: Number of tokens to take (default: 1)
            
        Returns:
            True when tokens are successfully obtained
        """
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                # Tokens available immediately
                self.tokens -= tokens
                self.metrics["requests_allowed"] += 1
                return True

            # Calculate wait time for tokens to become available
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.refill_rate

            # Update metrics
            self.metrics["requests_throttled"] += 1
            self.metrics["total_wait_time"] += wait_time
            self.metrics["peak_wait_time"] = max(
                self.metrics["peak_wait_time"],
                wait_time
            )

            logging.debug(
                f"TokenBucket '{self.name}': throttling for {wait_time:.3f}s "
                f"(need {tokens_needed:.2f} tokens)"
            )

        # Wait outside the lock to allow other operations
        await asyncio.sleep(wait_time)

        # Recursively try again after waiting
        return await self.take(tokens)

    async def try_take(self, tokens: int = 1) -> bool:
        """
        Attempt to take tokens without waiting.
        
        Args:
            tokens: Number of tokens to take
            
        Returns:
            True if tokens were available, False otherwise
        """
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                self.metrics["requests_allowed"] += 1
                return True

            self.metrics["requests_throttled"] += 1
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiter metrics."""
        return {
            "name": self.name,
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "current_tokens": self.tokens,
            "requests_allowed": self.metrics["requests_allowed"],
            "requests_throttled": self.metrics["requests_throttled"],
            "total_wait_time_seconds": self.metrics["total_wait_time"],
            "peak_wait_time_seconds": self.metrics["peak_wait_time"],
            "average_wait_time": (
                self.metrics["total_wait_time"] / self.metrics["requests_throttled"]
                if self.metrics["requests_throttled"] > 0
                else 0.0
            )
        }

    def reset(self) -> None:
        """Reset bucket to full capacity."""
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()


# Pre-configured rate limiters for common APIs
def create_sec_rate_limiter() -> TokenBucket:
    """
    Create rate limiter for SEC EDGAR API.
    
    SEC enforces 10 requests/second officially, but production
    experience indicates 5-7 req/sec prevents throttling.
    
    Returns:
        TokenBucket configured for SEC EDGAR
    """
    return TokenBucket(
        capacity=10,
        refill_rate=7.0,
        name="sec_edgar"
    )


def create_govinfo_rate_limiter() -> TokenBucket:
    """
    Create rate limiter for GovInfo API.
    
    GovInfo allows ~1000 requests/hour with api.data.gov key.
    
    Returns:
        TokenBucket configured for GovInfo
    """
    return TokenBucket(
        capacity=5,
        refill_rate=0.25,  # ~900 requests/hour with some buffer
        name="govinfo"
    )


class QueueManager:
    """
    Manages message queues with forensic tracking.
    Implements SQS FIFO, Kafka, and RabbitMQ patterns.
    """

    def __init__(self, queue_type: str = "FIFO"):
        self.queue_type = queue_type
        self.messages: deque = deque()
        self.dead_letter_queue: List[Dict[str, Any]] = []
        self.hash_chain = ForensicHashChain(f"queue_{queue_type}")
        self._lock = asyncio.Lock()
        self.message_groups: Dict[str, deque] = {}

    async def enqueue(
        self,
        message: Dict[str, Any],
        message_group_id: Optional[str] = None,
        deduplication_id: Optional[str] = None
    ) -> str:
        """
        Add message to queue with optional FIFO ordering.
        
        Args:
            message: Message payload
            message_group_id: FIFO group ID for ordering
            deduplication_id: ID for duplicate detection
            
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())

        envelope = {
            "message_id": message_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": message,
            "message_group_id": message_group_id,
            "deduplication_id": deduplication_id or self._compute_dedup_id(message),
            "attempts": 0,
            "visibility_timeout": None
        }

        async with self._lock:
            if self.queue_type == "FIFO" and message_group_id:
                # Add to specific message group
                if message_group_id not in self.message_groups:
                    self.message_groups[message_group_id] = deque()
                self.message_groups[message_group_id].append(envelope)
            else:
                # Standard queue
                self.messages.append(envelope)

            # Add to forensic chain
            await self.hash_chain.add_evidence(
                {
                    "event": "MESSAGE_ENQUEUED",
                    "message_id": message_id,
                    "group_id": message_group_id
                },
                IntegrityLevel.MEDIUM
            )

        return message_id

    async def dequeue(
        self,
        visibility_timeout: int = 30,
        message_group_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve message from queue with visibility timeout.
        
        Args:
            visibility_timeout: Seconds before message becomes visible again
            message_group_id: Specific group to dequeue from
            
        Returns:
            Message envelope or None if queue empty
        """
        async with self._lock:
            source_queue = None

            if message_group_id and message_group_id in self.message_groups:
                source_queue = self.message_groups[message_group_id]
            elif not message_group_id and self.messages:
                source_queue = self.messages

            if not source_queue:
                return None

            # Find first visible message
            for message in source_queue:
                if not message["visibility_timeout"] or \
                   datetime.now(timezone.utc) > datetime.fromisoformat(message["visibility_timeout"]):
                    # Set visibility timeout
                    message["visibility_timeout"] = (
                        datetime.now(timezone.utc) + timedelta(seconds=visibility_timeout)
                    ).isoformat()
                    message["attempts"] += 1

                    # Log dequeue
                    await self.hash_chain.add_evidence(
                        {
                            "event": "MESSAGE_DEQUEUED",
                            "message_id": message["message_id"],
                            "attempt": message["attempts"]
                        },
                        IntegrityLevel.MEDIUM
                    )

                    return message

            return None

    async def acknowledge(self, message_id: str):
        """Acknowledge successful message processing."""
        async with self._lock:
            # Remove from all queues
            for queue in [self.messages] + list(self.message_groups.values()):
                for i, msg in enumerate(queue):
                    if msg["message_id"] == message_id:
                        queue.remove(msg)

                        # Log acknowledgment
                        await self.hash_chain.add_evidence(
                            {
                                "event": "MESSAGE_ACKNOWLEDGED",
                                "message_id": message_id,
                                "final_attempts": msg["attempts"]
                            },
                            IntegrityLevel.MEDIUM
                        )
                        return

    async def send_to_dlq(self, message: Dict[str, Any], reason: str):
        """Send failed message to dead letter queue."""
        dlq_entry = {
            "original_message": message,
            "dlq_timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "original_attempts": message.get("attempts", 0)
        }

        self.dead_letter_queue.append(dlq_entry)

        # Log DLQ transfer
        await self.hash_chain.add_evidence(
            {
                "event": "MESSAGE_TO_DLQ",
                "message_id": message.get("message_id"),
                "reason": reason
            },
            IntegrityLevel.HIGH
        )

    def _compute_dedup_id(self, message: Dict[str, Any]) -> str:
        """Compute deduplication ID from message content."""
        canonical = json.dumps(message, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def get_metrics(self) -> Dict[str, Any]:
        """Get queue metrics."""
        return {
            "queue_type": self.queue_type,
            "messages_pending": len(self.messages),
            "message_groups": len(self.message_groups),
            "dlq_size": len(self.dead_letter_queue),
            "total_groups_messages": sum(
                len(q) for q in self.message_groups.values()
            )
        }

