# System Overview

JLAW is a DOJ-grade SEC filing forensic analysis platform built on a modular, layered architecture designed for reliability, scalability, and court-admissible evidence generation.

---

## Architecture Principles

### Core Design Principles

1. **Single Entry Point**: Master Execution Controller orchestrates all analysis
2. **Phase Gate Validation**: Mandatory quality gates between execution phases
3. **Evidence Chain Integrity**: Cryptographic proof of document provenance
4. **Graceful Degradation**: Continues with partial data when non-critical components fail
5. **Fail-Fast Validation**: Strict mode enforces immediate abort on critical failures

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MASTER EXECUTION CONTROLLER                      │
│                  (Single Canonical Entry Point)                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─▶ PHASE 1: Configuration & Target Acquisition
                                  │   └─▶ GATE: 100% configuration validation
                                  │
                                  ├─▶ PHASE 2: SEC EDGAR Data Collection
                                  │   └─▶ GATE: Minimum 5 filings (80% required)
                                  │
                                  ├─▶ PHASE 3: Document Parsing & Indexing
                                  │   └─▶ GATE: 80% documents parsed
                                  │
                                  ├─▶ PHASE 4: 15-Node Recursive Analysis
                                  │   ├─▶ SUB-PHASE 4.1: Core SEC Filing (Nodes 1-6)
                                  │   ├─▶ SUB-PHASE 4.2: Extended Intelligence (Nodes 7-12)
                                  │   ├─▶ SUB-PHASE 4.3: Quantitative Scoring (Nodes 13-14)
                                  │   ├─▶ SUB-PHASE 4.4: Market Correlation (Node 15)
                                  │   ├─▶ SUB-PHASE 4.5: Cross-Node Correlation
                                  │   └─▶ GATE: 12/15 nodes successful (80%)
                                  │
                                  ├─▶ PHASE 5: Advanced Detection Patterns
                                  │   └─▶ GATE: 20/23 patterns executed (87%)
                                  │
                                  ├─▶ PHASE 6: Dual-Agent AI Cross-Validation
                                  │   └─▶ GATE: At least 1 AI agent responsive
                                  │
                                  ├─▶ PHASE 7: Subagent Orchestration
                                  │
                                  ├─▶ PHASE 8: Evidence Chain Finalization
                                  │   ├─▶ Triple-Hash (SHA-256 + SHA3-512 + BLAKE2b)
                                  │   ├─▶ Merkle Tree (RFC 6962)
                                  │   ├─▶ RFC 3161 Timestamp Tokens
                                  │   └─▶ GATE: 100% hash match (ABORT on failure)
                                  │
                                  └─▶ PHASE 9: DOJ-Grade Dossier Generation
                                      └─▶ FRE 902(13)/(14) compliant output
```

---

## Component Layers

### Layer 1: Orchestration Layer

**Master Execution Controller** (`src/core/master_execution_controller.py`)

- Single canonical entry point for all forensic analysis
- Orchestrates 9-phase execution flow
- Enforces phase gate validation
- Manages strict execution mode
- Generates abort reports on failures

**Unified Orchestrator** (`src/core/unified_orchestrator.py`)

- Legacy orchestrator (deprecated, use Master Execution Controller)
- Provides backwards compatibility
- Will be removed in v5.0

### Layer 2: Analysis Engine Layer

**Recursive Engine** (`src/core/recursive_engine.py`)

- Implements 15-node recursive analysis
- Manages 4 sub-phases of node execution
- Handles cross-node correlation
- Tracks node dependencies and data flow

**15 Analysis Nodes** (`src/nodes/node1-node15/`)

- Phase 1 (Nodes 1-6): Core SEC Filing Analysis
- Phase 2 (Nodes 7-12): Extended Intelligence
- Phase 3 (Nodes 13-14): Quantitative Financial Scoring
- Phase 4 (Node 15): Market Correlation Engine

See [15-Node Pipeline](15_node_pipeline.md) for detailed node documentation.

### Layer 3: Detection Layer

**Advanced Pattern Detector** (`src/detection/advanced_pattern_detector.py`)

- 23 fraud detection algorithms
- 85-97% accuracy metrics
- Pattern-specific configuration

**Detection Patterns**:
- Options backdating (Erik Lie methodology)
- Channel stuffing (DSO analysis)
- Spring loading (pre-announcement timing)
- Bullet dodging (post-bad-news timing)
- Round-tripping (revenue manipulation)
- Cookie jar reserves (earnings smoothing)
- And 17 more patterns...

See [Detection Patterns](../api/detection_patterns.md) for complete list.

### Layer 4: Integration Layer

**SEC EDGAR Client** (`src/integrations/sec_edgar/edgar_client.py`)

- Bulletproof SEC API integration
- Shared rate limiter (9 req/sec)
- Persistent caching with stale fallback
- Circuit breaker protection
- Exponential backoff retry

**Database Integrations**:
- **Neo4j**: Executive network graph analysis
- **TimescaleDB**: Time-series financial metrics
- **Redis**: Rate limiting and caching

**AI Provider Integrations**:
- **OpenAI**: Primary GPT-4 validation
- **Anthropic**: Secondary Claude validation
- **Dual-agent cross-validation**: Consensus scoring

**Market Data Integration**:
- **Polygon.io**: Real-time market correlation

### Layer 5: Evidence Chain Layer

**Evidence Chain Components** (`src/core/evidence_chain/`)

- **Hash Service**: Triple-hash computation (SHA-256 + SHA3-512 + BLAKE2b)
- **Merkle Tree**: RFC 6962 compliant evidence tree
- **RFC 3161 Client**: Timestamp authority integration
- **Chain of Custody Logger**: Document provenance tracking

See [Evidence Chain Architecture](evidence_chain.md) for details.

### Layer 6: Reporting Layer

**Dossier Generator** (`src/reporting/`)

- DOJ-grade forensic reports
- FRE 902(13)/(14) compliant formatting
- Evidence chain inclusion
- Human-readable summaries
- JSON and PDF output formats

---

## Data Flow

### Document Acquisition → Analysis → Report

```
SEC EDGAR Filings
       │
       ├─▶ Download & Cache (with rate limiting)
       │
       ├─▶ Compute Triple-Hash (SHA-256 + SHA3-512 + BLAKE2b)
       │
       ├─▶ Log Chain of Custody
       │
       ├─▶ Parse & Index Documents
       │       ├─▶ Form 4 (Insider Trading)
       │       ├─▶ 10-K (Annual Reports)
       │       ├─▶ 10-Q (Quarterly Reports)
       │       ├─▶ DEF 14A (Proxy Statements)
       │       ├─▶ 8-K (Material Events)
       │       └─▶ 13D/13F (Beneficial Ownership)
       │
       ├─▶ 15-Node Recursive Analysis
       │       ├─▶ Phase 1: Core SEC Filing (Nodes 1-6)
       │       ├─▶ Phase 2: Extended Intelligence (Nodes 7-12)
       │       ├─▶ Phase 3: Quantitative Scoring (Nodes 13-14)
       │       └─▶ Phase 4: Market Correlation (Node 15)
       │
       ├─▶ 23 Detection Pattern Analysis
       │       ├─▶ Timing-based patterns
       │       ├─▶ Statistical anomaly detection
       │       └─▶ Comparative analysis
       │
       ├─▶ Dual AI Agent Validation
       │       ├─▶ OpenAI GPT-4 analysis
       │       ├─▶ Anthropic Claude analysis
       │       └─▶ Consensus scoring
       │
       ├─▶ Evidence Chain Finalization
       │       ├─▶ Build Merkle tree
       │       ├─▶ Generate RFC 3161 timestamps
       │       └─▶ Validate hash integrity
       │
       └─▶ Generate Forensic Dossier
               ├─▶ Executive summary
               ├─▶ Detailed findings
               ├─▶ Evidence chain proof
               └─▶ Recommendations
```

---

## Execution Modes

### Standard Mode

- All phases execute with quality gates
- Warnings logged for non-critical failures
- Continues with partial data when possible
- Exit code 0 on success

### Strict Forensic Mode

- DOJ-grade protocols enforced
- Cascade abort on critical failures
- Detailed failure reports generated
- Specific exit codes (0-7) for failure types
- 100% evidence chain integrity required

See [Orchestration Hierarchy](orchestration_hierarchy.md) for execution flow details.

---

## Scalability & Performance

### Async Architecture

- All I/O operations use `async`/`await`
- Concurrent SEC API calls (within rate limits)
- Parallel node execution (when dependencies allow)

### Caching Strategy

- **Persistent file-based cache** for SEC filings
- **Stale cache fallback** for reliability
- **Configurable TTLs**:
  - Submissions: 24h
  - Filings: 1h
  - XBRL: 24h
  - Tickers: 7 days
  - Documents: 30 days

### Rate Limiting

- **Shared rate limiter** prevents concurrent violations
- **Token bucket algorithm** with adaptive adjustment
- **Exponential backoff** on 429 errors
- **Conservative rate**: 9 req/sec (SEC allows 10)

---

## Reliability Features

### Circuit Breaker

- Three states: CLOSED, OPEN, HALF_OPEN
- Prevents cascading failures during SEC API outages
- Automatic recovery with exponential backoff

### Retry Strategies

- Exponential backoff (default)
- Linear backoff
- Fibonacci backoff
- Configurable max retries (default: 5)

### Graceful Degradation

- Continues with partial data when possible
- Skips optional nodes (e.g., Node 15 if Polygon API unavailable)
- Logs warnings instead of aborting
- **Exception**: Strict mode aborts on critical failures

---

## Security & Compliance

### Evidence Chain Integrity

- **Triple-hash**: SHA-256 + SHA3-512 + BLAKE2b
- **Merkle tree**: RFC 6962 compliant
- **RFC 3161 timestamps**: Cryptographic proof of time
- **Chain of custody**: Complete document provenance

### Court Admissibility

- **FRE 902(13)**: Certified records generated by electronic process
- **FRE 902(14)**: Certified data from electronic device
- Network timestamp authority (FreeTSA) for court-admissible timestamps

### Data Privacy

- No PII storage
- API keys secured via environment variables
- Audit logs separated from operational logs

---

## Next Steps

- **[15-Node Pipeline](15_node_pipeline.md)**: Detailed node documentation
- **[Evidence Chain](evidence_chain.md)**: Evidence integrity architecture
- **[Orchestration Hierarchy](orchestration_hierarchy.md)**: Execution flow details
- **[API Reference](../api/nodes.md)**: Complete API documentation
