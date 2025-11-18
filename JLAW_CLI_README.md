# JLAW Forensic System - CLI Interface

## Overview
Command-line interface for the complete JLAW Forensic Investigation Platform. Provides zero-tolerance forensic analysis of SEC filings with surgical precision.

## Installation

### Prerequisites
```bash
# Python 3.9+
python --version

# Required dependencies
pip install aiohttp aiofiles numpy pandas

# Optional (for full ML features)
pip install torch transformers scikit-learn joblib

# Optional (for cloud storage)
pip install boto3 azure-storage-blob
```

### Quick Start
```bash
# Clone repository
cd openai-agents-python

# Run CLI
python jlaw_forensics.py --help
```

## Commands

### 1. investigate
Launch complete forensic investigation of a company.

```bash
python jlaw_forensics.py investigate \
    --cik 0001318605 \
    --name "Tesla Inc" \
    --years 3
```

**Options:**
- `--cik` (required): Company CIK number
- `--name` (required): Company name
- `--years`: Years of history to analyze (default: 3)
- `--config`: Path to configuration file (JSON)
- `--output`: Save results to JSON file

**Output:**
- Complete investigation report
- Risk score (0-1)
- Criminal violation count
- Evidence stored count
- Recommendations
- Legal actions

**Example:**
```bash
python jlaw_forensics.py investigate \
    --cik 0000320193 \
    --name "Apple Inc" \
    --years 5 \
    --output apple_investigation.json
```

### 2. analyze
Analyze single SEC filing for fraud indicators.

```bash
python jlaw_forensics.py analyze \
    --cik 0001318605 \
    --accession 0001564590-24-000123
```

**Options:**
- `--cik` (required): Company CIK
- `--accession` (required): SEC accession number
- `--output`: Save results to JSON file

**Output:**
- Traditional forensic analysis
- ML fraud prediction
- Statute violations
- Combined risk score

**Example:**
```bash
python jlaw_forensics.py analyze \
    --cik 0001318605 \
    --accession 0001564590-24-000123 \
    --output filing_analysis.json
```

### 3. status
Check status of ongoing investigation.

```bash
python jlaw_forensics.py status \
    --case-id CASE_0001318605_20251118123456
```

**Options:**
- `--case-id` (required): Investigation case ID

**Output:**
- Current status (INITIATED, COLLECTING, ANALYZING, etc.)
- Filings analyzed count
- Violations found
- Current risk score
- Running time

### 4. verify
Verify complete system integrity.

```bash
python jlaw_forensics.py verify
```

**Output:**
- Hash chain verification (all 6 modules)
- Audit log integrity
- Storage verification
- Overall system status

**Exit Codes:**
- 0: System integrity valid
- 1: System integrity compromised

**Example:**
```bash
python jlaw_forensics.py verify
# ✅ VALID or ❌ INVALID for each component
```

### 5. monitor
Continuous system integrity monitoring.

```bash
python jlaw_forensics.py monitor
```

**Behavior:**
- Verifies system integrity every hour
- Logs results to forensic log
- Halts on integrity violation
- Press Ctrl+C to stop

**Use Cases:**
- Production environments
- Long-running investigations
- Compliance monitoring
- Tamper detection

---

## Configuration

### Environment Variables

```bash
# Storage provider
export STORAGE_PROVIDER="AWS"  # AWS, AZURE, or LOCAL

# API keys
export GOVINFO_API_KEY="your_api_key"
export SEC_USER_AGENT="YourCompany contact@email.com"

# AWS configuration
export AWS_REGION="us-east-1"
export FORENSIC_S3_BUCKET="your-forensic-bucket"

# Audit logging
export AUDIT_SIGNING_KEY="your_secret_key"

# Retention
export RETENTION_DAYS="2555"  # 7 years
```

### Configuration File

Create `forensic_config.json`:

```json
{
    "storage_provider": "LOCAL",
    "govinfo_api_key": "DEMO_KEY",
    "sec_user_agent": "JLAW forensics@jlaw.com",
    "retention_days": 2555,
    "rate_limits": {
        "sec_edgar": 7,
        "govinfo": 1000
    },
    "ml_models": {
        "enable_bert": true,
        "enable_isolation_forest": true,
        "ensemble_weights": {
            "han": 0.4,
            "isolation_forest": 0.3,
            "random_forest": 0.3
        }
    },
    "forensic_thresholds": {
        "high_risk": 0.7,
        "critical_risk": 0.85,
        "auto_escalate": 0.8
    }
}
```

Use with `--config`:
```bash
python jlaw_forensics.py investigate \
    --cik 0001318605 \
    --name "Tesla Inc" \
    --config forensic_config.json
```

---

## Output Formats

### Investigation Report

```json
{
    "case_id": "CASE_0001318605_20251118123456",
    "target": {
        "cik": "0001318605",
        "company": "Tesla Inc"
    },
    "summary": {
        "filings_analyzed": 12,
        "violations_detected": 15,
        "criminal_violations": 3,
        "evidence_stored": 13,
        "risk_score": 0.85,
        "status": "COMPLETE"
    },
    "detailed_findings": {
        "revenue_manipulations": [...],
        "accounting_frauds": [...],
        "disclosure_failures": [...],
        "executive_violations": [...]
    },
    "recommendations": [
        "IMMEDIATE: Initiate formal SEC investigation",
        "CRITICAL: 3 potential criminal violations detected - refer to DOJ"
    ],
    "legal_actions": [...],
    "forensic_certification": {...}
}
```

### Single Filing Analysis

```json
{
    "filing": {
        "cik": "0001318605",
        "accession": "0001564590-24-000123",
        "type": "10-K"
    },
    "forensic_analysis": {
        "risk_score": 0.75,
        "red_flags": 12,
        "delay_days": 45,
        "benford_suspicious": true,
        "revenue_anomalies": 3
    },
    "ml_prediction": {
        "fraud_probability": 0.87,
        "confidence": 0.92,
        "red_flag_sentences": ["..."],
        "top_features": {
            "income_growth_ratio": 0.342,
            "dso_change": 0.287
        }
    },
    "legal_violations": [...],
    "summary": {
        "combined_risk": 0.825,
        "criminal_violations": 2,
        "high_risk": true
    }
}
```

---

## Usage Examples

### Example 1: Quick Investigation
```bash
# Investigate Tesla with default settings
python jlaw_forensics.py investigate \
    --cik 0001318605 \
    --name "Tesla Inc"

# Output:
# ================================================================================
# INVESTIGATION COMPLETE: Tesla Inc
# ================================================================================
# Risk Score: 85.0%
# Criminal Violations: 3
# Filings Analyzed: 12
# Evidence Stored: 13
# ================================================================================
```

### Example 2: Deep Historical Analysis
```bash
# 5-year analysis with detailed output
python jlaw_forensics.py investigate \
    --cik 0001318605 \
    --name "Tesla Inc" \
    --years 5 \
    --output tesla_full_investigation.json

# Review results
cat tesla_full_investigation.json | jq '.summary'
```

### Example 3: Single Filing Check
```bash
# Quick check of specific filing
python jlaw_forensics.py analyze \
    --cik 0001318605 \
    --accession 0001564590-24-000123

# Output:
# ================================================================================
# FILING ANALYSIS: 0001564590-24-000123
# ================================================================================
# Traditional Risk: 75.0%
# ML Prediction: 87.0%
# Combined Risk: 82.5%
# Criminal Violations: 2
# ================================================================================
```

### Example 4: Continuous Monitoring
```bash
# Production monitoring mode
python jlaw_forensics.py monitor

# Logs:
# 2025-11-18 12:00:00 - INFO - Monitoring iteration 1
# 2025-11-18 12:00:01 - INFO - System integrity: VALID - Next check in 1 hour
# 2025-11-18 13:00:00 - INFO - Monitoring iteration 2
# ...
```

### Example 5: Batch Processing
```bash
#!/bin/bash
# Investigate multiple companies

COMPANIES=(
    "0001318605:Tesla Inc"
    "0000320193:Apple Inc"
    "0001652044:Alphabet Inc"
)

for entry in "${COMPANIES[@]}"; do
    IFS=':' read -r cik name <<< "$entry"
    
    python jlaw_forensics.py investigate \
        --cik "$cik" \
        --name "$name" \
        --output "investigations/${cik}_report.json"
    
    sleep 10  # Rate limiting
done
```

### Example 6: Daily Integrity Check
```bash
#!/bin/bash
# Daily cron job for integrity verification

LOG_FILE="integrity_$(date +%Y%m%d).log"

python jlaw_forensics.py verify > "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
    # Integrity compromised - send alert
    echo "CRITICAL: System integrity compromised" | mail -s "JLAW Alert" security@company.com
    exit 1
fi
```

---

## Logging

### Log Files
Automatic log file creation:
```
forensic_20251118.log
```

### Log Format
```
2025-11-18 12:34:56 - JLAWForensicSystem - INFO - Starting investigation: Tesla Inc (CIK: 0001318605)
2025-11-18 12:34:57 - ForensicOrchestrator - INFO - Investigation initiated: Case ID CASE_0001318605_20251118123456
2025-11-18 12:35:30 - SECForensicAnalyzer - INFO - Filing analyzed: 10-K - Risk: 0.75
2025-11-18 12:36:00 - AdvancedFraudDetector - INFO - ML prediction: 0.87 (confidence: 0.92)
```

### Log Levels
- **INFO**: Normal operations
- **WARNING**: High risk detected, auto-escalation
- **ERROR**: Analysis failures, retry attempts
- **CRITICAL**: Integrity violations, system halts

---

## Error Handling

### Exit Codes
- `0`: Success
- `1`: Fatal error or integrity compromise

### Common Errors

**Missing dependencies:**
```bash
ImportError: PyTorch and transformers required
```
**Solution:** `pip install torch transformers`

**Invalid CIK:**
```bash
ValueError: Invalid CIK format
```
**Solution:** Use 10-digit CIK with leading zeros

**API rate limit:**
```bash
CircuitBreakerOpenError: Too many requests
```
**Solution:** Wait and retry, or adjust rate limits in config

**Integrity violation:**
```bash
CRITICAL: SYSTEM INTEGRITY COMPROMISED
```
**Action:** Investigate immediately, check audit logs

---

## Integration

### Python API
```python
from jlaw_forensics import JLAWForensicSystem

# Initialize
system = JLAWForensicSystem()

# Investigate
report = await system.investigate_company(
    cik="0001318605",
    company_name="Tesla Inc",
    years_back=3
)

# Verify integrity
integrity = await system.verify_system_integrity()
```

### REST API Integration
See `examples/jarvis_law_sec_auditor/forensic_web_server.py` for FastAPI wrapper.

### Cron Jobs
```cron
# Daily 2 AM verification
0 2 * * * /usr/bin/python /path/to/jlaw_forensics.py verify

# Weekly investigation of watchlist
0 0 * * 0 /path/to/scripts/weekly_investigation.sh
```

---

## Performance

### Investigation Times
- **Single filing**: ~1-2 seconds
- **3-year investigation**: ~5-15 minutes
- **5-year investigation**: ~15-30 minutes

### Resource Usage
- **Memory**: ~1-2 GB (without BERT), ~2-4 GB (with BERT)
- **Disk**: ~100 MB per investigation (compressed)
- **CPU**: Moderate (intensive during ML prediction)

### Optimization Tips
1. Use `LOCAL` storage for testing (fastest)
2. Disable BERT if not needed (set `enable_bert: false`)
3. Reduce `years` parameter for quick checks
4. Use `--output` to save results (prevents re-running)

---

## Security

### Evidence Preservation
- **WORM storage**: Immutable evidence
- **Hash chains**: Tamper detection
- **Audit logs**: Complete trail
- **Chain of custody**: Legal admissibility

### Compliance
- ✅ FRE 902(13)(14): Self-authenticating evidence
- ✅ NIST SP 800-86: Forensic methodology
- ✅ Sarbanes-Oxley: 7-year retention
- ✅ DOJ guidelines: Chain of custody

### Access Control
Set appropriate permissions:
```bash
chmod 700 jlaw_forensics.py
chown forensics:forensics jlaw_forensics.py
```

---

## Troubleshooting

### Problem: Import errors
**Solution:** Ensure all dependencies installed
```bash
pip install -r requirements.txt
```

### Problem: Slow ML predictions
**Solution:** Disable BERT or use GPU
```json
{
    "ml_models": {
        "enable_bert": false
    }
}
```

### Problem: Storage failures
**Solution:** Check storage provider configuration
```bash
# For LOCAL
mkdir -p /var/forensic/worm

# For AWS
aws s3 ls s3://your-forensic-bucket

# For Azure
az storage container show --name forensic-evidence
```

### Problem: Rate limiting
**Solution:** Adjust rate limits or add delays
```json
{
    "rate_limits": {
        "sec_edgar": 5
    }
}
```

---

## Support

### Documentation
- Module READMEs in `src/forensics/`
- System summary: `src/forensics/SYSTEM_COMPLETE.md`
- Module completion docs: `src/forensics/MODULE_*_COMPLETE.md`

### Logs
Check `forensic_YYYYMMDD.log` for detailed operation logs

### Debugging
Run with Python's debug mode:
```bash
python -u jlaw_forensics.py investigate ... 2>&1 | tee debug.log
```

---

## File Location
`jlaw_forensics.py` (project root)

## Status
✅ **PRODUCTION READY**

## Version
1.0.0

## Last Updated
November 18, 2025

