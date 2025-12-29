# JLAW SEC Forensic Analysis System

## DOJ-Grade 15-Node Recursive Prosecutorial Engine

---

!!! success "Production Ready"
    JLAW v4.1.0 is a production-grade SEC filing forensic analysis platform implementing a **15-node recursive prosecutorial engine** with **23 fraud detection patterns**, **10 specialized Claude subagents**, and **dual AI agent cross-validation**.

---

## Overview

JLAW (Justice Law Analytics Workbench) is a comprehensive forensic analysis platform designed to analyze SEC EDGAR filings with DOJ-grade precision. The system produces courtroom-ready forensic dossiers with FRE 902(13)/(14) compliant evidence chains.

### Core Capabilities

- **15-Node Recursive Analysis Engine**: Sequential analysis phases covering all SEC filing types
- **23 Detection Algorithms**: 85-97% accuracy fraud pattern detection
- **10 Claude Specialized Agents**: Domain-specific forensic analysis
- **Dual AI Validation**: OpenAI + Anthropic cross-validation
- **Evidence Chain Integrity**: Triple-hash (SHA-256 + SHA3-512 + BLAKE2b) + Merkle tree + RFC 3161 timestamps
- **Strict Execution Mode**: DOJ-grade forensic protocols with mandatory phase gates

---

## Key Features

### Master Execution Controller

The **Master Execution Controller** is the single canonical entry point orchestrating the complete 9-phase execution flow:

1. **PHASE 1**: Configuration & Target Acquisition
2. **PHASE 2**: SEC EDGAR Data Collection
3. **PHASE 3**: Document Parsing & Indexing
4. **PHASE 4**: 15-Node Recursive Analysis (4 sub-phases)
5. **PHASE 5**: Advanced Detection Patterns (23 algorithms)
6. **PHASE 6**: Dual-Agent AI Cross-Validation
7. **PHASE 7**: Subagent Orchestration
8. **PHASE 8**: Evidence Chain Finalization
9. **PHASE 9**: DOJ-Grade Dossier Generation

Each phase includes **validation gates** that ensure data quality and system integrity before proceeding.

### Evidence Chain Compliance

JLAW implements court-admissible evidence chains:

- **FRE 902(13)/(14)**: Self-authenticating evidence standards
- **Triple-Hash Integrity**: SHA-256 + SHA3-512 + BLAKE2b
- **Merkle Tree**: RFC 6962 compliant for evidence verification
- **RFC 3161 Timestamps**: Cryptographic proof of document acquisition time

---

## Quick Links

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Quick Start Guide](quickstart.md)**

    ---
    
    Get started with JLAW in 5 minutes

-   :material-server: **[Deployment Guide](deployment/prerequisites.md)**

    ---
    
    Production deployment and configuration

-   :material-sitemap: **[Architecture Overview](architecture/system_overview.md)**

    ---
    
    Deep dive into system architecture

-   :material-api: **[API Reference](api/nodes.md)**

    ---
    
    Complete API documentation

-   :material-console: **[CLI Reference](user_guide/cli_reference.md)**

    ---
    
    Command-line interface guide

-   :material-bug: **[Troubleshooting](deployment/troubleshooting.md)**

    ---
    
    Common issues and solutions

</div>

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.10+ |
| RAM | 16 GB |
| Storage | 50 GB (for SEC filing cache) |
| CPU | 4 cores |

### Required Services

| Service | Purpose | Optional |
|---------|---------|----------|
| SEC EDGAR API | Filing acquisition | No |
| OpenAI API | Primary AI validation | No |
| Anthropic API | Secondary AI validation | No |
| Neo4j | Executive network analysis | Yes (Node 11) |
| Redis | Rate limiting & caching | Yes |
| TimescaleDB | Time-series metrics | Yes |
| Polygon.io | Market correlation | Yes (Node 15) |

---

## Core Metrics

| Metric | Value |
|--------|-------|
| Python Modules | 68 |
| Analysis Nodes | 15 |
| Detection Patterns | 23 (85-97% accuracy) |
| Claude Subagents | 10 |
| Execution Phases | 9 |
| Phase Gates | 6 |
| Exit Codes | 8 (0-7) |
| Strict Mode Tests | 69 |
| SEC Form Coverage | 11 types |
| AI Providers | 2 (OpenAI + Anthropic) |

---

## Investigation Types

JLAW supports various investigation types with optimized node execution:

- **Insider Trading**: §16 violations, timing analysis, options backdating
- **Accounting Fraud**: Revenue manipulation, earnings smoothing, cookie jar reserves
- **Executive Compensation**: Golden parachutes, backdating, tax exposure
- **Material Events**: 8-K analysis, restatements, disclosure timing
- **Financial Health**: Bankruptcy prediction, financial strength scoring

---

## Documentation Structure

- **[Quick Start](quickstart.md)**: 5-minute setup guide
- **[Architecture](architecture/system_overview.md)**: System design and components
- **[Deployment](deployment/prerequisites.md)**: Production deployment guides
- **[User Guide](user_guide/cli_reference.md)**: Day-to-day usage
- **[Development](development/contributing.md)**: Contributing to JLAW
- **[API Reference](api/nodes.md)**: Complete API documentation

---

## License

JLAW is licensed under the MIT License. See LICENSE file for details.

---

## Support

For issues, questions, or contributions:

- **GitHub Issues**: [TIMMAYTHETOOLMANN/JLAW](https://github.com/TIMMAYTHETOOLMANN/JLAW/issues)
- **Documentation**: [https://github.com/TIMMAYTHETOOLMANN/JLAW](https://github.com/TIMMAYTHETOOLMANN/JLAW)
