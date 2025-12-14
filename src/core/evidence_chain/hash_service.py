"""
Cryptographic Evidence Chain - Hash Service
============================================

Implements SHA-256 primary hashing with SHA3-512 secondary verification,
providing 128-bit collision resistance for prosecution-grade evidence chains.

Compliance: FRE 902(13)/(14), NIST SP 800-86, ISO/IEC 27037
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import base64


@dataclass
class HashResult:
    """Cryptographic hash result with triple-algorithm verification."""
    sha256: str
    sha3_512: str
    blake2b: str
    input_size: int
    computed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sha256": self.sha256,
            "sha3_512": self.sha3_512,
            "blake2b": self.blake2b,
            "input_size": self.input_size,
            "computed_at": self.computed_at.isoformat()
        }
    
    def verify(self, other: 'HashResult') -> bool:
        """Verify hash match with all three algorithms."""
        return (self.sha256 == other.sha256 and 
                self.sha3_512 == other.sha3_512 and
                self.blake2b == other.blake2b)


class HashService:
    """
    Prosecution-grade cryptographic hash service.
    
    Implements triple-algorithm hashing for evidence integrity:
    - SHA-256: Primary hash (NIST FIPS 180-4) - widely adopted, 128-bit collision resistance
    - SHA3-512: Secondary verification (NIST FIPS 202) - Keccak-based, quantum-resistant candidate
    - BLAKE2b: Tertiary verification - faster than SHA-3, used in cryptocurrencies
    
    This approach provides:
    - 128-bit collision resistance (SHA-256)
    - Algorithm diversity for long-term security
    - Court-accepted standards (widely adopted, peer-reviewed)
    - Future-proof against algorithm-specific attacks
    """
    
    @staticmethod
    def compute_hash(data: bytes) -> HashResult:
        """
        Compute triple-algorithm hash of binary data.
        
        Args:
            data: Raw bytes to hash
            
        Returns:
            HashResult with SHA-256, SHA3-512, and BLAKE2b hashes
        """
        sha256_hash = hashlib.sha256(data).hexdigest()
        sha3_512_hash = hashlib.sha3_512(data).hexdigest()
        blake2b_hash = hashlib.blake2b(data).hexdigest()
        
        return HashResult(
            sha256=sha256_hash,
            sha3_512=sha3_512_hash,
            blake2b=blake2b_hash,
            input_size=len(data)
        )
    
    @staticmethod
    def compute_hash_from_string(text: str, encoding: str = 'utf-8') -> HashResult:
        """Compute hash from string content."""
        return HashService.compute_hash(text.encode(encoding))
    
    @staticmethod
    def compute_hash_from_file(filepath: str) -> HashResult:
        """Compute hash from file contents."""
        with open(filepath, 'rb') as f:
            return HashService.compute_hash(f.read())
    
    @staticmethod
    def compute_hash_from_dict(data: Dict[str, Any]) -> HashResult:
        """Compute hash from dictionary (JSON-serialized)."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return HashService.compute_hash_from_string(json_str)
    
    @staticmethod
    def verify_integrity(data: bytes, expected_hash: HashResult) -> bool:
        """
        Verify data integrity against expected hash.
        
        Args:
            data: Data to verify
            expected_hash: Expected hash values
            
        Returns:
            True if both SHA-256 and SHA3-512 match
        """
        computed = HashService.compute_hash(data)
        return computed.verify(expected_hash)
    
    @staticmethod
    def create_chain_link(
        current_data: bytes,
        previous_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a hash chain link for evidence chain construction.
        
        Args:
            current_data: Current record data
            previous_hash: Hash of previous record (None for genesis)
            
        Returns:
            Chain link with current hash and previous reference
        """
        current_hash = HashService.compute_hash(current_data)
        
        return {
            "current_hash": current_hash.to_dict(),
            "previous_hash": previous_hash,
            "chain_position": 0 if previous_hash is None else -1,  # Set by chain
            "timestamp": datetime.utcnow().isoformat()
        }


@dataclass
class EvidenceRecord:
    """
    Prosecution-grade evidence record with cryptographic integrity.
    
    Implements the evidence chain specification from the blueprint:
    - Dual-algorithm hashing (SHA-256 + SHA3-512)
    - Chain linkage via previous record hash
    - Merkle root for batch verification
    - Violation flags for enforcement routing
    """
    id: str
    document_type: str  # 'Form4', 'DEF14A', '10K', '10Q', '8K', 'Schedule13D'
    content_hash: HashResult
    rfc3161_token: Optional[bytes] = None
    timestamp_authority: Optional[str] = None
    gen_time: Optional[datetime] = None
    previous_record_hash: Optional[str] = None
    merkle_root: Optional[str] = None
    violation_flags: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_type": self.document_type,
            "sha256_hash": self.content_hash.sha256,
            "sha3_512_hash": self.content_hash.sha3_512,
            "rfc3161_token": base64.b64encode(self.rfc3161_token).decode() if self.rfc3161_token else None,
            "timestamp_authority": self.timestamp_authority,
            "gen_time": self.gen_time.isoformat() if self.gen_time else None,
            "previous_record_hash": self.previous_record_hash,
            "merkle_root": self.merkle_root,
            "violation_flags": self.violation_flags,
            "metadata": self.metadata
        }
    
    def get_chain_hash(self) -> str:
        """Get the hash used for chain linkage (SHA-256)."""
        return self.content_hash.sha256

