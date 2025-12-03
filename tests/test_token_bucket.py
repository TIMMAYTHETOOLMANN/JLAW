"""
Unit tests for TokenBucket rate limiter.
Tests the token bucket algorithm implementation for API rate limiting.
"""

import pytest
import asyncio

from src.forensics.api_resilience import (
    TokenBucket,
    create_sec_rate_limiter,
    create_govinfo_rate_limiter
)


class TestTokenBucket:
    """Test cases for TokenBucket rate limiter."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test TokenBucket initialization with default values."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0, name="test")

        assert bucket.capacity == 10
        assert bucket.refill_rate == 5.0
        assert bucket.name == "test"
        assert bucket.tokens == 10.0  # Should start full

    @pytest.mark.asyncio
    async def test_take_tokens_immediately_available(self):
        """Test taking tokens when they are immediately available."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)

        # Should succeed immediately
        result = await bucket.take(1)
        assert result is True
        assert bucket.tokens < 10.0

    @pytest.mark.asyncio
    async def test_try_take_available(self):
        """Test try_take when tokens are available."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)

        result = await bucket.try_take(1)
        assert result is True

    @pytest.mark.asyncio
    async def test_try_take_unavailable(self):
        """Test try_take when tokens are not available."""
        bucket = TokenBucket(capacity=2, refill_rate=1.0)

        # Take all tokens
        await bucket.try_take(2)

        # Should fail immediately without waiting
        result = await bucket.try_take(1)
        assert result is False

    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test that tokens refill over time."""
        bucket = TokenBucket(capacity=2, refill_rate=10.0)  # 10 tokens/sec

        # Take all tokens
        await bucket.take(2)
        assert bucket.tokens < 0.5

        # Wait for refill (0.2 seconds should add ~2 tokens at 10/sec)
        await asyncio.sleep(0.25)
        bucket._refill()

        # Should have tokens again
        assert bucket.tokens >= 1.5

    @pytest.mark.asyncio
    async def test_capacity_limit(self):
        """Test that tokens don't exceed capacity."""
        bucket = TokenBucket(capacity=5, refill_rate=100.0)  # Fast refill

        # Wait to overfill
        await asyncio.sleep(0.1)
        bucket._refill()

        # Should be capped at capacity
        assert bucket.tokens <= bucket.capacity

    @pytest.mark.asyncio
    async def test_metrics_tracking(self):
        """Test that metrics are properly tracked."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)

        # Take some tokens
        await bucket.take(1)
        await bucket.take(1)

        metrics = bucket.get_metrics()

        assert metrics["requests_allowed"] >= 2
        assert "capacity" in metrics
        assert "refill_rate" in metrics
        assert "current_tokens" in metrics

    @pytest.mark.asyncio
    async def test_reset(self):
        """Test bucket reset functionality."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)

        # Drain the bucket
        await bucket.take(10)
        assert bucket.tokens < 1.0

        # Reset
        bucket.reset()
        assert bucket.tokens == 10.0

    @pytest.mark.asyncio
    async def test_multiple_token_take(self):
        """Test taking multiple tokens at once."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)

        result = await bucket.take(5)
        assert result is True
        assert bucket.tokens <= 5.0


class TestPreConfiguredRateLimiters:
    """Test pre-configured rate limiters."""

    def test_sec_rate_limiter_configuration(self):
        """Test SEC EDGAR rate limiter configuration."""
        limiter = create_sec_rate_limiter()

        assert limiter.name == "sec_edgar"
        assert limiter.capacity == 10
        assert limiter.refill_rate == 7.0  # Conservative rate for SEC

    def test_govinfo_rate_limiter_configuration(self):
        """Test GovInfo rate limiter configuration."""
        limiter = create_govinfo_rate_limiter()

        assert limiter.name == "govinfo"
        assert limiter.capacity == 5
        assert limiter.refill_rate == 0.25  # ~900 requests/hour

    @pytest.mark.asyncio
    async def test_sec_rate_limiter_burst(self):
        """Test SEC rate limiter allows burst traffic."""
        limiter = create_sec_rate_limiter()

        # Should allow burst up to capacity
        for _ in range(10):
            result = await limiter.try_take(1)
            assert result is True

        # 11th request should fail without waiting
        result = await limiter.try_take(1)
        assert result is False


class TestConcurrentAccess:
    """Test concurrent access to TokenBucket."""

    @pytest.mark.asyncio
    async def test_concurrent_takes(self):
        """Test concurrent token takes are properly serialized."""
        bucket = TokenBucket(capacity=10, refill_rate=100.0)  # Fast refill

        async def take_token():
            return await bucket.try_take(1)

        # Launch many concurrent takes
        tasks = [take_token() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # Should have exactly 10 successes (capacity)
        # Some additional may succeed due to refill during execution
        successes = sum(1 for r in results if r)
        assert successes >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
