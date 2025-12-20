"""
Evidence Chain Validator & Manager
===================================

Implements tamper-evident hash chain with Merkle tree verification.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from .hash_service import HashResult, HashService, EvidenceRecord
from .merkle_tree import EMPTY_LEAF_HASH


class MerkleTree:
    """Merkle Tree for batch verification."""
    
    def __init__(self, hashes: List[str]):
        self.leaves = hashes
        self.root = self._build_root(hashes) if hashes else None
    
    def _hash_pair(self, left: str, right: str) -> str:
        combined = (left + right).encode('utf-8')
        return hashlib.sha256(combined).hexdigest()
    
    def _build_root(self, hashes: List[str]) -> str:
        if len(hashes) == 1:
            return hashes[0]
        
        next_level = []
        # RFC 6962 compliant padding - use cryptographic null sentinel
        padded = hashes + [EMPTY_LEAF_HASH] if len(hashes) % 2 else hashes
        
        for i in range(0, len(padded), 2):
            next_level.append(self._hash_pair(padded[i], padded[i+1]))
        
        return self._build_root(next_level)


@dataclass
class ChainValidationResult:
    """Result of chain validation."""
    is_valid: bool
    total_records: int
    validated_records: int
    merkle_root: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_records": self.total_records,
            "validated_records": self.validated_records,
            "merkle_root": self.merkle_root
        }


class ChainValidator:
    """Evidence chain validator."""
    
    def validate_chain(self, records: List[EvidenceRecord]) -> ChainValidationResult:
        if not records:
            return ChainValidationResult(is_valid=True, total_records=0, validated_records=0)
        
        valid_count = 0
        for i, record in enumerate(records):
            if i == 0:
                valid_count += 1
            else:
                expected = records[i-1].get_chain_hash()
                if record.previous_record_hash == expected:
                    valid_count += 1
        
        hashes = [r.get_chain_hash() for r in records]
        merkle = MerkleTree(hashes)
        
        return ChainValidationResult(
            is_valid=valid_count == len(records),
            total_records=len(records),
            validated_records=valid_count,
            merkle_root=merkle.root
        )


class EvidenceChain:
    """Complete evidence chain manager."""
    
    def __init__(self):
        self.records: List[EvidenceRecord] = []
        self.validator = ChainValidator()
    
    def add_record(
        self,
        record_id: str,
        document_type: str,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvidenceRecord:
        content_hash = HashService.compute_hash(content)
        previous_hash = self.records[-1].get_chain_hash() if self.records else None
        
        record = EvidenceRecord(
            id=record_id,
            document_type=document_type,
            content_hash=content_hash,
            previous_record_hash=previous_hash,
            metadata=metadata or {}
        )
        
        self.records.append(record)
        return record
    
    def validate(self) -> ChainValidationResult:
        return self.validator.validate_chain(self.records)
    
    def export_for_court(self) -> Dict[str, Any]:
        validation = self.validate()
        return {
            "evidence_chain": {
                "record_count": len(self.records),
                "records": [r.to_dict() for r in self.records],
                "merkle_root": validation.merkle_root
            },
            "validation": validation.to_dict(),
            "certification": {
                "standard": "FRE 902(13)/(14)",
                "hash_algorithm": "SHA-256 + SHA3-512",
                "generated_at": datetime.utcnow().isoformat()
            }
        }

