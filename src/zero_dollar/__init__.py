"""
Zero-Dollar Transaction Anomaly Detection System
=================================================

DOJ-grade forensic analysis system for detecting and analyzing zero-dollar
transactions in SEC Form 4 filings per JLAW Zero-Dollar Transaction Forensic
Specification v1.0.

This package implements:
- Transaction data models with Form 4 field mapping
- Reporting person classifications per Section 16
- Anomaly detection types and severity levels
- Evidence chain tracking with FRE 902(13)/(14) compliance
- Temporal clustering and magnitude tier analysis
- PostgreSQL schema for forensic data storage

Reference: Section 2 (Definitional Framework) and Section 11 (Data Schema)
of the Zero-Dollar Transaction Forensic Specification.
"""

__version__ = "1.0.0"
__author__ = "JLAW Development Team"

# Import all public models
from .models import (
    # Transaction models
    Transaction,
    TransactionCluster,
    # Reporting person models
    ReportingPerson,
    ReportingPersonClassification,
    # Anomaly models
    AnomalyType,
    AnomalySeverity,
    EntityType,
    AnomalyFlag,
    MaterialEvent,
    EventProximityFlag,
    EntityReference,
    ControlIndicator,
    ControlAssessment,
    OwnershipNode,
    OwnershipChain,
    # Assessment models
    BehavioralScoreComponents,
    BehavioralRiskAssessment,
    EvidenceArtifact,
    MerkleProof,
    TrustedTimestamp,
    ChainOfCustodyRecord,
)

# Import all constants
from .constants import (
    # Transaction codes
    TransactionCode,
    TransactionCodeInfo,
    TRANSACTION_CODE_TAXONOMY,
    get_transaction_code_info,
    is_zero_dollar_suspicious,
    # Temporal windows
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
    # Magnitude tiers
    MagnitudeTier,
    MagnitudeThreshold,
    MAGNITUDE_THRESHOLDS,
    classify_magnitude,
    get_magnitude_threshold,
    calculate_magnitude_risk_score,
    get_tier_display_name,
)

# Import schema utilities
from .schema import get_schema_sql, SCHEMA_FILE

# Import acquisition module (PR #2)
from .acquisition import (
    SECEdgarAcquisition,
    FilingMetadata,
    Form4Filing,
    EdgarRateLimiter,
    EdgarAcquisitionError,
    EdgarRateLimitError,
    EdgarParsingError,
    EdgarNetworkError,
    enrich_with_issuer_metadata,
    calculate_derived_fields,
)

__all__ = [
    # Metadata
    "__version__",
    "__author__",
    # Transaction models
    "Transaction",
    "TransactionCluster",
    # Reporting person models
    "ReportingPerson",
    "ReportingPersonClassification",
    # Anomaly models
    "AnomalyType",
    "AnomalySeverity",
    "EntityType",
    "AnomalyFlag",
    "MaterialEvent",
    "EventProximityFlag",
    "EntityReference",
    "ControlIndicator",
    "ControlAssessment",
    "OwnershipNode",
    "OwnershipChain",
    # Assessment models
    "BehavioralScoreComponents",
    "BehavioralRiskAssessment",
    "EvidenceArtifact",
    "MerkleProof",
    "TrustedTimestamp",
    "ChainOfCustodyRecord",
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
    # Schema
    "get_schema_sql",
    "SCHEMA_FILE",
    # Acquisition (PR #2)
    "SECEdgarAcquisition",
    "FilingMetadata",
    "Form4Filing",
    "EdgarRateLimiter",
    "EdgarAcquisitionError",
    "EdgarRateLimitError",
    "EdgarParsingError",
    "EdgarNetworkError",
    "enrich_with_issuer_metadata",
    "calculate_derived_fields",
]
