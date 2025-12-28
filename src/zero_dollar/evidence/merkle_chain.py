"""
Merkle Tree Evidence Chain Module
==================================

Construct Merkle tree from evidence artifacts for aggregate integrity verification
per Section 9.3 of the JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Properties:
    - Root hash represents entire evidence corpus
    - Any tampering detectable via hash mismatch
    - Efficient O(log n) proof of inclusion for any artifact
"""

import hashlib
from typing import List, Optional
from dataclasses import dataclass

from .artifact import EvidenceArtifact


@dataclass
class MerkleProof:
    """Merkle inclusion proof for artifact."""
    artifact_hash: str
    proof_hashes: List[str]
    proof_directions: List[str]  # 'L' or 'R'
    root_hash: str


class MerkleEvidenceChain:
    """
    Construct Merkle tree from evidence artifacts for aggregate integrity verification.
    
    Properties:
        - Root hash represents entire evidence corpus
        - Any tampering detectable via hash mismatch
        - Efficient O(log n) proof of inclusion for any artifact
    """
    
    def __init__(self):
        self.artifacts: List[EvidenceArtifact] = []
        self.tree: List[List[str]] = []
        self.root_hash: Optional[str] = None
    
    def add_artifact(self, artifact: EvidenceArtifact) -> None:
        """Add artifact to chain and rebuild Merkle tree."""
        self.artifacts.append(artifact)
        self._rebuild_tree()
    
    def _rebuild_tree(self) -> None:
        """Rebuild Merkle tree from current artifacts."""
        if not self.artifacts:
            self.root_hash = None
            return
        
        # Leaf layer = artifact hashes
        current_layer = [a.hash_sha256 for a in self.artifacts]
        
        # Pad to power of 2 if necessary
        while len(current_layer) & (len(current_layer) - 1) != 0:
            current_layer.append(current_layer[-1])
        
        self.tree = [current_layer]
        
        # Build tree layers
        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                combined = current_layer[i] + current_layer[i + 1]
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_layer.append(parent_hash)
            current_layer = next_layer
            self.tree.append(current_layer)
        
        self.root_hash = current_layer[0]
    
    def get_proof(self, artifact_index: int) -> MerkleProof:
        """
        Generate Merkle proof for specific artifact.
        
        Args:
            artifact_index: Index of artifact in chain
        
        Returns:
            MerkleProof: Sibling hashes required to verify inclusion
        """
        if artifact_index < 0 or artifact_index >= len(self.artifacts):
            raise ValueError(f"Invalid artifact index: {artifact_index}")
        
        proof_hashes = []
        proof_directions = []
        
        index = artifact_index
        for layer in self.tree[:-1]:
            sibling_index = index ^ 1  # XOR to get sibling
            if sibling_index < len(layer):
                proof_hashes.append(layer[sibling_index])
                proof_directions.append('R' if index % 2 == 0 else 'L')
            index //= 2
        
        return MerkleProof(
            artifact_hash=self.artifacts[artifact_index].hash_sha256,
            proof_hashes=proof_hashes,
            proof_directions=proof_directions,
            root_hash=self.root_hash
        )
    
    def verify_proof(self, proof: MerkleProof) -> bool:
        """
        Verify Merkle proof for artifact inclusion.
        
        Args:
            proof: MerkleProof to verify
        
        Returns:
            bool: True if proof valid, False otherwise
        """
        current_hash = proof.artifact_hash
        
        for sibling_hash, direction in zip(proof.proof_hashes, proof.proof_directions):
            if direction == 'L':
                combined = sibling_hash + current_hash
            else:
                combined = current_hash + sibling_hash
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return current_hash == proof.root_hash
    
    def export_chain(self) -> dict:
        """Export complete chain for serialization."""
        return {
            'artifacts': [
                {
                    'artifact_id': a.artifact_id,
                    'artifact_type': a.artifact_type,
                    'hash_sha256': a.hash_sha256,
                    'timestamp_utc': a.timestamp_utc.isoformat(),
                    'chain_position': a.chain_position,
                    'previous_hash': a.previous_hash
                }
                for a in self.artifacts
            ],
            'root_hash': self.root_hash,
            'tree_depth': len(self.tree),
            'artifact_count': len(self.artifacts)
        }
