# JLAW System Prerequisites

## Overview

This document outlines all prerequisites for deploying and running the JLAW SEC Forensic Analysis System. The system requires specific API keys, external services, and dependencies to achieve DOJ-grade forensic analysis with FRE 902(13)/(14) compliant evidence chains.

## Critical Dependencies (P0)

### 1. RFC 3161 Timestamp Authority

**Purpose**: Court-admissible cryptographic timestamps for evidence chain integrity.

**Requirements**:
- `rfc3161ng>=2.1.3` Python library
- `cryptography>=41.0.0` Python library
- Internet connectivity to TSA endpoints

**Configuration**:
```bash
# requirements.txt already includes these dependencies
pip install -r requirements.txt
```

**Supported TSA Endpoints** (automatic fallback):
1. Primary: http://freetsa.org/tsr (free, public, court-admissible)
2. Fallback 1: http://timestamp.sectigo.com (commercial)
3. Fallback 2: http://timestamp.digicert.com (commercial)

**Validation**:
```bash
# Test RFC 3161 connectivity and functionality
python scripts/validate_rfc3161.py
```

**Key Features**:
- Multi-TSA fallback with automatic retry
- Exponential backoff (2s, 4s, 8s delays)
- Configurable timeout (default: 10 seconds)
- Pre-flight connectivity validation

---

### 2. Required API Keys

#### 2.1 SEC User-Agent (REQUIRED)

**Purpose**: Required by SEC EDGAR API for rate limiting compliance.

**Format**: `CompanyName/Version (contact@email.com)`

**Configuration** (in `.env`):
```bash
SEC_USER_AGENT="YourCompany/1.0 (admin@yourcompany.com)"
```

**Validation Rules**:
- ✅ Must include valid email address
- ✅ Must be at least 15 characters
- ❌ Cannot contain placeholders (YOUR_, CHANGE_ME, etc.)

**Reference**: https://www.sec.gov/os/accessing-edgar-data

#### 2.2 OpenAI API Key (REQUIRED)

**Purpose**: Primary AI agent for forensic analysis and pattern detection.

**Get Your Key**: https://platform.openai.com/api-keys

**Format**: `sk-proj-...` or `sk-...`

**Configuration** (in `.env`):
```bash
OPENAI_API_KEY="sk-proj-YOUR_ACTUAL_KEY_HERE"
```

**Usage**:
- GPT-4 forensic analysis
- Pattern detection algorithms
- Dual-agent cross-validation

#### 2.3 Anthropic API Key (REQUIRED)

**Purpose**: Secondary AI agent for cross-validation and consensus scoring.

**Get Your Key**: https://console.anthropic.com/settings/keys

**Format**: `sk-ant-...`

**Configuration** (in `.env`):
```bash
ANTHROPIC_API_KEY="sk-ant-api03-YOUR_ACTUAL_KEY_HERE"
```

**Usage**:
- Claude forensic analysis
- Cross-validation with OpenAI
- Consensus scoring for violations

**Note**: At least ONE of OpenAI or Anthropic is required. Both recommended for maximum accuracy.

---

## Validation Scripts

### validate_api_keys.py
Validates all API key configurations.

```bash
python scripts/validate_api_keys.py
```

**Checks**:
- ✅ SEC User-Agent format and email
- ✅ OpenAI API key format
- ✅ Anthropic API key format
- ✅ Placeholder detection
- ✅ At least one AI key configured

**Exit Codes**:
- `0`: All required keys valid
- `1`: Missing or invalid required keys
- `2`: Configuration errors

---

## Troubleshooting

### Issue: "SEC_USER_AGENT contains placeholder value"

**Solution**:
```bash
# Edit .env file
nano .env

# Replace placeholder with your actual info
SEC_USER_AGENT="MyCompany/1.0 (contact@mycompany.com)"
```

### Issue: "No TSA connectivity"

**Causes**:
- Firewall blocking HTTP/HTTPS traffic
- Network connectivity issues
- TSA service temporarily down

**Solution**:
```bash
# Test connectivity manually
curl -I http://freetsa.org/tsr

# Try alternative TSA
# System will automatically fallback to sectigo or digicert
```

### Issue: "API key format invalid"

**Common Mistakes**:
- ❌ `OPENAI_API_KEY=YOUR_KEY_HERE` (placeholder)
- ❌ `OPENAI_API_KEY=sk-123` (too short)
- ❌ `ANTHROPIC_API_KEY=sk-proj-123` (wrong prefix)

**Correct Format**:
- ✅ `OPENAI_API_KEY=sk-proj-abcd1234efgh5678...` (real key)
- ✅ `ANTHROPIC_API_KEY=sk-ant-api03-abcd1234...` (real key)
