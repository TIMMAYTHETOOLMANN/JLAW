"""
Behavioral Assessment and Evidence Chain Models
================================================

Data structures for behavioral risk assessment and FRE 902(13)/(14) compliant
evidence chain tracking.

Reference:
- Section 8: Behavioral Pattern Scoring Engine
- Section 9: Evidence Integrity Protocol
- Section 11.4: Assessment Schema
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class BehavioralScoreComponents:
    """
    Component scores for behavioral risk assessment.
    
    Breaks down the total behavioral risk score into constituent factors
    per Section 8.2 of the specification.
    
    Attributes:
        magnitude_score: Score based on transaction size (0-25)
        frequency_score: Score based on transaction frequency (0-25)
        timing_score: Score based on event proximity timing (0-20)
        filing_compliance_score: Score based on late filing patterns (0-15)
            Note: Also referred to as 'price_variance_score' in specification
        entity_complexity_score: Score based on ownership structure (0-15)
        total_score: Sum of all component scores (0-100)
    """
    magnitude_score: float
    frequency_score: float
    timing_score: float
    filing_compliance_score: float
    entity_complexity_score: float
    
    @property
    def total_score(self) -> float:
        """Calculate total behavioral risk score."""
        return (
            self.magnitude_score +
            self.frequency_score +
            self.timing_score +
            self.filing_compliance_score +
            self.entity_complexity_score
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'magnitude_score': self.magnitude_score,
            'frequency_score': self.frequency_score,
            'timing_score': self.timing_score,
            'filing_compliance_score': self.filing_compliance_score,
            'entity_complexity_score': self.entity_complexity_score,
            'total_score': self.total_score,
        }


@dataclass
class BehavioralRiskAssessment:
    """
    Comprehensive behavioral risk assessment for reporting person.
    
    Aggregates multiple risk factors to produce prosecutorial priority
    ranking per Section 8 of the specification.
    
    Attributes:
        assessment_id: Unique assessment identifier
        reporting_person_cik: Subject CIK
        reporting_person_name: Subject name
        issuer_cik: Issuer CIK
        issuer_name: Issuer name
        assessment_date: When assessment was performed
        score_components: Breakdown of risk score components
        zero_dollar_transaction_count: Count of zero-dollar transactions
        total_transaction_count: Total transactions analyzed
        temporal_clusters_detected: Count of temporal clusters
        anomaly_flags: List of anomaly flag IDs
        prosecutorial_priority: Priority ranking (1-5, 1=highest)
        recommendation: Human-readable recommendation
        next_steps: Suggested investigation steps
    """
    assessment_id: str
    reporting_person_cik: str
    reporting_person_name: str
    issuer_cik: str
    issuer_name: str
    assessment_date: datetime
    score_components: BehavioralScoreComponents
    zero_dollar_transaction_count: int
    total_transaction_count: int
    temporal_clusters_detected: int
    anomaly_flags: List[str] = field(default_factory=list)
    prosecutorial_priority: int = 5
    recommendation: str = ""
    next_steps: List[str] = field(default_factory=list)
    
    @property
    def risk_score(self) -> float:
        """Total behavioral risk score."""
        return self.score_components.total_score
    
    @property
    def risk_level(self) -> str:
        """
        Classify risk level based on score.
        
        Per Section 8.3 of JLAW Zero-Dollar Transaction Forensic Specification:
        - CRITICAL: 80-100 (Immediate referral to SEC Enforcement Division)
        - HIGH: 60-79 (Enhanced investigation and documentation)
        - MODERATE: 40-59 (Continued monitoring and periodic review)
        - LOW: 0-39 (Routine surveillance)
        
        Returns:
            Risk level: CRITICAL, HIGH, MODERATE, or LOW
        """
        if self.risk_score >= 80:
            return "CRITICAL"
        elif self.risk_score >= 60:
            return "HIGH"
        elif self.risk_score >= 40:
            return "MODERATE"
        else:
            return "LOW"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'assessment_id': self.assessment_id,
            'reporting_person_cik': self.reporting_person_cik,
            'reporting_person_name': self.reporting_person_name,
            'issuer_cik': self.issuer_cik,
            'issuer_name': self.issuer_name,
            'assessment_date': self.assessment_date.isoformat(),
            'score_components': self.score_components.to_dict(),
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'zero_dollar_transaction_count': self.zero_dollar_transaction_count,
            'total_transaction_count': self.total_transaction_count,
            'temporal_clusters_detected': self.temporal_clusters_detected,
            'anomaly_flags': self.anomaly_flags,
            'prosecutorial_priority': self.prosecutorial_priority,
            'recommendation': self.recommendation,
            'next_steps': self.next_steps,
        }


@dataclass
class EvidenceArtifact:
    """
    Cryptographically verified evidence artifact.
    
    Represents a single piece of evidence with FRE 902(13)/(14) compliant
    integrity verification per Section 7.1.
    
    Attributes:
        artifact_id: Unique artifact identifier
        artifact_type: Type of evidence (form4_filing, sec_document, etc.)
        source_url: Original SEC EDGAR URL
        acquisition_timestamp: When artifact was acquired
        sha256_hash: Primary SHA-256 hash
        sha3_512_hash: Secondary SHA3-512 hash
        blake2b_hash: Tertiary BLAKE2b hash
        file_size_bytes: Size of artifact in bytes
        content_type: MIME type (text/html, application/pdf, etc.)
        related_transaction_accession: Accession number if applicable
        custody_chain_id: Chain of custody tracking ID
        merkle_root: Merkle tree root hash
        is_verified: Whether integrity has been verified
    """
    artifact_id: str
    artifact_type: str
    source_url: str
    acquisition_timestamp: datetime
    sha256_hash: str
    sha3_512_hash: str
    blake2b_hash: str
    file_size_bytes: int
    content_type: str
    related_transaction_accession: Optional[str] = None
    custody_chain_id: Optional[str] = None
    merkle_root: Optional[str] = None
    is_verified: bool = False
    
    def verify_integrity(self, computed_hashes: Dict[str, str]) -> bool:
        """
        Verify artifact integrity against computed hashes.
        
        Args:
            computed_hashes: Dict with 'sha256', 'sha3_512', 'blake2b' keys
            
        Returns:
            True if all three hashes match
        """
        return (
            self.sha256_hash == computed_hashes.get('sha256', '') and
            self.sha3_512_hash == computed_hashes.get('sha3_512', '') and
            self.blake2b_hash == computed_hashes.get('blake2b', '')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'artifact_id': self.artifact_id,
            'artifact_type': self.artifact_type,
            'source_url': self.source_url,
            'acquisition_timestamp': self.acquisition_timestamp.isoformat(),
            'sha256_hash': self.sha256_hash,
            'sha3_512_hash': self.sha3_512_hash,
            'blake2b_hash': self.blake2b_hash,
            'file_size_bytes': self.file_size_bytes,
            'content_type': self.content_type,
            'related_transaction_accession': self.related_transaction_accession,
            'custody_chain_id': self.custody_chain_id,
            'merkle_root': self.merkle_root,
            'is_verified': self.is_verified,
        }


@dataclass
class MerkleProof:
    """
    Merkle tree proof for evidence verification.
    
    RFC 6962 compliant Merkle proof for verifying artifact inclusion
    in evidence tree per Section 7.2.
    
    Attributes:
        proof_id: Unique proof identifier
        artifact_id: Evidence artifact being proven
        leaf_hash: Hash of the leaf node (artifact hash)
        merkle_root: Root hash of the tree
        proof_path: List of sibling hashes in proof path
        tree_depth: Depth of the Merkle tree
        leaf_index: Position of leaf in tree
        timestamp: When proof was generated
        is_valid: Whether proof has been validated
    """
    proof_id: str
    artifact_id: str
    leaf_hash: str
    merkle_root: str
    proof_path: List[str]
    tree_depth: int
    leaf_index: int
    timestamp: datetime
    is_valid: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'proof_id': self.proof_id,
            'artifact_id': self.artifact_id,
            'leaf_hash': self.leaf_hash,
            'merkle_root': self.merkle_root,
            'proof_path': self.proof_path,
            'tree_depth': self.tree_depth,
            'leaf_index': self.leaf_index,
            'timestamp': self.timestamp.isoformat(),
            'is_valid': self.is_valid,
        }


@dataclass
class TrustedTimestamp:
    """
    RFC 3161 trusted timestamp token.
    
    Provides cryptographic proof of document existence at specific time
    per Section 7.3.
    
    Attributes:
        timestamp_id: Unique timestamp identifier
        artifact_id: Evidence artifact being timestamped
        timestamp_token: Base64-encoded RFC 3161 token
        timestamp_authority: TSA URL or identifier
        timestamp_value: Timestamp date/time from TSA
        hash_algorithm: Algorithm used (SHA-256, SHA3-512, etc.)
        signature: Digital signature from TSA
        is_verified: Whether timestamp has been verified
    """
    timestamp_id: str
    artifact_id: str
    timestamp_token: str
    timestamp_authority: str
    timestamp_value: datetime
    hash_algorithm: str
    signature: str
    is_verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp_id': self.timestamp_id,
            'artifact_id': self.artifact_id,
            'timestamp_token': self.timestamp_token,
            'timestamp_authority': self.timestamp_authority,
            'timestamp_value': self.timestamp_value.isoformat(),
            'hash_algorithm': self.hash_algorithm,
            'signature': self.signature,
            'is_verified': self.is_verified,
        }


@dataclass
class ChainOfCustodyRecord:
    """
    Chain of custody event record.
    
    Documents every access and modification to evidence per Section 7.4.
    
    Attributes:
        record_id: Unique record identifier
        artifact_id: Evidence artifact accessed
        event_type: Type of event (acquisition, verification, access, etc.)
        actor: System component or user performing action
        timestamp: When event occurred
        action_description: Human-readable description
        pre_action_hash: Artifact hash before action
        post_action_hash: Artifact hash after action (if modified)
        location: Physical or logical location
        metadata: Additional event metadata
    """
    record_id: str
    artifact_id: str
    event_type: str
    actor: str
    timestamp: datetime
    action_description: str
    pre_action_hash: str
    post_action_hash: Optional[str] = None
    location: str = "JLAW_EVIDENCE_CHAIN"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'record_id': self.record_id,
            'artifact_id': self.artifact_id,
            'event_type': self.event_type,
            'actor': self.actor,
            'timestamp': self.timestamp.isoformat(),
            'action_description': self.action_description,
            'pre_action_hash': self.pre_action_hash,
            'post_action_hash': self.post_action_hash,
            'location': self.location,
            'metadata': self.metadata,
        }
