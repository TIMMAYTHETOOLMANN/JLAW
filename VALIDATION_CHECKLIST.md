# DOJ Forensic Reporting Validation Checklist

This checklist ensures that generated reports meet DOJ-level quality standards using the Nike 2019 analysis as the baseline reference.

---

## Strict Execution Mode Pre-Flight Checks

### When to Use Strict Mode

✅ **Use `--strict` flag for:**
- Production forensic investigations
- DOJ/SEC referrals requiring evidence chain integrity
- High-stakes compliance audits
- Cases requiring guaranteed completeness
- Automated CI/CD pipelines with quality gates

❌ **Don't use strict mode for:**
- Initial exploratory analysis
- Development/testing
- Data availability checks
- Cases with known data gaps

### Pre-Flight Configuration Validation

Before running strict mode, verify configuration:

```bash
python -c "from config.secure_config import print_configuration_status; print_configuration_status()"
```

**Required:**
- [ ] SEC_USER_AGENT configured with valid email
- [ ] OPENAI_API_KEY configured
- [ ] ANTHROPIC_API_KEY configured (for dual-agent validation)
- [ ] Output directory exists and is writable
- [ ] All dependencies installed: `pip install -r requirements.txt`

**Optional (enhances analysis):**
- [ ] GOVINFO_API_KEY configured (for statute enrichment)
- [ ] POLYGON_API_KEY configured (for Node 15 market correlation)

### Automated Gate Validation in Strict Mode

When using `--strict` flag, the following items are **automatically enforced** via programmatic phase gates:

| Phase | Gate | Auto-Enforced in Strict Mode | Exit Code on Failure |
|-------|------|------------------------------|----------------------|
| 1 | Configuration | ✅ SEC API config valid, 6+ modules loaded | 1 |
| 2 | Data Collection | ✅ Min 5 filings, per-type minimums | 2 |
| 3 | Document Parsing | ✅ Min 1 parsed, 10 chunks indexed | 3 |
| 4 | Node Execution | ✅ 12/15 nodes successful, 80% rate | 4 |
| 5 | Pattern Detection | ✅ 20/23 patterns executed | 5 |
| 8 | Evidence Chain | ✅ Hash computed, custody records present | 6 |
| 9 | Dossier Generation | ✅ Report generated successfully | 7 |

**📖 See [STRICT_EXECUTION_MODE.md](STRICT_EXECUTION_MODE.md) for detailed gate requirements**

**🔧 See [docs/STRICT_MODE_TROUBLESHOOTING.md](docs/STRICT_MODE_TROUBLESHOOTING.md) for failure remediation**

---

## Pre-Generation Checks

### Environment Configuration
- [ ] OPENAI_API_KEY configured
- [ ] ANTHROPIC_API_KEY configured (for dual-agent)
- [ ] GOVINFO_API_KEY configured (optional, for statute enrichment)
- [ ] SEC_USER_AGENT configured for EDGAR access

### Infrastructure
- [ ] Output directory exists and is writable
- [ ] Chain of custody logger initialized
- [ ] Evidence packager initialized
- [ ] DOJ Report Generator initialized

---

## Report Structure Validation

### Executive Summary
- [ ] Case ID included
- [ ] Company name and CIK included
- [ ] Analysis period (start/end dates) documented
- [ ] Total filings analyzed count
- [ ] Violation summary by severity (CRITICAL/HIGH/MEDIUM/LOW)
- [ ] Total violation count
- [ ] Financial impact range (min/max damages)
- [ ] Disgorgement estimate included
- [ ] Criminal referral count (if applicable)
- [ ] Regulatory routing table (SEC/DOJ/IRS)

### Per-Filing Detailed Analysis
For each filing analyzed:
- [ ] Accession number with hyperlink to SEC
- [ ] Filing type identified
- [ ] Filing date documented
- [ ] Violation count per filing
- [ ] Critical/High severity counts
- [ ] Estimated damages for filing

### Violation Details
For each violation:
- [ ] Unique violation ID assigned
- [ ] Violation type classified
- [ ] Severity level (CRITICAL/HIGH/MEDIUM/LOW)
- [ ] Prosecutorial merit assessment (STRONG/MODERATE/WEAK)
- [ ] Statutory reference with citation
- [ ] Statutory summary/explanation
- [ ] Description of violation
- [ ] **Exact quotes from filing** (minimum 1)
- [ ] Document URL for source
- [ ] Document section reference
- [ ] Damage estimate table:
  - [ ] Civil penalty minimum
  - [ ] Civil penalty maximum
  - [ ] Disgorgement estimate
  - [ ] Criminal exposure (YES/NO)
- [ ] Detection source (OpenAI/Anthropic/Pattern/Node)
- [ ] Confirmation sources (if cross-validated)
- [ ] Evidence hash (SHA-256)
- [ ] Red flags list (if applicable)

### Dual-Agent Consensus Tracking
- [ ] Section header present
- [ ] Agent agreement summary table
- [ ] Per-filing breakdown:
  - [ ] OpenAI findings count
  - [ ] Anthropic findings count
  - [ ] Overlap count
  - [ ] Unique findings per agent
  - [ ] Confidence level (percentage)
- [ ] Overall statistics:
  - [ ] Total OpenAI findings
  - [ ] Total Anthropic findings
  - [ ] Total overlap
  - [ ] Average confidence

### Subagent Findings (if applicable)
- [ ] Section header present
- [ ] Findings grouped by subagent
- [ ] For each finding:
  - [ ] Finding type
  - [ ] Confidence score
  - [ ] Description
  - [ ] Supporting data

### Statistical Analysis
- [ ] Filings by type table
- [ ] Violations by type table (sorted by count)
- [ ] Severity distribution table with percentages

### Chain of Custody
- [ ] Section header present
- [ ] Evidence items table:
  - [ ] Record ID
  - [ ] Evidence type
  - [ ] Description
  - [ ] SHA-256 hash (truncated for display)
  - [ ] Collection timestamp
  - [ ] Verification status
- [ ] Integrity verification summary:
  - [ ] Total evidence items count
  - [ ] All hashes verified (YES/NO)
  - [ ] Collection period
- [ ] Report digital signature hash

---

## Evidence Integrity Validation

### Hash Verification
- [ ] All evidence items have SHA-256 hashes
- [ ] Content hashes match actual content
- [ ] Merkle root computed correctly (for packages)
- [ ] Package integrity verification passes

### Chain Linking
- [ ] First event linked to genesis hash
- [ ] Each event links to previous event hash
- [ ] Sequence numbers are consecutive
- [ ] Current head matches last event hash

### Tamper Detection
- [ ] Chain verification returns no errors
- [ ] All individual events verify successfully
- [ ] Sealed chains cannot be modified

---

## Statutory Citation Validation

### Citation Accuracy
- [ ] All violation types have mapped statutes
- [ ] Citations follow correct format (e.g., "15 U.S.C. § 78p(a)")
- [ ] Titles are descriptive and accurate
- [ ] Summaries explain the statute relevance

### Penalty Information
- [ ] Civil penalty ranges included
- [ ] Criminal exposure flag accurate
- [ ] Prison years maximum (if applicable)
- [ ] Calculation methodology documented

### GovInfo Integration (if API key provided)
- [ ] API responses cached
- [ ] Fallback to built-in database works
- [ ] Citation URLs valid

---

## Nike 2019 Baseline Comparison

### Required Sections Present
- [ ] Executive Summary ✓
- [ ] Target Information ✓
- [ ] Per-Filing Analysis ✓
- [ ] Violation Details with Statutory Citations ✓
- [ ] Dual-Agent Consensus ✓
- [ ] Evidence Chain ✓
- [ ] Financial Impact Assessment ✓
- [ ] Regulatory Routing Recommendations ✓

### Quality Metrics Met
- [ ] ≥1 exact quote per violation
- [ ] ≥1 statutory citation per violation
- [ ] Chain of custody records present
- [ ] Dual-agent validation performed (when available)
- [ ] Damage estimation included

### Format Compliance
- [ ] Markdown report readable and well-formatted
- [ ] JSON report valid and parseable
- [ ] Tables properly formatted
- [ ] Links/URLs valid
- [ ] Hashes displayed correctly (truncated format)

---

## Output File Validation

### Markdown Report (.md)
- [ ] File created successfully
- [ ] All sections present
- [ ] Tables render correctly
- [ ] Links are clickable
- [ ] No broken formatting

### JSON Report (.json)
- [ ] File created successfully
- [ ] Valid JSON (parseable)
- [ ] All required fields present:
  - [ ] metadata
  - [ ] summary
  - [ ] filing_reports
  - [ ] chain_of_custody
  - [ ] report_hash
- [ ] Timestamps in ISO 8601 format
- [ ] Numeric values are numbers (not strings)

### HTML Report (.html) (if generated)
- [ ] File created successfully
- [ ] Valid HTML structure
- [ ] Styling applied
- [ ] Tables render correctly
- [ ] Classification banner visible

---

## Post-Generation Verification

### Report Hash
- [ ] Report hash generated (SHA-256)
- [ ] Hash documented in report
- [ ] Hash verifiable against content

### File Integrity
- [ ] All output files created
- [ ] Files are non-empty
- [ ] Files accessible and readable

### Evidence Package
- [ ] Package created for case
- [ ] Merkle root computed
- [ ] Integrity verification passes
- [ ] Export files generated

### Custody Chain
- [ ] Chain sealed after report generation
- [ ] Final event recorded
- [ ] Chain exported (JSON and/or Markdown)
- [ ] Verification passes

---

## Test Execution

### Required Tests Pass
```bash
# Quality gate tests
pytest tests/test_doj_report_validation.py -v
# Expected: All tests pass

# Evidence integrity tests
pytest tests/test_evidence_integrity.py -v
# Expected: All tests pass

# Nike 2019 baseline tests
pytest tests/test_nike_2019_baseline.py -v
# Expected: All tests pass
```

### Key Test Cases
- [ ] `test_comprehensive_report_generation` - Report generates successfully
- [ ] `test_markdown_report_structure` - All sections present
- [ ] `test_violation_details_in_report` - Violations with quotes included
- [ ] `test_json_report_structure` - JSON valid and complete
- [ ] `test_package_creation` - Evidence package created
- [ ] `test_integrity_verification` - Package verifies
- [ ] `test_chain_verification` - Custody chain valid
- [ ] `test_tamper_detection` - Tampering detected
- [ ] `test_generate_nike_quality_report` - Meets baseline

---

## Sign-Off

| Check | Date | Verified By |
|-------|------|-------------|
| Pre-Generation | | |
| Report Structure | | |
| Evidence Integrity | | |
| Statutory Citations | | |
| Nike 2019 Baseline | | |
| Output Files | | |
| Test Execution | | |

**Report Ready for DOJ Submission:** [ ] YES  [ ] NO

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## Using Strict Execution Mode for DOJ-Grade Analysis

### Command

```bash
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
```

### Advantages

- **Guaranteed Completeness**: All phase gates ensure minimum data requirements met
- **Cascade Abort**: Execution halts on critical failures (no partial/incomplete results without markers)
- **Audit Trail**: Complete JSON audit trail with all events, metrics, and timestamps
- **Exit Codes**: Specific codes (1-7) indicate failure type for automated error handling
- **Abort Reports**: Human-readable reports with remediation guidance
- **Evidence Preservation**: All collected data saved even on abort

### Monitoring Execution

**Check real-time progress:**
```bash
tail -f output/CASE_*/audit_trail_*.json
```

**Review gate validations:**
```bash
cat output/CASE_*/audit_trail_*.json | jq '.phases | to_entries[] | {phase: .key, passed: .value.validation.passed}'
```

**Check if execution was aborted:**
```bash
cat output/CASE_*/audit_trail_*.json | jq '.summary.aborted'
```

### Handling Gate Failures

If a gate fails:

1. **Review the abort report:**
   ```bash
   cat output/CASE_*/ABORT_REPORT_*.txt
   ```

2. **Check specific failure reason:**
   ```bash
   cat output/CASE_*/audit_trail_*.json | jq '.summary.abort_reason'
   ```

3. **Follow remediation guidance** in abort report

4. **Fix root cause** (see [docs/STRICT_MODE_TROUBLESHOOTING.md](docs/STRICT_MODE_TROUBLESHOOTING.md))

5. **Re-run analysis** with corrected configuration

### Quality Assurance Benefits

**Automated Enforcement:**
- ✅ Minimum filing counts enforced (no insufficient data)
- ✅ Node execution threshold enforced (80% success rate required)
- ✅ Pattern detection coverage enforced (20/23 minimum)
- ✅ Evidence chain integrity enforced (hashes required)
- ✅ Report generation enforced (no missing dossiers)

**Eliminates Manual Checks:**
- ❌ No need to manually verify filing counts
- ❌ No need to manually check node success rates
- ❌ No need to manually verify evidence hashes
- ❌ No need to manually confirm report generation

**Documentation:**
- Complete audit trail for case management systems
- Machine-readable JSON for automated processing
- Human-readable abort reports for quick troubleshooting
- Evidence chain for court admissibility

---

*This checklist should be completed for each report generation to ensure DOJ-grade quality standards are met.*
