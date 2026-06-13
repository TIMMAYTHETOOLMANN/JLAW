# PROSECUTION BRIEF — NIKE, INC. (CIK 0000320187)

## Securities Fraud Investigation Master Reference Document

**Classification:** PROSECUTION-SENSITIVE — ATTORNEY WORK PRODUCT  
**Case Reference:** JLAW-NKE-2019-001  
**Target Entity:** NIKE, Inc. (NYSE: NKE)  
**CIK:** 0000320187  
**SIC Code:** 5130 — Apparel, Piece Goods & Notions  
**Investigation Period:** FY2019 (June 1, 2018 – May 31, 2019)  
**Document Version:** 3.0 (13-Section Expanded Edition)  
**Last Updated:** 2026-04-01  

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Statutory Framework](#2-statutory-framework)
3. [Target Company Profile](#3-target-company-profile)
4. [Investigation Scope & Objectives](#4-investigation-scope--objectives)
5. [Evidence Standards & Admissibility](#5-evidence-standards--admissibility)
6. [SEC Filing Corpus Inventory](#6-sec-filing-corpus-inventory)
7. [Phase 1 — Data Acquisition Protocol](#7-phase-1--data-acquisition-protocol)
8. [Phase 2 — Filing Analysis Protocol](#8-phase-2--filing-analysis-protocol)
9. [Phase 3 — Pattern Detection & Cross-Referencing](#9-phase-3--pattern-detection--cross-referencing)
10. [Phase 4 — Prosecutorial Findings Assembly](#10-phase-4--prosecutorial-findings-assembly)
11. [Enforcement Routing Matrix](#11-enforcement-routing-matrix)
12. [Evidence Integrity & Chain of Custody](#12-evidence-integrity--chain-of-custody)
13. [Investigation Protocol & Session Management](#13-investigation-protocol--session-management)

---

## 1. EXECUTIVE SUMMARY

This prosecution brief establishes the master reference framework for the JLAW
forensic analysis of NIKE, Inc. (CIK 0000320187) SEC filings spanning fiscal
year 2019. The investigation applies the full 16-node recursive prosecutorial
engine with 23 fraud detection patterns to identify potential securities
violations, insider trading anomalies, executive compensation irregularities,
and financial reporting inconsistencies.

### 1.1 Investigation Hypothesis

NIKE's FY2019 period encompasses significant corporate events including
executive transitions, share repurchase programs, and international tax
restructuring that present elevated fraud risk indicators warranting
systematic forensic scrutiny across all SEC filing categories.

### 1.2 Analytical Objectives

- Detect insider trading patterns via Form 4 temporal clustering analysis
- Identify executive compensation anomalies in DEF 14A proxy filings
- Verify SOX certification integrity across 10-K/10-Q submissions
- Cross-reference 13F institutional holdings for coordinated trading signals
- Map 8-K material event timing against insider transaction windows
- Assess Z-Score and F-Score financial health trajectory
- Correlate market price movements with filing disclosure timing

### 1.3 Expected Deliverables

- `narrative_report.md` — Prosecution-grade narrative with statutory citations
- `analysis.json` — Machine-readable findings with evidence chain hashes
- Evidence integrity attestation with triple-hash verification
- Enforcement routing recommendations (SEC/DOJ/IRS-CI)

---

## 2. STATUTORY FRAMEWORK

### 2.1 Primary Federal Securities Laws

| Statute | Citation | Application |
|---------|----------|-------------|
| Securities Act of 1933 | 15 U.S.C. §§ 77a–77aa | Registration and prospectus fraud |
| Securities Exchange Act of 1934 | 15 U.S.C. §§ 78a–78qq | Trading fraud, insider trading |
| Sarbanes-Oxley Act of 2002 | Pub.L. 107–204 | Certification fraud, whistleblower |
| Dodd-Frank Act of 2010 | Pub.L. 111–203 | Whistleblower incentives, systemic risk |

### 2.2 Key Regulatory Provisions

**Section 10(b) & Rule 10b-5** — Prohibition against fraud in connection with
the purchase or sale of securities. Elements: (1) material misrepresentation
or omission, (2) scienter, (3) connection with purchase/sale, (4) reliance,
(5) economic loss, (6) loss causation.

**Section 16(a)** — Reporting requirements for officers, directors, and 10%+
beneficial owners. Form 4 must be filed within 2 business days of transaction.
Late filings trigger §16(b) short-swing profit disgorgement analysis.

**Section 16(b)** — Short-swing profit rule. Any profit realized by an insider
from purchase and sale (or sale and purchase) within any 6-month period is
recoverable by the issuer.

**Section 13(d)** — Beneficial ownership reporting. Any person acquiring >5%
beneficial ownership must file Schedule 13D within 10 days.

**Section 14(a)** — Proxy solicitation requirements. DEF 14A must contain
accurate executive compensation disclosure per Item 402 of Regulation S-K.

**SOX §302** — CEO/CFO certification of quarterly and annual reports.
False certification: up to $1M fine and/or 10 years imprisonment.

**SOX §906** — Criminal penalties for willful certification of non-compliant
reports: up to $5M fine and/or 20 years imprisonment.

### 2.3 Sentencing Guidelines

- Securities fraud: 20 years max per count (18 U.S.C. § 1348)
- Wire fraud: 20 years max per count (18 U.S.C. § 1343)
- Mail fraud: 20 years max per count (18 U.S.C. § 1341)
- Conspiracy: 5 years max (18 U.S.C. § 371)
- Obstruction of justice: 20 years max (18 U.S.C. § 1519)

### 2.4 Civil Penalties

- SEC civil penalties: Up to $1,009,804 per violation (2024 adjusted)
- Disgorgement of ill-gotten gains plus prejudgment interest
- Officer/director bars
- Injunctive relief

---

## 3. TARGET COMPANY PROFILE

### 3.1 Corporate Overview

| Field | Value |
|-------|-------|
| **Legal Name** | NIKE, Inc. |
| **CIK** | 0000320187 |
| **Ticker** | NKE (NYSE) |
| **SIC** | 5130 — Apparel, Piece Goods & Notions |
| **State of Incorporation** | Oregon |
| **Fiscal Year End** | May 31 |
| **Headquarters** | One Bowerman Drive, Beaverton, OR 97005 |
| **Market Cap (FY2019)** | ~$137B |
| **Revenue (FY2019)** | $39.1B |
| **Employees** | ~76,700 |

### 3.2 Key Officers (FY2019)

| Officer | Title | Compensation Focus |
|---------|-------|--------------------|
| Mark Parker | Chairman, President & CEO | Total comp, equity grants |
| Andrew Campion | EVP & CFO | SOX certification, financial reporting |
| Hilary Krane | EVP, CAO & General Counsel | Legal oversight, compliance |
| Eric Sprunk | COO | Operational oversight |
| Elliott Hill | President, Consumer & Marketplace | Revenue recognition |

### 3.3 FY2019 Material Events

- Consumer Direct Offense acceleration strategy
- NIKE Digital growth (+35% YoY)
- International restructuring and tax optimization
- Share repurchase program execution ($4.3B)
- Executive transition planning
- Trade tensions impact (China tariffs)

---

## 4. INVESTIGATION SCOPE & OBJECTIVES

### 4.1 Temporal Scope

- **Primary Period:** June 1, 2018 – May 31, 2019 (FY2019)
- **Look-Back Window:** 6 months prior (§16(b) short-swing analysis)
- **Look-Forward Window:** 90 days post-FY (delayed reporting detection)

### 4.2 Filing Types Under Analysis

| Form Type | JLAW Node | Focus Area |
|-----------|-----------|------------|
| Form 4 | Node 1 | Insider trading timing, clustering |
| DEF 14A | Node 2 | Executive compensation, perquisites |
| 10-Q | Node 3 | Quarterly temporal consistency |
| 10-K | Node 4 | Annual SOX certification, MD&A |
| IRS Exposure | Node 5 | IRC §83 tax timing anomalies |
| Enforcement | Node 6 | Routing to SEC/DOJ/IRS-CI |
| 13F-HR | Node 7 | Institutional holdings shifts |
| SC 13D/13G | Node 8 | Beneficial ownership changes |
| 8-K | Node 9 | Material event timing |
| Form 144 | Node 10 | Restricted stock sale intentions |
| Network Map | Node 11 | Executive relationship graph |
| Earnings Calls | Node 12 | Sentiment vs. filing analysis |
| Z-Score | Node 13 | Bankruptcy prediction trajectory |
| F-Score | Node 14 | Financial strength assessment |
| Market Correlation | Node 15 | Price movement vs. disclosure timing |
| Customs/Trade | Node 16 | International trade compliance |

### 4.3 Detection Patterns Applied (23 Total)

1. Options Backdating (Erik Lie methodology)
2. Channel Stuffing (DSO acceleration analysis)
3. Spring Loading (pre-announcement timing)
4. Bullet Dodging (post-bad-news timing)
5. Round-Tripping (revenue manipulation)
6. Cookie Jar Reserves (earnings smoothing)
7. Big Bath Accounting (write-off clustering)
8. Revenue Recognition Fraud (ASC 606 violations)
9. Related Party Transactions (undisclosed conflicts)
10. Wash Trading (artificial volume)
11. Benford's Law Anomalies (digit distribution)
12. Temporal Clustering (transaction timing patterns)
13. Compensation Manipulation (pay ratio distortion)
14. Tax Shelter Abuse (offshore structuring)
15. Insider Trading Windows (blackout violations)
16. Share Repurchase Manipulation (buyback timing)
17. Segment Reporting Fraud (geographic shifting)
18. Goodwill Impairment Avoidance (delayed write-downs)
19. Pension Obligation Manipulation (discount rate gaming)
20. Lease Classification Manipulation (ASC 842)
21. Inventory Capitalization Fraud (cost inflation)
22. Foreign Currency Manipulation (translation gains)
23. Executive Perquisite Concealment (proxy omissions)

---

## 5. EVIDENCE STANDARDS & ADMISSIBILITY

### 5.1 Federal Rules of Evidence Compliance

All evidence artifacts produced by the JLAW platform must satisfy:

**FRE 901(a)** — Authentication requirement: Evidence must be sufficient to
support a finding that the item is what the proponent claims it is.

**FRE 902(13)** — Self-authenticating certified records of a regularly
conducted activity in electronic form (business records certification).

**FRE 902(14)** — Self-authenticating certified data copied from an electronic
device, storage medium, or file (digital evidence certification).

**FRE 1006** — Summaries of voluminous records: Charts, summaries, or
calculations may be used to prove the content of voluminous writings.

### 5.2 Evidence Integrity Requirements

Each evidence artifact must include:

1. **Triple-Hash Verification**
   - SHA-256 (primary — FRE 902(13) compliant)
   - SHA3-512 (secondary — enhanced security)
   - BLAKE2b (tertiary — performance + integrity)

2. **Merkle Tree Construction** (RFC 6962 compliant)
   - All evidence hashes form leaves of a Merkle tree
   - Root hash provides single attestation for entire evidence corpus
   - Individual leaf proofs enable selective verification

3. **RFC 3161 Timestamp Tokens**
   - Trusted timestamping authority attestation
   - Non-repudiation of evidence creation time
   - Admissible under FRE 902(13) as certified record

4. **Chain of Custody Logging**
   - Acquisition timestamp and source URL
   - Handler identification (system + operator)
   - Transformation log (parsing, extraction, analysis)
   - Export timestamp and destination

### 5.3 Daubert Standard Compliance

Expert testimony and forensic methodology must satisfy:

1. **Testability** — Algorithms are deterministic and reproducible
2. **Peer Review** — Detection patterns based on published research
3. **Error Rate** — Known false positive/negative rates (85–97% accuracy)
4. **Standards** — Follows SEC examination protocols and PCAOB standards
5. **General Acceptance** — Based on established forensic accounting methods

---

## 6. SEC FILING CORPUS INVENTORY

### 6.1 Expected Filing Types for NIKE FY2019

| Filing | Expected Count | Filing Window |
|--------|---------------|---------------|
| Form 4 | 50–150 | Within 2 business days of transaction |
| DEF 14A | 1 | 120 days before annual meeting |
| 10-K | 1 | 60 days after FY end (July 30, 2019) |
| 10-Q | 3 | 40 days after quarter end |
| 8-K | 5–15 | Within 4 business days of event |
| 13F-HR | 4 (quarterly) | 45 days after quarter end |
| SC 13D/13G | 0–5 | Within 10 days of 5% threshold |
| Form 144 | 0–10 | Filed with intended sale notice |
| Proxy Statement | 1 | With DEF 14A |

### 6.2 Corpus Structure

```
raw_data/
├── primary/        (PDF + XLS filings)
├── nits_secondary/ (supplemental filings)
└── xbrl/           (Company Facts JSON)
```

### 6.3 Binary File Handling

**PDF Files:** Extract using `pdfplumber` (primary) or `PyMuPDF` (fallback).
Do NOT skip binary files. Phase 1 protocol mandates complete corpus coverage.

**XLS/XLSX Files:** Extract using `pandas` with `openpyxl` engine.
Parse all worksheets. Capture header rows and data tables.

**Fallback Protocol:** If native extraction fails, use Bash subprocess with:
```bash
python -c "import pdfplumber; pdf = pdfplumber.open('file.pdf'); print(pdf.pages[0].extract_text())"
python -c "import pandas as pd; df = pd.read_excel('file.xls', engine='openpyxl'); print(df.to_string())"
```

---

## 7. PHASE 1 — DATA ACQUISITION PROTOCOL

### 7.1 Execution Sequence (MANDATORY ORDER)

1. **Read Research Report FIRST**
   - File: `docs/MD RESEARCH REPORT(S)/2019.md`
   - Purpose: Establish FY2019 narrative baseline
   - This provides context for all subsequent filing analysis
   - DO NOT proceed to raw filings without reading this first

2. **Load Investigation State**
   - File: `investigation_state.json`
   - Resume from last checkpoint if applicable
   - Initialize new state if first session

3. **Scan Corpus Directory**
   - Use `CorpusScanner` to inventory all files
   - Generate manifest with SHA-256 hashes
   - Categorize by filing type (PDF, XLS, XML, etc.)

4. **Index XBRL Data**
   - Use `XBRLIndexer` for Company Facts JSON
   - Cross-reference with corpus manifest
   - Extract fiscal year metadata

5. **Validate CIK**
   - Confirm CIK 0000320187 maps to NIKE, Inc.
   - Verify filing history completeness
   - Flag any missing expected filings

### 7.2 Binary Extraction Directives

When encountering PDF or XLS files:

```python
# PDF extraction with pdfplumber (primary)
import pdfplumber

def extract_pdf(filepath: str) -> str:
    """Extract text from SEC filing PDF."""
    text_parts = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)

# XLS extraction with pandas/openpyxl
import pandas as pd

def extract_xls(filepath: str) -> dict:
    """Extract data from SEC filing spreadsheet."""
    engine = "openpyxl" if filepath.endswith(".xlsx") else None
    sheets = pd.read_excel(filepath, sheet_name=None, engine=engine)
    return {name: df.to_dict(orient="records") for name, df in sheets.items()}
```

### 7.3 Rate Limiting

- SEC EDGAR API: 9 requests/second (conservative; SEC allows 10)
- Use `SharedRateLimiter` for concurrent access
- Exponential backoff on 429 responses (2x–4x slowdown)
- Always set `SEC_USER_AGENT` in environment

---

## 8. PHASE 2 — FILING ANALYSIS PROTOCOL

### 8.1 Node Execution Order

**Sub-Phase 2.1: Core SEC Filing Analysis (Nodes 1–6)**

| Node | Analysis | Key Metrics |
|------|----------|-------------|
| Node 1 | Form 4 Insider Trading | Transaction clustering, §16(a) timeliness |
| Node 2 | DEF 14A Compensation | Pay ratio, perquisite disclosure |
| Node 3 | 10-Q Temporal Consistency | Quarter-over-quarter variance |
| Node 4 | 10-K SOX Certification | §302/§906 compliance |
| Node 5 | IRC §83 Tax Exposure | Option exercise timing |
| Node 6 | Enforcement Routing | SEC/DOJ/IRS-CI classification |

**Sub-Phase 2.2: Extended Intelligence (Nodes 7–12)**

| Node | Analysis | Key Metrics |
|------|----------|-------------|
| Node 7 | 13F-HR Holdings | Institutional accumulation/distribution |
| Node 8 | SC 13D/13G Ownership | Activist investor positioning |
| Node 9 | 8-K Material Events | Event-to-disclosure lag |
| Node 10 | Form 144 Sales Intent | Pre-registration sale patterns |
| Node 11 | Executive Network | Relationship graph analysis |
| Node 12 | Earnings Calls | NLP sentiment vs. filing delta |

**Sub-Phase 2.3: Financial Health (Nodes 13–14)**

| Node | Analysis | Key Metrics |
|------|----------|-------------|
| Node 13 | Z-Score (Altman) | Bankruptcy risk trajectory |
| Node 14 | F-Score (Piotroski) | Financial strength signals |

**Sub-Phase 2.4: Market Correlation (Node 15)**

| Node | Analysis | Key Metrics |
|------|----------|-------------|
| Node 15 | Market Correlation | Price-to-disclosure timing |

**Sub-Phase 2.5: Trade Compliance (Node 16)**

| Node | Analysis | Key Metrics |
|------|----------|-------------|
| Node 16 | Customs/Trade | International trade anomalies |

### 8.2 Minimum Success Threshold

- 12/16 nodes must execute successfully (75% gate)
- Failed nodes generate error reports but don't halt pipeline
- Critical failures (Nodes 1, 3, 4) trigger cascade review

---

## 9. PHASE 3 — PATTERN DETECTION & CROSS-REFERENCING

### 9.1 Detection Algorithm Execution

All 23 detection patterns (§4.3) are executed against aggregated node outputs.
Minimum success threshold: 20/23 patterns executed (87% gate).

### 9.2 Cross-Node Correlation Matrix

The correlation engine compares findings across all nodes:

- **Insider Trading ↔ Material Events**: Form 4 transactions within 14-day
  window of 8-K filings indicate potential MNPI trading
- **Compensation ↔ SOX Certification**: DEF 14A compensation changes aligned
  with 10-K certification timing suggest incentive misalignment
- **Holdings Shifts ↔ Market Correlation**: 13F position changes correlated
  with price movements suggest information asymmetry
- **Earnings Sentiment ↔ Financial Health**: NLP sentiment divergence from
  Z-Score/F-Score trajectory indicates potential misrepresentation

### 9.3 Anomaly Scoring

Each detected anomaly receives a composite score:

| Score Range | Classification | Action |
|-------------|----------------|--------|
| 0.0–0.3 | Low Risk | Log, no escalation |
| 0.3–0.6 | Medium Risk | Flag for review |
| 0.6–0.8 | High Risk | Detailed analysis required |
| 0.8–1.0 | Critical | Immediate enforcement routing |

---

## 10. PHASE 4 — PROSECUTORIAL FINDINGS ASSEMBLY

### 10.1 Output Artifacts

**narrative_report.md** — Prosecution-grade narrative containing:
- Executive summary of findings
- Statutory violation analysis with specific citations
- Evidence summary with hash references
- Enforcement recommendation with routing classification
- Timeline of material events and insider transactions
- Cross-reference matrix of correlated anomalies
- Appendices with supporting data tables

**analysis.json** — Machine-readable findings containing:
- Complete node execution results
- Detection pattern outputs with confidence scores
- Anomaly list with severity classifications
- Evidence chain with triple-hash verification
- Merkle tree root hash and leaf proofs
- Enforcement routing recommendations
- Session metadata and execution timestamps

### 10.2 Narrative Quality Standards

The narrative report must meet prosecution grade:

1. **Factual precision** — Every claim supported by specific filing data
2. **Statutory citation** — Every violation mapped to specific statute/rule
3. **Evidence chain** — Every exhibit hash-verified and custody-logged
4. **Actionable recommendations** — Clear enforcement routing with basis
5. **Temporal accuracy** — All dates verified against SEC filing timestamps
6. **Quantitative support** — Dollar amounts, percentages, statistical measures

---

## 11. ENFORCEMENT ROUTING MATRIX

### 11.1 Routing Decision Tree

| Finding Category | Primary Route | Secondary Route | Threshold |
|-----------------|---------------|-----------------|-----------|
| Insider Trading (§10b/16a) | SEC Enforcement | DOJ Criminal | >$100K profit |
| SOX Certification Fraud | SEC Enforcement | DOJ Criminal | Material misstatement |
| Compensation Fraud | SEC Corp Finance | IRS-CI | >$1M discrepancy |
| Financial Reporting Fraud | SEC Enforcement | DOJ Fraud Section | Material restatement |
| Tax Evasion (IRC §83) | IRS-CI | DOJ Tax Division | >$250K exposure |
| Beneficial Ownership Violation | SEC Enforcement | — | >5% threshold |
| Market Manipulation | SEC Market Reg | DOJ Criminal | Pattern evidence |

### 11.2 Multi-Agency Coordination

Findings exceeding thresholds for multiple agencies are packaged as:
- **DOJ Referral Package** — Criminal prosecution brief
- **SEC Enforcement Bundle** — Administrative action support
- **IRS-CI Referral** — Tax fraud investigation support
- **Legislative Brief** — Congressional oversight notification

---

## 12. EVIDENCE INTEGRITY & CHAIN OF CUSTODY

### 12.1 Triple-Hash Computation

Every evidence artifact receives three independent hash computations:

```
SHA-256:   Standard cryptographic hash (FRE 902(13) primary)
SHA3-512:  Keccak-based hash (enhanced collision resistance)
BLAKE2b:   High-performance hash (parallel verification)
```

### 12.2 Merkle Tree Construction

All evidence hashes are assembled into an RFC 6962 compliant Merkle tree:

```
                    [Root Hash]
                   /            \
          [Internal]            [Internal]
         /          \          /          \
    [Leaf 1]   [Leaf 2]  [Leaf 3]   [Leaf 4]
    Filing 1   Filing 2  Filing 3   Filing 4
```

### 12.3 Custody Chain Events

| Event | Logger | Timestamp | Hash Verified |
|-------|--------|-----------|---------------|
| Acquisition | CorpusScanner | UTC ISO 8601 | SHA-256 |
| Classification | FilingClassifier | UTC ISO 8601 | Triple-hash |
| Analysis | Node Analyzer | UTC ISO 8601 | Triple-hash |
| Correlation | Pattern Detector | UTC ISO 8601 | Triple-hash |
| Export | Report Generator | UTC ISO 8601 | Merkle root |

### 12.4 Integrity Verification

Phase 8 gate: 100% hash match required. **ABORT on any integrity failure.**

```python
# Verification protocol
hash_service = HashService()
for artifact in evidence_chain:
    current_hashes = hash_service.compute_triple_hash(artifact.content)
    if current_hashes != artifact.original_hashes:
        raise EvidenceIntegrityError(
            f"Hash mismatch for {artifact.id}: "
            f"evidence has been modified or corrupted"
        )
```

---

## 13. INVESTIGATION PROTOCOL & SESSION MANAGEMENT

### 13.1 Session Initialization

Every investigation session must:

1. Read this PROSECUTION_BRIEF.md (complete, not summary)
2. Load `investigation_state.json` from repo root
3. Read `EXECUTION_AUTHORITY.md` for orchestrator directives
4. Verify evidence integrity of any prior session artifacts
5. Resume from last checkpoint or initialize new investigation

### 13.2 State Tracking

`investigation_state.json` tracks:

```json
{
  "case_id": "JLAW-NKE-2019-001",
  "current_fy": "FY2019",
  "phase": "pending",
  "last_checkpoint": null,
  "completed_nodes": [],
  "pending_nodes": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
  "findings_count": 0,
  "evidence_hashes": {},
  "session_history": []
}
```

### 13.3 FY Progression Protocol

1. Complete FY2019 analysis → produce `narrative_report.md` + `analysis.json`
2. Human review of outputs for prosecution grade assessment
3. Approval gate: outputs must meet §10.2 quality standards
4. Only after approval: advance to FY2020
5. Each FY produces independent evidence package

### 13.4 Error Recovery

- On phase gate failure: log error, preserve state, halt
- On node failure: log error, continue with remaining nodes
- On evidence integrity failure: ABORT immediately
- On session timeout: checkpoint state, resume on next session

### 13.5 Completion Criteria

Investigation is complete when:
- All fiscal years analyzed (FY2019 → FY2024)
- All narrative reports meet prosecution grade
- All evidence chains verified (100% hash match)
- Enforcement routing recommendations finalized
- Master dossier compiled with cross-FY correlation

---

## APPENDIX A — QUICK REFERENCE

### CLI Execution

```bash
# FY2019 Analysis — Strict Mode
jlaw_cli.py --cik 0000320187 --company "NIKE, Inc." --year 2019 --strict --auto

# Dry Run (no API calls)
jlaw_cli.py --cik 0000320187 --year 2019 --dry-run

# Skip Pre-flight (development only)
jlaw_cli.py --cik 0000320187 --year 2019 --skip-preflight
```

### Key File Locations

| File | Purpose |
|------|---------|
| `docs/prosecution/PROSECUTION_BRIEF.md` | This document |
| `investigation_state.json` | Session state tracker |
| `EXECUTION_AUTHORITY.md` | Orchestrator directives |
| `docs/MD RESEARCH REPORT(S)/2019.md` | FY2019 narrative baseline |
| `src/sec_agent/pipeline.py` | SEC-AGENT pipeline orchestrator |
| `src/sec_agent/ingestion/fy_analyzer.py` | FY analysis module |
| `src/core/unified_orchestrator.py` | Canonical orchestrator |

### Environment Variables

```bash
SEC_USER_AGENT="JLAW Forensics contact@jlaw.dev"
ANTHROPIC_API_KEY="sk-ant-..."
OPENAI_API_KEY="sk-..."
POLYGON_API_KEY="..."
```

---

*END OF PROSECUTION BRIEF — JLAW-NKE-2019-001*
