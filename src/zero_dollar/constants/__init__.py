"""
Zero-Dollar Transaction Constants
==================================

Centralized exports for all constants and configuration.
"""

# Transaction codes
from .transaction_codes import (
    TransactionCode,
    TransactionCodeInfo,
    TRANSACTION_CODE_TAXONOMY,
    get_transaction_code_info,
    is_zero_dollar_suspicious,
)

# Temporal windows
from .temporal_windows import (
    TemporalWindow,
    TemporalWindowDefinition,
    TEMPORAL_WINDOWS,
    TEMPORAL_CLUSTER_WEIGHTS,
    CLUSTERING_THRESHOLD,
    EVENT_PROXIMITY_WINDOWS,
    MAX_LATE_FILING_DAYS,
    MIN_CLUSTER_SIZE,
    calculate_cluster_score,
    get_applicable_windows,
)

# Magnitude tiers
from .magnitude_tiers import (
    MagnitudeTier,
    MagnitudeThreshold,
    MAGNITUDE_THRESHOLDS,
    classify_magnitude,
    get_magnitude_threshold,
    calculate_magnitude_risk_score,
    get_tier_display_name,
)

__all__ = [
    # Transaction codes
    "TransactionCode",
    "TransactionCodeInfo",
    "TRANSACTION_CODE_TAXONOMY",
    "get_transaction_code_info",
    "is_zero_dollar_suspicious",
    # Temporal windows
    "TemporalWindow",
    "TemporalWindowDefinition",
    "TEMPORAL_WINDOWS",
    "TEMPORAL_CLUSTER_WEIGHTS",
    "CLUSTERING_THRESHOLD",
    "EVENT_PROXIMITY_WINDOWS",
    "MAX_LATE_FILING_DAYS",
    "MIN_CLUSTER_SIZE",
    "calculate_cluster_score",
    "get_applicable_windows",
    # Magnitude tiers
    "MagnitudeTier",
    "MagnitudeThreshold",
    "MAGNITUDE_THRESHOLDS",
    "classify_magnitude",
    "get_magnitude_threshold",
    "calculate_magnitude_risk_score",
    "get_tier_display_name",
]
