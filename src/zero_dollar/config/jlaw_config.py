"""
JLAW Configuration Module
=========================

Configuration dataclass for JLAW zero-dollar transaction forensic engine.

This module provides configuration options for:
- SEC EDGAR acquisition parameters
- Detection algorithm thresholds
- Evidence chain settings
- Output formatting options
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class JLAWConfig:
    """
    Configuration for JLAW forensic analysis engine.
    
    Attributes:
        sec_user_agent: SEC EDGAR User-Agent (required for API access)
        output_directory: Directory for dossier and evidence output
        enable_caching: Whether to cache SEC filings locally
        cache_directory: Directory for cached SEC filings
        rate_limit_requests_per_second: SEC API rate limit (max 10/sec)
        temporal_clustering_eps_days: DBSCAN epsilon parameter (days)
        temporal_clustering_min_samples: DBSCAN min_samples parameter
        event_proximity_window_days: Days window for event proximity detection
        ownership_chain_max_depth: Maximum depth for ownership chain traversal
        enable_evidence_chain: Whether to generate cryptographic evidence chain
        enable_merkle_tree: Whether to build RFC 6962 Merkle tree
        enable_rfc3161_timestamp: Whether to request RFC 3161 timestamps
        narrative_output_format: Output format ('markdown', 'pdf', 'json')
        parallel_execution: Whether to execute modules in parallel
        max_workers: Maximum parallel workers for module execution
    """
    # SEC EDGAR Configuration
    sec_user_agent: str = "JLAW-Forensics contact@example.com"
    
    # Output Configuration
    output_directory: Path = field(default_factory=lambda: Path("./output"))
    
    # Caching Configuration
    enable_caching: bool = True
    cache_directory: Path = field(default_factory=lambda: Path("./.cache/sec_filings"))
    
    # Rate Limiting
    rate_limit_requests_per_second: int = 9  # Conservative (SEC allows 10/sec)
    
    # Temporal Clustering Parameters
    temporal_clustering_eps_days: int = 7  # DBSCAN epsilon in days
    temporal_clustering_min_samples: int = 2  # Minimum transactions per cluster
    
    # Event Proximity Parameters
    event_proximity_window_days: int = 30  # Days before/after material event
    
    # Ownership Chain Parameters
    ownership_chain_max_depth: int = 5  # Maximum traversal depth
    
    # Evidence Chain Configuration
    enable_evidence_chain: bool = True
    enable_merkle_tree: bool = True
    enable_rfc3161_timestamp: bool = False  # Requires TSA configuration
    
    # Narrative Generation
    narrative_output_format: str = "markdown"  # 'markdown', 'pdf', 'json'
    
    # Parallel Execution
    parallel_execution: bool = True
    max_workers: int = 3  # Temporal, Event, Ownership in parallel
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure paths are Path objects
        if isinstance(self.output_directory, str):
            self.output_directory = Path(self.output_directory)
        if isinstance(self.cache_directory, str):
            self.cache_directory = Path(self.cache_directory)
        
        # Validate rate limit
        if self.rate_limit_requests_per_second > 10:
            raise ValueError("SEC EDGAR rate limit cannot exceed 10 requests/second")
        
        # Validate output format
        valid_formats = {'markdown', 'pdf', 'json'}
        if self.narrative_output_format not in valid_formats:
            raise ValueError(f"Invalid output format: {self.narrative_output_format}. Must be one of {valid_formats}")
        
        # Create directories if they don't exist
        self.output_directory.mkdir(parents=True, exist_ok=True)
        if self.enable_caching:
            self.cache_directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'sec_user_agent': self.sec_user_agent,
            'output_directory': str(self.output_directory),
            'enable_caching': self.enable_caching,
            'cache_directory': str(self.cache_directory),
            'rate_limit_requests_per_second': self.rate_limit_requests_per_second,
            'temporal_clustering_eps_days': self.temporal_clustering_eps_days,
            'temporal_clustering_min_samples': self.temporal_clustering_min_samples,
            'event_proximity_window_days': self.event_proximity_window_days,
            'ownership_chain_max_depth': self.ownership_chain_max_depth,
            'enable_evidence_chain': self.enable_evidence_chain,
            'enable_merkle_tree': self.enable_merkle_tree,
            'enable_rfc3161_timestamp': self.enable_rfc3161_timestamp,
            'narrative_output_format': self.narrative_output_format,
            'parallel_execution': self.parallel_execution,
            'max_workers': self.max_workers,
        }
