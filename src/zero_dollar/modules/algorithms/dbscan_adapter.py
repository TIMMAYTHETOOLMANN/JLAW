"""
DBSCAN Temporal Clustering Adapter
===================================

Density-based spatial clustering adapter for temporal transaction analysis.

Implements DBSCAN clustering algorithm (Section 5.3.2) to identify temporally
proximate transaction groups indicative of coordinated structuring.

Regulatory Basis:
    - Same-day clustering suggests deliberate fragmentation per SEC Release 34-46421
    - Multi-day clustering within eps_days suggests coordinated execution

Reference:
    - Section 5.3.2: DBSCAN Clustering Algorithm
"""

import hashlib
import numpy as np
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from sklearn.cluster import DBSCAN

from src.zero_dollar.models import Transaction, TransactionCluster


def detect_temporal_clusters(
    distance_matrix: np.ndarray,
    transactions: List[Transaction],
    eps_days: int = 1,
    min_samples: int = 2
) -> List[TransactionCluster]:
    """
    Apply density-based clustering to identify temporally proximate transaction groups.
    
    Uses DBSCAN (Density-Based Spatial Clustering of Applications with Noise)
    algorithm to detect clusters of transactions occurring within eps_days of
    each other, requiring at least min_samples transactions per cluster.
    
    Regulatory Basis:
        - Same-day clustering suggests deliberate fragmentation per SEC Release 34-46421
        - Multi-day clustering within eps_days suggests coordinated execution
    
    Args:
        distance_matrix: Symmetric pairwise temporal distance matrix (n x n)
                        where M[i][j] = days between transaction i and j
        transactions: List of Transaction objects corresponding to matrix indices
        eps_days: Maximum temporal distance (in days) between transactions in cluster.
                 Default 1 (same-day clustering)
        min_samples: Minimum number of transactions required to form a cluster.
                    Default 2 (pairs of transactions)
    
    Returns:
        List of TransactionCluster objects, one per detected cluster.
        Transactions labeled as noise (-1) are excluded from output.
    
    Example:
        >>> distance_matrix = np.array([[0, 0, 5], [0, 0, 5], [5, 5, 0]])
        >>> clusters = detect_temporal_clusters(distance_matrix, transactions, eps_days=1)
        >>> len(clusters)  # Two transactions within 1 day
        1
    """
    # Apply DBSCAN clustering with precomputed distance matrix
    clustering = DBSCAN(eps=eps_days, min_samples=min_samples, metric='precomputed')
    labels = clustering.fit_predict(distance_matrix)
    
    # Group transactions by cluster label, excluding noise (-1)
    cluster_dict: Dict[int, List[Transaction]] = {}
    for idx, label in enumerate(labels):
        if label != -1:  # Exclude noise points
            if label not in cluster_dict:
                cluster_dict[label] = []
            cluster_dict[label].append(transactions[idx])
    
    # Create TransactionCluster objects
    clusters = []
    for cluster_id, cluster_transactions in cluster_dict.items():
        if len(cluster_transactions) < min_samples:
            continue  # Skip clusters below minimum size
        
        # Extract cluster metadata
        dates = [t.transaction_date for t in cluster_transactions]
        start_date = min(dates)
        end_date = max(dates)
        
        # Calculate aggregate metrics
        total_shares = sum(abs(t.shares) for t in cluster_transactions)
        zero_dollar_count = sum(1 for t in cluster_transactions if t.is_zero_dollar)
        
        # Get reporting person info (should be same across cluster)
        reporting_person_cik = cluster_transactions[0].reporting_person_cik
        reporting_person_name = cluster_transactions[0].reporting_person_name
        
        # Generate cluster identifier
        cluster_hash = _generate_cluster_id(
            reporting_person_cik,
            start_date,
            end_date,
            len(cluster_transactions)
        )
        
        # Initial cluster score (will be refined by scoring module)
        cluster_score = 0.0
        
        cluster = TransactionCluster(
            cluster_id=cluster_hash,
            reporting_person_cik=reporting_person_cik,
            reporting_person_name=reporting_person_name,
            transactions=cluster_transactions,
            start_date=start_date,
            end_date=end_date,
            total_shares=total_shares,
            zero_dollar_count=zero_dollar_count,
            cluster_score=cluster_score,
            detection_timestamp=datetime.utcnow()
        )
        
        clusters.append(cluster)
    
    return clusters


def _generate_cluster_id(
    reporting_person_cik: str,
    start_date,
    end_date,
    transaction_count: int
) -> str:
    """
    Generate unique cluster identifier using SHA-256 hash.
    
    Creates deterministic cluster ID from key attributes for evidence tracking.
    
    Args:
        reporting_person_cik: CIK of reporting person
        start_date: Earliest transaction date in cluster
        end_date: Latest transaction date in cluster
        transaction_count: Number of transactions in cluster
    
    Returns:
        Hexadecimal SHA-256 hash (first 16 characters)
    """
    content = f"{reporting_person_cik}|{start_date.isoformat()}|{end_date.isoformat()}|{transaction_count}"
    hash_obj = hashlib.sha256(content.encode('utf-8'))
    return hash_obj.hexdigest()[:16]


class DBSCANClusteringAdapter:
    """
    Adapter class for DBSCAN clustering with configurable parameters.
    
    Provides object-oriented interface to DBSCAN clustering algorithm
    with default parameters optimized for temporal transaction analysis.
    
    Attributes:
        eps_days: Maximum temporal distance for cluster membership (default: 1)
        min_samples: Minimum transactions per cluster (default: 2)
    """
    
    def __init__(self, eps_days: int = 1, min_samples: int = 2):
        """
        Initialize DBSCAN clustering adapter.
        
        Args:
            eps_days: Maximum temporal distance (days) for cluster membership
            min_samples: Minimum number of transactions to form cluster
        """
        self.eps_days = eps_days
        self.min_samples = min_samples
    
    def cluster(
        self,
        distance_matrix: np.ndarray,
        transactions: List[Transaction]
    ) -> List[TransactionCluster]:
        """
        Perform DBSCAN clustering on transactions.
        
        Args:
            distance_matrix: Pairwise temporal distance matrix
            transactions: List of transactions to cluster
        
        Returns:
            List of detected TransactionCluster objects
        """
        return detect_temporal_clusters(
            distance_matrix,
            transactions,
            self.eps_days,
            self.min_samples
        )
