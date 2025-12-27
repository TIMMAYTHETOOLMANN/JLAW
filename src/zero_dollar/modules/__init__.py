"""
Zero-Dollar Transaction Detection Modules
==========================================

Analysis modules for zero-dollar transaction forensic detection.

Modules:
    - temporal_clustering: Temporal pattern detection and clustering analysis
    - cluster_scoring: Anomaly scoring and escalation determination
    - algorithms: Clustering algorithms (DBSCAN)
    - event_proximity: Event proximity analysis for MNPI detection
    - material_event_taxonomy: SEC Form 8-K and earnings event classifications
    - mnpi_scoring: MNPI inference probability scoring
"""

from .temporal_clustering import (
    TemporalClusteringModule,
    TemporalClusteringOutput,
    calculate_temporal_distances,
    get_issuer_historical_median,
)
from .cluster_scoring import (
    calculate_cluster_anomaly_score,
    determine_escalation_recommendation,
)
from .algorithms.dbscan_adapter import (
    detect_temporal_clusters,
    DBSCANClusteringAdapter,
)
from .event_proximity import (
    EventProximityModule,
    EventProximityOutput,
    detect_event_proximity,
)
from .material_event_taxonomy import (
    EventCategory,
    FORM_8K_EVENTS,
    EARNINGS_EVENTS,
    get_event_category,
    get_all_event_types,
)
from .mnpi_scoring import (
    calculate_mnpi_score,
    get_event_citations,
    determine_mnpi_severity,
)

__all__ = [
    # Temporal Clustering
    "TemporalClusteringModule",
    "TemporalClusteringOutput",
    "calculate_temporal_distances",
    "get_issuer_historical_median",
    # Cluster Scoring
    "calculate_cluster_anomaly_score",
    "determine_escalation_recommendation",
    # Algorithms
    "detect_temporal_clusters",
    "DBSCANClusteringAdapter",
    # Event Proximity
    "EventProximityModule",
    "EventProximityOutput",
    "detect_event_proximity",
    # Material Event Taxonomy
    "EventCategory",
    "FORM_8K_EVENTS",
    "EARNINGS_EVENTS",
    "get_event_category",
    "get_all_event_types",
    # MNPI Scoring
    "calculate_mnpi_score",
    "get_event_citations",
    "determine_mnpi_severity",
]
