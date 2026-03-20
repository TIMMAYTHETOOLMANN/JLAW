# SEC EDGAR Bulletproof Configuration Guide (v4.1.0)

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration Reference](#configuration-reference)
- [Usage Examples](#usage-examples)
- [Node Integration](#node-integration)
- [Troubleshooting](#troubleshooting)
- [Performance Tuning](#performance-tuning)
- [Advanced Topics](#advanced-topics)

---

## Overview

The SEC EDGAR Bulletproof Configuration (v4.1.0) is a production-grade SEC EDGAR API client designed for maximum reliability and performance in forensic analysis environments. It provides advanced features beyond the standard SEC EDGAR client, including persistent caching, adaptive rate limiting, circuit breaker protection, and graceful degradation.

### Key Advantages

| Feature | Standard Client | Bulletproof Client |
|---------|----------------|-------------------|
| Rate Limiting | Fixed (9 req/sec) | Adaptive (6 req/sec base, adjusts dynamically) |
| Caching | None | Persistent file-based with TTL |
| Failure Handling | Retry with backoff | Circuit breaker + stale cache fallback |
| Retry Strategies | Exponential only | Exponential, Linear, Fibonacci |
| Statistics Tracking | Basic logging | Comprehensive metrics |
| Node Integration | Manual API calls | Specialized convenience methods |

### When to Use

**Use Bulletproof Client when:**
- Running long-running batch analyses
- Processing multiple companies concurrently
- SEC API stability is uncertain
- Need audit trail of document collection
- Require guaranteed data availability (via stale cache)

**Use Standard Client when:**
- Running quick one-off queries
- Testing/development with mock mode
- Minimal configuration needed

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                 BulletproofSECEdgarClient                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐     │
│  │   Cache      │  │ Rate Limiter │  │ Circuit Breaker │     │
│  │   Manager    │  │  (Adaptive)  │  │   (3 states)    │     │
│  └──────────────┘  └──────────────┘  └─────────────────┘     │
│         │                  │                    │              │
│         └──────────────────┴────────────────────┘              │
│                            ↓                                   │
│                    ┌──────────────┐                           │
│                    │ HTTP Session │                           │
│                    │   (aiohttp)  │                           │
│                    └──────────────┘                           │
│                            ↓                                   │
└────────────────────────────┼───────────────────────────────────┘
                             ↓
                    ┌──────────────┐
                    │  SEC EDGAR   │
                    │     API      │
                    └──────────────┘
```

### 1. Cache Manager

**Purpose**: Persistent file-based cache to reduce API calls and provide fallback data.

**Features**:
- File-based storage using Python pickle (no external dependencies)
- Configurable TTL per data type
- Stale cache fallback when fetch fails
- Automatic cleanup of expired entries
- MD5 hashing of cache keys for filesystem safety

**Cache TTLs**:
```python
submissions:  86400 seconds (24 hours)
filings:       3600 seconds (1 hour)
xbrl:         86400 seconds (24 hours)
tickers:     604800 seconds (7 days)
documents:  2592000 seconds (30 days)
```

### 2. Adaptive Rate Limiter

**Purpose**: Token bucket algorithm that adjusts speed based on SEC API responses.

**How It Works**:
1. **Normal Operation**: Maintains configured rate (default 6 req/sec)
2. **On 429 Error**: Slows down by 2x-4x (slowdown_factor)
3. **On Success**: Gradually speeds up (recovery_rate: 0.1)
4. **Burst Handling**: Allows brief bursts (burst_size: 3)

**Example Scenario**:
```
Initial rate:     6.0 req/sec
Hit 429 error:    3.0 req/sec (2x slowdown)
Hit 429 again:    1.5 req/sec (4x slowdown, max)
10 successes:     2.5 req/sec (gradual recovery)
20 successes:     4.5 req/sec (continuing recovery)
40 successes:     6.0 req/sec (fully recovered)
```

### 3. Circuit Breaker

**Purpose**: Prevent cascading failures by stopping requests during API outages.

**States**:
- **CLOSED**: Normal operation, all requests pass through
- **OPEN**: Failing, reject all requests immediately
- **HALF_OPEN**: Testing recovery, allow limited requests

**State Transitions**:
```
CLOSED ─[5 failures]→ OPEN ─[60s timeout]→ HALF_OPEN ─[2 successes]→ CLOSED
   ↑                                             │
   └─────────────[failure during test]───────────┘
```

**Configuration**:
```python
circuit_breaker_threshold: 5          # failures before opening
circuit_breaker_timeout: 60           # seconds before testing recovery
circuit_breaker_success_threshold: 2  # successes to close
```

### 4. Retry Strategies

**Exponential Backoff** (default):
```
Attempt 1: 1s delay
Attempt 2: 2s delay
Attempt 3: 4s delay
Attempt 4: 8s delay
Attempt 5: 16s delay
```

**Linear Backoff**:
```
Attempt 1: 1s delay
Attempt 2: 2s delay
Attempt 3: 3s delay
Attempt 4: 4s delay
Attempt 5: 5s delay
```

**Fibonacci Backoff**:
```
Attempt 1: 1s delay
Attempt 2: 1s delay
Attempt 3: 2s delay
Attempt 4: 3s delay
Attempt 5: 5s delay
```

---

## Installation

### Prerequisites

```bash
# Required dependencies (already in requirements.txt)
pip install aiohttp>=3.9.0
pip install aiolimiter>=1.1.0
```

### Verify Installation

```python
from src.integrations.sec_edgar_bulletproof_config import BulletproofSECEdgarClient

# Test initialization
config = BulletproofConfig(mock_mode=True)
client = BulletproofSECEdgarClient(config)
print("✓ Bulletproof client installed successfully")
```

---

## Configuration Reference

### Environment Variables

Create or update `.env` file:

```bash
# ============================================================================
# SEC EDGAR Bulletproof Configuration
# ============================================================================

# User Agent (REQUIRED - replace with your info)
SEC_USER_AGENT=YourCompany/1.0 (contact@yourcompany.com)

# Rate Limiting
SEC_RATE_LIMIT=6.0                    # requests per second (conservative)

# Caching
SEC_CACHE_ENABLED=true                # enable persistent cache
SEC_CACHE_DIR=.jlaw_cache/sec_edgar   # cache directory
SEC_STALE_CACHE_FALLBACK=true         # use expired cache if fetch fails

# Retry Configuration
SEC_MAX_RETRIES=5                     # maximum retry attempts
SEC_RETRY_STRATEGY=exponential        # exponential|linear|fibonacci

# Circuit Breaker
SEC_CIRCUIT_BREAKER_ENABLED=true      # enable circuit breaker

# Error Handling
SEC_RAISE_ON_FINAL_FAILURE=false      # graceful degradation (return None)

# Testing
SEC_MOCK_MODE=false                   # enable mock mode for testing
```

### Programmatic Configuration

```python
from src.integrations.sec_edgar_bulletproof_config import (
    BulletproofConfig,
    BulletproofSECEdgarClient,
    RetryStrategy
)

# Custom configuration
config = BulletproofConfig(
    user_agent="JLAW/4.1.0 (forensics@company.com)",
    rate_limit=5.0,                    # more conservative
    cache_enabled=True,
    stale_cache_fallback=True,
    circuit_breaker_enabled=True,
    max_retries=3,
    retry_strategy=RetryStrategy.EXPONENTIAL,
    raise_on_final_failure=False       # graceful degradation
)

# Load from environment
config = BulletproofConfig.from_env()

# Validate configuration
warnings = config.validate()
for warning in warnings:
    print(f"⚠️  {warning}")
```

---

## Usage Examples

### Basic Usage

```python
import asyncio
from src.integrations.sec_edgar_bulletproof_config import BulletproofSECEdgarClient

async def example_basic():
    """Basic usage example."""
    async with BulletproofSECEdgarClient() as client:
        # Get company submissions
        submissions = await client.get_company_submissions("320193")
        print(f"Company: {submissions['name']}")
        
        # Get XBRL facts
        facts = await client.get_xbrl_facts("320193")
        print(f"Facts available: {len(facts['facts'])}")

asyncio.run(example_basic())
```

### Using Specialized Methods

```python
async def example_specialized():
    """Using specialized methods for JLAW nodes."""
    async with BulletproofSECEdgarClient() as client:
        # Node 7: Get 10-K filings
        filings_10k = await client.get_10k_filings("AAPL", years=5)
        print(f"10-K filings: {len(filings_10k)}")
        
        # Node 8: Get 10-Q filings
        filings_10q = await client.get_10q_filings("AAPL", quarters=8)
        print(f"10-Q filings: {len(filings_10q)}")
        
        # Node 10: Get Form 4 filings
        from datetime import date, timedelta
        start_date = date.today() - timedelta(days=365)
        filings_form4 = await client.get_form4_filings(
            "AAPL",
            start_date=start_date
        )
        print(f"Form 4 filings: {len(filings_form4)}")

asyncio.run(example_specialized())
```

### Statistics Tracking

```python
async def example_statistics():
    """Track performance statistics."""
    async with BulletproofSECEdgarClient() as client:
        # Make several requests
        await client.get_company_submissions("320193")
        await client.get_xbrl_facts("320193")
        await client.get_company_submissions("320193")  # cache hit
        
        # Get statistics
        stats = client.get_statistics()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Success rate: {stats['success_rate']:.2%}")
        print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
        print(f"Retries: {stats['retries']}")
        
        # Get current state
        print(f"Circuit breaker: {client.get_circuit_breaker_state()}")
        print(f"Effective rate: {client.get_effective_rate_limit():.2f} req/sec")

asyncio.run(example_statistics())
```

### Error Handling

```python
async def example_error_handling():
    """Handle errors gracefully."""
    config = BulletproofConfig(
        raise_on_final_failure=False,  # return None instead of raising
        stale_cache_fallback=True      # use stale cache if available
    )
    
    async with BulletproofSECEdgarClient(config) as client:
        # This will return None if it fails (not raise exception)
        result = await client.get_company_submissions("INVALID_CIK")
        
        if result is None:
            print("Failed to fetch data, but didn't crash!")
        else:
            print(f"Successfully fetched: {result['name']}")

asyncio.run(example_error_handling())
```

---

## Node Integration

### Node 7: 10-K Annual Reports

```python
from src.integrations.sec_edgar_bulletproof_config import BulletproofSECEdgarClient

async def analyze_annual_reports(ticker: str):
    """Node 7: Analyze 10-K filings."""
    async with BulletproofSECEdgarClient() as client:
        # Get last 5 years of 10-K filings
        filings = await client.get_10k_filings(ticker, years=5)
        
        for filing in filings:
            print(f"Analyzing: {filing['form_type']} - {filing['filing_date']}")
            
            # Get filing content
            content = await client.get_filing_content(
                filing['cik'],
                filing['accession_number'],
                filing['primary_document']
            )
            
            # Perform analysis...
```

### Node 8: 10-Q Quarterly Reports

```python
async def analyze_quarterly_reports(ticker: str):
    """Node 8: Analyze 10-Q filings."""
    async with BulletproofSECEdgarClient() as client:
        # Get last 8 quarters of 10-Q filings
        filings = await client.get_10q_filings(ticker, quarters=8)
        
        for filing in filings:
            print(f"Quarter: {filing['report_date']}")
            # Perform quarterly analysis...
```

### Node 9: DEF 14A Proxy Statements

```python
async def analyze_proxy_statements(ticker: str):
    """Node 9: Analyze executive compensation."""
    async with BulletproofSECEdgarClient() as client:
        # Get last 5 years of DEF 14A filings
        filings = await client.get_def14a_filings(ticker, years=5)
        
        for filing in filings:
            print(f"Proxy statement: {filing['filing_date']}")
            # Extract compensation data...
```

### Node 10: Form 4 Insider Trading

```python
async def analyze_insider_trading(ticker: str):
    """Node 10: Analyze Form 4 insider transactions."""
    async with BulletproofSECEdgarClient() as client:
        from datetime import date, timedelta
        
        # Get Form 4 filings from last year
        start_date = date.today() - timedelta(days=365)
        filings = await client.get_form4_filings(
            ticker,
            start_date=start_date
        )
        
        print(f"Found {len(filings)} insider transactions")
        # Analyze trading patterns...
```

### Node 11: 8-K Material Events

```python
async def analyze_material_events(ticker: str):
    """Node 11: Analyze 8-K material events."""
    async with BulletproofSECEdgarClient() as client:
        # Get 8-K filings from last year
        filings = await client.get_8k_filings(ticker, days=365)
        
        for filing in filings:
            print(f"Material event: {filing['filing_date']}")
            # Analyze event disclosure...
```

### Node 12: 13D/13G Beneficial Ownership

```python
async def analyze_beneficial_ownership(ticker: str):
    """Node 12: Analyze Schedule 13D/13G filings."""
    async with BulletproofSECEdgarClient() as client:
        # Get last 3 years of 13D/13G filings
        filings = await client.get_13d_filings(ticker, years=3)
        
        for filing in filings:
            print(f"Ownership filing: {filing['form_type']} - {filing['filing_date']}")
            # Analyze ownership changes...
```

### Node 13: 13F Institutional Holdings

```python
async def analyze_institutional_holdings(ticker: str):
    """Node 13: Analyze 13F-HR institutional holdings."""
    async with BulletproofSECEdgarClient() as client:
        # Get last 8 quarters of 13F filings
        filings = await client.get_13f_filings(ticker, quarters=8)
        
        for filing in filings:
            print(f"Institutional holdings: {filing['filing_date']}")
            # Analyze holdings changes...
```

---

## Troubleshooting

### Common Issues

#### 1. User-Agent Warnings

**Problem**: Warnings about example.com in user agent
```
Configuration warning: User-Agent contains 'example.com'
```

**Solution**: Update `.env` file with real contact information:
```bash
SEC_USER_AGENT=YourCompany/1.0 (real-contact@yourcompany.com)
```

#### 2. Rate Limit Errors (429)

**Problem**: Getting 429 errors despite rate limiting
```
Rate limit hit - slowing down to 3.00 req/sec
```

**Solution**: This is normal! The adaptive rate limiter automatically slows down. If persistent:
```bash
# Reduce base rate limit
SEC_RATE_LIMIT=4.0  # more conservative
```

#### 3. Circuit Breaker Opens

**Problem**: Circuit breaker opens and rejects requests
```
Circuit breaker is OPEN - rejecting request
```

**Solution**: Wait for timeout (default 60s) or check SEC API status. The circuit breaker will automatically test recovery.

#### 4. Cache Not Working

**Problem**: Cache hit rate is 0%
```
Cache hit rate: 0.00%
```

**Solution**: Verify cache is enabled and directory exists:
```bash
# Check configuration
SEC_CACHE_ENABLED=true
SEC_CACHE_DIR=.jlaw_cache/sec_edgar

# Create directory if needed
mkdir -p .jlaw_cache/sec_edgar
```

#### 5. Stale Cache Fallback Not Triggering

**Problem**: Getting None instead of stale data when fetch fails

**Solution**: Ensure stale cache fallback is enabled:
```bash
SEC_STALE_CACHE_FALLBACK=true
```

---

## Performance Tuning

### For Maximum Speed

Prioritize speed over safety (not recommended for production):

```python
config = BulletproofConfig(
    rate_limit=9.0,                    # closer to SEC limit
    cache_enabled=True,                # still cache
    circuit_breaker_enabled=False,     # no circuit breaker
    max_retries=2,                     # fewer retries
    retry_strategy=RetryStrategy.LINEAR,  # faster recovery
    raise_on_final_failure=True        # fail fast
)
```

### For Maximum Reliability

Prioritize reliability over speed (recommended for production):

```python
config = BulletproofConfig(
    rate_limit=4.0,                    # very conservative
    cache_enabled=True,
    stale_cache_fallback=True,         # always use stale cache
    circuit_breaker_enabled=True,
    max_retries=5,                     # more retries
    retry_strategy=RetryStrategy.EXPONENTIAL,
    raise_on_final_failure=False       # graceful degradation
)
```

### For Batch Processing

Optimize for processing many companies:

```python
config = BulletproofConfig(
    rate_limit=6.0,
    cache_enabled=True,
    cache_ttl_submissions=172800,      # 2 days (longer cache)
    cache_ttl_filings=7200,            # 2 hours
    stale_cache_fallback=True,
    circuit_breaker_enabled=True,
    max_retries=5
)
```

### Cache Performance

**Optimal Cache Sizes by Use Case**:

| Use Case | Submissions TTL | Filings TTL | XBRL TTL |
|----------|----------------|-------------|----------|
| Development | 1 hour | 30 min | 1 hour |
| Production | 24 hours | 1 hour | 24 hours |
| Batch Analysis | 48 hours | 2 hours | 48 hours |
| Archival | 7 days | 24 hours | 7 days |

---

## Advanced Topics

### Custom Retry Strategy

```python
class CustomRetryStrategy:
    """Implement custom retry logic."""
    
    def get_delay(self, attempt: int) -> float:
        # Your custom logic here
        return min(attempt ** 2, 60.0)  # quadratic with max 60s

# Use in client
client._get_retry_delay = lambda attempt: CustomRetryStrategy().get_delay(attempt)
```

### Cache Inspection

```python
async def inspect_cache():
    """Inspect cache contents."""
    async with BulletproofSECEdgarClient() as client:
        cache_dir = Path(client.config.cache_dir)
        
        # Count cache entries
        cache_files = list(cache_dir.glob("*.cache"))
        print(f"Cache entries: {len(cache_files)}")
        
        # Show cache size
        total_size = sum(f.stat().st_size for f in cache_files)
        print(f"Cache size: {total_size / 1024 / 1024:.2f} MB")
        
        # Manual cleanup
        removed = client.cache.cleanup()
        print(f"Removed {removed} expired entries")
```

### Concurrent Requests

```python
async def concurrent_analysis(tickers: List[str]):
    """Analyze multiple companies concurrently."""
    async with BulletproofSECEdgarClient() as client:
        # Create tasks for all tickers
        tasks = [
            client.get_10k_filings(ticker, years=5)
            for ticker in tickers
        ]
        
        # Run concurrently (rate limiter ensures compliance)
        results = await asyncio.gather(*tasks)
        
        for ticker, filings in zip(tickers, results):
            print(f"{ticker}: {len(filings)} filings")

# Analyze 10 companies concurrently
asyncio.run(concurrent_analysis(["AAPL", "MSFT", "GOOGL", ...]))
```

### Mock Mode for Testing

```python
def test_with_mock_data():
    """Test code without making real API calls."""
    config = BulletproofConfig(
        mock_mode=True,               # enable mock mode
        cache_enabled=False           # don't cache mock data
    )
    
    async with BulletproofSECEdgarClient(config) as client:
        # Returns mock data instantly
        submissions = await client.get_company_submissions("1234567")
        assert submissions["name"] == "Mock Company Inc."
```

### Circuit Breaker Manual Control

```python
async def manual_circuit_control():
    """Manually control circuit breaker."""
    async with BulletproofSECEdgarClient() as client:
        # Check state
        state = client.get_circuit_breaker_state()
        print(f"Circuit breaker: {state}")
        
        # Force recovery by waiting and succeeding
        if state == "open":
            await asyncio.sleep(60)  # wait for timeout
            # Next successful request will transition to half-open
```

---

## Best Practices

### 1. Always Use Async Context Manager

```python
# ✅ Correct
async with BulletproofSECEdgarClient() as client:
    await client.get_company_submissions("320193")

# ❌ Incorrect (session not properly closed)
client = BulletproofSECEdgarClient()
await client.get_company_submissions("320193")
```

### 2. Handle CIK Resolution

```python
# ✅ Correct - handle None case
async with BulletproofSECEdgarClient() as client:
    cik = await client.cik_from_ticker("AAPL")
    if cik:
        filings = await client.get_filings(cik, form_types=["10-K"])
    else:
        print("Ticker not found")
```

### 3. Use Specialized Methods

```python
# ✅ Preferred - uses specialized method
filings = await client.get_10k_filings("AAPL", years=5)

# ⚠️  Manual - more code, same result
cik = await client.cik_from_ticker("AAPL")
filings = await client.get_filings(cik, form_types=["10-K"], limit=5)
```

### 4. Monitor Statistics

```python
# Periodically check statistics
async def monitor_health():
    async with BulletproofSECEdgarClient() as client:
        # ... perform operations ...
        
        stats = client.get_statistics()
        if stats['success_rate'] < 0.9:
            logger.warning("Low success rate detected")
        if stats['cache_hit_rate'] < 0.5:
            logger.info("Consider increasing cache TTL")
```

### 5. Configure for Environment

```python
# Development
config = BulletproofConfig(
    mock_mode=True,                   # use mock data
    cache_enabled=False,              # don't cache
    raise_on_final_failure=True       # fail fast for debugging
)

# Production
config = BulletproofConfig.from_env()  # use environment config
```

---

## Support & Contributing

For issues, questions, or contributions:
- GitHub Issues: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- Documentation: https://github.com/TIMMAYTHETOOLMANN/JLAW
- License: MIT

---

**Version**: 4.1.0  
**Last Updated**: December 2024  
**Author**: JLAW Forensic System Team
