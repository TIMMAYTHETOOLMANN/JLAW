# PATCH INTEGRATION GUIDE

## Integration Instructions

### 1. Late Form 4 Analyzer Integration

**File:** `src/forensics/insider_form4_analyzer.py`

**Action:**
- Replace the existing late filing detection logic with `BaselineCompliantLateFilingAnalyzer`
- Key change: Use CALENDAR days instead of business days
- Update: `_calculate_filing_deadline()` method

**Code Change:**
```python
# OLD (INCORRECT):
required_date = txn_date + timedelta(days=2)  # Works but uses business days concept
days_late = business_days_between(txn_date, file_date)

# NEW (CORRECT):
required_date = txn_date + timedelta(days=2)  # 2 CALENDAR days
days_late = (file_date - txn_date).days  # Total calendar days
```

### 2. SOX 302 Detector Integration

**File:** `src/forensics/sec_edgar_analyzer.py`

**Action:**
- Add `BaselineCompliantSOX302Detector` class
- Use for all 10-K and 10-Q filings
- Pattern matching for Exhibit 31.1 and 31.2

**Integration Point:**
- Call in main filing analysis loop
- Flag violation if certifications missing

### 3. Material Misstatement Detector Integration

**File:** `src/forensics/sec_edgar_analyzer.py`

**Action:**
- Add `BaselineCompliantMaterialMisstatementDetector` class
- Use for all 10-K and 10-Q filings
- Pattern matching for restatement language

**Integration Point:**
- Call in main filing analysis loop
- Scan filing text for baseline patterns

### 4. Zero-Dollar Detector Integration

**File:** `src/forensics/insider_form4_analyzer.py`

**Action:**
- Add `BaselineCompliantZeroDollarDetector` class (with deduplication)
- Use for all Form 4 transactions
- Maintain deduplication state across accessions

**Integration Point:**
- Initialize detector once per analysis run
- Call for each transaction
- Reset between filing batches

## Validation

After integration, run:
```bash
python execute_baseline_fix_integration.py
```

Expected output:
```
Compliance Score: 100.0%
Status: COMPLIANT
Compliant Metrics: 8/8
```

## Testing

```bash
# Run baseline validation
python validate_remediation_patch.py

# Run full forensic analysis
python run_nike_2019_analysis.py

# Compare output to baseline
python validate_pdf_baseline.py
```
