"""
Temporal Clustering Detection Module
=====================================

Identifies statistically improbable concentrations of zero-dollar transactions
within compressed temporal windows, indicative of coordinated structuring to
obscure aggregate disposition magnitude or avoid regulatory thresholds.

Per Section 5 of JLAW Zero-Dollar Transaction Forensic Specification.

Reference:
    - Section 5: Temporal Clustering Detection Module
    - Section 5.1: Module Objective
    - Section 5.2: Input Specification
    - Section 5.3: Algorithm Specification
    - Section 5.4: Output Specification
    - Section 5.5: Escalation Thresholds
"""

import hashlib
import numpy as np
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import List, Tuple, Optional

from src.zero_dollar.models import Transaction, TransactionCluster
from .algorithms.dbscan_adapter import detect_temporal_clusters
from .cluster_scoring import (
    calculate_cluster_anomaly_score,
    determine_escalation_recommendation,
)


@dataclass
class TemporalClusteringOutput:
    """
    Output from Temporal Clustering Detection Module.
    
    Contains all detected clusters, aggregate anomaly scores, and escalation
    recommendations per Section 5.4 of the specification.
    
    Attributes:
        reporting_person_cik: CIK of reporting person analyzed
        issuer_cik: CIK of issuer company
        analysis_period: Tuple of (start_date, end_date) for analysis window
        clusters_detected: List of detected TransactionCluster objects
        total_anomaly_score: Sum of all cluster anomaly scores
        escalation_recommendation: Escalation level (NONE/ENHANCED_MONITORING/INVESTIGATION/REFERRAL)
        regulatory_citations: List of applicable statutory/regulatory references
        detection_timestamp: When analysis was performed
        evidence_hash: SHA-256 hash of cluster evidence for chain of custody
    """
    reporting_person_cik: str
    issuer_cik: str
    analysis_period: Tuple[date, date]
    clusters_detected: List[TransactionCluster]
    total_anomaly_score: Decimal
    escalation_recommendation: str
    regulatory_citations: List[str] = field(default_factory=list)
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)
    evidence_hash: Optional[str] = None
    
    @property
    def cluster_count(self) -> int:
        """Number of clusters detected."""
        return len(self.clusters_detected)
    
    @property
    def total_transactions_in_clusters(self) -> int:
        """Total number of transactions across all clusters."""
        return sum(len(c.transactions) for c in self.clusters_detected)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'reporting_person_cik': self.reporting_person_cik,
            'issuer_cik': self.issuer_cik,
            'analysis_period': {
                'start_date': self.analysis_period[0].isoformat(),
                'end_date': self.analysis_period[1].isoformat(),
            },
            'cluster_count': self.cluster_count,
            'total_transactions_in_clusters': self.total_transactions_in_clusters,
            'clusters_detected': [c.to_dict() for c in self.clusters_detected],
            'total_anomaly_score': str(self.total_anomaly_score),
            'escalation_recommendation': self.escalation_recommendation,
            'regulatory_citations': self.regulatory_citations,
            'detection_timestamp': self.detection_timestamp.isoformat(),
            'evidence_hash': self.evidence_hash,
        }


class TemporalClusteringModule:
    """
    Temporal Clustering Detection Module.
    
    Identifies statistically improbable concentrations of zero-dollar
    transactions within compressed temporal windows.
    
    Per Section 5 of JLAW Zero-Dollar Transaction Forensic Specification.
    
    The module performs the following analysis steps:
        1. Filter transactions to zero-dollar subset
        2. Calculate pairwise temporal distance matrix
        3. Apply DBSCAN clustering algorithm
        4. Compute composite anomaly scores for each cluster
        5. Determine escalation recommendation
        6. Generate evidence hash for chain of custody
    
    Attributes:
        config: Configuration dictionary with optional parameters
        eps_days: DBSCAN epsilon parameter (maximum days between transactions)
        min_samples: DBSCAN minimum samples (minimum transactions per cluster)
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize Temporal Clustering Module.
        
        Args:
            config: Optional configuration dictionary with keys:
                   - eps_days: DBSCAN epsilon (default: 1 day)
                   - min_samples: Minimum cluster size (default: 2)
                   - issuer_historical_median: Historical baseline shares
        """
        self.config = config or {}
        self.eps_days = self.config.get('eps_days', 1)
        self.min_samples = self.config.get('min_samples', 2)
        self.issuer_historical_median = self.config.get('issuer_historical_median', None)
    
    async def analyze(
        self,
        transactions: List[Transaction]
    ) -> TemporalClusteringOutput:
        """
        Execute temporal clustering analysis on zero-dollar transactions.
        
        Performs complete analysis workflow per Section 5:
            1. Filter to zero-dollar transactions
            2. Calculate temporal distance matrix
            3. Detect clusters using DBSCAN
            4. Score each cluster for anomaly severity
            5. Determine escalation recommendation
            6. Compute evidence hash
        
        Args:
            transactions: List of Transaction objects to analyze
        
        Returns:
            TemporalClusteringOutput with detected clusters and recommendations
        
        Example:
            >>> module = TemporalClusteringModule()
            >>> output = await module.analyze(transactions)
            >>> print(f"Detected {output.cluster_count} clusters")
            >>> print(f"Escalation: {output.escalation_recommendation}")
        """
        # Validate input
        if not transactions:
            return self._empty_output()
        
        # Extract metadata
        reporting_person_cik = transactions[0].reporting_person_cik
        issuer_cik = transactions[0].issuer_cik
        dates = [t.transaction_date for t in transactions]
        analysis_period = (min(dates), max(dates))
        
        # Step 1: Filter to zero-dollar transactions
        zero_dollar_transactions = [t for t in transactions if t.is_zero_dollar]
        
        if len(zero_dollar_transactions) < self.min_samples:
            # Insufficient zero-dollar transactions for clustering
            return TemporalClusteringOutput(
                reporting_person_cik=reporting_person_cik,
                issuer_cik=issuer_cik,
                analysis_period=analysis_period,
                clusters_detected=[],
                total_anomaly_score=Decimal('0.0'),
                escalation_recommendation='NONE',
                regulatory_citations=self._get_regulatory_citations(),
            )
        
        # Step 2: Calculate pairwise temporal distance matrix
        distance_matrix, filtered_transactions = calculate_temporal_distances(
            zero_dollar_transactions
        )
        
        # Step 3: Detect temporal clusters using DBSCAN
        clusters = detect_temporal_clusters(
            distance_matrix,
            filtered_transactions,
            eps_days=self.eps_days,
            min_samples=self.min_samples
        )
        
        # Step 4: Calculate anomaly scores for each cluster
        total_score = Decimal('0.0')
        for cluster in clusters:
            cluster_score = calculate_cluster_anomaly_score(
                cluster.transactions,
                issuer_historical_median=self.issuer_historical_median
            )
            cluster.cluster_score = float(cluster_score)
            total_score += cluster_score
        
        # Step 5: Determine escalation recommendation
        escalation = determine_escalation_recommendation(total_score)
        
        # Step 6: Compute evidence hash
        evidence_hash = self._compute_evidence_hash(clusters)
        
        return TemporalClusteringOutput(
            reporting_person_cik=reporting_person_cik,
            issuer_cik=issuer_cik,
            analysis_period=analysis_period,
            clusters_detected=clusters,
            total_anomaly_score=total_score,
            escalation_recommendation=escalation,
            regulatory_citations=self._get_regulatory_citations(),
            evidence_hash=evidence_hash,
        )
    
    def _empty_output(self) -> TemporalClusteringOutput:
        """Return empty output for edge cases."""
        return TemporalClusteringOutput(
            reporting_person_cik="",
            issuer_cik="",
            analysis_period=(date.today(), date.today()),
            clusters_detected=[],
            total_anomaly_score=Decimal('0.0'),
            escalation_recommendation='NONE',
            regulatory_citations=[],
        )
    
    def _get_regulatory_citations(self) -> List[str]:
        """
        Get applicable regulatory citations for temporal clustering.
        
        Returns:
            List of statutory and regulatory references
        """
        return [
            "Securities Exchange Act of 1934, Section 16(a)",
            "SEC Release No. 34-46421 (August 27, 2002)",
            "17 CFR § 240.16a-3 (Form 4 Filing Requirements)",
            "Sarbanes-Oxley Act § 403 (Accelerated Filing Deadline)",
        ]
    
    def _compute_evidence_hash(self, clusters: List[TransactionCluster]) -> str:
        """
        Compute SHA-256 evidence hash for chain of custody.
        
        Creates tamper-evident hash of cluster evidence per FRE 902(13)/(14)
        requirements for electronic evidence authenticity.
        
        Args:
            clusters: List of detected clusters
        
        Returns:
            Hexadecimal SHA-256 hash of cluster evidence
        """
        if not clusters:
            return hashlib.sha256(b"").hexdigest()
        
        # Concatenate cluster identifiers and metadata
        evidence_content = []
        for cluster in sorted(clusters, key=lambda c: c.cluster_id):
            evidence_content.append(f"{cluster.cluster_id}")
            evidence_content.append(f"{cluster.start_date.isoformat()}")
            evidence_content.append(f"{cluster.end_date.isoformat()}")
            evidence_content.append(f"{len(cluster.transactions)}")
        
        evidence_str = "|".join(evidence_content)
        return hashlib.sha256(evidence_str.encode('utf-8')).hexdigest()


def calculate_temporal_distances(
    transactions: List[Transaction]
) -> Tuple[np.ndarray, List[Transaction]]:
    """
    Generate pairwise temporal distance matrix for all zero-dollar transactions.
    
    Per Section 5.3.1: Calculates the temporal distance (in days) between every
    pair of transactions to create a symmetric distance matrix suitable for
    DBSCAN clustering.
    
    Args:
        transactions: List of Transaction objects (should be zero-dollar only)
    
    Returns:
        Tuple of:
            - np.ndarray: Symmetric distance matrix where M[i][j] = days between i and j
            - List[Transaction]: Filtered zero-dollar transactions
    
    Example:
        >>> txn1 = Transaction(..., transaction_date=date(2020, 1, 1))
        >>> txn2 = Transaction(..., transaction_date=date(2020, 1, 2))
        >>> matrix, txns = calculate_temporal_distances([txn1, txn2])
        >>> matrix[0][1]  # Should be 1 day
        1.0
    """
    # Filter to zero-dollar transactions
    zero_dollar = [t for t in transactions if t.is_zero_dollar]
    
    n = len(zero_dollar)
    distance_matrix = np.zeros((n, n))
    
    # Calculate pairwise distances
    for i in range(n):
        for j in range(i + 1, n):
            delta = abs((zero_dollar[i].transaction_date - 
                        zero_dollar[j].transaction_date).days)
            distance_matrix[i][j] = delta
            distance_matrix[j][i] = delta  # Symmetric matrix
    
    return distance_matrix, zero_dollar


def get_issuer_historical_median(issuer_cik: str) -> Decimal:
    """
    Retrieve historical median transaction size for issuer.
    
    Used for Magnitude Concentration Score calculation in cluster scoring.
    Falls back to market-wide median if issuer-specific data unavailable.
    
    Args:
        issuer_cik: CIK of issuer company
    
    Returns:
        Decimal: Historical median transaction size (in shares)
    
    Note:
        Current implementation returns default fallback value.
        Future versions will query historical database or cache.
    """
    # TODO: Implement database/cache lookup for issuer-specific median
    # For now, return market-wide default
    return Decimal('10000')  # Default: 10,000 shares
