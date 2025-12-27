# Temporal Clustering Detection Module

## Overview

The Temporal Clustering Detection Module identifies statistically improbable concentrations of zero-dollar transactions within compressed temporal windows, indicative of coordinated structuring to obscure aggregate disposition magnitude or avoid regulatory thresholds.

**Specification Reference:** JLAW Zero-Dollar Transaction Forensic Specification v1.0, Section 5

---

## Quick Start

```python
from src.zero_dollar.models import Transaction
from src.zero_dollar.modules import TemporalClusteringModule
from decimal import Decimal
from datetime import date

# Create module instance
module = TemporalClusteringModule(config={
    'eps_days': 1,              # Same-day clustering
    'min_samples': 2,           # Minimum 2 transactions per cluster
    'issuer_historical_median': Decimal('10000')  # Historical baseline
})

# Prepare transactions (zero-dollar transactions will be auto-filtered)
transactions = [
    Transaction(
        accession_number="...",
        issuer_cik="0000320187",
        issuer_name="NIKE, Inc.",
        reporting_person_cik="0001111111",
        reporting_person_name="John Smith",
        transaction_date=date(2020, 1, 15),
        filing_date=date(2020, 1, 17),
        transaction_code="G",
        shares=Decimal("50000"),
        price_per_share=Decimal("0.00"),
        transaction_acquired_disposed="D",
        shares_owned_following=Decimal("950000"),
        direct_indirect="D",
    ),
    # ... more transactions
]

# Run analysis
output = await module.analyze(transactions)

# Check results
print(f"Clusters detected: {output.cluster_count}")
print(f"Anomaly score: {output.total_anomaly_score}")
print(f"Escalation: {output.escalation_recommendation}")
```

---

## Anomaly Scoring Components

The module computes a composite anomaly score (0-100) using four weighted components:

### 1. Temporal Density Score (TDS) - Weight: 30%

Measures how tightly transactions are clustered in time.

**Formula:** `min(100, 100 / max(avg_gap_days, 0.1))`

**Example:**
- Same-day transactions: TDS = 100
- 1-day avg gap: TDS = 100
- 10-day avg gap: TDS = 10

### 2. Magnitude Concentration Score (MCS) - Weight: 35%

Compares aggregate volume to historical baseline.

**Formula:** `min(100, (aggregate_shares / historical_median) * 10)`

**Example:**
- 150,000 shares vs 10,000 median: MCS = 100
- 20,000 shares vs 10,000 median: MCS = 20

### 3. Code Heterogeneity Score (CHS) - Weight: 20%

Penalizes use of multiple transaction codes.

**Formula:** `min(100, unique_codes * 25)`

**Example:**
- 1 code (all "G"): CHS = 25
- 2 codes ("G" + "A"): CHS = 50
- 4 codes: CHS = 100

### 4. Zero-Price Consistency Score (ZCS) - Weight: 15%

Rewards systematic zero-dollar pricing.

**Formula:** `zero_price_ratio * 100`

**Example:**
- 100% zero-dollar: ZCS = 100
- 50% zero-dollar: ZCS = 50

---

## Escalation Thresholds

| Score Range | Level | Action |
|-------------|-------|--------|
| 0.00 - 24.99 | **NONE** | Standard archival; no escalation |
| 25.00 - 49.99 | **ENHANCED_MONITORING** | Add to watchlist; quarterly re-analysis |
| 50.00 - 74.99 | **INVESTIGATION** | Manual analyst review within 48 hours |
| 75.00 - 100.00+ | **REFERRAL** | Automatic escalation to enforcement queue |

---

## Configuration Parameters

### `eps_days` (int, default: 1)

Maximum temporal distance (in days) between transactions in a cluster.

- `1`: Same-day clustering only (strict)
- `2`: Within 2-day filing window (Section 16(a))
- `7`: Weekly clustering window

### `min_samples` (int, default: 2)

Minimum number of transactions required to form a cluster.

- `2`: Pairs of transactions (default)
- `3`: Triplets or larger

### `issuer_historical_median` (Decimal, default: 10000)

Historical median transaction size for the issuer, used in MCS calculation.

---

## Output Structure

```python
@dataclass
class TemporalClusteringOutput:
    reporting_person_cik: str
    issuer_cik: str
    analysis_period: Tuple[date, date]
    clusters_detected: List[TransactionCluster]
    total_anomaly_score: Decimal
    escalation_recommendation: str
    regulatory_citations: List[str]
    detection_timestamp: datetime
    evidence_hash: str
```

### Key Properties

- `cluster_count`: Number of clusters detected
- `total_transactions_in_clusters`: Total transactions across all clusters
- `to_dict()`: Serialize output to dictionary

---

## Cluster Details

Each detected cluster includes:

```python
@dataclass
class TransactionCluster:
    cluster_id: str                      # Unique SHA-256 hash
    reporting_person_cik: str
    reporting_person_name: str
    transactions: List[Transaction]      # Transactions in cluster
    start_date: date                     # Earliest transaction
    end_date: date                       # Latest transaction
    total_shares: Decimal                # Aggregate volume
    zero_dollar_count: int               # Zero-dollar transaction count
    cluster_score: float                 # Anomaly score for this cluster
    detection_timestamp: datetime
```

### Properties

- `cluster_span_days`: Temporal span (days)
- `transaction_count`: Number of transactions
- `zero_dollar_ratio`: Ratio of zero-dollar transactions
- `average_notional_value`: Average value of non-zero transactions

---

## Regulatory Citations

The module automatically includes these regulatory citations in output:

1. **Securities Exchange Act of 1934, Section 16(a)**
   - Insider trading reporting requirements

2. **SEC Release No. 34-46421 (August 27, 2002)**
   - Same-day clustering as deliberate fragmentation

3. **17 CFR § 240.16a-3 (Form 4 Filing Requirements)**
   - Form 4 filing regulations

4. **Sarbanes-Oxley Act § 403 (Accelerated Filing Deadline)**
   - 2-business-day filing deadline

---

## Evidence Chain

Each analysis generates a SHA-256 evidence hash for FRE 902(13)/(14) compliance:

```python
evidence_hash = output.evidence_hash  # Tamper-evident hash
```

The hash is computed from:
- Cluster identifiers
- Start/end dates
- Transaction counts

This provides a cryptographic audit trail for chain of custody.

---

## Testing

Run the comprehensive test suite:

```bash
python tests/test_temporal_clustering.py
```

Run the demonstration:

```bash
python examples/temporal_clustering_demo.py
```

---

## Algorithm Details

### DBSCAN Clustering

The module uses **Density-Based Spatial Clustering of Applications with Noise (DBSCAN)** from scikit-learn:

1. **Distance Matrix:** Pairwise temporal distances calculated in days
2. **Core Points:** Transactions within `eps_days` of at least `min_samples` others
3. **Cluster Formation:** Connected core points form clusters
4. **Noise Handling:** Isolated transactions excluded (labeled -1)

### Advantages

- No need to specify number of clusters a priori
- Can find arbitrarily shaped clusters
- Robust to noise (isolated transactions)
- Deterministic results

---

## Performance Considerations

- **Time Complexity:** O(n²) for distance matrix, O(n log n) for clustering
- **Space Complexity:** O(n²) for distance matrix storage
- **Recommended Limits:** 
  - < 1,000 transactions per analysis for optimal performance
  - Use batch processing for larger datasets

---

## Common Use Cases

### 1. Same-Day Structuring Detection

Detect executives splitting large dispositions into same-day fragments:

```python
module = TemporalClusteringModule(config={'eps_days': 1})
```

### 2. Filing Window Clustering

Detect clustering within Section 16(a) 2-day filing window:

```python
module = TemporalClusteringModule(config={'eps_days': 2})
```

### 3. Earnings Blackout Period

Detect clustering within 30-day pre-earnings window:

```python
module = TemporalClusteringModule(config={'eps_days': 30, 'min_samples': 3})
```

---

## Troubleshooting

### No Clusters Detected

**Cause:** Transactions too spread out or below minimum cluster size.

**Solution:** 
- Increase `eps_days` to capture wider windows
- Decrease `min_samples` to detect smaller patterns

### Low Anomaly Scores

**Cause:** Transactions spread over time or small volume.

**Solution:** This is expected behavior. Not all zero-dollar transactions are anomalous.

### High Memory Usage

**Cause:** Large transaction lists (>10,000).

**Solution:** 
- Process in batches by reporting person
- Filter by date range before analysis

---

## Integration with Other Modules

This module is **PR #3** in the Zero-Dollar Detection series:

- **PR #1:** Data Models ✅ (Transaction, TransactionCluster)
- **PR #2:** EDGAR Acquisition ✅ (Form 4 parsing)
- **PR #3:** Temporal Clustering ✅ (This module)
- **PR #4:** Related Entity Detection (Upcoming)
- **PR #5:** Event Proximity Analysis (Upcoming)
- **PR #6:** Behavioral Risk Scoring (Upcoming)
- **PR #7:** Evidence Chain (Upcoming)
- **PR #8:** Forensic Dossier Generation (Upcoming)

---

## Support

For issues or questions:
- Review specification: JLAW Zero-Dollar Transaction Forensic Specification v1.0
- Check test suite: `tests/test_temporal_clustering.py`
- Run demo: `examples/temporal_clustering_demo.py`

---

## License

This module is part of the JLAW forensic analysis platform.
All rights reserved.
