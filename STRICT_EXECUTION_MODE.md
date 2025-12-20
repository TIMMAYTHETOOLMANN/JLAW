# Strict Execution Mode Documentation

## Overview

Strict Execution Mode enforces DOJ-grade forensic analysis quality standards by implementing mandatory phase gates, data contract validation, and cascade abort protocols. This mode eliminates silent failures and ensures complete, actionable forensic dossiers.

## Usage

### Command Line

```bash
# Standard strict mode
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto

# Strict mode with custom output directory
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto --output /path/to/output
```

### Key Differences from Standard Mode

| Feature | Standard Mode | Strict Mode |
|---------|--------------|-------------|
| Phase Gates | Advisory warnings only | Mandatory validation |
| Failures | Graceful degradation | Immediate abort with specific exit code |
| Data Contracts | Not enforced | Strictly enforced |
| Audit Trail | Basic logging | Comprehensive JSON audit trail |
| Exit Codes | Generic (0 or 1) | Specific per failure type (1-7) |
| Partial Results | Discarded | Preserved with INCOMPLETE markers |

## Architecture

### Components

1. **StrictExecutionController** (`src/core/strict_execution_controller.py`)
   - Orchestrates execution with gate enforcement
   - Triggers cascade abort on failures
   - Manages audit trail and exit codes

2. **PhaseGateValidator** (`src/core/phase_gate_validator.py`)
   - Validates phase outputs against data contracts
   - Returns PASS/FAIL/OVERRIDE_REQUIRED decisions
   - Tracks validation history

3. **DataContracts** (`src/core/data_contracts.py`)
   - Defines required data for each phase
   - Validates minimum thresholds
   - Reports specific contract violations

4. **ExecutionAudit** (`src/core/execution_audit.py`)
   - Real-time event tracking
   - Phase metrics and timing
   - Node execution records
   - Abort report generation

5. **Configuration** (`config/strict_execution_config.py`)
   - Configurable thresholds per phase
   - Preset configurations (default, strict, DOJ, SEC)
   - Exit codes and remediation guidance

## Phase Gates

### Phase 1: Configuration & Target Acquisition

**Requirements:**
- SEC EDGAR Client initialized and available
- Minimum 6 modules loaded (strict mode)
- SEC API configuration valid

**Gate Failure:**
- Exit Code: 1
- Remediation: Check API credentials, module dependencies, connectivity

### Phase 2: SEC EDGAR Data Collection

**Requirements:**
- Minimum total filings collected (default: 1, strict: 5)
- Per-type minimums met (if configured):
  - 10-K: 1 filing minimum
  - 10-Q: 3 filings minimum
  - DEF 14A: 1 filing minimum
  - Form 4: 10 filings minimum
  - 8-K: 5 filings minimum

**Gate Failure:**
- Exit Code: 2
- Remediation: Check CIK validity, date range, SEC EDGAR access, rate limiting

### Phase 3: DocsGPT Document Parsing & Indexing

**Requirements:**
- Minimum documents parsed (default: 1)
- Minimum chunks indexed (strict mode: 10)

**Gate Failure:**
- Exit Code: 3
- Remediation: Check filing accessibility, parser dependencies, document formats

### Phase 4: 15-Node Recursive Analysis

**Requirements:**
- Minimum nodes successful (default: 12 out of 15)
- Minimum success rate (default: 80%)
- Node results data present

**Gate Failure:**
- Exit Code: 4
- Remediation: Check data quality, node dependencies, analysis parameters

### Phase 5: Advanced Detection Patterns

**Requirements:**
- Minimum patterns executed (default: 20 out of 23)

**Gate Failure:**
- Exit Code: 5
- Remediation: Check detection module configuration, input data completeness

### Phase 8: Evidence Chain Finalization

**Requirements:**
- Custody records present (> 0)
- Evidence chain hash computed

**Gate Failure:**
- Exit Code: 6
- Remediation: Check hash computation, custody logging, data preservation

### Phase 9: DOJ-Grade Dossier Generation

**Requirements:**
- Report generation successful

**Gate Failure:**
- Exit Code: 7
- Remediation: Check report generator dependencies, output permissions

## Exit Codes

| Code | Meaning | Phase |
|------|---------|-------|
| 0 | Complete success | - |
| 1 | Configuration/initialization failure | Phase 1 |
| 2 | Data collection failure | Phase 2 |
| 3 | Document parsing failure | Phase 3 |
| 4 | Node execution below threshold | Phase 4 |
| 5 | Pattern detection failure | Phase 5 |
| 6 | Evidence chain integrity failure | Phase 8 |
| 7 | Dossier generation failure | Phase 9 |

## Configuration Presets

### Default (Non-Strict)

```python
config = load_config("default")
# strict_mode = False
# min_filings_total = 1
# min_nodes_successful = 12
# No halt on failures
```

### Strict

```python
config = load_config("strict")
# strict_mode = True
# min_filings_total = 5
# min_nodes_successful = 12
# Halts on critical failures
```

### DOJ Investigation

```python
config = load_config("doj")
# strict_mode = True
# min_filings_total = 10
# min_nodes_successful = 14 (93% success rate)
# min_patterns_executed = 22
# require_dual_agent_validation = True
```

### SEC Referral

```python
config = load_config("sec")
# strict_mode = True
# min_filings_total = 5
# min_nodes_successful = 12
# require_dual_agent_validation = False
```

## Cascade Abort Protocol

When a critical failure occurs in strict mode:

1. **Evidence Preservation**
   - All collected data saved to output directory
   - Partial analysis results retained
   - No data loss

2. **Partial Dossier Generation**
   - Incomplete dossier created with clear markers
   - "INCOMPLETE - EXECUTION HALTED" noted
   - Contains all findings up to failure point

3. **Detailed Forensics**
   - Complete stack traces logged
   - Failure reason documented
   - Phase and gate information captured

4. **Audit Trail**
   - JSON audit trail saved to output directory
   - Contains all events, metrics, and timestamps
   - Machine-readable for case management integration

5. **Abort Report**
   - Human-readable abort report generated
   - Phase status breakdown
   - Gate validation results
   - Remediation guidance

6. **Specific Exit Code**
   - Non-zero exit code returned
   - Indicates failure type
   - Enables automated error handling

## Audit Trail Format

The audit trail is saved as `audit_trail_<case_id>_<timestamp>.json`:

```json
{
  "summary": {
    "case_id": "JLAW-320187-20240101120000",
    "execution_start": "2024-01-01T12:00:00",
    "execution_end": "2024-01-01T12:15:30",
    "total_duration_seconds": 930.5,
    "aborted": false,
    "gates": {
      "total_validated": 5,
      "passed": 5,
      "failed": 0,
      "pass_rate": "100.0%"
    },
    "nodes": {
      "total_executed": 15,
      "successful": 14,
      "failed": 1
    }
  },
  "phases": {
    "Phase 1: Configuration": {
      "start": "2024-01-01T12:00:00",
      "end": "2024-01-01T12:00:05",
      "duration_seconds": 5.2,
      "records": {"extracted": 6, "expected": 6},
      "validation": {"passed": true, "violations": []}
    }
    // ... more phases
  },
  "nodes": [
    {
      "node_id": "NODE_1",
      "node_name": "Form 4 Analysis",
      "status": "success",
      "violations_found": 3,
      "duration_seconds": 2.5
    }
    // ... more nodes
  ],
  "events": [
    {
      "timestamp": "2024-01-01T12:00:00",
      "event_type": "phase_start",
      "phase": "Phase 1: Configuration",
      "message": "Starting phase"
    }
    // ... more events
  ]
}
```

## Best Practices

### When to Use Strict Mode

✅ **Use strict mode for:**
- Production forensic investigations
- DOJ/SEC referrals
- High-stakes compliance audits
- Cases requiring evidence chain integrity
- Automated CI/CD pipelines

❌ **Don't use strict mode for:**
- Initial exploratory analysis
- Development/testing
- Data availability checks
- Cases with known data gaps

### Handling Gate Failures

1. **Review the Abort Report**
   - Located in output directory
   - Contains detailed failure information
   - Includes remediation guidance

2. **Check the Audit Trail**
   - Machine-readable JSON format
   - Complete event history
   - Phase-by-phase metrics

3. **Address Root Cause**
   - Follow remediation guidance
   - Fix configuration issues
   - Resolve data availability problems

4. **Re-run Analysis**
   - Use same case ID to track attempts
   - Review previous audit trails
   - Verify fixes resolved issues

### Custom Configuration

Create custom configurations by extending `StrictExecutionConfig`:

```python
from config.strict_execution_config import StrictExecutionConfig, AnalysisThresholds

custom_config = StrictExecutionConfig(
    strict_mode=True,
    thresholds=AnalysisThresholds(
        min_filings_total=15,
        min_filings_per_type={
            "10-K": 3,
            "10-Q": 8,
            "DEF 14A": 2,
            "4": 30,
            "8-K": 15,
        },
        min_nodes_successful=15,  # All nodes must succeed
        min_node_success_rate=1.0,  # 100% success rate
        min_patterns_executed=23,  # All patterns
        require_evidence_chain=True,
        require_dual_agent_validation=True,
    )
)
```

## Integration with CI/CD

### Shell Script Example

```bash
#!/bin/bash
set -e

# Run strict mode analysis
python JLAW_UNIFIED.py --cik $CIK --year $YEAR --strict --auto --output $OUTPUT_DIR

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Forensic analysis completed successfully"
    # Upload results to case management system
    upload_results.sh $OUTPUT_DIR
elif [ $EXIT_CODE -eq 2 ]; then
    echo "✗ Data collection failed - check SEC EDGAR access"
    exit 1
elif [ $EXIT_CODE -eq 4 ]; then
    echo "✗ Node execution below threshold - review data quality"
    exit 1
else
    echo "✗ Analysis failed with exit code $EXIT_CODE"
    exit 1
fi
```

### GitHub Actions Example

```yaml
name: Forensic Analysis

on:
  workflow_dispatch:
    inputs:
      cik:
        required: true
      year:
        required: true

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Strict Mode Analysis
        run: |
          python JLAW_UNIFIED.py \
            --cik ${{ github.event.inputs.cik }} \
            --year ${{ github.event.inputs.year }} \
            --strict --auto \
            --output output/${{ github.event.inputs.cik }}
        
      - name: Upload Audit Trail
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: audit-trail
          path: output/**/audit_trail_*.json
      
      - name: Upload Abort Reports
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: abort-reports
          path: output/**/ABORT_REPORT_*.txt
```

## Troubleshooting

### Common Issues

**Issue: "SEC API configuration invalid"**
- Solution: Set `SEC_USER_AGENT` environment variable with contact email
- Example: `SEC_USER_AGENT="MyCompany forensics@company.com"`

**Issue: "Insufficient filings collected"**
- Solution: Verify CIK number, check date range, ensure SEC EDGAR access
- May need to adjust `min_filings_total` threshold

**Issue: "Node execution below threshold"**
- Solution: Check data quality, verify all dependencies installed
- Review individual node error messages in logs

**Issue: "Gate validation failed"**
- Solution: Review specific contract violations in abort report
- May need to relax thresholds for edge cases
- Consider using non-strict mode for exploratory analysis

## See Also

- [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md) - Quality gate requirements
- [test_strict_execution.py](tests/test_strict_execution.py) - Test examples
- [test_phase_gates.py](tests/test_phase_gates.py) - Gate validation tests
