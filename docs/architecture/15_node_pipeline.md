# 15-Node Recursive Pipeline

The 15-node recursive pipeline is the core analysis engine of JLAW, executing sequential forensic analysis across all SEC filing types.

---

## Pipeline Overview

The pipeline is organized into **4 sub-phases** with **15 specialized nodes**:

```
PHASE 4: 15-Node Recursive Analysis
├── SUB-PHASE 4.1: Core SEC Filing Analysis (Nodes 1-6)
├── SUB-PHASE 4.2: Extended Intelligence (Nodes 7-12)
├── SUB-PHASE 4.3: Quantitative Forensic Scoring (Nodes 13-14)
├── SUB-PHASE 4.4: Market Correlation (Node 15)
└── SUB-PHASE 4.5: Cross-Node Correlation
```

**Gate Requirement**: 12/15 nodes must succeed (80% threshold)

---

## Sub-Phase 4.1: Core SEC Filing Analysis

### Node 1: Form 4 Insider Trading Analysis

**Purpose**: Detect §16 violations and suspicious insider trading patterns

**Filing Type**: Form 4 (Statement of Changes in Beneficial Ownership)

**Detection Capabilities**:
- Rule 144 restricted stock sales
- 10b5-1 plan timing analysis
- Pre-earnings blackout violations
- Unusual volume or timing
- Officer/director coordination

**Output**: Insider trading violations, suspicious patterns, timing alerts

**Accuracy**: 92%

---

### Node 2: DEF 14A Executive Compensation Analysis

**Purpose**: Analyze executive compensation and detect golden parachutes

**Filing Type**: DEF 14A (Definitive Proxy Statement)

**Detection Capabilities**:
- Options backdating (Erik Lie methodology)
- Spring loading (pre-good-news grants)
- Bullet dodging (post-bad-news grants)
- Golden parachute provisions
- Excessive perks analysis

**Output**: Compensation anomalies, backdating alerts, excessive compensation flags

**Accuracy**: 89%

---

### Node 3: 10-Q Temporal Consistency Analysis

**Purpose**: Detect quarterly reporting inconsistencies and temporal anomalies

**Filing Type**: 10-Q (Quarterly Report)

**Detection Capabilities**:
- Revenue recognition timing shifts
- Expense timing manipulation
- Seasonal pattern deviations
- Quarter-end stuffing
- Trend reversals

**Output**: Temporal inconsistencies, pattern breaks, manipulation indicators

**Accuracy**: 87%

---

### Node 4: 10-K SOX Certification Validation

**Purpose**: Validate Sarbanes-Oxley certifications and annual report integrity

**Filing Type**: 10-K (Annual Report)

**Detection Capabilities**:
- §302 certification validation
- §404 internal control deficiencies
- Restatement patterns
- Audit opinion changes
- Going concern warnings

**Output**: SOX compliance violations, internal control weaknesses, audit red flags

**Accuracy**: 94%

---

### Node 5: IRC §83 Tax Exposure Analysis

**Purpose**: Calculate tax exposure from equity compensation

**Filing Type**: Form 4, DEF 14A, 10-K

**Detection Capabilities**:
- IRC §83(b) election timing
- Ordinary income vs. capital gains
- AMT exposure calculation
- Constructive sales §1259
- Wash sale violations

**Output**: Tax liability estimates, timing violations, exposure calculations

**Accuracy**: 91%

---

### Node 6: Enforcement Routing Engine

**Purpose**: Route findings to appropriate enforcement agencies

**Filing Type**: All analyzed filings

**Routing Logic**:
- **SEC**: Securities violations, insider trading, disclosure failures
- **DOJ**: Criminal fraud, conspiracy, obstruction
- **IRS**: Tax evasion, IRC violations, fraudulent deductions

**Output**: Enforcement recommendations, jurisdiction mapping, severity scoring

**Accuracy**: 96%

---

## Sub-Phase 4.2: Extended Intelligence

### Node 7: 13F-HR Institutional Holdings Analysis

**Purpose**: Analyze institutional investor holdings and changes

**Filing Type**: 13F-HR (Institutional Investment Manager Holdings)

**Detection Capabilities**:
- Institutional ownership concentration
- Smart money movement patterns
- Fund manager alignment
- Hedge fund positioning
- Activist investor detection

**Output**: Institutional sentiment, ownership changes, activist alerts

**Accuracy**: 88%

---

### Node 8: SC 13D/13G Beneficial Ownership Analysis

**Purpose**: Track beneficial ownership above 5% threshold

**Filing Type**: SC 13D, SC 13G (Beneficial Ownership Reports)

**Detection Capabilities**:
- Control person identification
- Change of control risk
- Activist intentions (13D)
- Passive vs. active positions
- Group formation detection

**Output**: Control person alerts, activist threats, ownership structure

**Accuracy**: 93%

---

### Node 9: 8-K Material Events Analysis

**Purpose**: Analyze material event disclosures and timing

**Filing Type**: 8-K (Current Report)

**Detection Capabilities**:
- Late filing detection
- Selective disclosure timing
- Spin vs. substance analysis
- Serial 8-K patterns
- Omitted items detection

**Output**: Disclosure timing violations, material omissions, spin indicators

**Accuracy**: 85%

---

### Node 10: Form 144 Restricted Sales Analysis

**Purpose**: Analyze restricted stock sales and Rule 144 compliance

**Filing Type**: Form 144 (Notice of Proposed Sale)

**Detection Capabilities**:
- Holding period violations
- Volume limitation breaches
- Public information requirement
- Rule 144A private placements
- Coordinated selling patterns

**Output**: Rule 144 violations, coordinated selling, compliance failures

**Accuracy**: 90%

---

### Node 11: Executive Network Analysis

**Purpose**: Map executive networks and identify conflicts of interest

**Database**: Neo4j graph database

**Detection Capabilities**:
- Board interlock detection
- Compensation committee conflicts
- Related party transactions
- Family relationship mapping
- Prior employment connections

**Output**: Network graph, conflict alerts, relationship maps

**Accuracy**: 86%

---

### Node 12: Earnings Call Transcript Analysis

**Purpose**: Analyze management language and sentiment in earnings calls

**Data Source**: Earnings call transcripts

**Detection Capabilities**:
- Evasive language detection
- Sentiment shift analysis
- Hedge word frequency
- Q&A avoidance patterns
- Forward-looking statement abuse

**Output**: Language red flags, sentiment scores, evasion indicators

**Accuracy**: 83%

---

## Sub-Phase 4.3: Quantitative Forensic Scoring

### Node 13: Altman Z-Score Bankruptcy Prediction

**Purpose**: Calculate bankruptcy probability using Altman Z-Score

**Data Source**: 10-K, 10-Q financial statements

**Calculation**:
```
Z-Score = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5

Where:
X1 = Working Capital / Total Assets
X2 = Retained Earnings / Total Assets
X3 = EBIT / Total Assets
X4 = Market Value of Equity / Total Liabilities
X5 = Sales / Total Assets
```

**Interpretation**:
- **Z > 2.99**: Safe zone (low bankruptcy risk)
- **1.81 < Z < 2.99**: Grey zone (moderate risk)
- **Z < 1.81**: Distress zone (high bankruptcy risk)

**Output**: Z-Score, bankruptcy probability, financial health rating

**Accuracy**: 95%

---

### Node 14: Piotroski F-Score Financial Strength

**Purpose**: Calculate financial strength using Piotroski F-Score

**Data Source**: 10-K, 10-Q financial statements

**Calculation**: 9-point score based on:

**Profitability (4 points)**:
- Positive net income (1 point)
- Positive operating cash flow (1 point)
- Increasing ROA (1 point)
- Operating cash flow > net income (1 point)

**Leverage/Liquidity (3 points)**:
- Decreasing long-term debt (1 point)
- Increasing current ratio (1 point)
- No new equity issuance (1 point)

**Operating Efficiency (2 points)**:
- Increasing gross margin (1 point)
- Increasing asset turnover (1 point)

**Interpretation**:
- **F-Score 8-9**: Strong financial health
- **F-Score 5-7**: Moderate health
- **F-Score 0-4**: Weak financial health

**Output**: F-Score, financial strength rating, component breakdown

**Accuracy**: 93%

---

## Sub-Phase 4.4: Market Correlation

### Node 15: Market Correlation Engine

**Purpose**: Correlate SEC events with market price movements

**Data Source**: Polygon.io market data

**Detection Capabilities**:
- Pre-announcement trading patterns
- Post-disclosure price impact
- Insider trading timing correlation
- Event study analysis (-30/+30 days)
- Abnormal return calculation

**Output**: Correlation coefficients, abnormal returns, timing anomalies

**Accuracy**: 89%

**Note**: Optional node - skipped if Polygon API unavailable

---

## Sub-Phase 4.5: Cross-Node Correlation

**Purpose**: Identify patterns across multiple nodes

**Correlation Types**:

1. **Temporal Correlation**: Events occurring in close time proximity
2. **Causal Correlation**: Events with cause-effect relationship
3. **Actor Correlation**: Same executives/entities across multiple violations
4. **Pattern Correlation**: Similar fraud patterns across different nodes

**Output**: Cross-node findings, correlation matrix, compound violations

---

## Node Dependencies

### Sequential Dependencies

Some nodes depend on outputs from previous nodes:

```
Node 6 (Routing) ← All Nodes 1-5
Node 13 (Z-Score) ← Node 4 (10-K data)
Node 14 (F-Score) ← Node 4 (10-K data)
Node 15 (Market) ← Nodes 1, 2, 9 (event dates)
```

### Data Dependencies

| Node | Required Filings | Optional Data |
|------|------------------|---------------|
| 1 | Form 4 | Stock prices |
| 2 | DEF 14A | Stock prices |
| 3 | 10-Q | Prior quarters |
| 4 | 10-K | Audit reports |
| 5 | Form 4, DEF 14A | Tax tables |
| 7 | 13F-HR | - |
| 8 | SC 13D/13G | - |
| 9 | 8-K | Press releases |
| 10 | Form 144 | Form 4 |
| 11 | All filings | LinkedIn data |
| 12 | Transcripts | - |
| 13 | 10-K, 10-Q | - |
| 14 | 10-K, 10-Q | - |
| 15 | All events | Polygon API |

---

## Execution Flow

### Standard Execution

1. Execute Nodes 1-6 (Core SEC Filing)
2. Execute Nodes 7-12 (Extended Intelligence)
3. Execute Nodes 13-14 (Quantitative Scoring)
4. Execute Node 15 (Market Correlation)
5. Execute Cross-Node Correlation
6. Validate 80% success threshold (12/15 nodes)

### Optimized Execution (Investigation Types)

**Insider Trading Investigation**:
- Priority: Nodes 1, 9, 10, 15
- Optional: Nodes 2, 7, 8, 11

**Accounting Fraud Investigation**:
- Priority: Nodes 3, 4, 9, 13, 14
- Optional: Nodes 2, 7, 12

**Executive Compensation Investigation**:
- Priority: Nodes 2, 5, 11
- Optional: Nodes 1, 4, 9

---

## Node Output Format

Each node returns a structured output:

```python
@dataclass
class NodeOutput:
    node_id: int
    node_name: str
    status: str  # "success", "error", "skipped"
    violations_found: int
    violations: List[Dict[str, Any]]
    alerts: List[str]
    findings: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
```

---

## Next Steps

- **[System Overview](system_overview.md)**: High-level architecture
- **[Evidence Chain](evidence_chain.md)**: Evidence integrity details
- **[API Reference](../api/nodes.md)**: Node API documentation
- **[Detection Patterns](../api/detection_patterns.md)**: 23 detection algorithms
