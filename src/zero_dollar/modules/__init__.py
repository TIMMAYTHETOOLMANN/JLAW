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
    - ownership_chain: Beneficial ownership chain resolution (Section 7)
    - footnote_parser: Form 4 footnote parsing and entity extraction
    - entity_classifier: Entity type classification taxonomy
    - control_assessment: Beneficial ownership control assessment
    - hsr_analysis: Hart-Scott-Rodino threshold analysis
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
from .ownership_chain import (
    BeneficialOwnershipModule,
    OwnershipChain,
    OwnershipNode,
    construct_ownership_chain,
)
from .footnote_parser import (
    parse_ownership_footnotes,
    calculate_parse_confidence,
    extract_entity_names,
    detect_ownership_transfer,
    extract_control_indicators,
)
from .entity_classifier import (
    EntityTypeInfo,
    ENTITY_TYPE_TAXONOMY,
    get_entity_type_info,
    get_control_presumption,
    classify_entity_by_description,
)
from .control_assessment import (
    ControlIndicator,
    ControlAssessment,
    assess_control_indicators,
    calculate_control_probability,
    generate_control_recommendation,
    assess_voting_control,
    assess_dispositive_control,
)
from .hsr_analysis import (
    HSRAnalysis,
    check_hsr_circumvention,
    HSR_THRESHOLD_2024,
    HSR_SIZE_OF_PERSON_2024,
    calculate_hsr_threshold_distance,
    detect_threshold_fragmentation,
    get_hsr_filing_requirements,
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
    # Ownership Chain (Section 7)
    "BeneficialOwnershipModule",
    "OwnershipChain",
    "OwnershipNode",
    "construct_ownership_chain",
    # Footnote Parser
    "parse_ownership_footnotes",
    "calculate_parse_confidence",
    "extract_entity_names",
    "detect_ownership_transfer",
    "extract_control_indicators",
    # Entity Classifier
    "EntityTypeInfo",
    "ENTITY_TYPE_TAXONOMY",
    "get_entity_type_info",
    "get_control_presumption",
    "classify_entity_by_description",
    # Control Assessment
    "ControlIndicator",
    "ControlAssessment",
    "assess_control_indicators",
    "calculate_control_probability",
    "generate_control_recommendation",
    "assess_voting_control",
    "assess_dispositive_control",
    # HSR Analysis
    "HSRAnalysis",
    "check_hsr_circumvention",
    "HSR_THRESHOLD_2024",
    "HSR_SIZE_OF_PERSON_2024",
    "calculate_hsr_threshold_distance",
    "detect_threshold_fragmentation",
    "get_hsr_filing_requirements",
]
