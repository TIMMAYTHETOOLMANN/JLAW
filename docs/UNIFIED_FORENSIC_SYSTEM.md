# Unified Forensic Analysis System v4.0

## Overview

The JLAW Unified Forensic Analysis System is a comprehensive, single-command platform for DOJ-grade forensic analysis of SEC filings. It integrates all JLAW modules into a linear, context-reinforcing execution pipeline that produces prosecution-ready documentation.

## Key Features

### 13-Phase Linear Pipeline

1. **Document Acquisition** - Comprehensive SEC EDGAR filing collection
2. **DocsGPT Parsing** - 9+ format support with HYBRID semantic chunking
3. **Agent-Powered Scraping** - Dual-agent AI extraction (OpenAI + Anthropic)
4. **Quantitative Forensics** - Beneish M-Score, Altman Z-Score, Benford's Law
5. **Revenue Recognition** - DSO trends, hockey stick detection, cash divergence
6. **Financial Flow Analysis** - Circular flows, enrichment schemes, coordinated activity
7. **Linguistic Deception** - Hedging patterns, obfuscation metrics
8. **Temporal Analysis** - Timeline reconstruction, late filing detection
9. **Contradiction Detection** - Cross-document semantic analysis
10. **ML Fraud Detection** - BERT/XGBoost ensemble scoring
11. **Statutory Mapping** - GovInfo API real-time enrichment
12. **Dual-Agent Prosecution** - Multi-agent validation with 75% agreement threshold
13. **Report Generation** - DOJ-grade comprehensive output package

### Context Propagation

Each phase enriches the forensic context with intelligence that informs all subsequent phases, creating a cumulative analytical depth unmatched by isolated analysis tools.

## Installation

### Prerequisites

```bash
Python 3.9+
pip or uv package manager
```

### Required Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `aiohttp` - Async HTTP for SEC API
- `numpy`, `pandas`, `scikit-learn` - Quantitative analysis
- `beautifulsoup4`, `lxml` - Document parsing
- `pyyaml` - Configuration management
- `openai` - OpenAI Agent SDK (optional)
- `anthropic` - Anthropic Claude (optional)

## Quick Start

### Basic Usage

```bash
# Analyze Nike 2019 by ticker
python jlaw_forensic.py --ticker NKE --year 2019

# Analyze by CIK with custom date range
python jlaw_forensic.py --cik 0000320187 \
    --start-date 2019-01-01 \
    --end-date 2019-12-31

# Verbose output
python jlaw_forensic.py --ticker NKE --year 2019 --verbose
```

### Configuration

Create or modify `config/unified_forensic.yaml`:

```yaml
unified_forensic:
  version: "4.0.0"
  
  # Enable/disable modules
  modules:
    quantitative_forensics: true
    linguistic_analysis: true
    contradiction_detection: true
    ml_fraud_detection: true
    
  # Agent configuration
  agents:
    openai:
      enabled: true
      model: "gpt-4o"
    anthropic:
      enabled: true
      model: "claude-3-5-sonnet-20241022"
      
  # Financial forensics thresholds
  financial_forensics:
    revenue_analyzer:
      dso_spike_threshold: 0.3
      hockey_stick_threshold: 0.4
```

### Environment Variables

Set API keys in `.env`:

```bash
# OpenAI (for agent-based analysis)
OPENAI_API_KEY=sk-...

# Anthropic (for deep reasoning validation)
ANTHROPIC_API_KEY=sk-ant-...

# SEC EDGAR (no key required, but email recommended)
SEC_USER_EMAIL=your.email@example.com

# GovInfo API (for statute enrichment)
GOVINFO_API_KEY=...
```

## Output Structure

The system generates a comprehensive forensic package:

```
output/{COMPANY}_{YEAR}_FORENSIC_ANALYSIS_{TIMESTAMP}/
├── FORENSIC_REPORT.md              # DOJ-grade main report
├── executive_summary.md            # 2-page executive brief
├── machine_readable/
│   ├── violations.json             # All violations with evidence
│   ├── timeline.json               # Chronological event sequence
│   ├── contradictions.json         # Cross-document inconsistencies
│   ├── quantitative_scores.json    # Beneish, Benford, fraud scores
│   ├── linguistic_analysis.json    # Hedging, obfuscation metrics
│   ├── financial_flows.json        # Transaction flow patterns
│   ├── revenue_recognition.json    # DSO, hockey stick analysis
│   └── statute_mapping.json        # USC/CFR references
├── evidence/
│   ├── chain_of_custody.json       # SHA-256 hashed evidence chain
│   ├── source_documents/           # Cached original filings
│   └── extracted_quotes/           # Verbatim evidence extracts
└── appendices/
    ├── methodology.md              # FRE 702 methodology documentation
    ├── legal_framework.md          # Applicable statutes/CFR
    └── enforcement_precedents.md   # Historical case citations
```

## Report Format

The main `FORENSIC_REPORT.md` follows the Nike 2019 benchmark format with:

### Per-Filing Analysis
- Filing type and date
- Accession number with hyperlinked SEC EDGAR URL
- Violations found count
- Detailed violation breakdown with:
  - Severity level (CRITICAL/HIGH/MEDIUM/LOW)
  - Statutory reference (15 USC § 78p(a), etc.)
  - Description and evidence summary
  - **Exact quotes** from source documents
  - Document location (direct URL)
  - Prosecutorial merit assessment
  - Estimated damages
  - Criminal referral recommendation
  - GovInfo cross-references

### Statutory Framework
- Complete statute table with penalties
- GovInfo.gov official source links
- CFR regulatory mappings

### Criminal Referral Summary
- Violations recommended for DOJ review
- Applicable criminal statutes
- Evidence hash chain

## Module Details

### DocsGPT Integration

Utilizes advanced document parsing with 9+ format support:
- PDF (pdfplumber)
- HTML/XML (BeautifulSoup4)
- XBRL (SEC-specific)
- DOCX, XLSX, PPTX (Office formats)
- JSON, TXT (structured data)

**HYBRID Chunking Strategy:**
- Semantic boundary detection
- Section-aware splitting
- Overlapping context windows
- Optimized for SEC document structure

### Financial Forensics

**Revenue Recognition Analyzer:**
- Days Sales Outstanding (DSO) trend analysis
- Quarter-end revenue concentration (hockey stick)
- Deferred revenue decline tracking
- Cash flow vs revenue divergence
- Gross margin volatility detection

**Financial Flow Analyzer:**
- Circular flow detection (wash trading patterns)
- Enrichment scheme identification (zero-dollar grants → sales)
- Coordinated insider activity detection
- Rapid turnover detection (short-swing violations)
- Transaction graph analysis

### Agent SDK Integration

**OpenAI Agent SDK:**
- Self-healing URL resolution
- Tool orchestration with guardrails
- Primary violation detection pass

**Anthropic Claude:**
- Deep reasoning with extended context
- Multi-pass analysis (default 2 passes)
- Structured JSON violation extraction
- Validation and conflict resolution

### Quantitative Forensics

**Beneish M-Score (8-factor model):**
- Detects earnings manipulation
- Threshold: -1.78 (scores above suggest manipulation)

**Altman Z-Score:**
- Bankruptcy prediction model
- Zones: Safe (>2.99), Grey (1.81-2.99), Distress (<1.81)

**Benford's Law:**
- First-digit frequency analysis
- Chi-squared test for anomalies
- Applied to financial figures

### ML Fraud Detection

**BERT Hierarchical Attention Network:**
- Document-level fraud classification
- Word and sentence-level attention
- GPU-accelerated (optional)

**XGBoost Ensemble:**
- Feature-based fraud scoring
- Incorporates quantitative signals
- Real-time inference

### Statutory Mapping

**GovInfo API Integration:**
- Real-time statute enrichment
- 15 USC (Securities laws)
- 17 CFR (SEC regulations)
- 18 USC (Criminal statutes)
- Complete penalty frameworks

## Advanced Usage

### Custom Configuration

```python
from src.forensics.unified_forensic_pipeline import UnifiedForensicPipeline
from src.forensics.forensic_context import ForensicContext

# Initialize with custom config
pipeline = UnifiedForensicPipeline()

# Execute pipeline programmatically
context = await pipeline.execute(
    ticker="NKE",
    year=2019
)

# Access results
print(f"Violations: {len(context.violations)}")
print(f"Fraud Probability: {context.fraud_probability:.2%}")
```

### Selective Phase Execution

Edit `config/unified_forensic.yaml` to disable phases:

```yaml
modules:
  quantitative_forensics: true
  linguistic_analysis: false  # Disable linguistic analysis
  ml_fraud_detection: false   # Disable ML (for CPU-only systems)
```

### Batch Processing

```bash
# Process multiple companies
for ticker in AAPL MSFT GOOGL; do
    python jlaw_forensic.py --ticker $ticker --year 2023
done
```

## Performance Considerations

### Resource Requirements

**Minimum:**
- 4 GB RAM
- 2 CPU cores
- 10 GB disk space

**Recommended:**
- 16 GB RAM
- 8 CPU cores
- GPU for ML fraud detection (NVIDIA, 4GB VRAM)
- 100 GB disk space

### Optimization

- **Caching:** Enable SEC filing cache to reduce API calls
- **Parallel Processing:** Adjust `max_concurrent_filings` in config
- **ML Models:** Disable BERT on CPU-only systems
- **Rate Limiting:** Configure SEC API rate limits (10 req/sec default)

## Troubleshooting

### Common Issues

**"No module named 'openai'"**
```bash
pip install openai anthropic
```

**"OPENAI_API_KEY not set"**
- Agent features require API keys
- System continues with manual analysis if keys not set

**"SEC API rate limit exceeded"**
- Reduce `requests_per_second` in config
- Enable caching to minimize API calls

**"Out of memory during ML analysis"**
- Disable BERT: `ml_fraud.use_bert: false`
- Reduce `max_concurrent_filings`

## Legal Notice

This system is designed for forensic analysis and educational purposes. All findings should be reviewed by qualified legal professionals before taking action. Evidence chains follow DOJ standards but should be validated in accordance with applicable legal requirements.

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- Documentation: https://github.com/TIMMAYTHETOOLMANN/JLAW/docs

## License

See LICENSE file for details.

## Version History

**v4.0.0** - Unified Forensic System
- 13-phase linear pipeline
- Full DocsGPT integration
- Dual-agent AI analysis
- Financial forensics modules
- GovInfo API integration
- DOJ-grade report generation

---

*JLAW Unified Forensic Analyzer - DOJ Criminal Division Standards*
