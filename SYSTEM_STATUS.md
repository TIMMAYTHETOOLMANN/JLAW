# JLAW - SEC FORENSIC ANALYSIS SYSTEM
## Production Configuration - December 4, 2025

---

## ✅ SYSTEM STATUS: PRODUCTION READY

The SEC Forensic Analyzer is a **universal, hardened forensic analysis system** capable of analyzing ANY company's SEC filings for securities law violations.

---

## Production Entry Point

```bash
python sec_forensic_analyzer.py --help
```

### Key Commands

```bash
# Analyze any company by CIK
python sec_forensic_analyzer.py --cik <CIK> --year <YEAR>

# Analyze by stock ticker
python sec_forensic_analyzer.py --ticker <TICKER> --year <YEAR>

# Custom date range
python sec_forensic_analyzer.py --cik <CIK> --start YYYY-MM-DD --end YYYY-MM-DD

# Specific filing categories
python sec_forensic_analyzer.py --cik <CIK> --year <YEAR> --category insider
```

---

## System Architecture

```
JLAW/
├── sec_forensic_analyzer.py      # PRODUCTION ENTRY POINT
├── SEC_FORENSIC_ANALYZER_README.md
├── src/
│   └── forensics/
│       ├── dual_agent.py         # Dual-agent coordinator
│       ├── govinfo_api_client.py # GovInfo statute lookup
│       ├── config_manager.py     # Configuration
│       └── ...
├── output/                       # Generated reports
├── archive/
│   └── calibration_runs/
│       └── 20251204_initial/     # Archived calibration artifacts
└── docs/
    └── NIKE INC. (NKE) - 2019...pdf  # Benchmark reference
```

---

## Capabilities

### Violation Detection
| Type | Statute | Detection |
|------|---------|-----------|
| Late Form 3/4/5 | 15 U.S.C. § 78p(a) | ✅ |
| Zero-Dollar Transactions | 15 U.S.C. § 78p(a) | ✅ |
| Material Misstatements | 15 U.S.C. § 78j(b) | ✅ |
| SOX 302 Deficiencies | 15 U.S.C. § 7241 | ✅ |
| SOX 404 Issues | 15 U.S.C. § 7262 | ✅ |
| Beneficial Ownership | 15 U.S.C. § 78m(d) | ✅ |

### Filing Types
| Category | Types |
|----------|-------|
| Insider | 3, 4, 5 (and amendments) |
| Periodic | 10-K, 10-Q, 20-F, 40-F |
| Current | 8-K, 6-K |
| Proxy | DEF 14A, DEFA14A |
| Registration | S-1, S-3, S-4, F-1, F-3 |
| Beneficial | SC 13D, SC 13G |

### Integrations
| System | Status | Purpose |
|--------|--------|---------|
| SEC EDGAR | ✅ Live | Filing data source |
| GovInfo API | ✅ Ready | Statute verification |
| Dual-Agent | ✅ Ready | OpenAI + Anthropic |

---

## Report Output

Each analysis generates:

1. **Markdown Report** - Human-readable DOJ-level investigation
2. **JSON Report** - Machine-readable complete database

Reports include:
- Executive summary
- Per-filing detailed analysis
- Statutory framework with GovInfo URLs
- Criminal referral summary
- Enforcement precedent citations
- Evidence chain of custody (SHA-256 hashes)

---

## Calibration Reference

All initial calibration runs archived at:
```
archive/calibration_runs/20251204_initial/
```

Contains benchmark analysis artifacts for Nike 2019 validation.

---

## Configuration

Environment variables (`.env`):
- `OPENAI_API_KEY` - OpenAI API access
- `ANTHROPIC_API_KEY` - Anthropic Claude access
- `GOVINFO_API_KEY` - GovInfo statute lookup

---

*JLAW SEC Forensic Analyzer v1.0 - Universal Production System*

