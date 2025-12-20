# Strict Mode Troubleshooting Guide

## Overview

This guide provides detailed troubleshooting information for JLAW's Strict Execution Mode. When a phase gate fails, the system generates specific exit codes and provides remediation guidance.

## Quick Reference: Exit Codes

| Exit Code | Phase | Meaning | Typical Duration to Fix |
|-----------|-------|---------|------------------------|
| 0 | - | Complete success | N/A |
| 1 | Phase 1 | Configuration/initialization failure | 5-15 minutes |
| 2 | Phase 2 | Data collection failure | 10-30 minutes |
| 3 | Phase 3 | Document parsing failure | 5-20 minutes |
| 4 | Phase 4 | Node execution below threshold | 15-60 minutes |
| 5 | Phase 5 | Pattern detection failure | 10-30 minutes |
| 6 | Phase 8 | Evidence chain integrity failure | 5-15 minutes |
| 7 | Phase 9 | Dossier generation failure | 5-20 minutes |

## Exit Code 1: Configuration/Initialization Failure

### What It Means

Phase 1 (Configuration & Target Acquisition) failed validation. The system could not properly initialize required modules or validate SEC API configuration.

### Gate Requirements

- SEC EDGAR Client initialized and available
- Minimum 6 modules loaded (strict mode)
- SEC API configuration valid

### Common Causes

1. **Missing SEC_USER_AGENT**
   ```
   Error: SEC_USER_AGENT environment variable not set
   ```

2. **Invalid SEC_USER_AGENT format**
   ```
   Error: SEC_USER_AGENT must include a valid email address
   ```

3. **Placeholder values in configuration**
   ```
   Error: SEC_USER_AGENT contains placeholder value
   ```

4. **Module import failures**
   ```
   Error: Failed to import required modules
   ```

### Remediation Steps

#### Issue: Missing or Invalid SEC_USER_AGENT

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your User-Agent:
   ```bash
   SEC_USER_AGENT="YourOrganization/1.0 (contact@yourorg.com)"
   ```

3. Verify configuration:
   ```bash
   python -c "from config.secure_config import print_configuration_status; print_configuration_status()"
   ```

#### Issue: Module Import Failures

1. Verify all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Check for version conflicts:
   ```bash
   pip check
   ```

3. Reinstall specific packages if needed:
   ```bash
   pip install --upgrade --force-reinstall openai anthropic
   ```

### Example Fix

**Before (Exit Code 1):**
```bash
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 1 Gate FAILED: SEC API configuration invalid
Exit Code: 1
```

**After (Exit Code 0):**
```bash
$ export SEC_USER_AGENT="MyCompany/1.0 (admin@mycompany.com)"
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 1 Gate PASSED: All modules initialized
...
Exit Code: 0
```

---

## Exit Code 2: Data Collection Failure

### What It Means

Phase 2 (SEC EDGAR Data Collection) failed to collect sufficient filings to meet the minimum requirements.

### Gate Requirements

- Minimum total filings collected (default: 1, strict: 5)
- Per-type minimums met (if configured):
  - 10-K: 1 filing minimum
  - 10-Q: 3 filings minimum
  - DEF 14A: 1 filing minimum
  - Form 4: 10 filings minimum
  - 8-K: 5 filings minimum

### Common Causes

1. **Invalid CIK number**
   ```
   Error: No company found with CIK 999999
   ```

2. **Date range too narrow**
   ```
   Error: Only 2 filings found, minimum 5 required
   ```

3. **SEC API rate limiting**
   ```
   Error: SEC API rate limit exceeded, max retries reached
   ```

4. **No filings of required type**
   ```
   Error: No 10-K filings found in date range
   ```

### Remediation Steps

#### Issue: Invalid CIK

1. Verify CIK on SEC EDGAR:
   - Visit https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany
   - Search by company name or ticker
   - Use the 10-digit CIK (with leading zeros)

2. Use correct CIK format:
   ```bash
   # Correct: 10-digit with leading zeros
   python JLAW_UNIFIED.py --cik 0000320187 --year 2019 --strict

   # Also accepts without leading zeros (auto-padded)
   python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict
   ```

#### Issue: Insufficient Filings

1. **Expand date range:**
   ```bash
   # Instead of 1 year, try 3 years
   python JLAW_UNIFIED.py --cik 320187 --start-year 2017 --end-year 2019 --strict
   ```

2. **Adjust thresholds** (for edge cases):
   - Edit `config/strict_execution_config.py`
   - Lower `min_filings_total` for specific cases
   - Document why threshold was adjusted

3. **Use non-strict mode** for initial exploration:
   ```bash
   python JLAW_UNIFIED.py --cik 320187 --year 2019 --auto
   ```

#### Issue: Rate Limiting

1. Wait 60 seconds and retry
2. Verify SEC_USER_AGENT is properly set
3. Check for other processes using SEC API
4. Review SEC EDGAR access policies

### Example Fix

**Before (Exit Code 2):**
```bash
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 2 Gate FAILED: Insufficient filings collected (2 < 5)
Exit Code: 2
```

**After (Exit Code 0):**
```bash
# Expand date range to capture more filings
$ python JLAW_UNIFIED.py --cik 320187 --start-year 2017 --end-year 2019 --strict --auto
Phase 2 Gate PASSED: 15 filings collected
...
Exit Code: 0
```

---

## Exit Code 3: Document Parsing Failure

### What It Means

Phase 3 (DocsGPT Document Parsing & Indexing) failed to parse and index sufficient documents.

### Gate Requirements

- Minimum documents parsed (default: 1)
- Minimum chunks indexed (strict mode: 10)

### Common Causes

1. **Corrupted filing documents**
   ```
   Error: Failed to parse filing 0001193125-19-000001
   ```

2. **Unsupported document format**
   ```
   Error: Document format not supported
   ```

3. **Chunking failures**
   ```
   Error: Failed to create text chunks from document
   ```

4. **Vector store errors**
   ```
   Error: Failed to index chunks in FAISS
   ```

### Remediation Steps

#### Issue: Document Access Problems

1. Verify filing accessibility on SEC EDGAR:
   ```bash
   curl -A "MyOrg/1.0 (contact@org.com)" \
     "https://www.sec.gov/Archives/edgar/data/320187/000119312519000001/0001193125-19-000001.txt"
   ```

2. Check network connectivity to SEC EDGAR

3. Review SEC EDGAR status page for outages

#### Issue: Parsing Failures

1. **Enable debug logging:**
   ```python
   import logging
   logging.getLogger('src.forensics.docsgpt').setLevel(logging.DEBUG)
   ```

2. **Check document format:**
   - Verify the filing type is supported
   - Check if document is HTML, XML, or XBRL
   - Review parser logs for specific errors

3. **Retry with different filings:**
   - Some filings may be corrupted
   - Try a different date range
   - Use non-strict mode to identify problem filings

#### Issue: Chunking/Indexing Failures

1. Verify OpenAI API key is set:
   ```bash
   echo $OPENAI_API_KEY
   ```

2. Test embedding generation:
   ```python
   from openai import OpenAI
   client = OpenAI()
   response = client.embeddings.create(
       model="text-embedding-3-large",
       input="test"
   )
   print(len(response.data[0].embedding))  # Should be 3072
   ```

3. Check available memory for FAISS:
   ```bash
   free -h
   ```

### Example Fix

**Before (Exit Code 3):**
```bash
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 3 Gate FAILED: Insufficient chunks indexed (5 < 10)
Exit Code: 3
```

**After (Exit Code 0):**
```bash
# Verify OpenAI API key is set
$ export OPENAI_API_KEY="sk-..."
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 3 Gate PASSED: 150 chunks indexed
...
Exit Code: 0
```

---

## Exit Code 4: Node Execution Below Threshold

### What It Means

Phase 4 (15-Node Recursive Analysis) did not meet the minimum success rate for node execution.

### Gate Requirements

- Minimum nodes successful (default: 12 out of 15)
- Minimum success rate (default: 80%)
- Node results data present

### Common Causes

1. **Data quality issues**
   ```
   Error: Node 7 failed - insufficient data for analysis
   ```

2. **API failures**
   ```
   Error: Node 15 failed - Polygon.io API error
   ```

3. **Dependency issues**
   ```
   Error: Node failed to import required module
   ```

4. **Insufficient filings**
   ```
   Error: Node requires minimum 3 10-K filings, only 1 found
   ```

### Remediation Steps

#### Issue: Data Quality

1. **Review node-specific requirements:**
   - Node 2: Requires DEF 14A filings
   - Node 3: Requires 10-Q filings
   - Node 4: Requires 10-K filings
   - Node 10: Requires Form 4 filings

2. **Check audit trail for specific failures:**
   ```bash
   # Review the audit trail JSON
   cat output/CASE_*/audit_trail_*.json | jq '.nodes'
   ```

3. **Run nodes individually for debugging:**
   ```python
   from src.nodes.node2_def14a import CompensationAnalyzer
   analyzer = CompensationAnalyzer()
   result = analyzer.analyze(filing_data)
   ```

#### Issue: API Failures

1. **Verify API keys:**
   ```bash
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   echo $POLYGON_API_KEY  # Optional, only for Node 15
   ```

2. **Check API rate limits:**
   - Review API provider status pages
   - Verify account quotas
   - Check for billing issues

3. **Use mock mode for testing:**
   ```bash
   SEC_MOCK_MODE=true python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict
   ```

#### Issue: Insufficient Data

1. **Lower threshold temporarily:**
   - Edit `config/strict_execution_config.py`
   - Set `min_nodes_successful = 10` instead of 12
   - Document the reason for adjustment

2. **Expand data collection:**
   ```bash
   # Collect more years of data
   python JLAW_UNIFIED.py --cik 320187 --start-year 2016 --end-year 2019 --strict
   ```

### Example Fix

**Before (Exit Code 4):**
```bash
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 4 Gate FAILED: Only 10/15 nodes successful (67% < 80%)
Exit Code: 4
```

**After (Exit Code 0):**
```bash
# Verify all API keys are set
$ export OPENAI_API_KEY="sk-..."
$ export ANTHROPIC_API_KEY="sk-ant-..."
# Expand data range
$ python JLAW_UNIFIED.py --cik 320187 --start-year 2017 --end-year 2019 --strict --auto
Phase 4 Gate PASSED: 14/15 nodes successful (93%)
...
Exit Code: 0
```

---

## Exit Code 5: Pattern Detection Failure

### What It Means

Phase 5 (Advanced Detection Patterns) failed to execute the minimum number of required patterns.

### Gate Requirements

- Minimum patterns executed (default: 20 out of 23)

### Common Causes

1. **Missing dependencies**
   ```
   Error: scikit-learn not installed for Isolation Forest
   ```

2. **Insufficient data for pattern**
   ```
   Error: Benford's Law requires minimum 100 data points
   ```

3. **Pattern execution errors**
   ```
   Error: Beneish M-Score calculation failed
   ```

### Remediation Steps

#### Issue: Missing Dependencies

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   pip install scikit-learn pandas numpy
   ```

2. Verify installation:
   ```bash
   python -c "import sklearn; print(sklearn.__version__)"
   ```

#### Issue: Insufficient Data

1. Check data availability for patterns:
   - Beneish M-Score: Requires financial statement data
   - Benford's Law: Requires 100+ numeric values
   - Altman Z-Score: Requires balance sheet data
   - Piotroski F-Score: Requires 2 years of data

2. Run with expanded date range:
   ```bash
   python JLAW_UNIFIED.py --cik 320187 --start-year 2015 --end-year 2019 --strict
   ```

#### Issue: Pattern Execution Errors

1. Review pattern-specific logs
2. Test patterns individually
3. Lower threshold if needed (document reason)

### Example Fix

**Before (Exit Code 5):**
```bash
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 5 Gate FAILED: Only 18/23 patterns executed
Exit Code: 5
```

**After (Exit Code 0):**
```bash
# Install missing dependencies
$ pip install scikit-learn
# Expand data range
$ python JLAW_UNIFIED.py --cik 320187 --start-year 2017 --end-year 2019 --strict --auto
Phase 5 Gate PASSED: 22/23 patterns executed
...
Exit Code: 0
```

---

## Exit Code 6: Evidence Chain Integrity Failure

### What It Means

Phase 8 (Evidence Chain Finalization) failed to properly compute hashes or maintain custody records.

### Gate Requirements

- Custody records present (> 0)
- Evidence chain hash computed

### Common Causes

1. **Hash computation failure**
   ```
   Error: Failed to compute SHA-256 hash
   ```

2. **Missing custody logs**
   ```
   Error: No custody records found
   ```

3. **File system issues**
   ```
   Error: Cannot write to evidence directory
   ```

### Remediation Steps

#### Issue: Hash Computation

1. Verify cryptography libraries:
   ```bash
   python -c "import hashlib; print(hashlib.sha256(b'test').hexdigest())"
   ```

2. Check for file corruption:
   ```bash
   # Verify collected evidence files
   ls -lh output/CASE_*/raw/
   ```

#### Issue: Custody Records

1. Verify evidence chain modules loaded:
   ```python
   from src.core.evidence_chain.hash_service import HashService
   from src.reporting.chain_of_custody_logger import ChainOfCustodyLogger
   ```

2. Check output directory permissions:
   ```bash
   chmod 755 output/
   ```

#### Issue: File System

1. Verify write permissions:
   ```bash
   touch output/test.txt && rm output/test.txt
   ```

2. Check disk space:
   ```bash
   df -h
   ```

3. Verify output directory exists:
   ```bash
   mkdir -p output
   ```

### Example Fix

**Before (Exit Code 6):**
```bash
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 8 Gate FAILED: Evidence chain hash not computed
Exit Code: 6
```

**After (Exit Code 0):**
```bash
# Ensure output directory has correct permissions
$ mkdir -p output && chmod 755 output
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 8 Gate PASSED: Evidence chain finalized with SHA-256 hash
...
Exit Code: 0
```

---

## Exit Code 7: Dossier Generation Failure

### What It Means

Phase 9 (DOJ-Grade Dossier Generation) failed to create the final forensic report.

### Gate Requirements

- Report generation successful

### Common Causes

1. **Missing report generator**
   ```
   Error: Report generator not initialized
   ```

2. **Template issues**
   ```
   Error: Report template not found
   ```

3. **File write errors**
   ```
   Error: Cannot write report to output directory
   ```

4. **Data serialization failures**
   ```
   Error: Failed to serialize JSON report
   ```

### Remediation Steps

#### Issue: Report Generator

1. Verify report modules:
   ```python
   from src.reporting.doj_report_generator import DOJReportGenerator
   ```

2. Check for missing dependencies:
   ```bash
   pip install jinja2 markdown reportlab
   ```

#### Issue: Template Problems

1. Verify template files exist:
   ```bash
   ls -la src/reporting/templates/
   ```

2. Reinstall if needed:
   ```bash
   git checkout src/reporting/templates/
   ```

#### Issue: File Write Errors

1. Check output directory permissions:
   ```bash
   chmod 755 output/
   ```

2. Verify disk space:
   ```bash
   df -h
   ```

#### Issue: Serialization

1. Check data structure:
   ```python
   import json
   # Review collected data for serialization issues
   ```

2. Validate JSON output:
   ```bash
   python -m json.tool output/CASE_*/report_*.json
   ```

### Example Fix

**Before (Exit Code 7):**
```bash
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 9 Gate FAILED: Report generation failed
Exit Code: 7
```

**After (Exit Code 0):**
```bash
# Ensure report dependencies are installed
$ pip install jinja2 markdown reportlab
# Ensure output directory has correct permissions
$ mkdir -p output && chmod 755 output
$ python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
Phase 9 Gate PASSED: Dossier generated successfully
Exit Code: 0
```

---

## Using Abort Reports

When strict mode fails, an abort report is generated in the output directory:

```bash
output/CASE_320187_20191231/ABORT_REPORT_*.txt
```

This report contains:
- Failure reason and phase
- Gate validation results
- Phase-by-phase status
- Specific remediation guidance
- Recommended next steps

### Example Abort Report

```
═══════════════════════════════════════════════════════════════
        JLAW FORENSIC ANALYSIS - EXECUTION ABORTED
═══════════════════════════════════════════════════════════════

CASE INFORMATION
  Case ID: CASE-320187-20240120
  Company: NIKE, Inc. (CIK: 0000320187)
  Execution Start: 2024-01-20 10:30:00
  Abort Time: 2024-01-20 10:32:15
  Total Duration: 2m 15s

ABORT REASON
  Phase: Phase 2 (SEC EDGAR Data Collection)
  Gate: Data collection validation
  Failure: Insufficient filings collected (2 < 5)
  Exit Code: 2

PHASE STATUS
  ✓ Phase 1: Configuration & Target Acquisition (PASSED)
  ✗ Phase 2: SEC EDGAR Data Collection (FAILED)
  - Phase 3: Document Parsing (SKIPPED)
  - Phase 4: 15-Node Analysis (SKIPPED)
  - Phase 5: Pattern Detection (SKIPPED)
  - Phase 8: Evidence Chain (SKIPPED)
  - Phase 9: Dossier Generation (SKIPPED)

REMEDIATION GUIDANCE
  1. Verify CIK number is correct
  2. Expand date range to capture more filings
  3. Check SEC EDGAR API access and rate limits
  4. Review filing availability for this company

RECOMMENDED ACTIONS
  - Try: python JLAW_UNIFIED.py --cik 320187 --start-year 2017 --end-year 2019 --strict
  - Or use non-strict mode for exploration
  - Review audit trail: output/CASE_*/audit_trail_*.json

═══════════════════════════════════════════════════════════════
```

## Using Audit Trails

The audit trail JSON file contains detailed execution information:

```bash
output/CASE_320187_20191231/audit_trail_*.json
```

### Useful Queries

**Get all gate validations:**
```bash
cat audit_trail_*.json | jq '.phases | to_entries[] | {phase: .key, passed: .value.validation.passed}'
```

**Get failed nodes:**
```bash
cat audit_trail_*.json | jq '.nodes[] | select(.status == "failed")'
```

**Get phase durations:**
```bash
cat audit_trail_*.json | jq '.phases | to_entries[] | {phase: .key, duration: .value.duration_seconds}'
```

**Get violation counts:**
```bash
cat audit_trail_*.json | jq '.nodes[] | {node: .node_name, violations: .violations_found}'
```

## Best Practices

### 1. Start with Non-Strict Mode

For initial exploration or when data availability is uncertain:
```bash
python JLAW_UNIFIED.py --cik 320187 --year 2019 --auto
```

### 2. Use Strict Mode for Production

For DOJ/SEC referrals and high-stakes investigations:
```bash
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
```

### 3. Review Abort Reports

Always read the abort report for specific guidance:
```bash
cat output/CASE_*/ABORT_REPORT_*.txt
```

### 4. Check Audit Trails

Use the JSON audit trail for detailed diagnostics:
```bash
python -m json.tool output/CASE_*/audit_trail_*.json | less
```

### 5. Verify Configuration First

Before long analysis sessions:
```bash
python -c "from config.secure_config import print_configuration_status; print_configuration_status()"
```

### 6. Monitor Logs

Enable verbose logging for troubleshooting:
```bash
export JLAW_LOG_LEVEL=DEBUG
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
```

## Getting Help

### Internal Resources

- [STRICT_EXECUTION_MODE.md](../STRICT_EXECUTION_MODE.md) - Full strict mode documentation
- [SEC_API_SETUP.md](SEC_API_SETUP.md) - SEC EDGAR configuration guide
- [VALIDATION_CHECKLIST.md](../VALIDATION_CHECKLIST.md) - Quality gate requirements

### External Resources

- SEC EDGAR API: https://www.sec.gov/edgar/sec-api-documentation
- SEC Support: oit@sec.gov
- OpenAI Status: https://status.openai.com
- Anthropic Status: https://status.anthropic.com

### Common Solutions Summary

| Exit Code | Quick Fix | Time to Fix |
|-----------|-----------|-------------|
| 1 | Set SEC_USER_AGENT in .env | 5 min |
| 2 | Expand date range | 10 min |
| 3 | Verify OPENAI_API_KEY | 5 min |
| 4 | Set all API keys, expand data | 20 min |
| 5 | Install dependencies | 10 min |
| 6 | Fix output directory permissions | 5 min |
| 7 | Install report dependencies | 10 min |

---

*For additional support, review the abort report and audit trail files generated in the output directory.*
