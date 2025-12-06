# JARVIS:LAW Black Site Protocol - API Integration Guide

**Status**: ✅ CONFIGURED  
**OpenAI API**: Integrated  
**GovInfo/SEC EDGAR API**: Integrated  
**Date**: November 8, 2025

---

## 🔐 API Keys Configured

### OpenAI API
- **Purpose**: LLM-powered forensic analysis
- **Status**: ✅ CONFIGURED
- **Model**: GPT-4 (configurable)
- **Usage**: Autonomous violation detection, legal brief generation

### GovInfo/SEC EDGAR API
- **Purpose**: Enhanced metadata extraction from government databases
- **Status**: ✅ CONFIGURED
- **Compatibility**: Works with both GovInfo.gov and SEC EDGAR Online
- **Usage**: Filing metadata, document search, enhanced data extraction

---

## 📁 Configuration Files

### `.env` File (Created)
Location: `./.../.env`

```bash
# OpenAI Configuration
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>

# GovInfo/SEC EDGAR Configuration
GOVINFO_API_KEY=<YOUR_GOVINFO_API_KEY>
SEC_EDGAR_API_KEY=<YOUR_SEC_EDGAR_API_KEY>

# SEC.gov Configuration
SEC_USER_AGENT=JarvisLAW/1.0 (forensics@domain.com)
SEC_RATE_LIMIT_REQUESTS_PER_SECOND=10

# System Configuration
ENVIRONMENT=production
DEBUG=false
EVIDENCE_CHAIN_ENABLED=true
```

### `.gitignore` (Created)
Prevents API keys from being committed to version control:
- `.env` files
- API key files
- Evidence chain data
- Sensitive filing archives

---

## 🔧 Configuration Module

### `config.py` (Created)

Centralized configuration management with automatic API key loading:

```python
from config import Config

# Access API keys
openai_key = Config.OPENAI_API_KEY
govinfo_key = Config.GOVINFO_API_KEY

# Get SEC-compliant headers (includes API key if available)
headers = Config.get_sec_headers()

# Check configuration status
status = Config.validate()

# Print configuration summary
Config.print_status()
```

---

## 🎯 How API Keys Are Used

### 1. OpenAI API (GPT-4)

**Used for**:
- Forensic analysis of SEC filings
- Violation detection
- Legal brief generation
- Natural language processing of complex financial documents

**Integration points**:
- `jarvis_law_alpha.py` - Main agent
- Autonomous analysis workflows
- Legal brief generation

**Example**:
```python
from agents import Agent
from agents.extensions.models.litellm_model import LitellmModel

model = LitellmModel(
    model="gpt-4",
    api_key=Config.OPENAI_API_KEY
)

agent = Agent(
    name="JARVIS:LAW Alpha",
    model=model,
    instructions="Analyze SEC filings for violations..."
)
```

### 2. GovInfo/SEC EDGAR API

**Used for**:
- Enhanced filing metadata extraction
- Document search across government databases
- Direct API access to SEC EDGAR Online
- Structured JSON responses vs HTML scraping

**Integration points**:
- `tools/govinfo_api.py` - GovInfo API client
- `tools/sec_crawler.py` - SEC scraper (API key added to headers)
- Metadata enrichment workflows

**Example**:
```python
from tools.govinfo_api import get_filing_metadata

# Get enhanced metadata
metadata = get_filing_metadata("SEC-FILING-ID")

# API key automatically loaded from Config
```

---

## 🔒 Security Features

### API Key Protection

1. **Environment Variables**: Keys stored in `.env` file
2. **Git Ignore**: `.env` excluded from version control
3. **No Hardcoding**: Keys never hardcoded in source
4. **Preview Only**: Test scripts show only partial keys
5. **Local Storage**: Keys never transmitted except to authorized APIs

### Request Headers

SEC-compliant headers automatically include:
- User-Agent (required by SEC)
- API key (when available, for SEC EDGAR Online)
- Accept headers
- Language preferences

```python
headers = {
    'User-Agent': 'JarvisLAW/1.0 (forensics@domain.com)',
    'X-Api-Key': 'QLSbdMWeb3Qa...istqD',  # Added if SEC_EDGAR_API_KEY set
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}
```

---

## 🧪 Testing API Integration

### Quick Test

```bash
python test_config.py
```

**Expected output**:
```
✓ Configuration module imported successfully
✓ OpenAI API Key: SET
✓ GovInfo API Key: SET
✓ Directories created
✓ System ready for operations
```

### Verify API Keys

```python
from config import Config

Config.print_status()
```

### Test SEC API Access

```python
from tools.sec_crawler import fetch_company_info_by_cik

# Test with API key in headers
info = fetch_company_info_by_cik("0000320187")
print(info)
```

### Test GovInfo API

```python
from tools.govinfo_api import get_filing_metadata

# Requires GOVINFO_API_KEY
metadata = get_filing_metadata("TEST-DOC-ID")
print(metadata)
```

---

## 📊 API Usage Limits

### OpenAI API
- **Rate Limits**: Per account tier
- **Cost**: Pay per token
- **Best Practice**: Use GPT-4 for complex analysis, GPT-3.5 for simpler tasks
- **Monitoring**: Track token usage in OpenAI dashboard

### GovInfo/SEC EDGAR API
- **Rate Limits**: SEC.gov enforces 10 requests/second
- **Cost**: Free (government API)
- **Best Practice**: Auto rate-limiting built into `sec_crawler.py`
- **Compliance**: User-Agent required, auto-configured

---

## 🎮 Usage Examples

### Example 1: Full Autonomous Scan with API Keys

```python
from sec_workflow import scan_by_ticker

# Uses both APIs:
# - GovInfo/SEC EDGAR for enhanced metadata
# - OpenAI for forensic analysis
results = scan_by_ticker("AAPL", "10-K", 2020, 2023)

print(f"Filings analyzed: {results['total_filings']}")
print(f"Violations detected: {results['violations_count']}")
```

### Example 2: CLI with API Integration

```bash
# Automatically uses API keys from .env
python black_site_cli.py --ticker NIKE --form 4 --start 2019 --end 2025
```

### Example 3: Manual API Key Override

```python
from tools.govinfo_api import get_filing_metadata

# Override default API key
metadata = get_filing_metadata(
    "DOC-ID",
    api_key="custom-api-key"
)
```

---

## 🔄 API Fallback Behavior

### If API Keys Not Available

**OpenAI API**:
- System continues with scraping/archival
- Analysis features disabled
- Manual review required

**GovInfo API**:
- Falls back to HTML scraping
- Metadata extraction still works
- Slightly slower, no JSON responses

**Both modules gracefully degrade** - core scraping and evidence chain features work regardless of API availability.

---

## 🚀 Production Deployment

### Environment Variables (Recommended)

For production, set environment variables directly:

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-..."
$env:GOVINFO_API_KEY="QLSbdM..."

# Windows (CMD)
set OPENAI_API_KEY=sk-...
set GOVINFO_API_KEY=QLSbdM...

# Linux/Mac
export OPENAI_API_KEY="sk-..."
export GOVINFO_API_KEY="QLSbdM..."
```

### Docker Deployment

```dockerfile
ENV OPENAI_API_KEY=sk-...
ENV GOVINFO_API_KEY=QLSbdM...
ENV SEC_EDGAR_API_KEY=QLSbdM...
```

### Cloud Deployment

Use secret management:
- AWS Secrets Manager
- Azure Key Vault
- Google Cloud Secret Manager

---

## 📋 Configuration Checklist

- [x] `.env` file created
- [x] OpenAI API key configured
- [x] GovInfo/SEC EDGAR API key configured
- [x] `.gitignore` updated
- [x] `config.py` module created
- [x] API keys loaded in modules
- [x] Security headers configured
- [x] Rate limiting configured
- [x] Test script created
- [x] Documentation updated

---

## 🎖️ API Integration Complete

**Status**: ✅ OPERATIONAL

Both API keys are now integrated and ready for use:

1. **OpenAI API** - Powers forensic analysis
2. **GovInfo/SEC EDGAR API** - Enhances metadata extraction

**Test configuration**:
```bash
python test_config.py
```

**Execute first scan with APIs**:
```bash
python black_site_cli.py --nike
```

---

**JARVIS:LAW Black Site Protocol**  
*API Integration v1.0.0 - November 8, 2025*  
*All systems armed with full API access*

