# SEC EDGAR API Setup Guide

## Overview

The JLAW forensic analysis system relies on the SEC EDGAR API to retrieve company filings. This guide explains how to properly configure your system to access the SEC EDGAR API without encountering rate limiting issues.

## SEC API Requirements

The SEC requires all automated systems accessing EDGAR to:

1. **Declare a User-Agent** that includes:
   - Your company/organization name or project name
   - A valid contact email address
   
2. **Respect rate limits**:
   - Maximum 10 requests per second
   - JLAW uses 9 req/sec for safety buffer

**Official SEC Documentation:** https://www.sec.gov/os/accessing-edgar-data

## Configuration

### Step 1: Copy Environment Template

```bash
cp .env.example .env
```

### Step 2: Set Your User-Agent

Edit the `.env` file and update the `SEC_USER_AGENT` line with your information:

```bash
# ❌ INCORRECT - Will be rejected:
SEC_USER_AGENT=YourProject contact@your-email.org

# ✅ CORRECT - Replace with your actual information:
SEC_USER_AGENT=UniversityResearch/1.0 (professor@university.edu)
SEC_USER_AGENT=CompanyName/2.0 (compliance@company.com)
SEC_USER_AGENT=MyForensicTool/1.0 (admin@myorganization.org)
```

**Format Requirements:**
- Include your organization/project name
- Include a valid, monitored email address
- No placeholder text like "YourProject" or "your-email"
- Minimum 15 characters total

### Step 3: Verify Configuration

Run the configuration check tool:

```bash
python -c "from config.secure_config import print_configuration_status; print_configuration_status()"
```

Expected output:
```
============================================================
JLAW SEC FORENSIC ANALYZER - CONFIGURATION STATUS
============================================================

  SEC User Agent       : ✅ SET (UniversityResearch/1.0...)

------------------------------------------------------------
SEC API CONFIGURATION VALIDATION
------------------------------------------------------------

  ✅ SEC API configuration is valid
  ✅ User-Agent contains email address
  ✅ Ready to make SEC EDGAR API requests

============================================================
```

## Rate Limiting

JLAW implements multiple layers of rate limiting protection:

### 1. Shared Rate Limiter (Singleton Pattern)

All `SECEdgarClient` instances share a single rate limiter to prevent concurrent violations:

```python
from src.integrations.sec_edgar.edgar_client import SECEdgarClient

# These all share the same rate limiter
async with SECEdgarClient() as client1:
    async with SECEdgarClient() as client2:
        # Requests from both clients are rate-limited together
        ...
```

### 2. Safety Buffer

- SEC allows: 10 requests/second
- JLAW uses: 9 requests/second (10% buffer)
- Minimum interval: 111ms between requests

### 3. Exponential Backoff

If a 429 (Rate Limit) error occurs, JLAW automatically retries with exponential backoff:

- Attempt 1: Wait 1 second, retry
- Attempt 2: Wait 2 seconds, retry
- Attempt 3: Wait 4 seconds, retry
- Attempt 4: Wait 8 seconds, final retry
- After 4 attempts: Fail with error

## Mock Mode

For testing or development without making real API calls, enable mock mode:

### Method 1: Environment Variable

```bash
# In .env file
SEC_MOCK_MODE=true
```

### Method 2: Constructor Parameter

```python
from src.integrations.sec_edgar.edgar_client import SECEdgarClient

async with SECEdgarClient(mock_mode=True) as client:
    # Returns sample data, no real API calls
    submissions = await client.get_company_submissions("320193")
```

Mock mode returns realistic sample data for:
- Company submissions
- XBRL facts
- Ticker mappings
- Filing documents

## Troubleshooting

### Error: "SEC API rate limit (429) - max retries exceeded"

**Causes:**
1. Invalid or missing User-Agent
2. Too many concurrent requests
3. Multiple instances running simultaneously

**Solutions:**
1. Verify User-Agent configuration (see Step 3 above)
2. Ensure only one instance of JLAW is running
3. Check for other processes accessing SEC EDGAR API
4. Wait 60 seconds before retrying

### Error: "SEC_USER_AGENT contains placeholder value"

**Cause:** You're using the example placeholder from `.env.example`

**Solution:** Update `SEC_USER_AGENT` in `.env` with your actual information (see Step 2)

### Error: "SEC_USER_AGENT must include a valid email address"

**Cause:** User-Agent doesn't contain an email address or email format is invalid

**Solution:** Add a valid email address to your User-Agent:
```bash
SEC_USER_AGENT=MyProject/1.0 (admin@mycompany.com)
```

### Error: "SEC fetch forbidden (403)"

**Causes:**
1. Invalid User-Agent format
2. Accessing deprecated URL format
3. SEC blocking your IP (very rare)

**Solutions:**
1. Verify User-Agent is properly set
2. Check that you're using the correct API endpoints
3. For Form 4 files, JLAW automatically tries fallback URLs

### Warning: "Phase 1: SEC API configuration is INVALID"

**Cause:** Configuration validation failed during startup

**Solution:** 
1. Run the configuration check tool (Step 3)
2. Fix any reported issues
3. Restart JLAW

## Advanced Configuration

### Custom Rate Limiting

While JLAW uses a shared rate limiter, you can verify the configuration:

```python
from src.integrations.sec_edgar.edgar_client import _SHARED_RATE_LIMITER

print(f"Rate: {_SHARED_RATE_LIMITER.requests_per_second} req/sec")
print(f"Min interval: {_SHARED_RATE_LIMITER.min_interval:.3f} seconds")
print(f"Requests processed: {_SHARED_RATE_LIMITER.request_count}")
```

### Logging

Enable debug logging to see detailed rate limiting information:

```python
import logging

logging.getLogger('src.integrations.sec_edgar.edgar_client').setLevel(logging.DEBUG)
```

Example output:
```
DEBUG: SEC EDGAR Client initialized with User-Agent: UniversityResearch/1.0...
DEBUG: Rate limiter: 100 requests processed
WARNING: SEC API rate limit (429) hit. Retry 1/3 after 1s delay
INFO: SEC fetch successful after retry
```

## Best Practices

1. **Always set a valid User-Agent** before running JLAW
2. **Run configuration validation** before long analysis sessions
3. **Use mock mode** for testing and development
4. **Monitor logs** for rate limiting warnings
5. **Run only one instance** of JLAW per machine
6. **Be respectful** of SEC's infrastructure

## SEC Contact Information

If you experience persistent issues accessing EDGAR:

- **Email:** [oit@sec.gov](mailto:oit@sec.gov)
- **Subject:** "EDGAR Public Dissemination Service (PDS) - Technical Support"
- **Include:** Your User-Agent string and description of the issue

## Additional Resources

- [SEC EDGAR Developer Resources](https://www.sec.gov/edgar/sec-api-documentation)
- [SEC EDGAR Rate Limiting Policy](https://www.sec.gov/os/accessing-edgar-data)
- [EDGAR Company Search](https://www.sec.gov/edgar/searchedgar/companysearch.html)
- [CIK Lookup Tool](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany)

## Version History

- **v2.0** (2024-12-18): Added shared rate limiter, exponential backoff, mock mode
- **v1.0** (2024): Initial SEC EDGAR integration
