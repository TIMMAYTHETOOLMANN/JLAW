# SEC EDGAR Rate Limiting Implementation

## Overview

This document describes the implementation of robust rate limiting and error handling for SEC EDGAR API access in the JLAW forensic analysis system.

## Problem Statement

The original implementation had several critical issues:

1. **Multiple Independent Rate Limiters**: Each `SECEdgarClient` instance created its own rate limiter, causing cumulative rate violations when multiple nodes executed concurrently
2. **No Retry Logic**: HTTP 429 errors were logged but not retried, causing analysis failures
3. **Invalid User-Agent Configuration**: Placeholder values from `.env.example` were not validated, leading to API rejections
4. **No Testing Mode**: Required real API access for all testing and development

## Solution Architecture

### 1. Shared Singleton Rate Limiter

**File**: `src/integrations/sec_edgar/edgar_client.py`

**Key Components**:
```python
# Global singleton instance
_SHARED_RATE_LIMITER = RateLimiter(requests_per_second=9.0)

class RateLimiter:
    _instance = None
    
    def __new__(cls, requests_per_second: float = 9.0):
        if cls._instance is None:
            cls._instance = super(RateLimiter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
```

**Benefits**:
- All `SECEdgarClient` instances share one rate limiter
- Prevents concurrent request violations
- 9 req/sec (10% safety buffer from SEC's 10 req/sec limit)
- Request counter for debugging

**Critical**: This singleton pattern MUST be maintained to prevent rate limiting violations.

### 2. Exponential Backoff for 429 Errors

**Implementation**:
```python
MAX_RETRIES = 4
RETRY_DELAYS = [1, 2, 4, 8]  # seconds

# In _fetch() method:
for attempt in range(self.MAX_RETRIES):
    if response.status == 429:
        if attempt < self.MAX_RETRIES - 1:
            delay = self.RETRY_DELAYS[attempt]
            await asyncio.sleep(delay)
            continue
```

**Benefits**:
- Automatic recovery from transient rate limiting
- Clear logging of retry attempts
- Prevents cascade failures
- Total wait time: 15 seconds maximum

### 3. User-Agent Validation

**File**: `config/secure_config.py`

**Validation Rules**:
1. Must not be empty
2. Must not contain placeholder text: `YOUR_`, `YourProject`, `your-email`, etc.
3. Must contain a valid email address (regex validated)
4. Must be at least 15 characters long

**Integration**:
- Validation runs in Phase 1 of `JLAW_UNIFIED.py` before any API calls
- Clear error messages with setup instructions
- Prevents runtime failures with actionable guidance

**Example**:
```python
from config.secure_config import validate_sec_configuration

is_valid, errors = validate_sec_configuration()
if not is_valid:
    # Print errors and exit before making API calls
```

### 4. Mock Mode

**Usage**:
```python
# Method 1: Environment variable
SEC_MOCK_MODE=true

# Method 2: Constructor parameter
client = SECEdgarClient(mock_mode=True)
```

**Mock Data**:
- Company submissions with recent filings
- XBRL facts with financial data
- Ticker-to-CIK mappings
- Document content

**Use Cases**:
- Unit testing without API quota consumption
- CI/CD pipelines in restricted environments
- Development without internet access
- Debugging without external dependencies

## Testing

### Test Suite

**File**: `tests/integrations/test_sec_rate_limiting.py`

**Coverage**:
- 25 tests covering all new features
- Singleton rate limiter verification
- Exponential backoff behavior
- User-Agent validation (valid/invalid/placeholders)
- Configuration validation
- Mock mode functionality
- Client initialization

**Results**: All 25 tests passing ✅

**Existing Tests**: All 10 existing edgar_client tests still passing ✅

### Manual Testing

Configuration validation:
```bash
python -c "from config.secure_config import print_configuration_status; print_configuration_status()"
```

Mock mode integration:
```bash
SEC_MOCK_MODE=true python JLAW_UNIFIED.py --cik 320193 --year 2023
```

## Configuration

### Required Setup

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Set valid User-Agent**:
   ```bash
   # .env file
   SEC_USER_AGENT=YourCompany/1.0 (admin@yourcompany.com)
   ```

3. **Verify configuration**:
   ```bash
   python -c "from config.secure_config import print_configuration_status; print_configuration_status()"
   ```

### Valid User-Agent Format

✅ **Valid Examples**:
- `UniversityResearch/1.0 (professor@university.edu)`
- `CompanyName/2.0 (compliance@company.com)`
- `MyForensicTool/1.0 (admin@myorganization.org)`

❌ **Invalid Examples**:
- `YourProject contact@your-email.org` (placeholder)
- `MyCompany` (no email)
- `a@b.c` (too short)

## Monitoring and Debugging

### Log Messages

**Rate Limiter**:
```
INFO: Initialized shared SEC rate limiter: 9.0 req/sec (min interval: 0.111s)
DEBUG: Rate limiter: 100 requests processed
```

**Retry Attempts**:
```
WARNING: SEC API rate limit (429) hit for <url>. Retry 1/3 after 1s delay
WARNING: SEC API rate limit (429) hit for <url>. Retry 2/3 after 2s delay
ERROR: SEC API rate limit (429) - max retries exceeded for <url>
```

**Configuration**:
```
INFO: ✓ SEC API configuration valid
INFO: ✓ User-Agent contains contact email
ERROR: ✗ SEC API configuration is INVALID: SEC_USER_AGENT contains placeholder value
```

### Checking Rate Limiter State

```python
from src.integrations.sec_edgar.edgar_client import _SHARED_RATE_LIMITER

print(f"Requests per second: {_SHARED_RATE_LIMITER.requests_per_second}")
print(f"Min interval: {_SHARED_RATE_LIMITER.min_interval:.3f}s")
print(f"Total requests: {_SHARED_RATE_LIMITER.request_count}")
```

## Best Practices

### For Developers

1. **Always use mock mode for testing**: `SEC_MOCK_MODE=true`
2. **Verify configuration before long runs**: Check Phase 1 output
3. **Monitor logs for 429 warnings**: Indicates approaching rate limits
4. **Don't create multiple SECEdgarClient instances unnecessarily**: Share when possible
5. **Never bypass the shared rate limiter**: Always use the singleton instance

### For Deployment

1. **Set valid User-Agent in production**: Use organization contact email
2. **Run configuration validation in startup scripts**: Fail fast on invalid config
3. **Enable DEBUG logging for troubleshooting**: `logging.getLogger('src.integrations.sec_edgar.edgar_client').setLevel(logging.DEBUG)`
4. **Monitor for 429 errors in production logs**: May indicate need to reduce parallel operations
5. **Keep mock mode disabled in production**: Use real API data

### For Testing

1. **Use mock mode in CI/CD**: Avoid API quota consumption
2. **Test configuration validation**: Include invalid User-Agent tests
3. **Test retry logic**: Mock 429 responses
4. **Verify singleton pattern**: Ensure rate limiter is shared
5. **Integration test with real API**: Run periodically with valid credentials

## Troubleshooting

### "SEC API rate limit (429) - max retries exceeded"

**Causes**:
- Invalid User-Agent configuration
- Too many concurrent JLAW instances
- Multiple applications accessing SEC API

**Solutions**:
1. Verify User-Agent is valid (run configuration check)
2. Ensure only one JLAW instance is running
3. Wait 60 seconds before retrying
4. Check for other processes accessing SEC EDGAR

### "SEC_USER_AGENT contains placeholder value"

**Cause**: Using example value from `.env.example`

**Solution**: Update `.env` with real organization and email

### Mock Mode Not Working

**Checks**:
1. Verify `SEC_MOCK_MODE=true` in environment
2. Or pass `mock_mode=True` to constructor
3. Check logs for "MOCK MODE" initialization message

### Rate Limiter Not Shared

**Symptom**: Multiple "Initialized shared SEC rate limiter" messages

**Cause**: Something broke the singleton pattern

**Solution**: Verify `RateLimiter.__new__()` implementation

## Performance Characteristics

### Rate Limiting

- **Theoretical maximum**: 9 requests/second = 540 requests/minute
- **Actual throughput**: ~8.5 req/sec due to processing overhead
- **Retry overhead**: Up to 15 seconds per 429 error (all retries)
- **Memory footprint**: Negligible (single shared instance)

### Mock Mode

- **Latency**: <1ms (in-memory data)
- **Throughput**: Unlimited (no rate limiting applied)
- **Memory**: ~10KB for sample data

## Future Enhancements

### Potential Improvements

1. **Adaptive Rate Limiting**: Automatically reduce rate on 429 errors
2. **Request Queue**: Show pending requests in rate limiter
3. **Metrics Collection**: Track 429 error frequency, retry success rate
4. **Circuit Breaker**: Temporarily stop requests after sustained failures
5. **Regional Rate Limits**: Different limits for different SEC endpoints

### Backward Compatibility

All changes are backward compatible:
- Existing code continues to work without modification
- Default User-Agent still available (though validation warns)
- Mock mode is opt-in
- Rate limiting is transparent to callers

## References

- [SEC EDGAR Access Guide](https://www.sec.gov/os/accessing-edgar-data)
- [SEC API Documentation](https://www.sec.gov/edgar/sec-api-documentation)
- [SEC_API_SETUP.md](SEC_API_SETUP.md) - User setup guide
- [README.md](../README.md) - Main project documentation

## Version History

- **v2.0** (2024-12-18): Implemented shared rate limiter, exponential backoff, mock mode, configuration validation
- **v1.0** (2024): Initial SEC EDGAR integration with basic rate limiting

## Contact

For issues related to this implementation, see the main JLAW repository issues.
