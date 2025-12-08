# JLAW Unified Forensic Analysis System

## Overview

The JLAW Unified Forensic Analysis System is a single-command, comprehensive SEC filing forensic analysis platform that executes **ALL analytical modules at maximum depth** in a linear, context-reinforcing pipeline. This is not a quick scan or surface-level analysis tool—it's a tactical forensic weapon for deep investigative research.

## Key Features

### 🎯 Single Command Execution
```bash
# Analyze by CIK and year
python jlaw_forensic.py --cik 0000320187 --year 2019

# Analyze by ticker and year
python jlaw_forensic.py --ticker NKE --year 2019

# Analyze custom date range
python jlaw_forensic.py --ticker NKE --start-date 2019-01-01 --end-date 2019-12-31
```

### 🔬 13-Phase Linear Pipeline

The system executes a comprehensive 13-phase analysis where each phase receives complete intelligence from all previous phases:

| Phase | Module | Purpose |
|-------|--------|---------|
| **1** | Document Acquisition | Fetch all SEC filings via EDGAR API |
| **2** | DocsGPT Document Parsing | Semantic parsing with HYBRID chunking strategy |
| **3** | Agent-Powered Scraping | Intelligent extraction with OpenAI/Anthropic agents |
| **4** | Quantitative Forensics | Benford's Law, Altman Z-Score, Beneish M-Score |
| **5** | Revenue Recognition | DSO trends, hockey stick patterns, cash divergence |
| **6** | Financial Flow Analysis | Circular flows, enrichment schemes, coordinated activity |
| **7** | Linguistic Deception | Hedging patterns, obfuscation metrics, certainty scores |
| **8** | Temporal Analysis | Timeline anomalies, filing delays, event sequencing |
| **9** | Contradiction Detection | Cross-document inconsistencies with exact quotes |
| **10** | ML Fraud Detection | BERT/XGBoost fraud probability, ensemble scores |
| **11** | Statutory Mapping | 15 USC/17 CFR violations with GovInfo links |
| **12** | Dual-Agent Prosecution | OpenAI initial + Anthropic deep validation |
| **13** | Report Generation | Full DOJ-grade output stack |

### 📊 Comprehensive Output Stack

Every analysis generates a complete forensic package:

```
output/{COMPANY}_{YEAR}_FORENSIC_ANALYSIS_{TIMESTAMP}/
├── FORENSIC_REPORT.md                    # DOJ-grade human-readable report
├── executive_summary.md                   # 2-page executive brief
├── machine_readable/
│   ├── violations.json                    # All violations with evidence
│   ├── timeline.json                      # Temporal analysis
│   ├── contradictions.json                # Cross-doc inconsistencies
│   ├── quantitative_scores.json           # Benford, Beneish, Altman
│   ├── linguistic_analysis.json           # Deception metrics
│   ├── financial_flows.json               # Flow analysis results
│   ├── revenue_recognition.json           # DSO/hockey stick results
│   └── statute_mapping.json               # Legal framework mapping
├── evidence/
│   ├── chain_of_custody.json              # SHA-256 hashes
│   └── source_documents/                  # Cached SEC filings
└── appendices/
    ├── methodology.md                     # Analysis methodology
    └── legal_framework.md                 # Statutory references
```

## Installation

### Prerequisites

- Python 3.11 or 3.12 (recommended: 3.11 for maximum third‑party ABI compatibility)
- Required API keys (optional, for full functionality):
  - `OPENAI_API_KEY` - For OpenAI agent analysis
  - `ANTHROPIC_API_KEY` - For Anthropic agent analysis
  - `GOVINFO_API_KEY` - For GovInfo statute verification
  - `SEC_USER_AGENT` - Your organization contact info (required by SEC)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/TIMMAYTHETOOLMANN/JLAW.git
cd JLAW
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Note on environment hardening:
- NumPy is pinned to `< 2.0` (currently `numpy==1.26.4`) to avoid ABI mismatches observed with some compiled dependencies. Keep this pin unless you explicitly validate NumPy 2.x compatibility for all modules in your environment.
- No external Benford’s library is required; the system uses an internal analyzer. `benfordspy` was removed from `requirements.txt` as it is not available on PyPI.

3. Configure API keys (create `.env` file):
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Verify installation:
```bash
python jlaw_forensic.py --help
```

## Usage

### Basic Usage

```bash
# Analyze Nike 2019 filings
python jlaw_forensic.py --ticker NKE --year 2019

# Analyze with CIK number
python jlaw_forensic.py --cik 0000320187 --year 2019

# Analyze custom date range
python jlaw_forensic.py --ticker NKE --start-date 2019-01-01 --end-date 2019-12-31
```

### Advanced Options

```bash
# Verbose logging
python jlaw_forensic.py --ticker NKE --year 2019 --verbose

# Custom output directory
python jlaw_forensic.py --ticker NKE --year 2019 --output-dir /path/to/output

# Skip report generation (for testing pipeline only)
python jlaw_forensic.py --ticker NKE --year 2019 --no-report

# Limit to specific filing types (default is ALL filings)
python jlaw_forensic.py --ticker NKE --year 2019 --filing-types "10-K,10-Q,8-K,4,DEF 14A"
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `--cik CIK` | Company CIK number (e.g., 0000320187) |
| `--ticker TICKER` | Company ticker symbol (e.g., NKE) |
| `--year YEAR` | Analysis year (e.g., 2019) |
| `--start-date DATE` | Start date in YYYY-MM-DD format |
| `--end-date DATE` | End date in YYYY-MM-DD format |
| `--output-dir DIR` | Base directory for report output (default: output/) |
| `--verbose` | Enable verbose logging |
| `--no-report` | Skip report generation (testing only) |
| `--filing-types TYPES` | Comma-separated SEC filing types to include (e.g., `10-K,10-Q,8-K,4,DEF 14A`). Use `all` (default) for ALL filings |

### One-Click Execution (Windows)

For a fully guided, single-click experience on Windows, use the included PowerShell script:

```powershell
# From the project root
PowerShell -ExecutionPolicy Bypass -File .\one_click_analyze.ps1
```

The script will:
- Verify Python and pip
- Install dependencies from `requirements.txt`
- Optionally validate API keys
- Prompt for `Ticker/CIK`, `Year` or `Start/End` dates
- Prompt for `Filing Types` (default: ALL)
- Run the full 13-phase analysis and open the output folder

#### Non‑Interactive recipes

Option A — Use the one‑click script with flags (no prompts):

```powershell
# Example: NIKE 2019, verbose, output to .\output
PowerShell -ExecutionPolicy Bypass -File .\one_click_analyze.ps1 -Ticker NKE -Year 2019 -OutputDir output -Verbose
# Optional flags:
#   -CIK 0000320187
#   -StartDate 2019-01-01 -EndDate 2019-12-31
#   -FilingTypes "10-K,10-Q,8-K,4,DEF 14A"   # default: all
#   -NoReport                                   # skip report generation
#   -SkipDeps                                   # skip dependency installation
#   -SkipKeyCheck                               # skip API key validation
```

Option B — Call the unified pipeline directly (bypasses PowerShell script):

```powershell
# Example: NIKE 2019, verbose, output to .\output
python jlaw_forensic.py --ticker NKE --year 2019 --verbose --output-dir output
```

Optional pre‑flight checks:

```powershell
python verify_api_keys.py
python verify_multi_tier_sec.py   # 7/7 expected pass with multi‑tier fetcher
```

To snapshot multi‑tier health for records:

```powershell
python scripts/gen_health_snapshot.py
```

### CI Pipeline (GitHub Actions)

This repository includes a lightweight CI workflow that installs dependencies, executes verification scripts, and uploads health/diff artifacts when present.

- Workflow: `.github/workflows/forensic_ci.yml`
- Badge (replace OWNER/REPO with your GitHub org/repo):

```
![JLAW Forensic CI](https://github.com/OWNER/REPO/actions/workflows/forensic_ci.yml/badge.svg)
```

The workflow performs the following (best‑effort) steps:
- Install dependencies (Python 3.11, pip cache)
- Run `verify_multi_tier_sec.py` (continue‑on‑error)
- Generate health snapshot via `scripts/gen_health_snapshot.py` (continue‑on‑error)
- Run `pytest -q test_single_filing.py` (skips if `GOVINFO_API_KEY` not set)
- Run `scripts/diff_artifacts.py` to diff latest NIKE 2019 artifacts (continue‑on‑error)
- Upload `forensic_reports/` as a build artifact

## Architecture

### Context Propagation

The system uses a `ForensicContext` dataclass that accumulates intelligence across all phases:

```python
@dataclass
class ForensicContext:
    # Company metadata
    company_name: str
    cik: str
    analysis_period_start: str
    analysis_period_end: str
    
    # Phase 1-2: Document Layer
    filings: List[SECFiling]
    parsed_documents: List[ParsedDocument]
    chunks: List[DocumentChunk]
    
    # Phase 3: Agent Analysis
    agent_findings: Dict[str, Any]
    
    # Phase 4: Quantitative Layer
    benford_results: Dict[str, BenfordAnalysis]
    beneish_score: float
    altman_z_score: float
    fraud_probability: float
    
    # Phase 5-6: Financial Flow Layer
    revenue_analysis: RevenueAnalysisResult
    flow_analysis: FlowAnalysisResult
    
    # Phase 7-8: Linguistic/Temporal Layer
    deception_metrics: Dict[str, float]
    timeline_anomalies: List[TimelineAnomaly]
    
    # Phase 9-10: Detection Layer
    contradictions: List[Contradiction]
    ml_fraud_scores: Dict[str, float]
    
    # Phase 11-12: Legal Layer
    violations: List[Violation]
    statute_mappings: List[StatuteMapping]
    criminal_referrals: List[CriminalReferral]
```

### Key Components

1. **jlaw_forensic.py** - Main CLI entry point
2. **unified_forensic_pipeline.py** - Pipeline orchestrator
3. **unified_report_generator.py** - Report generation engine
4. **forensic_context.py** - Context propagation dataclass
5. **docsgpt/** - Document parsing with semantic chunking
6. **financial_forensics/** - Revenue and flow analysis modules
7. **agent_sec_analyzer.py** - OpenAI agent integration
8. **anthropic_agent_analyzer.py** - Anthropic agent integration

## Report Format

### Main Report Structure

The `FORENSIC_REPORT.md` follows DOJ-level investigation standards:

1. **Header** - Company, period, summary statistics
2. **Executive Summary** - High-level findings
3. **Violations by Type** - Categorized violations
4. **Violations by Severity** - CRITICAL, HIGH, MEDIUM, LOW
5. **Statutory Framework** - Legal references with GovInfo links
6. **Per-Filing Detailed Analysis** - Violation-by-violation breakdown with:
   - Severity classification
   - Statutory reference
   - Detailed description
   - Evidence summary
   - Exact quotes from documents
   - Document location
   - Prosecutorial merit assessment
   - Estimated damages
   - Criminal referral recommendation
7. **Criminal Referral Summary** - DOJ referral recommendations
8. **Chain of Custody** - SHA-256 evidence hashes
9. **Conclusion** - Summary and recommendations

### Machine-Readable Outputs

All findings are also exported as JSON for programmatic access:

- **violations.json** - Structured violation data
- **timeline.json** - Temporal anomalies
- **contradictions.json** - Cross-document inconsistencies
- **quantitative_scores.json** - Fraud detection scores
- **linguistic_analysis.json** - Deception metrics
- **financial_flows.json** - Flow analysis
- **revenue_recognition.json** - Revenue quality metrics
- **statute_mapping.json** - Legal framework

## Integration

### DocsGPT Integration

The system fully utilizes DocsGPT for advanced document processing:

- **ParserFactory** - Multi-format document parsing
- **SECChunker** - HYBRID semantic chunking strategy
- **DocumentAnalysisOrchestrator** - Coordinated analysis
- **VectorStore** - FAISS-based semantic search

### Agent SDK Integration

Dual-agent analysis using:

- **OpenAI Agents SDK** - Initial violation detection with self-healing extraction
- **Anthropic Claude** - Deep reasoning and validation
- **OpenRouter Fallback** - Alternative provider support

### Financial Forensics

Specialized modules for:

- **Revenue Recognition Analysis**
  - Days Sales Outstanding (DSO) trends
  - Hockey stick pattern detection
  - Cash flow divergence
  - Deferred revenue analysis

- **Financial Flow Analysis**
  - Circular flow detection
  - Enrichment scheme identification
  - Coordinated insider activity
  - Transaction flow mapping

## Development

### Testing

```bash
# Run basic infrastructure test
python test_unified_pipeline.py

# Test with minimal data (no API keys required)
python jlaw_forensic.py --ticker TEST --year 2019 --no-report
```

### Extending the Pipeline

To add a new phase:

1. Create analyzer module in `src/forensics/`
2. Add phase method to `UnifiedForensicPipeline`
3. Update `ForensicContext` with new data structures
4. Update `UnifiedReportGenerator` to include findings

### Contributing

1. Follow existing code structure and patterns
2. Maintain context propagation through all phases
3. Add comprehensive logging for debugging
4. Update tests and documentation
5. Ensure reports match DOJ-grade standards

## Performance

### Execution Time

Typical analysis times (depends on filing count and API availability):

- **Small company (10-20 filings)**: 5-10 minutes
- **Medium company (50-100 filings)**: 15-30 minutes
- **Large company (100+ filings)**: 30-60+ minutes

### Resource Requirements

- **Memory**: 4-8 GB recommended
- **Storage**: 1-2 GB per analysis (includes cached filings)
- **Network**: SEC API rate limited to ~10 requests/second

## Legal Compliance

This system is designed for:

- ✅ Legal research and analysis
- ✅ Academic investigation
- ✅ Personal forensic study
- ✅ Compliance monitoring

It is **NOT** intended for:

- ❌ Illegal insider trading
- ❌ Market manipulation
- ❌ Unauthorized disclosure of non-public information
- ❌ Violation of securities laws

All SEC data is public information obtained through official EDGAR API channels.

## Support

- **Issues**: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory

## License

See LICENSE file for details.

## Acknowledgments

- SEC EDGAR API for public filing data
- DocsGPT for advanced document processing
- OpenAI and Anthropic for AI-powered analysis
- GovInfo.gov for statutory references

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: Production-Ready Infrastructure (Phase implementations ongoing)
