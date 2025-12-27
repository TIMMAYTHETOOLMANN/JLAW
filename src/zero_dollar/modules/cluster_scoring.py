"""
Cluster Anomaly Scoring
========================

Composite anomaly scoring for temporal transaction clusters.

Implements multi-component risk scoring per Section 5.3.3 of the JLAW
Zero-Dollar Transaction Forensic Specification.

Scoring Components:
    1. Temporal Density Score (TDS): Inverse of average inter-transaction time
    2. Magnitude Concentration Score (MCS): Aggregate shares relative to historical baseline
    3. Code Heterogeneity Score (CHS): Penalty for multiple transaction codes
    4. Zero-Price Consistency Score (ZCS): Bonus for systematic zero-pricing

Reference:
    - Section 5.3.3: Cluster Anomaly Scoring
    - Section 5.5: Escalation Thresholds
"""

from decimal import Decimal
from typing import List
from src.zero_dollar.models import Transaction


# Scoring weights (calibrated via historical enforcement action correlation)
W_TDS = Decimal('0.30')  # Temporal Density Score weight
W_MCS = Decimal('0.35')  # Magnitude Concentration Score weight
W_CHS = Decimal('0.20')  # Code Heterogeneity Score weight
W_ZCS = Decimal('0.15')  # Zero-Price Consistency Score weight


def calculate_cluster_anomaly_score(
    cluster_transactions: List[Transaction],
    issuer_historical_median: Decimal = None
) -> Decimal:
    """
    Compute composite anomaly score for transaction cluster.
    
    Implements the four-component scoring formula per Section 5.3.3:
    
        ANOMALY_SCORE = (TDS * W_tds) + (MCS * W_mcs) + (CHS * W_chs) + (ZCS * W_zcs)
    
    Scoring Components:
        1. Temporal Density Score (TDS): Measures transaction concentration in time
           - Formula: min(100, 100 / max(avg_gap_days, 0.1))
           - Higher score = transactions more tightly clustered
        
        2. Magnitude Concentration Score (MCS): Compares volume to historical baseline
           - Formula: min(100, (aggregate_shares / historical_median) * 10)
           - Higher score = unusually large aggregate volume
        
        3. Code Heterogeneity Score (CHS): Penalizes diverse transaction codes
           - Formula: min(100, unique_codes * 25)
           - Higher score = more transaction types (potential obfuscation)
        
        4. Zero-Price Consistency Score (ZCS): Rewards systematic zero-pricing
           - Formula: zero_price_ratio * 100
           - Higher score = higher proportion of zero-dollar transactions
    
    Weights (calibrated via historical enforcement action correlation):
        W_tds = 0.30 (30%)
        W_mcs = 0.35 (35%)
        W_chs = 0.20 (20%)
        W_zcs = 0.15 (15%)
    
    Args:
        cluster_transactions: List of Transaction objects in cluster
        issuer_historical_median: Historical median transaction size for issuer.
                                 If None, uses market-wide default.
    
    Returns:
        Decimal: Normalized score [0.0 - 100.0] where higher = more anomalous
    
    Example:
        >>> transactions = [txn1, txn2, txn3]  # 3 same-day zero-dollar transactions
        >>> score = calculate_cluster_anomaly_score(transactions)
        >>> score >= Decimal('50.0')  # High anomaly score
        True
    """
    if not cluster_transactions:
        return Decimal('0.0')
    
    # Component 1: Temporal Density Score (TDS)
    tds = _calculate_temporal_density_score(cluster_transactions)
    
    # Component 2: Magnitude Concentration Score (MCS)
    mcs = _calculate_magnitude_concentration_score(
        cluster_transactions,
        issuer_historical_median
    )
    
    # Component 3: Code Heterogeneity Score (CHS)
    chs = _calculate_code_heterogeneity_score(cluster_transactions)
    
    # Component 4: Zero-Price Consistency Score (ZCS)
    zcs = _calculate_zero_price_consistency_score(cluster_transactions)
    
    # Weighted composite score
    composite_score = (
        (tds * W_TDS) +
        (mcs * W_MCS) +
        (chs * W_CHS) +
        (zcs * W_ZCS)
    )
    
    return composite_score


def _calculate_temporal_density_score(transactions: List[Transaction]) -> Decimal:
    """
    Calculate Temporal Density Score (TDS).
    
    Measures how tightly clustered transactions are in time.
    Formula: min(100, 100 / max(avg_gap_days, 0.1))
    
    Args:
        transactions: List of transactions in cluster
    
    Returns:
        Temporal density score [0.0 - 100.0]
    """
    if len(transactions) <= 1:
        return Decimal('100.0')  # Single transaction = maximum density
    
    # Sort by transaction date
    sorted_txns = sorted(transactions, key=lambda t: t.transaction_date)
    
    # Calculate inter-transaction gaps
    gaps = []
    for i in range(1, len(sorted_txns)):
        gap_days = (sorted_txns[i].transaction_date - 
                   sorted_txns[i-1].transaction_date).days
        gaps.append(gap_days)
    
    # Average gap (add 0.1 to avoid division by zero)
    avg_gap = sum(gaps) / len(gaps) if gaps else 0.0
    avg_gap = max(avg_gap, 0.1)
    
    # Score inversely proportional to average gap
    score = Decimal('100.0') / Decimal(str(avg_gap))
    
    return min(Decimal('100.0'), score)


def _calculate_magnitude_concentration_score(
    transactions: List[Transaction],
    issuer_historical_median: Decimal = None
) -> Decimal:
    """
    Calculate Magnitude Concentration Score (MCS).
    
    Compares aggregate transaction volume to historical baseline.
    Formula: min(100, (aggregate_shares / historical_median) * 10)
    
    Args:
        transactions: List of transactions in cluster
        issuer_historical_median: Historical median transaction size
    
    Returns:
        Magnitude concentration score [0.0 - 100.0]
    """
    # Use default baseline if not provided
    if issuer_historical_median is None:
        issuer_historical_median = Decimal('10000')  # Default: 10,000 shares
    
    # Calculate aggregate shares
    aggregate_shares = sum(abs(t.shares) for t in transactions)
    
    # Avoid division by zero
    if issuer_historical_median == Decimal('0'):
        return Decimal('0.0')
    
    # Score based on ratio to historical median
    ratio = aggregate_shares / issuer_historical_median
    score = ratio * Decimal('10')
    
    return min(Decimal('100.0'), score)


def _calculate_code_heterogeneity_score(transactions: List[Transaction]) -> Decimal:
    """
    Calculate Code Heterogeneity Score (CHS).
    
    Penalizes use of multiple transaction codes, which may indicate
    obfuscation attempts or complex transaction structuring.
    
    Formula: min(100, unique_codes * 25)
    
    Args:
        transactions: List of transactions in cluster
    
    Returns:
        Code heterogeneity score [0.0 - 100.0]
    """
    # Count unique transaction codes
    unique_codes = len(set(t.transaction_code for t in transactions))
    
    # 25 points per unique code (max 4 codes = 100 points)
    score = Decimal(str(unique_codes)) * Decimal('25')
    
    return min(Decimal('100.0'), score)


def _calculate_zero_price_consistency_score(transactions: List[Transaction]) -> Decimal:
    """
    Calculate Zero-Price Consistency Score (ZCS).
    
    Rewards systematic use of zero-dollar pricing, which is the primary
    focus of this detection system.
    
    Formula: zero_price_ratio * 100
    
    Args:
        transactions: List of transactions in cluster
    
    Returns:
        Zero-price consistency score [0.0 - 100.0]
    """
    if not transactions:
        return Decimal('0.0')
    
    # Count zero-dollar transactions
    zero_dollar_count = sum(1 for t in transactions if t.is_zero_dollar)
    
    # Calculate ratio
    zero_ratio = Decimal(str(zero_dollar_count)) / Decimal(str(len(transactions)))
    
    # Convert to 0-100 scale
    score = zero_ratio * Decimal('100')
    
    return score


def determine_escalation_recommendation(total_score: Decimal) -> str:
    """
    Map total anomaly score to escalation level.
    
    Implements threshold-based escalation per Section 5.5:
    
    | Total Anomaly Score | Escalation Level       | Required Action                          |
    |---------------------|------------------------|------------------------------------------|
    | 0.00 - 24.99        | NONE                   | Standard archival; no escalation         |
    | 25.00 - 49.99       | ENHANCED_MONITORING    | Add to watchlist; quarterly re-analysis  |
    | 50.00 - 74.99       | INVESTIGATION          | Manual analyst review within 48 hours    |
    | 75.00 - 100.00+     | REFERRAL               | Automatic escalation to enforcement queue|
    
    Args:
        total_score: Total anomaly score from cluster analysis
    
    Returns:
        Escalation level: 'NONE', 'ENHANCED_MONITORING', 'INVESTIGATION', or 'REFERRAL'
    
    Example:
        >>> determine_escalation_recommendation(Decimal('80.5'))
        'REFERRAL'
        >>> determine_escalation_recommendation(Decimal('35.0'))
        'ENHANCED_MONITORING'
    """
    if total_score >= Decimal('75.0'):
        return 'REFERRAL'
    elif total_score >= Decimal('50.0'):
        return 'INVESTIGATION'
    elif total_score >= Decimal('25.0'):
        return 'ENHANCED_MONITORING'
    else:
        return 'NONE'
