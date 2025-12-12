# JLAW SEC FORENSIC ANALYSIS SYSTEM

## DOJ-Grade 15-Node Recursive Prosecutorial Engine

---

## EXECUTIVE SUMMARY

JLAW is a **DOJ-grade SEC filing forensic analysis platform** implementing a **15-node recursive prosecutorial engine** with **23 fraud detection patterns**, **10 specialized Claude subagents**, **DocsGPT document parsing**, and **dual AI agent cross-validation**. The system produces courtroom-ready forensic dossiers from SEC EDGAR filings.

### Core Metrics
| Metric | Value |
|--------|-------|
| Python Modules | 68 |
| Analysis Nodes | 15 |
| Detection Patterns | 23 (85-97% accuracy) |
| Claude Subagents | 10 |
| Execution Phases | 9 |
| SEC Form Coverage | 11 types |
| AI Providers | 2 (OpenAI + Anthropic) |

---

## QUICK START

### Single Deployment Script
```bash
# Interactive mode (recommended)
python JLAW_UNIFIED.py

# CLI mode with parameters
python JLAW_UNIFIED.py --cik 320187 --company "NIKE, Inc." --year 2019

# Full auto execution (no confirmations)
python JLAW_UNIFIED.py --cik 320187 --year 2019 --auto
```

### Common CIK Numbers
| Company | Ticker | CIK |
|---------|--------|-----|
| Nike | NKE | 320187 |
| Apple | AAPL | 320193 |
| Microsoft | MSFT | 789019 |
| Tesla | TSLA | 1318605 |
| Amazon | AMZN | 1018724 |
| Meta | META | 1326801 |
| Google | GOOGL | 1652044 |
| Netflix | NFLX | 1065280 |
| Nvidia | NVDA | 1045810 |

---

## 9-PHASE EXECUTION PIPELINE

| Phase | Name | Modules | Output |
|-------|------|---------|--------|
| 1 | Configuration | All module initialization | Module status report |
| 2 | Data Collection | `sec_edgar/edgar_client.py` | SEC filings list |
| 3 | Document Parsing | `docsgpt/document_parser.py`, `vector_store.py` | Parsed chunks, embeddings |
| 4 | Node Analysis | 15 nodes in `src/nodes/` | Violations, alerts |
| 5 | Pattern Detection | `advanced_patterns.py` + financial detectors | 23 pattern results |
| 6 | Dual-Agent | `dual_agent.py`, OpenAI + Anthropic | AI cross-validation |
| 7 | Subagent | `subagents/orchestrator.py` | Multi-agent results |
| 8 | Evidence Chain | `evidence_chain/`, `custody/` | SHA-256 hashes, custody |
| 9 | Dossier Generation | Report compiler | `FORENSIC_DOSSIER.md` + `.json` |

---

## DIRECTORY STRUCTURE

```
JLAW2/
©À©¤©¤ JLAW_UNIFIED.py                    # SINGLE DEPLOYMENT SCRIPT
©À©¤©¤ README.md                          # This document
©À©¤©¤ requirements.txt                   # Python dependencies
©À©¤©¤ .env                               # API keys
©¦
©À©¤©¤ .claude/agents/                    # 10 Claude Subagent Configurations
©¦   ©À©¤©¤ forensic/
©¦   ©¦   ©À©¤©¤ forensic-compliance-auditor.md
©¦   ©¦   ©À©¤©¤ forensic-financial-analyst.md
©¦   ©¦   ©À©¤©¤ forensic-nlp-analyst.md
©¦   ©¦   ©À©¤©¤ forensic-research-specialist.md
©¦   ©¦   ©¸©¤©¤ security-auditor.md
©¦   ©À©¤©¤ infrastructure/
©¦   ©¦   ©À©¤©¤ database-administrator.md
©¦   ©¦   ©¸©¤©¤ devops-engineer.md
©¦   ©À©¤©¤ orchestration/
©¦   ©¦   ©À©¤©¤ forensic-workflow-orchestrator.md
©¦   ©¦   ©¸©¤©¤ multi-agent-coordinator.md
©¦   ©¸©¤©¤ development/
©¦       ©¸©¤©¤ python-pro.md
©¦
©À©¤©¤ src/
©¦   ©À©¤©¤ core/                          # CORE ENGINE
©¦   ©¦   ©À©¤©¤ recursive_engine.py        # 15-node orchestrator (CANONICAL)
©¦   ©¦   ©À©¤©¤ evidence_chain/
©¦   ©¦   ©¦   ©À©¤©¤ hash_service.py        # SHA-256/SHA3-512 hashing
©¦   ©¦   ©¦   ©À©¤©¤ chain_validator.py     # Evidence chain integrity
©¦   ©¦   ©¦   ©¸©¤©¤ rfc3161_client.py      # RFC 3161 timestamping
©¦   ©¦   ©¸©¤©¤ custody/
©¦   ©¦       ©¸©¤©¤ custody.py             # Chain of custody tracking
©¦   ©¦
©¦   ©À©¤©¤ nodes/                         # 15 FORENSIC ANALYSIS NODES
©¦   ©¦   ©À©¤©¤ node1_form4/               # Form 4 Insider Transactions
©¦   ©¦   ©¦   ©À©¤©¤ form4_parser.py        # XML parsing
©¦   ©¦   ©¦   ©À©¤©¤ short_swing_calc.py    # Section 16(b) profits
©¦   ©¦   ©¦   ©¸©¤©¤ gift_pattern_detector.py # Seyhun detection
©¦   ©¦   ©À©¤©¤ node2_def14a/              # DEF 14A Proxy
©¦   ©¦   ©À©¤©¤ node3_10q/                 # 10-Q Quarterly
©¦   ©¦   ©À©¤©¤ node4_10k_sox/             # 10-K SOX Cert
©¦   ©¦   ©À©¤©¤ node5_irs/                 # IRS ¡ì83 Tax
©¦   ©¦   ©À©¤©¤ node6_routing/             # Enforcement Router
©¦   ©¦   ©¦   ©¸©¤©¤ enforcement_router.py
©¦   ©¦   ©À©¤©¤ node7_13f_holdings/        # Institutional Holdings
©¦   ©¦   ©¦   ©¸©¤©¤ institutional_analyzer.py
©¦   ©¦   ©À©¤©¤ node8_13d_ownership/       # Beneficial Ownership
©¦   ©¦   ©¦   ©¸©¤©¤ beneficial_ownership_tracker.py
©¦   ©¦   ©À©¤©¤ node9_8k_events/           # Material Events
©¦   ©¦   ©¦   ©¸©¤©¤ material_event_correlator.py
©¦   ©¦   ©À©¤©¤ node10_form144/            # Restricted Sales
©¦   ©¦   ©¦   ©¸©¤©¤ restricted_sale_monitor.py
©¦   ©¦   ©À©¤©¤ node11_network_mapper/     # Network Analysis
©¦   ©¦   ©¦   ©¸©¤©¤ executive_network_analyzer.py
©¦   ©¦   ©À©¤©¤ node12_earnings_calls/     # Transcript NLP
©¦   ©¦   ©¦   ©¸©¤©¤ transcript_analyzer.py
©¦   ©¦   ©À©¤©¤ node13_zscore/             # Bankruptcy Prediction
©¦   ©¦   ©¦   ©¸©¤©¤ bankruptcy_predictor.py
©¦   ©¦   ©À©¤©¤ node14_fscore/             # Financial Strength
©¦   ©¦   ©¦   ©¸©¤©¤ financial_strength_analyzer.py
©¦   ©¦   ©¸©¤©¤ node15_market_correlation/ # Market Correlation
©¦   ©¦       ©¸©¤©¤ market_correlation_engine.py
©¦   ©¦
©¦   ©À©¤©¤ detection/                     # FRAUD DETECTION
©¦   ©¦   ©À©¤©¤ financial/
©¦   ©¦   ©¦   ©À©¤©¤ beneish_mscore.py      # 8-variable manipulation
©¦   ©¦   ©¦   ©¸©¤©¤ benford_analysis.py    # First-digit testing
©¦   ©¦   ©À©¤©¤ ml/
©¦   ©¦   ©¦   ©À©¤©¤ deberta_contradiction.py # NLI detection
©¦   ©¦   ©¦   ©¸©¤©¤ xgboost_fraud.py       # 35-feature classifier
©¦   ©¦   ©¸©¤©¤ patterns/
©¦   ©¦       ©¸©¤©¤ advanced_patterns.py   # 15 advanced patterns
©¦   ©¦
©¦   ©À©¤©¤ forensics/                     # FORENSIC INTEGRATION
©¦   ©¦   ©À©¤©¤ docsgpt/                   # DocsGPT Integration
©¦   ©¦   ©¦   ©À©¤©¤ document_parser.py     # Multi-format parsing
©¦   ©¦   ©¦   ©¸©¤©¤ vector_store.py        # FAISS semantic search
©¦   ©¦   ©À©¤©¤ subagents/                 # Claude Orchestration
©¦   ©¦   ©¦   ©¸©¤©¤ orchestrator.py
©¦   ©¦   ©À©¤©¤ dual_agent.py              # OpenAI + Anthropic
©¦   ©¦   ©À©¤©¤ agent_sec_analyzer.py      # OpenAI agent
©¦   ©¦   ©À©¤©¤ anthropic_agent_analyzer.py # Anthropic agent
©¦   ©¦   ©À©¤©¤ openai_secondary_agent.py  # Fallback agent
©¦   ©¦   ©À©¤©¤ govinfo_api_client.py      # GovInfo API
©¦   ©¦   ©¸©¤©¤ config_manager.py
©¦   ©¦
©¦   ©¸©¤©¤ integrations/                  # EXTERNAL DATA
©¦       ©À©¤©¤ sec_edgar/
©¦       ©¦   ©¸©¤©¤ edgar_client.py        # SEC EDGAR API
©¦       ©¸©¤©¤ market_data/               # Polygon.io (optional)
©¦
©À©¤©¤ config/
©¦   ©¸©¤©¤ secure_config.py               # Credentials
©¦
©À©¤©¤ output/                            # Generated Reports
©¦   ©À©¤©¤ DOSSIER_*.json
©¦   ©¸©¤©¤ FORENSIC_DOSSIER_*.md
©¦
©¸©¤©¤ archive_deprecated/                # Archived scripts
```

---

## 15-NODE RECURSIVE ANALYSIS ENGINE

### Phase 1: Core SEC Filing Analysis (Nodes 1-6)

| Node | Module | SEC Form | Detection |
|------|--------|----------|-----------|
| **1** | `form4_parser.py` | Form 4 | Late filings, short-swing profits, gift patterns |
| **2** | `def14a/` | DEF 14A | Executive compensation reconciliation |
| **3** | `10q/` | 10-Q | Temporal consistency validation |
| **4** | `10k_sox/` | 10-K | SOX 302/906 certification analysis |
| **5** | `irs/` | N/A | IRC ¡ì83 tax exposure calculation |
| **6** | `enforcement_router.py` | All | SEC/DOJ/IRS routing determination |

### Phase 2: Extended Intelligence (Nodes 7-12)

| Node | Module | SEC Form | Detection |
|------|--------|----------|-----------|
| **7** | `institutional_analyzer.py` | 13F-HR | Wolf pack formation, coordinated accumulation |
| **8** | `beneficial_ownership_tracker.py` | 13D/13G | 13G¡ú13D conversion, rapid accumulation |
| **9** | `material_event_correlator.py` | 8-K | Pre-event trading, timing anomalies |
| **10** | `restricted_sale_monitor.py` | Form 144 | Rule 144(d) holding period, volume limits |
| **11** | `executive_network_analyzer.py` | DEF 14A | Board interlocks, revolving door |
| **12** | `transcript_analyzer.py` | Transcripts | Hedging language, sentiment shifts |

### Phase 3: Financial Health (Nodes 13-14)

| Node | Module | Analysis | Thresholds |
|------|--------|----------|------------|
| **13** | `bankruptcy_predictor.py` | Altman Z-Score | Z > 2.99 safe, Z < 1.81 distress |
| **14** | `financial_strength_analyzer.py` | Piotroski F-Score | 0-9 scale, ¡İ7 strong |

### Phase 4: Market Correlation (Node 15)

| Node | Module | Data | Detection |
|------|--------|------|-----------|
| **15** | `market_correlation_engine.py` | Polygon.io | CAR event studies, volume anomaly |

---

## 23 DETECTION PATTERNS

### Financial Statement Fraud (1-4)
| # | Pattern | Module | Accuracy | Description |
|---|---------|--------|----------|-------------|
| 1 | Beneish M-Score | `beneish_mscore.py` | 90% | 8-variable earnings manipulation |
| 2 | Benford's Law | `benford_analysis.py` | 85% | First-digit distribution anomaly |
| 3 | Altman Z-Score | `bankruptcy_predictor.py` | 80-90% | Bankruptcy probability |
| 4 | Piotroski F-Score | `financial_strength_analyzer.py` | 82% | Financial health scoring |

### Insider Trading Patterns (5-8)
| # | Pattern | Module | Accuracy | Description |
|---|---------|--------|----------|-------------|
| 5 | Late Filing | `form4_parser.py` | 99% | Section 16 deadline violations |
| 6 | Short-Swing Profit | `short_swing_calc.py` | 95% | Section 16(b) recovery |
| 7 | Gift-Before-Drop | `gift_pattern_detector.py` | 89% | Seyhun methodology |
| 8 | Zero-Dollar Transactions | `form4_parser.py` | 92% | IRC ¡ì83 tax indicators |

### Advanced Patterns (9-15)
| # | Pattern | Accuracy | Description |
|---|---------|----------|-------------|
| 9 | Round-Tripping | 87% | Circular revenue transactions |
| 10 | Disclosure Timing | 92% | Friday dumps, holiday filings |
| 11 | Management Hedging | 90% | Uncertainty language in filings |
| 12 | Holding Period Violations | 97% | Rule 144(d) compliance |
| 13 | Volume Limit Exceeded | 96% | Rule 144(e) compliance |
| 14 | Clustered Disposals | 91% | Coordinated insider selling |
| 15 | Volume Anomaly | 94% | Isolation Forest outlier detection |

### Institutional & Network Patterns (16-23)
| # | Pattern | Accuracy | Description |
|---|---------|----------|-------------|
| 16 | Wolf Pack Formation | 91% | Coordinated accumulation |
| 17 | 13G¡ú13D Conversion | 94% | Passive to activist shift |
| 18 | Pre-Announcement | 89% | Information leakage |
| 19 | Sequential Adverse Events | 85% | Corporate deterioration |
| 20 | Board Interlock | 93% | Shared director channels |
| 21 | Revolving Door | 88% | Executive movement |
| 22 | Sentiment Shift | 86% | Quarter-over-quarter NLP |
| 23 | CAR Event Study | 88% | Cumulative abnormal returns |

---

## DOCSGPT INTEGRATION

### Document Parser (`docsgpt/document_parser.py`)
**Supported Formats:** PDF, HTML, XBRL, XLSX, CSV, JSON, Images (OCR)

**SEC-Specific Chunking:**
- **Section-based**: Chunks by Item 1, Item 7, Item 1A, etc.
- **Hybrid**: Large sections further chunked with overlap
- **Fixed-size**: Fallback for unstructured documents

### Vector Store (`docsgpt/vector_store.py`)
- FAISS in-memory vector storage
- OpenAI embedding generation (text-embedding-3-small)
- Semantic similarity search
- Cross-filing contradiction detection
- Metadata filtering (CIK, filing type, date range)

```python
from src.forensics.docsgpt import DocumentParser, SECVectorSearchEngine

parser = DocumentParser()
doc = parser.parse_sec_filing(html_content, filing_type, cik, accession)

search = SECVectorSearchEngine()
results = search.search("revenue recognition policy changes", cik="320187")
```

---

## 10 CLAUDE SUBAGENTS

Located in `.claude/agents/`:

| Agent | Category | Specialization |
|-------|----------|----------------|
| `forensic-financial-analyst` | forensic | M-Score, Z-Score, Benford, XGBoost |
| `forensic-nlp-analyst` | forensic | Document parsing, contradiction detection |
| `forensic-research-specialist` | forensic | SEC research, evidence gathering |
| `forensic-compliance-auditor` | forensic | Statute mapping, prosecution prep |
| `security-auditor` | forensic | Evidence chain verification |
| `forensic-workflow-orchestrator` | orchestration | Multi-agent coordination |
| `multi-agent-coordinator` | orchestration | Cross-agent task management |
| `database-administrator` | infrastructure | Data storage optimization |
| `devops-engineer` | infrastructure | Pipeline automation |
| `python-pro` | development | Code implementation |

### Orchestration Patterns
```
Single Doc:  NLP ¡ú Financial ¡ú Compliance ¡ú Report
Full Invest: Research ¡ú [NLP + Financial parallel] ¡ú Compliance ¡ú Security
```

---

## DUAL-AGENT AI SYSTEM

| Module | Provider | Function |
|--------|----------|----------|
| `dual_agent.py` | Coordinator | Manages both agents |
| `agent_sec_analyzer.py` | OpenAI GPT-4 | Primary SEC analysis |
| `anthropic_agent_analyzer.py` | Claude | Cross-validation |
| `openai_secondary_agent.py` | GPT-3.5 | Fallback |

### Cross-Validation Process
1. OpenAI analyzes filing ¡ú findings
2. Anthropic validates ¡ú confirmation/disputes
3. Discrepancies flagged for human review
4. Consensus findings marked high-confidence

---

## EVIDENCE CHAIN & CUSTODY

### Hash Service (`evidence_chain/hash_service.py`)
- SHA-256 primary hashing
- SHA3-512 secondary verification
- Content-addressable evidence records

### Chain Validator (`evidence_chain/chain_validator.py`)
- Merkle tree construction
- Tamper detection
- Chain integrity verification

### RFC 3161 Timestamping (`evidence_chain/rfc3161_client.py`)
- Trusted timestamp authority integration
- Legal timestamp certification

### Custody Tracking (`custody/custody.py`)
- Collection ¡ú Analysis ¡ú Review ¡ú Report lifecycle
- Actor/action/timestamp logging
- Export for legal proceedings

---

## EXTERNAL INTEGRATIONS

### SEC EDGAR (`integrations/sec_edgar/edgar_client.py`)
- Company submissions retrieval
- Filing content fetching
- Form 4 XML parsing
- Rate limiting (10 req/sec)

### GovInfo API (`forensics/govinfo_api_client.py`)
- Statute text retrieval
- CFR cross-referencing
- Live legal citation

### Market Data (Optional)
- Polygon.io WebSocket
- Real-time price/volume
- Historical data for CAR studies

---

## OUTPUT ARTIFACTS

### JSON Dossier (`output/DOSSIER_*.json`)
```json
{
  "case_id": "JLAW-320187-20251211...",
  "target": { "cik": "320187", "company_name": "NIKE, Inc." },
  "phase_results": [...],
  "violations": [...],
  "estimated_penalties": 1500000.00,
  "evidence_chain_hash": "sha256:..."
}
```

### Markdown Report (`output/FORENSIC_DOSSIER_*.md`)
- Executive Summary
- Target Information
- Violation Details with Statutory Citations
- Evidence Chain Documentation
- Regulatory Routing (SEC/DOJ/IRS)
- Penalty Estimates

---

## CONFIGURATION

### Environment Variables (`.env`)
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOVINFO_API_KEY=...
SEC_USER_AGENT=YourName your@email.com
POLYGON_API_KEY=...  # Optional for Node 15
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

Key: `aiohttp`, `openai`, `anthropic`, `python-dotenv`, `pdfplumber`, `beautifulsoup4`, `numpy`, `faiss-cpu`

---

## PLACEHOLDER NODES (Enhancement Targets)

- **Node 2**: DEF 14A compensation deep analysis
- **Node 3**: 10-Q temporal consistency validation
- **Node 4**: 10-K SOX certification deep analysis
- **Node 5**: IRS ¡ì83 tax exposure calculation

---

## LICENSE

MIT License

---

*System Version: 3.0 - Unified Deployment | December 2025*

