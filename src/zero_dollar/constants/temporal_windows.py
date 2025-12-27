"""
Temporal Window Constants
==========================

Temporal clustering windows and detection thresholds for zero-dollar analysis.

Reference:
- Section 4.2: Temporal Clustering Algorithm
- Section 5.2: Event Proximity Analysis
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class TemporalWindow(str, Enum):
    """
    Temporal windows for transaction clustering.
    
    Defines time windows used to detect suspicious transaction patterns.
    
    Values:
        SAME_DAY: Transactions on same day
        SHORT_SWING: 2-day window (Section 16(a) filing deadline)
        FILING_DEADLINE: 7-day window around filing deadline
        BLACKOUT_PERIOD: 30-day blackout period before earnings
        QUARTERLY: 90-day quarterly window
        ANNUAL: 365-day annual window
    """
    SAME_DAY = "same_day"
    SHORT_SWING = "short_swing"
    FILING_DEADLINE = "filing_deadline"
    BLACKOUT_PERIOD = "blackout_period"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


@dataclass
class TemporalWindowDefinition:
    """
    Definition of temporal window for clustering.
    
    Attributes:
        window_type: Type of temporal window
        days: Number of days in window
        weight: Weight for clustering score (0.0-1.0)
        description: Human-readable description
        detection_threshold: Minimum transactions to trigger alert
    """
    window_type: TemporalWindow
    days: int
    weight: float
    description: str
    detection_threshold: int


# Temporal Window Definitions
TEMPORAL_WINDOWS: Dict[TemporalWindow, TemporalWindowDefinition] = {
    TemporalWindow.SAME_DAY: TemporalWindowDefinition(
        window_type=TemporalWindow.SAME_DAY,
        days=1,
        weight=1.0,
        description="Multiple transactions on the same day",
        detection_threshold=3,
    ),
    TemporalWindow.SHORT_SWING: TemporalWindowDefinition(
        window_type=TemporalWindow.SHORT_SWING,
        days=2,
        weight=0.9,
        description="Section 16(a) 2-business-day filing window",
        detection_threshold=3,
    ),
    TemporalWindow.FILING_DEADLINE: TemporalWindowDefinition(
        window_type=TemporalWindow.FILING_DEADLINE,
        days=7,
        weight=0.7,
        description="One-week window around filing deadline",
        detection_threshold=4,
    ),
    TemporalWindow.BLACKOUT_PERIOD: TemporalWindowDefinition(
        window_type=TemporalWindow.BLACKOUT_PERIOD,
        days=30,
        weight=0.8,
        description="30-day pre-earnings blackout period",
        detection_threshold=5,
    ),
    TemporalWindow.QUARTERLY: TemporalWindowDefinition(
        window_type=TemporalWindow.QUARTERLY,
        days=90,
        weight=0.5,
        description="Quarterly clustering window",
        detection_threshold=8,
    ),
    TemporalWindow.ANNUAL: TemporalWindowDefinition(
        window_type=TemporalWindow.ANNUAL,
        days=365,
        weight=0.3,
        description="Annual transaction pattern",
        detection_threshold=12,
    ),
}


# Temporal Cluster Scoring Weights
TEMPORAL_CLUSTER_WEIGHTS: Dict[str, float] = {
    # Base score components
    "transaction_count": 0.25,  # Weight for number of transactions
    "zero_dollar_ratio": 0.30,  # Weight for ratio of zero-dollar transactions
    "temporal_density": 0.20,   # Weight for temporal concentration
    "magnitude_variance": 0.15, # Weight for magnitude disproportion
    "filing_latency": 0.10,     # Weight for late filing patterns
}


# Clustering Detection Threshold
CLUSTERING_THRESHOLD: float = 15.0
"""
Minimum cluster score to trigger anomaly flag.

Cluster scores range from 0-100. Scores above this threshold
warrant investigation per Section 4.2.
"""


# Event Proximity Windows (days before/after event)
EVENT_PROXIMITY_WINDOWS: Dict[str, int] = {
    "earnings_announcement": 30,
    "merger_announcement": 60,
    "dividend_announcement": 14,
    "material_lawsuit": 45,
    "executive_departure": 30,
    "restatement": 90,
    "sec_investigation": 180,
}


# Maximum days for late filing before escalation
MAX_LATE_FILING_DAYS: int = 30
"""
Maximum calendar days after transaction before filing is considered
severely late and warrants automatic escalation.

SEC requires 2 business days. This allows for weekends/holidays
plus some grace period. Beyond 30 days indicates severe non-compliance.
"""


# Minimum transactions for cluster formation
MIN_CLUSTER_SIZE: int = 2
"""
Minimum number of transactions required to form a cluster.

While technically a single transaction can be anomalous, clustering
analysis requires at least 2 transactions to identify patterns.
"""


def calculate_cluster_score(
    transaction_count: int,
    zero_dollar_count: int,
    span_days: int,
    total_shares: float,
    max_shares: float,
    late_filing_count: int,
) -> float:
    """
    Calculate temporal cluster risk score.
    
    Implements the scoring algorithm per Section 4.2 of the specification.
    
    Args:
        transaction_count: Total transactions in cluster
        zero_dollar_count: Count of zero-dollar transactions
        span_days: Temporal span of cluster in days
        total_shares: Total shares across all transactions
        max_shares: Maximum shares in any single transaction
        late_filing_count: Count of late filings in cluster
        
    Returns:
        Cluster risk score (0-100)
    """
    # Component 1: Transaction frequency (0-25)
    frequency_score = min(25.0, transaction_count * 2.5)
    
    # Component 2: Zero-dollar ratio (0-30)
    zero_ratio = zero_dollar_count / transaction_count if transaction_count > 0 else 0
    zero_score = zero_ratio * 30.0
    
    # Component 3: Temporal density (0-20)
    if span_days > 0:
        density = transaction_count / span_days
        density_score = min(20.0, density * 10.0)
    else:
        density_score = 20.0  # All transactions on same day = maximum density
    
    # Component 4: Magnitude variance (0-15)
    if total_shares > 0:
        variance_ratio = max_shares / total_shares
        variance_score = variance_ratio * 15.0
    else:
        variance_score = 0.0
    
    # Component 5: Filing compliance (0-10)
    filing_score = min(10.0, late_filing_count * 3.0)
    
    # Total score
    total = frequency_score + zero_score + density_score + variance_score + filing_score
    
    return min(100.0, total)


def get_applicable_windows(span_days: int) -> list[TemporalWindow]:
    """
    Get applicable temporal windows for a given span.
    
    Args:
        span_days: Span of transactions in days
        
    Returns:
        List of applicable temporal windows
    """
    applicable = []
    for window_type, definition in TEMPORAL_WINDOWS.items():
        if span_days <= definition.days:
            applicable.append(window_type)
    return applicable
