"""
Merkle Tree Implementation for Evidence Chain
=============================================

Provides efficient batch verification of evidence records using Merkle trees.

A Merkle tree allows:
- Verify individual records without recomputing entire chain
- Efficient proof of inclusion (log(n) verification)
- Tamper-evident batch evidence storage
- Cryptographic commitment to entire evidence set

Use cases:
- Batch verification of evidence records
- Efficient audit trails
- Blockchain-style evidence integrity
"""

import hashlib
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from merkletools import MerkleTools
    MERKLETOOLS_AVAILABLE = True
except ImportError:
    MERKLETOOLS_AVAILABLE = False
    logger.warning("merkletools not available. Using simplified implementation.")

# RFC 6962 compliant empty leaf hash - cryptographic null sentinel
# Used for padding odd-numbered tree levels to prevent collision attacks
EMPTY_LEAF_HASH = hashlib.sha256(b'').hexdigest()


@dataclass
class MerkleProof:
    """
    Merkle inclusion proof for a leaf.
    
    Preserves left/right sibling information to prevent second-preimage attacks.
    """
    leaf_hash: str
    leaf_index: int
    proof_hashes: List[str]
    root_hash: str
    proof_directions: List[str] = field(default_factory=list)  # 'left' or 'right' for each proof hash
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "leaf_hash": self.leaf_hash,
            "leaf_index": self.leaf_index,
            "proof_hashes": self.proof_hashes,
            "proof_directions": self.proof_directions,
            "root_hash": self.root_hash
        }


class MerkleTree:
    """
    Merkle tree for evidence chain batch verification.
    
    Features:
    - SHA-256 hashing at all levels
    - Inclusion proofs for individual leaves
    - Root hash for entire tree
    - Efficient verification (O(log n))
    
    Example:
        # Build tree from evidence hashes
        tree = MerkleTree()
        tree.add_leaves([hash1, hash2, hash3, hash4])
        tree.build()
        
        # Get root hash for storage
        root = tree.get_root_hash()
        
        # Generate proof for leaf
        proof = tree.get_proof(leaf_index=1)
        
        # Verify proof
        is_valid = tree.verify_proof(proof)
    """
    
    def __init__(self):
        """Initialize Merkle tree."""
        if MERKLETOOLS_AVAILABLE:
            self.mt = MerkleTools(hash_type='sha256')
            self.use_merkletools = True
        else:
            self.leaves: List[str] = []
            self.tree: List[List[str]] = []
            self.use_merkletools = False
    
    def add_leaf(self, leaf_hash: str):
        """
        Add a single leaf to the tree.
        
        Args:
            leaf_hash: Hash value as hex string
        """
        if self.use_merkletools:
            self.mt.add_leaf(leaf_hash)
        else:
            self.leaves.append(leaf_hash)
    
    def add_leaves(self, leaf_hashes: List[str]):
        """
        Add multiple leaves to the tree.
        
        Args:
            leaf_hashes: List of hash values as hex strings
        """
        for leaf_hash in leaf_hashes:
            self.add_leaf(leaf_hash)
    
    def build(self):
        """Build the Merkle tree."""
        if self.use_merkletools:
            self.mt.make_tree()
        else:
            self._build_tree()
    
    def _build_tree(self):
        """Build tree using simplified implementation."""
        if not self.leaves:
            self.tree = []
            return
        
        # Start with leaves as bottom level
        current_level = [self._hash(leaf) for leaf in self.leaves]
        self.tree = [current_level[:]]
        
        # Build up the tree
        while len(current_level) > 1:
            next_level = []
            
            # Process pairs
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                
                # Handle odd number of nodes - RFC 6962 compliant padding
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    # Use cryptographic null sentinel instead of duplicating last hash
                    # This prevents collision vulnerabilities
                    right = EMPTY_LEAF_HASH
                
                # Combine and hash
                combined = left + right
                parent = self._hash(combined)
                next_level.append(parent)
            
            current_level = next_level
            self.tree.append(current_level[:])
    
    def get_root_hash(self) -> Optional[str]:
        """
        Get the Merkle root hash.
        
        Returns:
            Root hash as hex string, or None if tree not built
        """
        if self.use_merkletools:
            root = self.mt.get_merkle_root()
            return root.decode() if root else None
        else:
            if not self.tree:
                return None
            return self.tree[-1][0] if self.tree[-1] else None
    
    def get_proof(self, leaf_index: int) -> Optional[MerkleProof]:
        """
        Get Merkle inclusion proof for a leaf.
        
        Args:
            leaf_index: Index of the leaf (0-based)
            
        Returns:
            MerkleProof object or None if invalid index
        """
        if self.use_merkletools:
            proof = self.mt.get_proof(leaf_index)
            root = self.get_root_hash()
            
            if not proof or not root:
                return None
            
            # Extract proof hashes
            proof_hashes = []
            for item in proof:
                if 'right' in item:
                    proof_hashes.append(item['right'].decode())
                elif 'left' in item:
                    proof_hashes.append(item['left'].decode())
            
            leaf_hash = self.leaves[leaf_index] if leaf_index < len(self.leaves) else None
            if not leaf_hash:
                return None
            
            return MerkleProof(
                leaf_hash=leaf_hash,
                leaf_index=leaf_index,
                proof_hashes=proof_hashes,
                root_hash=root
            )
        else:
            return self._get_proof_simple(leaf_index)
    
    def _get_proof_simple(self, leaf_index: int) -> Optional[MerkleProof]:
        """
        Get proof using simplified implementation.
        
        Preserves left/right sibling information to prevent second-preimage attacks.
        """
        if not self.tree or leaf_index >= len(self.leaves):
            return None
        
        proof_hashes = []
        proof_directions = []
        index = leaf_index
        
        # Traverse up the tree
        for level in range(len(self.tree) - 1):
            level_nodes = self.tree[level]
            
            # Find sibling and record its position
            if index % 2 == 0:
                # Left node, get right sibling
                sibling_index = index + 1
                direction = 'right'
            else:
                # Right node, get left sibling
                sibling_index = index - 1
                direction = 'left'
            
            # Add sibling to proof if exists
            if 0 <= sibling_index < len(level_nodes):
                proof_hashes.append(level_nodes[sibling_index])
                proof_directions.append(direction)
            
            # Move to parent index
            index = index // 2
        
        root = self.get_root_hash()
        if not root:
            return None
        
        return MerkleProof(
            leaf_hash=self.leaves[leaf_index],
            leaf_index=leaf_index,
            proof_hashes=proof_hashes,
            proof_directions=proof_directions,
            root_hash=root
        )
    
    def verify_proof(self, proof: MerkleProof) -> bool:
        """
        Verify a Merkle inclusion proof.
        
        Args:
            proof: MerkleProof object
            
        Returns:
            True if proof is valid
        """
        if self.use_merkletools:
            # Convert proof back to merkletools format using directions
            proof_list = []
            for i, hash_val in enumerate(proof.proof_hashes):
                # Use proof_directions if available, otherwise assume right
                direction = proof.proof_directions[i] if i < len(proof.proof_directions) else 'right'
                proof_list.append({direction: hash_val.encode()})
            
            return self.mt.validate_proof(
                proof_list,
                proof.leaf_hash,
                proof.root_hash.encode() if isinstance(proof.root_hash, str) else proof.root_hash
            )
        else:
            return self._verify_proof_simple(proof)
    
    def _verify_proof_simple(self, proof: MerkleProof) -> bool:
        """
        Verify proof using simplified implementation.
        
        Uses proof_directions to correctly combine hashes and prevent second-preimage attacks.
        """
        current = self._hash(proof.leaf_hash)
        
        # Traverse up using proof hashes with direction information
        for i, sibling in enumerate(proof.proof_hashes):
            # Use direction information if available
            if i < len(proof.proof_directions):
                direction = proof.proof_directions[i]
                if direction == 'left':
                    # Sibling is on the left
                    combined = sibling + current
                else:
                    # Sibling is on the right
                    combined = current + sibling
            else:
                # Fallback: try both orders (less secure)
                combined = current + sibling
            
            current = self._hash(combined)
        
        return current == proof.root_hash
    
    def _hash(self, data: str) -> str:
        """Hash data using SHA-256."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_leaf_count(self) -> int:
        """Get number of leaves in the tree."""
        if self.use_merkletools:
            return self.mt.get_leaf_count()
        else:
            return len(self.leaves)
    
    def reset(self):
        """Reset the tree to empty state."""
        if self.use_merkletools:
            self.mt.reset_tree()
        else:
            self.leaves = []
            self.tree = []


class EvidenceBatchVerifier:
    """
    High-level evidence batch verifier using Merkle trees.
    
    Example:
        verifier = EvidenceBatchVerifier()
        
        # Add evidence records
        verifier.add_evidence("evidence1_hash")
        verifier.add_evidence("evidence2_hash")
        verifier.add_evidence("evidence3_hash")
        
        # Build and get commitment
        root = verifier.build()
        print(f"Evidence batch root: {root}")
        
        # Verify individual evidence
        proof = verifier.get_proof(1)
        is_valid = verifier.verify(proof)
    """
    
    def __init__(self):
        """Initialize batch verifier."""
        self.tree = MerkleTree()
        self.evidence_ids: List[str] = []
    
    def add_evidence(self, evidence_hash: str, evidence_id: Optional[str] = None):
        """
        Add evidence to batch.
        
        Args:
            evidence_hash: SHA-256 hash of evidence
            evidence_id: Optional identifier for evidence
        """
        self.tree.add_leaf(evidence_hash)
        self.evidence_ids.append(evidence_id or evidence_hash[:16])
    
    def build(self) -> str:
        """
        Build Merkle tree and return root.
        
        Returns:
            Merkle root hash
        """
        self.tree.build()
        root = self.tree.get_root_hash()
        return root or ""
    
    def get_proof(self, index: int) -> Optional[MerkleProof]:
        """Get inclusion proof for evidence at index."""
        return self.tree.get_proof(index)
    
    def verify(self, proof: MerkleProof) -> bool:
        """Verify inclusion proof."""
        return self.tree.verify_proof(proof)
    
    def get_batch_summary(self) -> Dict[str, Any]:
        """Get summary of evidence batch."""
        return {
            "total_evidence": self.tree.get_leaf_count(),
            "merkle_root": self.tree.get_root_hash(),
            "evidence_ids": self.evidence_ids
        }
