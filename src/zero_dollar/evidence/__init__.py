"""
Evidence Integrity & Chain of Custody Protocol
===============================================

Implements forensically defensible evidence integrity through:
- Cryptographic hashing (SHA-256)
- RFC 3161 trusted timestamping
- Merkle tree verification
- Chain of custody tracking

Compliance:
    - FRE 901(b)(9) - Electronic record authentication
    - NIST SP 800-107 - Secure Hash Standard
    - RFC 3161 - Time-Stamp Protocol
    - RFC 6962 - Certificate Transparency

Module Structure:
    - artifact.py: Evidence artifact creation and verification
    - merkle_chain.py: Merkle tree construction and proof generation
    - timestamp.py: RFC 3161 trusted timestamping
    - custody.py: Chain of custody tracking and export

Reference:
    JLAW Zero-Dollar Transaction Forensic Specification v1.0, Section 9
"""

from .artifact import (
    EvidenceArtifact,
    create_evidence_artifact,
    verify_artifact_integrity,
    verify_chain_link,
)
from .merkle_chain import (
    MerkleEvidenceChain,
    MerkleProof,
)
from .timestamp import (
    TrustedTimestamp,
    request_trusted_timestamp,
    verify_timestamp_token,
    TimestampError,
)
from .custody import (
    ChainOfCustodyRecord,
    VerificationEvent,
)

__all__ = [
    'EvidenceArtifact',
    'create_evidence_artifact',
    'verify_artifact_integrity',
    'verify_chain_link',
    'MerkleEvidenceChain',
    'MerkleProof',
    'TrustedTimestamp',
    'request_trusted_timestamp',
    'verify_timestamp_token',
    'TimestampError',
    'ChainOfCustodyRecord',
    'VerificationEvent',
]
