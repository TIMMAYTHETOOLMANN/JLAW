# JLAW Quantitative Scoring Engines - Technical Reference

## Overview

This document provides detailed technical reference for the enhanced quantitative scoring engines (Nodes 13-15) and the Linear Execution Orchestrator implemented in JLAW Final System Integration Patch v4.1.1.

---

## Node 13: Altman Z-Score Bankruptcy Prediction Engine

**Module**: `src/nodes/node13_zscore/altman_zscore_engine.py`

### Three Model Variants

1. **Original (1968)**: Public manufacturing companies
   - Formula: `Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5`
   - Uses market value of equity
   
2. **Private (Z')**: Private companies
   - Formula: `Z' = 0.717*X1 + 0.847*X2 + 3.107*X3 + 0.420*X4 + 0.998*X5`
   - Uses book value of equity
   
3. **Non-Manufacturing (Z'')**: Service companies
   - Formula: `Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4`
   - Excludes sales/total assets component

### Component Ratios

- **X1**: Working Capital / Total Assets
- **X2**: Retained Earnings / Total Assets
- **X3**: EBIT / Total Assets
- **X4**: Market Value Equity / Total Liabilities
- **X5**: Sales / Total Assets

### Classification Zones

- **Safe Zone**: Z > 2.99 (Low bankruptcy risk)
- **Gray Zone**: 1.81 < Z < 2.99 (Moderate risk)
- **Distress Zone**: Z < 1.81 (High bankruptcy risk)

### Forensic Features

- SHA-256 evidence hashing for each calculation
- SOX 302 disclosure requirement assessment
- SEC MD&A (17 CFR § 229.303) compliance checking
- XBRL integration for automatic data extraction

### Usage Example

```python
from src.nodes.node13_zscore import AltmanZScoreEngine, ZScoreInput, ZScoreModel

engine = AltmanZScoreEngine()
input_data = ZScoreInput(
    cik="0000320193",
    company_name="Apple Inc.",
    fiscal_year=2023,
    fiscal_period="FY",
    current_assets=135405000000,
    current_liabilities=145308000000,
    total_assets=352755000000,
    total_liabilities=290437000000,
    retained_earnings=214403000000,
    ebit=119103000000,
    sales=383285000000,
    net_income=96995000000,
    market_value_equity=2800000000000
)

result = engine.calculate(input_data, ZScoreModel.ORIGINAL)
print(f"Z-Score: {result.z_score:.2f}")
print(f"Classification: {result.classification.value}")
print(f"Evidence Hash: {result.evidence_hash_sha256}")
```

---

## Node 14: Piotroski F-Score Fundamental Strength Engine

**Module**: `src/nodes/node14_fscore/piotroski_fscore_engine.py`

### 9 Binary Signals (0 or 1)

**Profitability (F1-F4)**:
- **F1**: Positive Return on Assets (ROA > 0)
- **F2**: Positive Operating Cash Flow (CFO > 0)
- **F3**: Increasing ROA (ΔROA > 0)
- **F4**: Quality of Earnings (CFO > Net Income) - **Accruals Quality Detector**

**Leverage/Liquidity (F5-F7)**:
- **F5**: Decreasing Long-term Debt (ΔLT Debt < 0)
- **F6**: Increasing Current Ratio (ΔCurrent Ratio > 0)
- **F7**: No New Equity Issued (ΔShares ≤ 0)

**Operating Efficiency (F8-F9)**:
- **F8**: Increasing Gross Margin (ΔGross Margin > 0)
- **F9**: Increasing Asset Turnover (ΔAsset Turnover > 0)

### Classification

- **Strong**: 8-9 points (High-quality fundamentals)
- **Moderate**: 5-7 points (Mixed signals)
- **Weak**: 0-4 points (Poor fundamentals)

### Accruals Quality Assessment

- **Good**: CFO > Net Income (negative accruals)
- **Acceptable**: Accruals < 5% of total assets
- **Poor**: Accruals > 5% of total assets (potential earnings manipulation)

### Forensic Features

- Individual signal forensic notes with calculations
- Year-over-year comparison framework
- Accruals quality detection for SEC fraud investigation
- SHA-256 evidence hashing

### Usage Example

```python
from src.nodes.node14_fscore import PiotroskiFScoreEngine, FiscalPeriodData

engine = PiotroskiFScoreEngine()

current = FiscalPeriodData(
    fiscal_year=2023, fiscal_period="FY",
    net_income=96995000000, revenue=383285000000,
    cost_of_goods_sold=214137000000, total_assets=352755000000,
    current_assets=135405000000, current_liabilities=145308000000,
    long_term_debt=106000000000, cash_flow_from_operations=110543000000,
    shares_outstanding=15550000000
)

prior = FiscalPeriodData(
    fiscal_year=2022, fiscal_period="FY",
    net_income=99803000000, revenue=394328000000,
    cost_of_goods_sold=223546000000, total_assets=352583000000,
    current_assets=135405000000, current_liabilities=153982000000,
    long_term_debt=120069000000, cash_flow_from_operations=122151000000,
    shares_outstanding=15943000000
)

result = engine.calculate("0000320193", "Apple Inc.", current, prior)
print(f"F-Score: {result.f_score}/9")
print(f"Classification: {result.classification.value}")
print(f"Accruals Quality: {result.accruals_quality}")
for signal in result.signals:
    print(f"  {signal.signal_id}: {signal.value} - {signal.description}")
```

---

## Node 15: Market Correlation & Anomaly Detection Engine

**Module**: `src/nodes/node15_market_correlation/market_anomaly_detector.py`

### Detection Methods

**1. Volume Anomaly Detection**:
- Z-score methodology with 2.5σ threshold (99th percentile)
- Trailing 20-day window for mean/std calculation
- Relative volume ratio (current/average)

**2. Price Movement Analysis**:
- Single-day moves > 10% flagged
- Cumulative Abnormal Returns (CAR) calculation
- Event study methodology

**3. Pre-Announcement Trading**:
- 7-day window before SEC filings (Form 4, 8-K)
- Volume and price correlation analysis
- Gift-before-drop pattern detection (Seyhun et al.)

**4. Anomaly Types**:
- Volume Spike
- Price Movement
- Pre-Announcement Trading
- Gift-Before-Drop Pattern
- Wash Trading
- Layering

### Severity Levels

- **Critical**: Z-score > 3.5σ or suspicious pre-filing activity
- **High**: Z-score > 2.5σ or major price movements
- **Moderate**: Unusual but not extreme patterns
- **Low**: Minor deviations

### Polygon.io Integration

- REST API for historical OHLCV data
- Rate limiting (5 req/min free tier, configurable)
- Mock mode for testing without API key
- Automatic retry with exponential backoff

### Forensic Features

- SHA-256 evidence hashing for each anomaly
- SEC filing correlation (Form 4, 8-K timestamps)
- Legal citations (17 CFR § 240.10b-5, 18 U.S.C. § 1348)
- FRE 902(13)/(14) compliant evidence chain

### Usage Example

```python
from src.nodes.node15_market_correlation import MarketCorrelationEngine
from datetime import date

engine = MarketCorrelationEngine(polygon_api_key="YOUR_API_KEY")

result = engine.analyze(
    symbol="AAPL",
    cik="0000320193",
    company_name="Apple Inc.",
    start_date=date(2023, 1, 1),
    end_date=date(2023, 12, 31),
    sec_filings=[
        {"form_type": "8-K", "filing_date": date(2023, 5, 15)},
        {"form_type": "Form 4", "filing_date": date(2023, 6, 1)}
    ]
)

print(f"Bars Analyzed: {result.bars_analyzed}")
print(f"Anomalies Detected: {result.total_anomalies}")
print(f"Critical Alerts: {result.critical_anomalies}")

for anomaly in result.anomalies:
    print(f"\n{anomaly.anomaly_type.value} - {anomaly.severity.value}")
    print(f"  Date: {anomaly.detection_date}")
    print(f"  {anomaly.description}")
    if anomaly.correlated_filing:
        print(f"  Filing: {anomaly.correlated_filing} on {anomaly.filing_date}")
```

---

## Linear Execution Orchestrator

**Module**: `src/core/linear_orchestrator.py`

The Linear Execution Orchestrator manages the sequential execution of all 15 forensic analysis nodes across 4 phases with dependency-aware ordering, error handling, and evidence chain generation.

### Strict Execution Mode Integration

The orchestrator integrates with **Strict Execution Mode** (see [STRICT_EXECUTION_MODE.md](../STRICT_EXECUTION_MODE.md)) to enforce mandatory quality gates:

**Phase 4 Gate: 15-Node Recursive Analysis**
- **Requirement:** Minimum 12 of 15 nodes successful
- **Requirement:** Minimum 80% success rate
- **Requirement:** Node results data present
- **Validation:** Automatic in strict mode
- **Exit Code:** 4 on failure

**How Phase Gates Validate Node Execution:**

1. **Node Success Tracking**
   - Each node execution tracked with NodeStatus enum
   - Status: PENDING → RUNNING → COMPLETED/FAILED/SKIPPED
   - Success count incremented only for COMPLETED nodes

2. **Success Rate Calculation**
   ```python
   success_rate = (successful_nodes / total_nodes) * 100
   # Must be >= 80% in strict mode (12 out of 15 nodes)
   ```

3. **Gate Validation**
   - After Phase 4 completes, gate validator checks:
     - `successful_nodes >= min_nodes_successful` (12)
     - `success_rate >= min_node_success_rate` (80%)
     - Node results data structure present

4. **Cascade Abort on Failure**
   - If < 80% success rate, execution aborts
   - Exit code 4 returned
   - Abort report generated with:
     - Which nodes failed
     - Failure reasons
     - Remediation guidance
   - Audit trail saved with node-by-node status

**Benefits:**
- ✅ Guarantees minimum data quality for prosecution
- ✅ Prevents incomplete analysis from proceeding
- ✅ Provides clear failure diagnostics
- ✅ Enables automated quality control in CI/CD

**Usage:**
```bash
# Standard mode (advisory only)
python JLAW_UNIFIED.py --cik 320187 --year 2019 --auto

# Strict mode (enforces 80% node success)
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto
```

**Troubleshooting Node Failures:**
See [docs/STRICT_MODE_TROUBLESHOOTING.md](../docs/STRICT_MODE_TROUBLESHOOTING.md) for Exit Code 4 remediation.

### 4-Phase Execution Pipeline

**Phase 1: Core SEC Filing Analysis (Nodes 1-6)**
- Form 4, DEF 14A, 10-Q, 10-K analysis
- IRC §83 tax exposure calculation
- Multi-agency routing logic

**Phase 2: Extended Intelligence (Nodes 7-12)**
- Institutional holdings (13F)
- Beneficial ownership (13D/13G)
- Material events (8-K)
- Network analysis and NLP

**Phase 3: Quantitative Forensic Scoring (Nodes 13-15)**
- Altman Z-Score bankruptcy prediction
- Piotroski F-Score fundamental analysis
- Market correlation and anomaly detection

**Phase 4: Cross-Node Correlation & Evidence Synthesis**
- Pattern clustering across nodes
- Temporal correlation analysis
- Unified forensic scoring

### Node Dependencies

```python
NODE_CONFIG = {
    1: {"name": "Form4_Insider", "phase": 1, "deps": []},
    2: {"name": "DEF14A_Compensation", "phase": 1, "deps": []},
    3: {"name": "10Q_Quarterly", "phase": 1, "deps": []},
    4: {"name": "10K_SOX", "phase": 1, "deps": []},
    5: {"name": "IRC83_Tax", "phase": 1, "deps": [1, 2]},
    6: {"name": "Enforcement_Routing", "phase": 1, "deps": [1, 2, 3, 4, 5]},
    7: {"name": "13F_Holdings", "phase": 2, "deps": []},
    8: {"name": "13D_Ownership", "phase": 2, "deps": []},
    9: {"name": "8K_Events", "phase": 2, "deps": []},
    10: {"name": "Form144_Restricted", "phase": 2, "deps": [1]},
    11: {"name": "Network_Mapper", "phase": 2, "deps": [1, 2, 7, 8]},
    12: {"name": "Earnings_NLP", "phase": 2, "deps": [3, 4]},
    13: {"name": "Altman_ZScore", "phase": 3, "deps": [3, 4]},
    14: {"name": "Piotroski_FScore", "phase": 3, "deps": [3, 4]},
    15: {"name": "Market_Correlation", "phase": 3, "deps": [1, 9]},
}
```

### Triple-Hash Evidence Chain

**FRE 902(13)/(14) Compliant**:
- **SHA-256**: Document-level hashing (64 hex chars)
- **SHA3-512**: Evidence chain linking (128 hex chars)
- **BLAKE2b**: Additional integrity layer (128 hex chars)

All three hashes are generated for the complete forensic analysis result, ensuring cryptographic integrity for court admissibility.

### Regulatory Routing Logic

**SEC Routing** (17 CFR § 240.10b-5):
- Any violations > 0

**DOJ Routing** (18 U.S.C. § 1348):
- Violations ≥ 5 (criminal exposure threshold)

**IRS Routing** (IRC § 83):
- Triggered by Node 5 tax exposure findings

### Prosecution Recommendation

Based on total violations across all nodes:
- **≥10 violations**: "IMMEDIATE PROSECUTION RECOMMENDED"
- **≥5 violations**: "PROSECUTION WARRANTED"
- **≥3 violations**: "INVESTIGATION RECOMMENDED"
- **≥1 violations**: "MONITORING RECOMMENDED"
- **0 violations**: "NO ACTION REQUIRED"

### Usage Example

```python
from src.core.linear_orchestrator import LinearExecutionOrchestrator
from datetime import date
import asyncio

async def main():
    orchestrator = LinearExecutionOrchestrator(
        sec_user_agent="MyOrg/1.0 (contact@myorg.com)",
        polygon_api_key="YOUR_POLYGON_KEY"  # Optional
    )

    result = await orchestrator.execute_analysis(
        company_cik="0000320193",
        company_name="Apple Inc.",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        case_id="CASE-AAPL-2023"  # Optional
    )

    # Access results
    print(f"Case ID: {result.case_id}")
    print(f"Total Violations: {result.total_violations}")
    print(f"Prosecution Recommendation: {result.prosecution_recommendation}")
    print(f"Estimated Penalties: ${result.estimated_penalties['civil_minimum']:,} - ${result.estimated_penalties['civil_maximum']:,}")
    print(f"\nEvidence Chain Integrity:")
    print(f"  SHA-256:  {result.evidence_chain_sha256}")
    print(f"  SHA3-512: {result.evidence_chain_sha3_512}")
    print(f"  BLAKE2b:  {result.evidence_chain_blake2b}")

    # Serialize to JSON
    import json
    result_json = json.dumps(result.to_dict(), indent=2)
    
    return result

# Run
asyncio.run(main())
```

---

## Legal Framework Coverage

### Securities Law
- **17 CFR § 240.10b-5**: Securities fraud (Rule 10b-5)
- **17 CFR § 240.10b5-1/10b5-2**: Insider trading rules
- **17 CFR § 229.303**: MD&A disclosure requirements
- **SOX Section 302**: CEO/CFO certification of financial statements
- **SOX Section 404**: Internal control assessment
- **SOX Section 906**: CEO/CFO criminal liability for false certifications

### Criminal Law
- **18 U.S.C. § 1348**: Securities and commodities fraud

### Tax Law
- **IRC § 83**: Property transferred in connection with performance of services

---

## Testing

Comprehensive test suite in `tests/test_final_patch.py`:

```bash
# Run all tests
pytest tests/test_final_patch.py -v

# Run specific test class
pytest tests/test_final_patch.py::TestNode13ZScore -v
pytest tests/test_final_patch.py::TestNode14FScore -v
pytest tests/test_final_patch.py::TestNode15MarketCorrelation -v
pytest tests/test_final_patch.py::TestLinearOrchestrator -v
```

**Test Coverage**:
- 29 tests total, all passing
- Node 13: 7 tests (enums, validation, calculation, classification, hashing, serialization)
- Node 14: 5 tests (enums, validation, calculation, signal details, accruals quality)
- Node 15: 5 tests (enums, OHLCV calculations, volume profiles, PolygonClient, engine)
- Orchestrator: 6 tests (phase execution, dependencies, triple-hash, serialization)
- Integration: 6 tests (imports, backward compatibility, cryptography)

---

## References

1. **Altman, E.I. (1968)**. "Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy." *Journal of Finance*, 23(4), 589-609.

2. **Piotroski, J.D. (2000)**. "Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers." *Journal of Accounting Research*, 38(Supplement), 1-41.

3. **SEC EDGAR API Documentation**: https://www.sec.gov/edgar/sec-api-documentation

4. **Polygon.io API Documentation**: https://polygon.io/docs/stocks

5. **Federal Rules of Evidence 902(13)/(14)**: Self-authenticating certified records generated by an electronic process or system

---

## Version History

- **v4.1.1** (December 2024): Added enhanced quantitative scoring engines (Nodes 13-15) and Linear Execution Orchestrator with triple-hash evidence chain
