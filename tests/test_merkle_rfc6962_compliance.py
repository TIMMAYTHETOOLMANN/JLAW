"""
RFC 6962 Merkle Tree Compliance Tests
=====================================

Tests to validate that all Merkle tree implementations use RFC 6962 compliant
padding with EMPTY_LEAF_HASH sentinel instead of duplicating the last hash.

This prevents hash collision vulnerabilities and ensures court-admissible evidence.
"""

import hashlib
import pytest
from typing import List

from src.core.evidence_chain.merkle_tree import EMPTY_LEAF_HASH, MerkleTree
from src.core.evidence_chain.chain_validator import ChainValidator, MerkleTree as ValidatorMerkleTree
from src.reporting.evidence_packager import EvidencePackage


class TestRFC6962Compliance:
    """Test RFC 6962 compliance across all Merkle tree implementations."""
    
    def test_empty_leaf_hash_constant(self):
        """Verify EMPTY_LEAF_HASH is the SHA256 of empty string."""
        expected = hashlib.sha256(b'').hexdigest()
        assert EMPTY_LEAF_HASH == expected
        assert EMPTY_LEAF_HASH == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    
    def test_merkle_tree_odd_leaves_no_duplication(self):
        """Test that MerkleTree uses EMPTY_LEAF_HASH for odd-numbered leaves."""
        tree = MerkleTree()
        
        # Add odd number of leaves (3)
        hashes = [
            hashlib.sha256(b'leaf1').hexdigest(),
            hashlib.sha256(b'leaf2').hexdigest(),
            hashlib.sha256(b'leaf3').hexdigest(),
        ]
        
        tree.add_leaves(hashes)
        tree.build()
        
        # Manually compute expected root using EMPTY_LEAF_HASH padding
        # Note: MerkleTree._build_tree hashes leaves first, then builds tree
        # Level 0: hash the input hashes
        h0 = hashlib.sha256(hashes[0].encode()).hexdigest()
        h1 = hashlib.sha256(hashes[1].encode()).hexdigest()
        h2 = hashlib.sha256(hashes[2].encode()).hexdigest()
        
        # Level 1: pair hashed leaves
        h01 = hashlib.sha256((h0 + h1).encode()).hexdigest()
        h23 = hashlib.sha256((h2 + EMPTY_LEAF_HASH).encode()).hexdigest()
        
        # Level 2: root
        expected_root = hashlib.sha256((h01 + h23).encode()).hexdigest()
        
        actual_root = tree.get_root_hash()
        assert actual_root == expected_root
    
    def test_merkle_tree_no_duplicate_when_odd(self):
        """Verify that the last hash is NOT duplicated for odd-numbered lists."""
        tree = MerkleTree()
        
        # Single leaf
        single_hash = hashlib.sha256(b'single').hexdigest()
        tree.add_leaf(single_hash)
        tree.build()
        
        # For single leaf, root should be hash of the leaf
        assert tree.get_root_hash() == hashlib.sha256(single_hash.encode()).hexdigest()
        
        # Add two leaves to make it even
        tree2 = MerkleTree()
        hash1 = hashlib.sha256(b'leaf1').hexdigest()
        hash2 = hashlib.sha256(b'leaf2').hexdigest()
        tree2.add_leaves([hash1, hash2])
        tree2.build()
        
        # Even number should not use EMPTY_LEAF_HASH
        # Remember: MerkleTree hashes the inputs first
        h1 = hashlib.sha256(hash1.encode()).hexdigest()
        h2 = hashlib.sha256(hash2.encode()).hexdigest()
        expected = hashlib.sha256((h1 + h2).encode()).hexdigest()
        assert tree2.get_root_hash() == expected
    
    def test_evidence_packager_merkle_uses_empty_leaf_hash(self):
        """Test that EvidencePackage._compute_merkle_root uses EMPTY_LEAF_HASH."""
        from datetime import datetime
        from src.reporting.evidence_packager import EvidenceItem
        
        package = EvidencePackage(
            package_id="TEST-001",
            case_id="TEST",
            company_name="Test Corp",
            cik="123456"
        )
        
        # Add odd number of items (3)
        for i in range(3):
            item = EvidenceItem(
                item_id=f"EV-{i:03d}",
                item_type="test",
                description="Test item",
                source_url="https://example.com",
                source_document="Test",
                extraction_timestamp=datetime.utcnow(),
                content=f"Content {i}",
                content_type="text",
                filing_accession="ACC-001",
                filing_type="Test",
                filing_date="2019-01-01",
                document_section="Test"
            )
            package.add_item(item)
        
        # Get the hashes
        hashes = [item.content_hash for item in package.items]
        
        # Manually compute expected root with EMPTY_LEAF_HASH
        h01 = hashlib.sha256((hashes[0] + hashes[1]).encode()).hexdigest()
        h23 = hashlib.sha256((hashes[2] + EMPTY_LEAF_HASH).encode()).hexdigest()
        expected_root = hashlib.sha256((h01 + h23).encode()).hexdigest()
        
        # Verify package uses correct root
        assert package.merkle_root == expected_root
    
    def test_chain_validator_merkle_uses_empty_leaf_hash(self):
        """Test that ChainValidator uses EMPTY_LEAF_HASH for odd lists."""
        # Create odd number of hashes (5)
        hashes = [
            hashlib.sha256(f'hash{i}'.encode()).hexdigest()
            for i in range(5)
        ]
        
        # Build merkle tree using chain validator
        validator_tree = ValidatorMerkleTree(hashes)
        
        # Manually compute expected root with EMPTY_LEAF_HASH padding
        # Level 1: 5 hashes -> 3 parents (last one uses EMPTY_LEAF_HASH)
        level1 = []
        level1.append(hashlib.sha256((hashes[0] + hashes[1]).encode('utf-8')).hexdigest())
        level1.append(hashlib.sha256((hashes[2] + hashes[3]).encode('utf-8')).hexdigest())
        level1.append(hashlib.sha256((hashes[4] + EMPTY_LEAF_HASH).encode('utf-8')).hexdigest())
        
        # Level 2: 3 hashes -> 2 parents (last one uses EMPTY_LEAF_HASH)
        level2 = []
        level2.append(hashlib.sha256((level1[0] + level1[1]).encode('utf-8')).hexdigest())
        level2.append(hashlib.sha256((level1[2] + EMPTY_LEAF_HASH).encode('utf-8')).hexdigest())
        
        # Level 3: 2 hashes -> 1 root
        expected_root = hashlib.sha256((level2[0] + level2[1]).encode('utf-8')).hexdigest()
        
        assert validator_tree.root == expected_root
    
    def test_vulnerability_prevented_no_collision(self):
        """Test that EMPTY_LEAF_HASH prevents hash collision vulnerability."""
        # This test ensures that trees with different structures produce different roots
        
        # Tree 1: [A, B, C] with EMPTY_LEAF_HASH padding
        tree1 = MerkleTree()
        h1 = hashlib.sha256(b'A').hexdigest()
        h2 = hashlib.sha256(b'B').hexdigest()
        h3 = hashlib.sha256(b'C').hexdigest()
        tree1.add_leaves([h1, h2, h3])
        tree1.build()
        root1 = tree1.get_root_hash()
        
        # Tree 2: [A, B, C, C] - what would happen if we duplicated last hash
        tree2 = MerkleTree()
        tree2.add_leaves([h1, h2, h3, h3])
        tree2.build()
        root2 = tree2.get_root_hash()
        
        # These MUST be different (they would be the same with duplicate padding)
        assert root1 != root2, "Trees with different structures must have different roots"
    
    def test_single_leaf_special_case(self):
        """Test that single leaf trees are handled correctly."""
        tree = MerkleTree()
        single_hash = hashlib.sha256(b'single').hexdigest()
        tree.add_leaf(single_hash)
        tree.build()
        
        # Single leaf root should be hash of the leaf itself
        expected = hashlib.sha256(single_hash.encode()).hexdigest()
        assert tree.get_root_hash() == expected
    
    def test_empty_tree(self):
        """Test that empty trees are handled correctly."""
        tree = MerkleTree()
        tree.build()
        
        # Empty tree should have None root
        assert tree.get_root_hash() is None
    
    def test_large_odd_tree(self):
        """Test RFC 6962 compliance with larger odd-numbered tree."""
        tree = MerkleTree()
        
        # Create 7 leaves (odd)
        hashes = [hashlib.sha256(f'leaf{i}'.encode()).hexdigest() for i in range(7)]
        tree.add_leaves(hashes)
        tree.build()
        
        # Verify root is computed correctly
        root = tree.get_root_hash()
        assert root is not None
        assert len(root) == 64  # SHA-256 hex is 64 chars
        
        # Verify it's deterministic
        tree2 = MerkleTree()
        tree2.add_leaves(hashes)
        tree2.build()
        assert tree.get_root_hash() == tree2.get_root_hash()


class TestMerkleTreeIntegrity:
    """Test that Merkle trees maintain integrity and detect tampering."""
    
    def test_tamper_detection(self):
        """Test that modifying a leaf is detected."""
        tree = MerkleTree()
        
        original_hashes = [
            hashlib.sha256(b'leaf1').hexdigest(),
            hashlib.sha256(b'leaf2').hexdigest(),
            hashlib.sha256(b'leaf3').hexdigest(),
        ]
        
        tree.add_leaves(original_hashes)
        tree.build()
        original_root = tree.get_root_hash()
        
        # Build new tree with tampered leaf
        tampered_tree = MerkleTree()
        tampered_hashes = original_hashes.copy()
        tampered_hashes[1] = hashlib.sha256(b'TAMPERED').hexdigest()
        tampered_tree.add_leaves(tampered_hashes)
        tampered_tree.build()
        
        # Roots must be different
        assert original_root != tampered_tree.get_root_hash()
    
    def test_order_matters(self):
        """Test that leaf order affects the root."""
        tree1 = MerkleTree()
        tree2 = MerkleTree()
        
        hashes = [
            hashlib.sha256(b'A').hexdigest(),
            hashlib.sha256(b'B').hexdigest(),
            hashlib.sha256(b'C').hexdigest(),
        ]
        
        tree1.add_leaves(hashes)
        tree1.build()
        
        tree2.add_leaves([hashes[2], hashes[1], hashes[0]])  # Reversed
        tree2.build()
        
        # Different order should produce different root
        assert tree1.get_root_hash() != tree2.get_root_hash()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
