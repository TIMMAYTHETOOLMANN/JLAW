# QUICK START GUIDE - SEC FORENSIC ANALYZER v3.0

## FASTEST PATH TO ANALYSIS

### 1. RUN NIKE 2019 ANALYSIS (30 seconds)
```bash
RUN_ENHANCED_ANALYSIS.bat
# Press 1
```

### 2. CUSTOM COMPANY ANALYSIS (1 minute)
```bash
python sec_forensic_analyzer_v3_enhanced.py --cik YOUR_CIK --year 2019 --enable-all
```

### 3. VERIFY SYSTEM (10 seconds)
```bash
python -c "from sec_forensic_analyzer_v3_enhanced import *; print('✅')"
```

---

## KEY FILES

| File | Purpose |
|------|---------|
| `sec_forensic_analyzer_v3_enhanced.py` | Main analyzer |
| `RUN_ENHANCED_ANALYSIS.bat` | Interactive menu |
| `config/nike_2019.yaml` | Nike config |
| `ENHANCED_ANALYZER_v3_README.md` | Full docs |
| `DEPLOYMENT_SUMMARY_v3.md` | Deployment status |

---

## REQUIRED API KEYS

Add to `.env` file:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOVINFO_API_KEY=your_key
```

---

## OUTPUT LOCATION
```
forensic_reports/
└── forensic_report_NKE_[id].json  ← Main results
```

---

## HELP
```bash
python sec_forensic_analyzer_v3_enhanced.py --help
```

---

**Status:** ✅ READY  
**Version:** 3.0.0-NEXUS-ENHANCED

