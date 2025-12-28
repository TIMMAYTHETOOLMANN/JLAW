"""
Chain of Custody Record Module
===============================

Complete chain of custody tracking for evidence packages per
Section 9.4 of the JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Implements:
    - Verification event logging
    - Comprehensive integrity verification
    - ZIP export for court submission
"""

import json
import zipfile
from io import BytesIO
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import List, Optional

from .artifact import EvidenceArtifact, verify_artifact_integrity, verify_chain_link
from .merkle_chain import MerkleEvidenceChain
from .timestamp import TrustedTimestamp


@dataclass
class VerificationEvent:
    """Single verification event in custody log."""
    timestamp: datetime
    verifier: str
    verification_type: str  # HASH, CHAIN_LINK, MERKLE_PROOF, TIMESTAMP
    result: str  # VERIFIED, FAILED
    details: str


@dataclass
class ChainOfCustodyRecord:
    """Complete chain of custody record for evidence package."""
    case_id: str
    created_utc: datetime
    created_by: str
    evidence_artifacts: List[EvidenceArtifact]
    merkle_chain: MerkleEvidenceChain
    trusted_timestamps: List[TrustedTimestamp]
    integrity_status: str  # VERIFIED, COMPROMISED, PENDING
    last_verified_utc: datetime
    verification_log: List[VerificationEvent] = field(default_factory=list)
    
    def add_verification_event(
        self,
        verifier: str,
        verification_type: str,
        result: str,
        details: str
    ) -> None:
        """Add verification event to log."""
        event = VerificationEvent(
            timestamp=datetime.now(timezone.utc),
            verifier=verifier,
            verification_type=verification_type,
            result=result,
            details=details
        )
        self.verification_log.append(event)
        self.last_verified_utc = event.timestamp
    
    def verify_integrity(self) -> bool:
        """
        Verify complete integrity of evidence package.
        
        Checks:
        1. All artifact hashes valid
        2. All chain links valid
        3. Merkle root matches
        4. Timestamps valid
        """
        all_valid = True
        
        # Verify artifact hashes
        for artifact in self.evidence_artifacts:
            if not verify_artifact_integrity(artifact):
                self.add_verification_event(
                    verifier='SYSTEM',
                    verification_type='HASH',
                    result='FAILED',
                    details=f"Artifact {artifact.artifact_id} hash mismatch"
                )
                all_valid = False
        
        # Verify chain links
        for i in range(1, len(self.evidence_artifacts)):
            if not verify_chain_link(self.evidence_artifacts[i], self.evidence_artifacts[i-1]):
                self.add_verification_event(
                    verifier='SYSTEM',
                    verification_type='CHAIN_LINK',
                    result='FAILED',
                    details=f"Chain link broken at position {i}"
                )
                all_valid = False
        
        # Verify Merkle root
        if self.merkle_chain.root_hash:
            for i, artifact in enumerate(self.evidence_artifacts):
                proof = self.merkle_chain.get_proof(i)
                if not self.merkle_chain.verify_proof(proof):
                    self.add_verification_event(
                        verifier='SYSTEM',
                        verification_type='MERKLE_PROOF',
                        result='FAILED',
                        details=f"Merkle proof failed for artifact {artifact.artifact_id}"
                    )
                    all_valid = False
        
        # Add final verification result
        self.integrity_status = 'VERIFIED' if all_valid else 'COMPROMISED'
        self.add_verification_event(
            verifier='SYSTEM',
            verification_type='FULL_INTEGRITY_CHECK',
            result='VERIFIED' if all_valid else 'FAILED',
            details=f"Complete integrity check: {len(self.evidence_artifacts)} artifacts, "
                   f"{len(self.merkle_chain.artifacts)} merkle nodes verified"
        )
        
        return all_valid
    
    def export_custody_package(self) -> bytes:
        """
        Export complete chain of custody for external verification or court submission.
        
        Format: ZIP archive containing:
            - custody_manifest.json (metadata and structure)
            - artifacts/ (individual artifact files)
            - merkle_proofs/ (inclusion proofs)
            - timestamps/ (RFC 3161 timestamp tokens)
            - verification_log.json (verification event log)
        """
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Manifest
            manifest = {
                'case_id': self.case_id,
                'created_utc': self.created_utc.isoformat(),
                'created_by': self.created_by,
                'artifact_count': len(self.evidence_artifacts),
                'merkle_root_hash': self.merkle_chain.root_hash,
                'integrity_status': self.integrity_status,
                'last_verified_utc': self.last_verified_utc.isoformat()
            }
            zf.writestr('custody_manifest.json', json.dumps(manifest, indent=2))
            
            # Individual artifacts
            for i, artifact in enumerate(self.evidence_artifacts):
                artifact_data = {
                    'artifact_id': artifact.artifact_id,
                    'artifact_type': artifact.artifact_type,
                    'hash_sha256': artifact.hash_sha256,
                    'timestamp_utc': artifact.timestamp_utc.isoformat(),
                    'chain_position': artifact.chain_position,
                    'previous_hash': artifact.previous_hash,
                    'source_data_hex': artifact.source_data.hex()
                }
                zf.writestr(f'artifacts/{artifact.artifact_id}.json', json.dumps(artifact_data, indent=2))
            
            # Merkle proofs
            for i in range(len(self.evidence_artifacts)):
                proof = self.merkle_chain.get_proof(i)
                proof_data = {
                    'artifact_hash': proof.artifact_hash,
                    'proof_hashes': proof.proof_hashes,
                    'proof_directions': proof.proof_directions,
                    'root_hash': proof.root_hash
                }
                zf.writestr(f'merkle_proofs/proof_{i}.json', json.dumps(proof_data, indent=2))
            
            # Timestamps
            for i, ts in enumerate(self.trusted_timestamps):
                ts_data = {
                    'hash_timestamped': ts.hash_timestamped,
                    'timestamp_utc': ts.timestamp_utc.isoformat(),
                    'tsa_certificate': ts.tsa_certificate,
                    'timestamp_token': ts.timestamp_token,
                    'verification_url': ts.verification_url
                }
                zf.writestr(f'timestamps/timestamp_{i}.json', json.dumps(ts_data, indent=2))
            
            # Verification log
            log_data = {
                'events': [
                    {
                        'timestamp': e.timestamp.isoformat(),
                        'verifier': e.verifier,
                        'verification_type': e.verification_type,
                        'result': e.result,
                        'details': e.details
                    }
                    for e in self.verification_log
                ]
            }
            zf.writestr('verification_log.json', json.dumps(log_data, indent=2))
        
        return zip_buffer.getvalue()
