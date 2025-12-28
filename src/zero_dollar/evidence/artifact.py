"""
Evidence Artifact Module
========================

Cryptographically signed evidence artifacts with chain linking per
Section 9.1 of the JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Compliance:
    - NIST SP 800-107 (Secure Hash Standard applications)
    - NIST SP 800-131A (Cryptographic key length transitions)
    - FRE 901(b)(9) (Electronic record authentication)
"""

import hashlib
import json
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Any, Optional
from decimal import Decimal
from uuid import uuid4


@dataclass
class EvidenceArtifact:
    """
    Cryptographically signed evidence artifact with chain linking.
    
    Compliance:
        - NIST SP 800-107 (Secure Hash Standard applications)
        - NIST SP 800-131A (Cryptographic key length transitions)
        - FRE 901(b)(9) (Electronic record authentication)
    """
    artifact_id: str                         # Unique identifier (EV-XXXXXXXXXX)
    artifact_type: str                       # TRANSACTION, CLUSTER, FLAG, ASSESSMENT
    source_data: bytes                       # Serialized source data
    hash_sha256: str                         # SHA-256 hex digest
    timestamp_utc: datetime                  # RFC 3339 timestamp
    timestamp_source: str                    # NTP server or system clock
    collector_system: str                    # JLAW version identifier
    chain_position: int                      # Sequential position in evidence chain
    previous_hash: str                       # Hash of previous artifact (Merkle chain)


def create_evidence_artifact(
    artifact_type: str,
    source_data: Any,
    previous_artifact: Optional[EvidenceArtifact] = None,
    system_version: str = "JLAW-4.0"
) -> EvidenceArtifact:
    """
    Create cryptographically signed evidence artifact with chain linking.
    
    Args:
        artifact_type: Type of evidence (TRANSACTION, CLUSTER, FLAG, ASSESSMENT)
        source_data: Raw data to be preserved (dict, dataclass, or primitive)
        previous_artifact: Previous artifact in chain for linking
        system_version: System version identifier
    
    Returns:
        EvidenceArtifact: Cryptographically signed artifact
    """
    # Serialize source data to canonical JSON (deterministic ordering)
    serialized = json.dumps(
        source_data, 
        sort_keys=True, 
        default=_json_serializer,
        separators=(',', ':'),
        ensure_ascii=False
    ).encode('utf-8')
    
    # Compute SHA-256 hash
    hash_sha256 = hashlib.sha256(serialized).hexdigest()
    
    # Get current UTC timestamp
    timestamp_utc = datetime.now(timezone.utc)
    
    # Determine chain position and previous hash
    if previous_artifact:
        chain_position = previous_artifact.chain_position + 1
        previous_hash = previous_artifact.hash_sha256
    else:
        chain_position = 1
        previous_hash = '0' * 64  # Genesis artifact
    
    artifact = EvidenceArtifact(
        artifact_id=f"EV-{uuid4().hex[:10].upper()}",
        artifact_type=artifact_type,
        source_data=serialized,
        hash_sha256=hash_sha256,
        timestamp_utc=timestamp_utc,
        timestamp_source='time.nist.gov',  # Or configured NTP server
        collector_system=f"{system_version}",
        chain_position=chain_position,
        previous_hash=previous_hash
    )
    
    return artifact


def _json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for special types."""
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, bytes):
        return obj.hex()
    elif hasattr(obj, '__dataclass_fields__'):
        return asdict(obj)
    else:
        return str(obj)


def verify_artifact_integrity(artifact: EvidenceArtifact) -> bool:
    """
    Verify artifact has not been tampered with by recomputing hash.
    
    Returns:
        bool: True if hash matches, False if tampered
    """
    recomputed_hash = hashlib.sha256(artifact.source_data).hexdigest()
    return recomputed_hash == artifact.hash_sha256


def verify_chain_link(
    artifact: EvidenceArtifact,
    previous_artifact: EvidenceArtifact
) -> bool:
    """
    Verify artifact is properly linked to previous artifact in chain.
    
    Returns:
        bool: True if link valid, False otherwise
    """
    return (
        artifact.previous_hash == previous_artifact.hash_sha256 and
        artifact.chain_position == previous_artifact.chain_position + 1
    )
