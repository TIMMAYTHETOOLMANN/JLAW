# API Configuration Guide

## ✅ Your Configuration is Set Up!

Your API access for SEC EDGAR and GovInfo has been successfully configured.

**Important Distinction**:
- **SEC EDGAR**: No API key required - only needs User-Agent with email
- **GovInfo (data.gov)**: API key required for enhanced access (optional for SEC-only use)

**Your Settings**: Stored securely in `.env` (see `docs/API_SETUP_GUIDE.md`)

---

## 📋 Configuration

Your `.env` file in the project root:

```bash
# SEC EDGAR Configuration (No API key required - only User-Agent with email)
SEC_USER_AGENT=JLAW Forensic System your-email@example.com
SEC_EMAIL=your-email@example.com

# GovInfo API Configuration (API key for data.gov services - optional)
GOVINFO_API_KEY=<your-govinfo-api-key>
```

---

## 🔒 Security Best Practices

1. **Never commit .env to git**:
   ```bash
   # .env is already in .gitignore
   echo ".env" >> .gitignore
   ```

2. **Protect your GovInfo API key**:
   - Don't share it publicly
   - Don't include it in code repositories
   - Don't send it via unsecured channels
   - Per data.gov terms: "This API key is for your use and should not be shared"

3. **SEC EDGAR User-Agent**:
   - Email in User-Agent is public (required by SEC)
   - SEC recommends (but doesn't require) including your contact info
   - No API key needed for SEC access

---

## 🧪 Testing Your API Key

Run the verification test:

```bash
python test_sec_api_key.py
```

This will verify:
- ✅ Configuration is loaded correctly
- ✅ SEC EDGAR API is accessible
- ✅ Company data can be retrieved
- ✅ Bulk data endpoints work
- ✅ Rate limiting is configured properly

---

## 🚀 Using the API in JLAW

### Basic Usage

```python
from src.forensics import get_config

# Get configuration
config = get_config()

# Access SEC settings (no API key - only User-Agent)
print(f"SEC Email: {config.config.sec.user_email}")
print(f"SEC User-Agent: {config.config.sec.user_agent}")

# Access GovInfo API key (optional)
if config.config.govinfo.api_key:
    print(f"GovInfo API Key: {config.config.govinfo.api_key}")

# Get headers for SEC requests (no API key in headers)
sec_headers = config.get_sec_headers()

# Get params for GovInfo requests (includes API key)
govinfo_params = config.get_govinfo_params()
```

### Complete Investigation Example

```python
from jlaw_forensics import JLAWForensicSystem

# Initialize system (automatically loads API key from .env)
jlaw = JLAWForensicSystem()

# Run forensic analysis on a company
results = await jlaw.investigate_company(
    cik='0000320193',  # Apple Inc.
    filing_types=['10-K', '10-Q'],
    years=3
)

# Generate prosecution dossier
dossier = await jlaw.generate_dossier(results)
```

---

## 📊 SEC EDGAR API Capabilities

With proper User-Agent configuration (no API key needed), you can:

1. **Company Information**:
   ```python
   GET https://data.sec.gov/submissions/CIK{cik}.json
   ```

2. **Filing Downloads**:
   ```python
   GET https://www.sec.gov/cgi-bin/browse-edgar
   ```

3. **Bulk Data Access**:
   ```python
   GET https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
   ```

4. **Real-time Filings**:
   ```python
   GET https://data.sec.gov/submissions/
   ```

---

## ⚡ Rate Limiting

**SEC Requirements**:
- Maximum 10 requests per second
- Must include User-Agent with contact email

**JLAW Configuration** (already set in .env):
```bash
SEC_REQUESTS_PER_SECOND=10
SEC_MAX_RETRIES=3
```

The system automatically handles:
- ✅ Rate limiting (10 requests/second)
- ✅ Exponential backoff on failures
- ✅ Retry logic with circuit breakers
- ✅ Request queuing

---

## 🔧 Advanced Configuration

### Environment Variables

All available configuration options in `.env`:

```bash
# SEC EDGAR (No API key - only User-Agent with email)
SEC_EMAIL=your_email@example.com
SEC_USER_AGENT=Your App your_email@example.com
SEC_REQUESTS_PER_SECOND=10
SEC_MAX_RETRIES=3

# GovInfo API (Optional - for data.gov services)
GOVINFO_API_KEY=your_govinfo_key_here

# System
STORAGE_PROVIDER=LOCAL
STORAGE_PATH=./forensic_storage
LOG_LEVEL=INFO
MAX_WORKERS=16
ENABLE_GPU=true

# Analysis Thresholds
MATERIALITY_THRESHOLD=0.05
SIMILARITY_THRESHOLD=0.85
BENFORD_CRITICAL_VALUE=15.507

# Output
DOSSIER_OUTPUT_PATH=./dossiers
EXHIBIT_OUTPUT_PATH=./exhibits
```

### Programmatic Configuration

```python
from src.forensics.config_manager import ConfigurationManager

# Custom configuration
config = ConfigurationManager(config_path='./custom.env')

# Access settings
print(config.config.sec_api.api_key)
print(config.config.materiality_threshold)

# Get request headers
headers = config.get_sec_headers()

# Export configuration (without secrets)
config.export_config('./config_export.json', include_secrets=False)
```

---

## 📚 API Resources

### Official Documentation

- **SEC EDGAR API**: https://www.sec.gov/edgar/sec-api-documentation
- **Data.gov API**: https://api.data.gov/docs/
- **SEC Developer Resources**: https://www.sec.gov/developer

### Useful SEC Endpoints

1. **Company Search**: `https://www.sec.gov/cgi-bin/browse-edgar?company={name}&action=getcompany`
2. **CIK Lookup**: `https://www.sec.gov/cgi-bin/browse-edgar?CIK={cik}&action=getcompany`
3. **Recent Filings**: `https://data.sec.gov/submissions/CIK{cik}.json`
4. **XBRL Facts**: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`

---

## 🐛 Troubleshooting

### "Required environment variable SEC_EMAIL not set"

**Solution**: Ensure `.env` file exists in project root with:
```bash
SEC_EMAIL=your-email@example.com
SEC_USER_AGENT=JLAW Forensic System your-email@example.com
```

### "403 Forbidden" errors from SEC

**Problem**: SEC requires User-Agent with contact email (no API key)

**Solution**: Verify `.env` has proper User-Agent:
```bash
SEC_USER_AGENT=JLAW Forensic System your-email@example.com
```

The User-Agent **must** include your contact email per SEC requirements.

### "Rate limit exceeded"

**Solution**: System automatically handles rate limiting (max 10/second per SEC). If you see this:
1. Check `SEC_REQUESTS_PER_SECOND` is ≤ 10
2. System will automatically retry with backoff
3. Check logs for circuit breaker status

### "GovInfo API key appears to be invalid"

**Note**: This is the GovInfo API key for data.gov services (optional for SEC-only use).

**Solution**: If you want to use GovInfo services, verify your key:
```bash
GOVINFO_API_KEY=<your-govinfo-key-from-data.gov>
```

---

## ✅ Verification Checklist

Run through this checklist to ensure everything works:

- [ ] `.env` file exists in project root
- [ ] `SEC_EMAIL` is set with your email
- [ ] `SEC_USER_AGENT` includes your email
- [ ] `GOVINFO_API_KEY` is set (optional for GovInfo services)
- [ ] Run `python test_sec_api_key.py` - all tests pass
- [ ] Can retrieve SEC company data (no API key needed)
- [ ] Can download SEC filings (no API key needed)
- [ ] GovInfo API works (if configured)
- [ ] Rate limiting is working (10 req/sec)

---

## 🎯 Next Steps

Now that your API is configured, you can:

1. **Run forensic analyses**:
   ```bash
   python jlaw_forensics.py --cik 0000320193 --years 3
   ```

2. **Test all 9 modules**:
   ```bash
   python test_modules_3_and_4.py
   python test_temporal_reconciliation.py
   ```

3. **Generate prosecution dossiers**:
   ```python
   from src.forensics import ForensicDossierGenerator
   
   dossier_gen = ForensicDossierGenerator()
   dossier = await dossier_gen.generate_forensic_dossier(results)
   ```

4. **Start investigating companies**:
   - Access SEC filings automatically
   - Run 9-module forensic analysis
   - Generate court-ready evidence packages

---

## 📞 Support

**SEC EDGAR Help**: https://www.sec.gov/os/accessing-edgar-data  
**Data.gov Support**: https://www.data.gov/contact  

**JLAW System Issues**: Check logs in `forensic_YYYYMMDD.log`

---

**Your API key is ready to use! The system is now fully operational.** 🚀

