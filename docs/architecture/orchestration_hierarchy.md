# Orchestration Hierarchy

The Master Execution Controller is the single canonical entry point that orchestrates all forensic analysis through a hierarchical, phase-based execution model.

---

## Hierarchy Overview

```
┌────────────────────────────────────────────────────────────┐
│          MASTER EXECUTION CONTROLLER (MEC)                 │
│         src/core/master_execution_controller.py            │
│                                                            │
│  Single canonical entry point for all analysis            │
│  Orchestrates 9-phase execution flow                      │
│  Enforces phase gate validation                           │
│  Manages strict execution mode                            │
└────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌────────────────┐   ┌──────────────┐
│ Recursive    │   │   Pattern      │   │   Reporting  │
│ Engine       │   │   Detector     │   │   Generator  │
│              │   │                │   │              │
│ 15-Node      │   │ 23 Detection   │   │ DOJ-Grade    │
│ Pipeline     │   │ Algorithms     │   │ Dossiers     │
└──────────────┘   └────────────────┘   └──────────────┘
        │
        ├─▶ Node 1: Form 4 Insider Trading
        ├─▶ Node 2: DEF 14A Compensation
        ├─▶ Node 3: 10-Q Temporal Analysis
        ├─▶ Node 4: 10-K SOX Validation
        ├─▶ Node 5: IRC §83 Tax Exposure
        ├─▶ Node 6: Enforcement Routing
        ├─▶ Node 7: 13F-HR Institutional
        ├─▶ Node 8: SC 13D/13G Ownership
        ├─▶ Node 9: 8-K Material Events
        ├─▶ Node 10: Form 144 Restricted
        ├─▶ Node 11: Executive Networks
        ├─▶ Node 12: Earnings Transcripts
        ├─▶ Node 13: Altman Z-Score
        ├─▶ Node 14: Piotroski F-Score
        └─▶ Node 15: Market Correlation
```

---

## 9-Phase Execution Flow

### PHASE 1: Configuration & Target Acquisition

**Purpose**: Load configuration and validate target company

**Gate Requirement**: 100% configuration validation

**Components**:
- Environment variable loading
- SEC User-Agent validation
- API key verification
- Target company lookup (CIK resolution)
- Date range validation

**Output**: Validated configuration object

**Failure Exit Code**: 1

---

### PHASE 2: SEC EDGAR Data Collection

**Purpose**: Acquire SEC filings from EDGAR database

**Gate Requirement**: Minimum 5 filings (80% of expected)

**Components**:
- SEC EDGAR API client
- Rate limiting (9 req/sec)
- Persistent caching with stale fallback
- Circuit breaker protection
- Exponential backoff retry

**Filing Types**:
- Form 4 (Insider Trading)
- 10-K (Annual Reports)
- 10-Q (Quarterly Reports)
- DEF 14A (Proxy Statements)
- 8-K (Material Events)
- SC 13D/13G (Beneficial Ownership)
- 13F-HR (Institutional Holdings)
- Form 144 (Restricted Sales)

**Output**: Downloaded filing documents with metadata

**Failure Exit Code**: 2

---

### PHASE 3: Document Parsing & Indexing

**Purpose**: Parse and index all downloaded documents

**Gate Requirement**: 80% documents parsed successfully

**Components**:
- XML parsing (Form 4, 8-K)
- HTML parsing (10-K, 10-Q, DEF 14A)
- XBRL parsing (financial statements)
- PDF parsing (exhibits)
- Text extraction and indexing

**Output**: Parsed document structures

**Failure Exit Code**: 3

---

### PHASE 4: 15-Node Recursive Analysis

**Purpose**: Execute comprehensive forensic analysis

**Gate Requirement**: 12/15 nodes successful (80% threshold)

#### SUB-PHASE 4.1: Core SEC Filing Analysis (Nodes 1-6)

**Nodes**:
1. Form 4 Insider Trading (§16 violations)
2. DEF 14A Executive Compensation
3. 10-Q Temporal Consistency
4. 10-K SOX Certification
5. IRC §83 Tax Exposure
6. Enforcement Routing

**Sequential Execution**: Nodes 1-5 → Node 6 (depends on all previous)

---

#### SUB-PHASE 4.2: Extended Intelligence (Nodes 7-12)

**Nodes**:
7. 13F-HR Institutional Holdings
8. SC 13D/13G Beneficial Ownership
9. 8-K Material Events
10. Form 144 Restricted Sales
11. Executive Network Analysis (Neo4j)
12. Earnings Call Transcripts

**Parallel Execution**: Nodes can run concurrently

---

#### SUB-PHASE 4.3: Quantitative Forensic Scoring (Nodes 13-14)

**Nodes**:
13. Altman Z-Score (Bankruptcy Prediction)
14. Piotroski F-Score (Financial Strength)

**Sequential Execution**: Both depend on Node 4 (10-K data)

---

#### SUB-PHASE 4.4: Market Correlation (Node 15)

**Node**:
15. Market Correlation Engine (Polygon.io)

**Optional**: Skipped if Polygon API unavailable

---

#### SUB-PHASE 4.5: Cross-Node Correlation

**Purpose**: Identify patterns across multiple nodes

**Correlations**:
- Temporal: Events in close time proximity
- Causal: Events with cause-effect relationship
- Actor: Same executives across violations
- Pattern: Similar fraud patterns

**Output**: Cross-node findings, correlation matrix

---

**Phase 4 Failure Exit Code**: 4

---

### PHASE 5: Advanced Detection Patterns

**Purpose**: Apply 23 fraud detection algorithms

**Gate Requirement**: 20/23 patterns executed (87% threshold)

**Pattern Categories**:

1. **Timing-Based Patterns**:
   - Options backdating
   - Spring loading
   - Bullet dodging
   - Pre-announcement trading

2. **Statistical Patterns**:
   - Benford's Law deviations
   - DSO analysis (channel stuffing)
   - Revenue recognition timing
   - Earnings smoothing

3. **Comparative Patterns**:
   - Peer comparison
   - Industry benchmarks
   - Historical trends
   - Seasonal adjustments

**Accuracy**: 85-97% depending on pattern

**Output**: Pattern match results, violation flags

**Failure Exit Code**: 5

---

### PHASE 6: Dual-Agent AI Cross-Validation

**Purpose**: Validate findings with AI agents

**Gate Requirement**: At least 1 AI agent responsive

**Agents**:
- **OpenAI GPT-4**: Primary validation
- **Anthropic Claude**: Secondary validation

**Validation Process**:
1. Send findings to both agents
2. Request independent analysis
3. Compare consensus scores
4. Flag high-confidence findings
5. Generate confidence metrics

**Output**: AI validation results, consensus scores

**Failure Exit Code**: N/A (warnings only)

---

### PHASE 7: Subagent Orchestration

**Purpose**: Deploy specialized Claude subagents

**Subagents** (10 total):
1. Insider Trading Specialist
2. Compensation Analyst
3. Accounting Fraud Detective
4. SOX Compliance Auditor
5. Tax Exposure Calculator
6. Material Events Analyst
7. Network Analyzer
8. Bankruptcy Predictor
9. Financial Strength Evaluator
10. Market Correlation Expert

**Execution**: Parallel deployment with timeout

**Output**: Subagent findings, specialized insights

---

### PHASE 8: Evidence Chain Finalization

**Purpose**: Establish court-admissible evidence chain

**Gate Requirement**: 100% hash match (ABORT on failure)

**Components**:

1. **Triple-Hash Computation**:
   - SHA-256 (primary)
   - SHA3-512 (secondary)
   - BLAKE2b (tertiary)

2. **Merkle Tree Construction**:
   - RFC 6962 compliant
   - Single root hash
   - Inclusion proofs

3. **RFC 3161 Timestamps**:
   - Network TSA (FreeTSA)
   - Cryptographic proof of time
   - Certificate validation

4. **Chain of Custody Logging**:
   - Document acquisition
   - Processing steps
   - Access control
   - Storage locations

**Output**: Evidence chain proof, custody logs

**Failure Exit Code**: 6 (CRITICAL - evidence integrity failure)

---

### PHASE 9: DOJ-Grade Dossier Generation

**Purpose**: Generate courtroom-ready forensic report

**Components**:

1. **Executive Summary**:
   - Key findings
   - Violation counts
   - Severity scores
   - Recommendations

2. **Detailed Findings**:
   - Node-by-node results
   - Pattern detection results
   - AI validation consensus
   - Evidence references

3. **Evidence Chain Inclusion**:
   - Merkle root hash
   - Timestamp tokens
   - Custody logs
   - Hash verification

4. **FRE 902(13)/(14) Compliance**:
   - Self-authenticating records
   - Certified electronic data
   - Process documentation
   - Certificate of authenticity

**Output Formats**:
- JSON (machine-readable)
- PDF (human-readable)
- TXT (summary)

**Failure Exit Code**: 7

---

## Execution Modes

### Standard Mode

**Behavior**:
- All phases execute with quality gates
- Warnings logged for non-critical failures
- Continues with partial data when possible
- Exit code 0 on success

**Usage**:
```bash
python jlaw_cli.py --cik 320187 --year 2019
```

---

### Strict Forensic Mode

**Behavior**:
- DOJ-grade protocols enforced
- Cascade abort on critical failures
- Detailed failure reports generated
- Specific exit codes (0-7) for failure types
- 100% evidence chain integrity required

**Usage**:
```bash
python jlaw_cli.py --cik 320187 --year 2019 --strict --auto
```

**Characteristics**:
- ✅ Mandatory phase gates
- ✅ Cascade abort
- ✅ Detailed failure reports
- ✅ Specific exit codes
- ✅ 100% evidence integrity
- ✅ No partial data
- ✅ Full audit trail

---

### Auto Mode

**Behavior**:
- No interactive confirmations
- Automatic execution through all phases
- Suitable for batch processing
- Logs all decisions

**Usage**:
```bash
python jlaw_cli.py --cik 320187 --year 2019 --auto
```

---

## Phase Gate Validation

### Gate Logic

Each phase gate validates:

1. **Data Completeness**: Required data present
2. **Data Quality**: Data passes validation rules
3. **Success Threshold**: Minimum success percentage met
4. **Critical Errors**: No critical failures occurred

### Gate Pass/Fail

**Pass**: Proceed to next phase
**Fail (Standard Mode)**: Log warning, attempt to continue
**Fail (Strict Mode)**: Cascade abort, generate failure report

---

## Error Handling Hierarchy

```
Critical Errors → Cascade Abort (Strict Mode)
     │
     ├─▶ Configuration failure (Exit Code 1)
     ├─▶ Evidence chain failure (Exit Code 6)
     └─▶ No filings found (Exit Code 2)

Non-Critical Errors → Log Warning (Standard Mode)
     │
     ├─▶ Optional node failure (e.g., Node 15)
     ├─▶ Optional database unavailable (e.g., Neo4j)
     └─▶ Optional API unavailable (e.g., Polygon)

Recoverable Errors → Retry with Backoff
     │
     ├─▶ SEC API rate limit (429)
     ├─▶ Network timeout
     └─▶ Temporary service outage
```

---

## Execution Audit Trail

All execution decisions are logged for audit:

```json
{
  "execution_id": "uuid-here",
  "mode": "strict",
  "phases": [
    {
      "phase": "PHASE_1",
      "status": "complete",
      "gate_passed": true,
      "duration": 5.2
    },
    {
      "phase": "PHASE_2",
      "status": "complete",
      "gate_passed": true,
      "filings_collected": 47,
      "duration": 120.5
    }
  ]
}
```

---

## Next Steps

- **[System Overview](system_overview.md)**: High-level architecture
- **[15-Node Pipeline](15_node_pipeline.md)**: Detailed node documentation
- **[Evidence Chain](evidence_chain.md)**: Evidence integrity details
- **[CLI Reference](../user_guide/cli_reference.md)**: Command-line usage
