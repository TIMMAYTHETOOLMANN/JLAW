"""
Phase 5 Security Hardening Tests
=================================

Comprehensive tests for security hardening and evidence chain integrity.

Test Categories:
1. Secrets Management Audit
2. Evidence Chain Integrity (FRE 902(13)/(14) compliance)
3. Triple-hash generation
4. Merkle tree edge cases
5. RFC 3161 timestamp validation
6. Chain of custody lifecycle
7. Tampering detection simulation

Compliance: FRE 902(13)/(14), NIST SP 800-86, RFC 6962
"""

import hashlib
import asyncio
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


class TestTripleHashEvidenceGeneration:
    """
    Test Suite: Triple-hash evidence generation.
    
    Verifies evidence objects are hashed with SHA-256, SHA3-512, and BLAKE2b.
    Covers all algorithm variants and expected outputs.
    """
    
    def test_hash_service_computes_sha256(self):
        """Test SHA-256 hash generation."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = b"test evidence data for hashing"
        result = HashService.compute_hash(data)
        
        # Verify SHA-256 is computed correctly
        expected_sha256 = hashlib.sha256(data).hexdigest()
        assert result.sha256 == expected_sha256
        assert len(result.sha256) == 64  # SHA-256 produces 64 hex chars
    
    def test_hash_service_computes_sha3_512(self):
        """Test SHA3-512 hash generation."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = b"test evidence data for hashing"
        result = HashService.compute_hash(data)
        
        # Verify SHA3-512 is computed correctly
        expected_sha3_512 = hashlib.sha3_512(data).hexdigest()
        assert result.sha3_512 == expected_sha3_512
        assert len(result.sha3_512) == 128  # SHA3-512 produces 128 hex chars
    
    def test_hash_service_computes_blake2b(self):
        """Test BLAKE2b hash generation."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = b"test evidence data for hashing"
        result = HashService.compute_hash(data)
        
        # Verify BLAKE2b is computed correctly
        expected_blake2b = hashlib.blake2b(data).hexdigest()
        assert result.blake2b == expected_blake2b
        assert len(result.blake2b) == 128  # BLAKE2b default produces 128 hex chars
    
    def test_triple_hash_all_different(self):
        """Test that all three hashes are different."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = b"sample data"
        result = HashService.compute_hash(data)
        
        # All hashes should be different
        assert result.sha256 != result.sha3_512
        assert result.sha256 != result.blake2b
        assert result.sha3_512 != result.blake2b
    
    def test_triple_hash_deterministic(self):
        """Test that triple-hash is deterministic."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = b"deterministic test data"
        
        result1 = HashService.compute_hash(data)
        result2 = HashService.compute_hash(data)
        
        assert result1.sha256 == result2.sha256
        assert result1.sha3_512 == result2.sha3_512
        assert result1.blake2b == result2.blake2b
    
    def test_triple_hash_from_string(self):
        """Test triple-hash from string input."""
        from src.core.evidence_chain.hash_service import HashService
        
        text = "String evidence content"
        result = HashService.compute_hash_from_string(text)
        
        assert result.sha256 is not None
        assert result.sha3_512 is not None
        assert result.blake2b is not None
    
    def test_triple_hash_from_dict(self):
        """Test triple-hash from dictionary (JSON-serialized)."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = {
            "violation_id": "V-001",
            "type": "LATE_FORM4",
            "amount": 50000.0
        }
        result = HashService.compute_hash_from_dict(data)
        
        # Should produce consistent hashes
        result2 = HashService.compute_hash_from_dict(data)
        assert result.sha256 == result2.sha256
    
    def test_triple_hash_empty_data(self):
        """Test triple-hash of empty data."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = b""
        result = HashService.compute_hash(data)
        
        # Should still produce valid hashes
        assert result.sha256 == hashlib.sha256(b"").hexdigest()
        assert result.sha3_512 == hashlib.sha3_512(b"").hexdigest()
        assert result.blake2b == hashlib.blake2b(b"").hexdigest()
    
    def test_hash_result_to_dict(self):
        """Test HashResult serialization."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = b"test data"
        result = HashService.compute_hash(data)
        
        result_dict = result.to_dict()
        
        assert "sha256" in result_dict
        assert "sha3_512" in result_dict
        assert "blake2b" in result_dict
        assert "input_size" in result_dict
        assert result_dict["input_size"] == len(data)
    
    def test_hash_result_verify(self):
        """Test HashResult verification."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = b"test data"
        result1 = HashService.compute_hash(data)
        result2 = HashService.compute_hash(data)
        
        assert result1.verify(result2)
        
        # Different data should fail verification
        result3 = HashService.compute_hash(b"different data")
        assert not result1.verify(result3)
    
    def test_verify_integrity_success(self):
        """Test successful integrity verification."""
        from src.core.evidence_chain.hash_service import HashService
        
        data = b"original evidence data"
        expected_hash = HashService.compute_hash(data)
        
        assert HashService.verify_integrity(data, expected_hash)
    
    def test_verify_integrity_failure(self):
        """Test failed integrity verification (tampering detected)."""
        from src.core.evidence_chain.hash_service import HashService
        
        original_data = b"original evidence data"
        expected_hash = HashService.compute_hash(original_data)
        
        # Simulate tampering
        tampered_data = b"modified evidence data"
        
        assert not HashService.verify_integrity(tampered_data, expected_hash)


class TestMerkleTreeEdgeCases:
    """
    Test Suite: Merkle tree construction with odd-leaf edge cases.
    
    Ensures RFC 6962 compliance for odd/even leaf node scenarios.
    """
    
    def test_single_leaf(self):
        """Test Merkle tree with single leaf."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree = MerkleTree()
        tree.add_leaf("single_hash_value")
        tree.build()
        
        root = tree.get_root_hash()
        assert root is not None
        # Single leaf root should be hash of the leaf
        expected = hashlib.sha256("single_hash_value".encode()).hexdigest()
        assert root == expected
    
    def test_two_leaves(self):
        """Test Merkle tree with two leaves (even)."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree = MerkleTree()
        tree.add_leaves(["hash1", "hash2"])
        tree.build()
        
        root = tree.get_root_hash()
        assert root is not None
    
    def test_three_leaves_odd(self):
        """Test Merkle tree with three leaves (odd - uses EMPTY_LEAF_HASH)."""
        from src.core.evidence_chain.merkle_tree import MerkleTree, EMPTY_LEAF_HASH
        
        tree = MerkleTree()
        hashes = ["hash1", "hash2", "hash3"]
        tree.add_leaves(hashes)
        tree.build()
        
        root = tree.get_root_hash()
        assert root is not None
        
        # Manually compute expected root with EMPTY_LEAF_HASH
        h0 = hashlib.sha256("hash1".encode()).hexdigest()
        h1 = hashlib.sha256("hash2".encode()).hexdigest()
        h2 = hashlib.sha256("hash3".encode()).hexdigest()
        
        h01 = hashlib.sha256((h0 + h1).encode()).hexdigest()
        h23 = hashlib.sha256((h2 + EMPTY_LEAF_HASH).encode()).hexdigest()
        
        expected_root = hashlib.sha256((h01 + h23).encode()).hexdigest()
        assert root == expected_root
    
    def test_five_leaves_odd(self):
        """Test Merkle tree with five leaves (odd)."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree = MerkleTree()
        hashes = [hashlib.sha256(f"leaf{i}".encode()).hexdigest() for i in range(5)]
        tree.add_leaves(hashes)
        tree.build()
        
        root = tree.get_root_hash()
        assert root is not None
        assert len(root) == 64  # SHA-256 hex length
    
    def test_seven_leaves_odd(self):
        """Test Merkle tree with seven leaves (odd)."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree = MerkleTree()
        hashes = [hashlib.sha256(f"evidence{i}".encode()).hexdigest() for i in range(7)]
        tree.add_leaves(hashes)
        tree.build()
        
        root = tree.get_root_hash()
        assert root is not None
    
    def test_empty_tree(self):
        """Test empty Merkle tree."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree = MerkleTree()
        tree.build()
        
        root = tree.get_root_hash()
        assert root is None
    
    def test_empty_leaf_hash_constant(self):
        """Test EMPTY_LEAF_HASH is correct SHA-256 of empty string."""
        from src.core.evidence_chain.merkle_tree import EMPTY_LEAF_HASH
        
        expected = hashlib.sha256(b"").hexdigest()
        assert EMPTY_LEAF_HASH == expected
    
    def test_proof_generation_even_leaves(self):
        """Test Merkle proof generation with even number of leaves."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree = MerkleTree()
        hashes = [hashlib.sha256(f"leaf{i}".encode()).hexdigest() for i in range(4)]
        tree.add_leaves(hashes)
        tree.build()
        
        proof = tree.get_proof(0)
        assert proof is not None
        assert proof.leaf_index == 0
    
    def test_proof_generation_odd_leaves(self):
        """Test Merkle proof generation with odd number of leaves."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree = MerkleTree()
        hashes = [hashlib.sha256(f"leaf{i}".encode()).hexdigest() for i in range(5)]
        tree.add_leaves(hashes)
        tree.build()
        
        proof = tree.get_proof(4)  # Last leaf
        assert proof is not None
        assert proof.leaf_index == 4
    
    def test_proof_verification(self):
        """Test Merkle proof verification."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree = MerkleTree()
        hashes = [hashlib.sha256(f"leaf{i}".encode()).hexdigest() for i in range(4)]
        tree.add_leaves(hashes)
        tree.build()
        
        for i in range(4):
            proof = tree.get_proof(i)
            if proof:
                assert tree.verify_proof(proof)
    
    def test_no_hash_duplication_vulnerability(self):
        """Test that odd leaves don't duplicate (RFC 6962 compliance)."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree1 = MerkleTree()
        tree1.add_leaves(["A", "B", "C"])  # 3 leaves (odd)
        tree1.build()
        
        tree2 = MerkleTree()
        tree2.add_leaves(["A", "B", "C", "C"])  # 4 leaves with C duplicated
        tree2.build()
        
        # Roots must be different (vulnerability if same)
        assert tree1.get_root_hash() != tree2.get_root_hash()
    
    def test_deterministic_roots(self):
        """Test that same leaves produce same root."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        hashes = [hashlib.sha256(f"leaf{i}".encode()).hexdigest() for i in range(5)]
        
        tree1 = MerkleTree()
        tree1.add_leaves(hashes)
        tree1.build()
        
        tree2 = MerkleTree()
        tree2.add_leaves(hashes)
        tree2.build()
        
        assert tree1.get_root_hash() == tree2.get_root_hash()
    
    def test_order_sensitive(self):
        """Test that leaf order affects root."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        hashes = [hashlib.sha256(f"leaf{i}".encode()).hexdigest() for i in range(3)]
        
        tree1 = MerkleTree()
        tree1.add_leaves(hashes)
        tree1.build()
        
        tree2 = MerkleTree()
        tree2.add_leaves(hashes[::-1])  # Reversed order
        tree2.build()
        
        assert tree1.get_root_hash() != tree2.get_root_hash()


class TestRFC3161TimestampValidation:
    """
    Test Suite: RFC 3161 timestamp token validation.
    
    Verifies timestamp tokens against trusted authorities and
    tests protocol compliance.
    """
    
    @pytest.fixture(autouse=True)
    def skip_if_no_aiohttp(self):
        """Skip tests if aiohttp is not available."""
        try:
            import aiohttp
        except ImportError:
            pytest.skip("aiohttp not installed - skipping RFC3161 tests")
    
    def test_rfc3161_client_initialization(self):
        """Test RFC3161Client can be initialized."""
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        client = RFC3161Client(authority="local")
        assert client.authority == "local"
    
    def test_authorities_available(self):
        """Test that multiple TSA authorities are available."""
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        assert "freetsa" in RFC3161Client.AUTHORITIES
        assert "digicert" in RFC3161Client.AUTHORITIES
        assert "sectigo" in RFC3161Client.AUTHORITIES
    
    def test_local_timestamp_creation(self):
        """Test local timestamp creation (for testing only)."""
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        data = b"test evidence data"
        token = RFC3161Client.create_local_timestamp(data)
        
        assert token is not None
        assert token.authority == "local"
        assert token.message_imprint == hashlib.sha256(data).hexdigest()
    
    def test_timestamp_token_verification(self):
        """Test timestamp token verifies against original data."""
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        data = b"evidence to timestamp"
        token = RFC3161Client.create_local_timestamp(data)
        
        assert RFC3161Client.verify_timestamp(token, data)
        
        # Should fail with different data
        assert not RFC3161Client.verify_timestamp(token, b"different data")
    
    def test_timestamp_token_dataclass(self):
        """Test TimestampToken has required fields."""
        from src.core.evidence_chain.rfc3161_client import TimestampToken
        import dataclasses
        
        assert dataclasses.is_dataclass(TimestampToken)
        
        fields = {f.name for f in dataclasses.fields(TimestampToken)}
        assert "token_data" in fields
        assert "gen_time" in fields
        assert "message_imprint" in fields
        assert "authority" in fields
    
    def test_timestamp_token_to_dict(self):
        """Test TimestampToken serialization."""
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        data = b"test data"
        token = RFC3161Client.create_local_timestamp(data)
        
        token_dict = token.to_dict()
        
        assert "gen_time" in token_dict
        assert "message_imprint" in token_dict
        assert "authority" in token_dict
    
    @pytest.mark.asyncio
    async def test_strict_mode_rejects_local(self):
        """Test that strict mode rejects local timestamps."""
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        client = RFC3161Client(authority="local")
        
        with pytest.raises(RuntimeError, match="NOT court-admissible"):
            await client.timestamp(b"test data")
    
    def test_local_timestamp_warning(self):
        """Test that local timestamps are marked appropriately."""
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        token = RFC3161Client.create_local_timestamp(b"test", "local")
        
        # Should be identifiable as local/non-court-admissible
        assert token.authority in ["local", "fallback_local"]


class TestChainOfCustodyLifecycle:
    """
    Test Suite: Chain of custody lifecycle testing.
    
    Tests complete custody chain workflows including creation,
    event recording, verification, and export.
    """
    
    def test_custody_chain_creation(self):
        """Test custody chain creation."""
        from src.core.custody.custody import ChainOfCustody, CustodyAction
        
        chain = ChainOfCustody(evidence_id="EV-001")
        
        assert chain.evidence_id == "EV-001"
        assert len(chain.entries) == 0
    
    def test_record_custody_action(self):
        """Test recording custody action."""
        from src.core.custody.custody import ChainOfCustody, CustodyAction
        
        chain = ChainOfCustody(evidence_id="EV-001")
        
        entry = chain.record_action(
            action=CustodyAction.RETRIEVED,
            custodian="System",
            evidence_hash="abc123"
        )
        
        assert entry is not None
        assert entry.action == CustodyAction.RETRIEVED
        assert len(chain.entries) == 1
    
    def test_multiple_custody_actions(self):
        """Test recording multiple custody actions."""
        from src.core.custody.custody import ChainOfCustody, CustodyAction
        
        chain = ChainOfCustody(evidence_id="EV-001")
        
        chain.record_action(CustodyAction.RETRIEVED, "Collector", "hash1")
        chain.record_action(CustodyAction.VERIFIED, "Verifier", "hash1")
        chain.record_action(CustodyAction.STORED, "Storage", "hash1")
        chain.record_action(CustodyAction.ANALYZED, "Analyst", "hash1")
        
        assert len(chain.entries) == 4
    
    def test_custody_entry_hashing(self):
        """Test custody entry hash computation."""
        from src.core.custody.custody import CustodyEntry, CustodyAction
        
        entry = CustodyEntry(
            custody_id="COC-001-0001",
            evidence_id="EV-001",
            custodian="Test User",
            action=CustodyAction.RETRIEVED,
            timestamp=datetime.utcnow(),
            hash_at_transfer="abc123"
        )
        
        entry_hash = entry.compute_hash()
        assert entry_hash is not None
        assert len(entry_hash) == 64  # SHA-256
    
    def test_custody_entry_deterministic(self):
        """Test custody entry hash is deterministic."""
        from src.core.custody.custody import CustodyEntry, CustodyAction
        
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        entry1 = CustodyEntry(
            custody_id="COC-001-0001",
            evidence_id="EV-001",
            custodian="Test User",
            action=CustodyAction.RETRIEVED,
            timestamp=timestamp,
            hash_at_transfer="abc123"
        )
        
        entry2 = CustodyEntry(
            custody_id="COC-001-0001",
            evidence_id="EV-001",
            custodian="Test User",
            action=CustodyAction.RETRIEVED,
            timestamp=timestamp,
            hash_at_transfer="abc123"
        )
        
        assert entry1.compute_hash() == entry2.compute_hash()
    
    def test_export_for_court(self):
        """Test custody chain export for court."""
        from src.core.custody.custody import ChainOfCustody, CustodyAction
        
        chain = ChainOfCustody(evidence_id="EV-001")
        chain.record_action(CustodyAction.RETRIEVED, "Collector", "hash1")
        chain.record_action(CustodyAction.VERIFIED, "Verifier", "hash1")
        
        export = chain.export_for_court()
        
        assert "evidence_id" in export
        assert "custody_chain" in export
        assert "certification" in export
        assert export["certification"]["standard"] == "FRE 902(13)/(14)"


class TestTamperingDetection:
    """
    Test Suite: Tampering detection simulation.
    
    Tests that evidence tampering is properly detected.
    """
    
    def test_detect_hash_tampering(self):
        """Test detection of hash tampering."""
        from src.core.evidence_chain.hash_service import HashService
        
        original_data = b"Original evidence content"
        original_hash = HashService.compute_hash(original_data)
        
        # Attempt to tamper with data
        tampered_data = b"Modified evidence content"
        
        # Verification should fail
        assert not HashService.verify_integrity(tampered_data, original_hash)
    
    def test_detect_merkle_tampering(self):
        """Test detection of Merkle tree tampering."""
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        # Build original tree
        original_hashes = ["hash1", "hash2", "hash3", "hash4"]
        tree1 = MerkleTree()
        tree1.add_leaves(original_hashes)
        tree1.build()
        original_root = tree1.get_root_hash()
        
        # Tamper with one leaf
        tampered_hashes = ["hash1", "TAMPERED", "hash3", "hash4"]
        tree2 = MerkleTree()
        tree2.add_leaves(tampered_hashes)
        tree2.build()
        tampered_root = tree2.get_root_hash()
        
        # Roots must be different (tampering detected)
        assert original_root != tampered_root
    
    def test_detect_subtle_tampering(self):
        """Test detection of subtle single-character tampering."""
        from src.core.evidence_chain.hash_service import HashService
        
        original = b"This is important evidence worth $1,000,000.00"
        original_hash = HashService.compute_hash(original)
        
        # Change just one character
        tampered = b"This is important evidence worth $1,000,000.01"
        
        assert not HashService.verify_integrity(tampered, original_hash)
    
    def test_detect_chain_link_tampering(self):
        """Test detection of chain link tampering."""
        from src.core.evidence_chain.chain_validator import EvidenceChain
        
        chain = EvidenceChain()
        
        # Add records
        chain.add_record("R-001", "Form4", b"Record 1 data")
        chain.add_record("R-002", "Form4", b"Record 2 data")
        chain.add_record("R-003", "Form4", b"Record 3 data")
        
        # Chain should be valid initially
        validation = chain.validate()
        assert validation.is_valid
        
        # Tamper with middle record's previous_record_hash
        chain.records[1].previous_record_hash = "FORGED_HASH"
        
        # Chain should now be invalid
        validation_after = chain.validate()
        assert not validation_after.is_valid


class TestFRE902Compliance:
    """
    Test Suite: FRE 902(13)/(14) compliance validation.
    
    Automated compliance checks for US Federal Rules of Evidence.
    """
    
    def test_fre_certification_generator(self):
        """Test FRE 902(14) certification generation."""
        from src.core.custody.custody import FRECertification
        
        cert = FRECertification(
            certifier_name="John Doe",
            certifier_title="Chief Forensic Analyst",
            organization="JLAW Forensics Inc."
        )
        
        certification_text = cert.generate_902_14_certification(
            evidence_id="EV-2024-001",
            hash_value="abc123def456"
        )
        
        assert "FRE" in certification_text or "FEDERAL RULES OF EVIDENCE" in certification_text.upper()
        assert "902(14)" in certification_text
        assert "EV-2024-001" in certification_text
        assert "John Doe" in certification_text
    
    def test_compliance_validator_triple_hash(self):
        """Test compliance validator for triple-hash."""
        from src.core.security_hardening import FREComplianceValidator
        from src.core.evidence_chain.hash_service import HashService
        
        data = b"evidence data"
        hash_result = HashService.compute_hash(data)
        
        is_valid, msg = FREComplianceValidator.validate_triple_hash(hash_result)
        assert is_valid
        assert "verified" in msg.lower()
    
    def test_compliance_validator_merkle(self):
        """Test compliance validator for Merkle tree."""
        from src.core.security_hardening import FREComplianceValidator
        from src.core.evidence_chain.merkle_tree import MerkleTree
        
        tree = MerkleTree()
        tree.add_leaves(["hash1", "hash2", "hash3"])
        tree.build()
        
        root = tree.get_root_hash()
        is_valid, msg = FREComplianceValidator.validate_merkle_tree(root, 3)
        
        assert is_valid
        assert "valid" in msg.lower()
    
    def test_compliance_validator_rejects_local_timestamp(self):
        """Test compliance validator rejects local timestamps."""
        from src.core.security_hardening import FREComplianceValidator
        
        try:
            from src.core.evidence_chain.rfc3161_client import RFC3161Client
            token = RFC3161Client.create_local_timestamp(b"data", "local")
        except ImportError:
            # Create a mock token if aiohttp not available
            from dataclasses import dataclass
            from datetime import datetime
            
            @dataclass
            class MockToken:
                token_data: bytes = b"mock"
                gen_time: datetime = None
                message_imprint: str = "abc123"
                authority: str = "local"
                
            token = MockToken(gen_time=datetime.utcnow())
        
        is_valid, msg = FREComplianceValidator.validate_timestamp_token(token)
        assert not is_valid
        assert "NOT court-admissible" in msg
    
    def test_compliance_validator_custody_chain(self):
        """Test compliance validator for chain of custody."""
        from src.core.security_hardening import FREComplianceValidator
        from src.core.custody.custody import ChainOfCustody, CustodyAction
        
        chain = ChainOfCustody(evidence_id="EV-001")
        chain.record_action(CustodyAction.RETRIEVED, "Collector", "hash1")
        
        is_valid, msg = FREComplianceValidator.validate_chain_of_custody(chain)
        assert is_valid
    
    def test_compliance_validator_empty_custody_fails(self):
        """Test compliance validator fails for empty custody chain."""
        from src.core.security_hardening import FREComplianceValidator
        from src.core.custody.custody import ChainOfCustody
        
        chain = ChainOfCustody(evidence_id="EV-001")
        # No entries recorded
        
        is_valid, msg = FREComplianceValidator.validate_chain_of_custody(chain)
        assert not is_valid


class TestSecretsManagement:
    """
    Test Suite: Secrets management audit.
    
    Tests secrets encryption, rotation, and scoping.
    """
    
    def test_secret_metadata_creation(self):
        """Test SecretMetadata creation."""
        from src.core.security_hardening import SecretMetadata, SecretType
        
        metadata = SecretMetadata(
            name="TEST_API_KEY",
            secret_type=SecretType.API_KEY,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=90),
            scopes=["read", "write"],
            description="Test API key"
        )
        
        assert metadata.name == "TEST_API_KEY"
        assert metadata.secret_type == SecretType.API_KEY
        assert not metadata.is_expired()
    
    def test_secret_expiration_check(self):
        """Test secret expiration detection."""
        from src.core.security_hardening import SecretMetadata, SecretType
        
        # Not expired
        active_secret = SecretMetadata(
            name="ACTIVE_KEY",
            secret_type=SecretType.API_KEY,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        assert not active_secret.is_expired()
        
        # Expired
        expired_secret = SecretMetadata(
            name="EXPIRED_KEY",
            secret_type=SecretType.API_KEY,
            created_at=datetime.utcnow() - timedelta(days=100),
            expires_at=datetime.utcnow() - timedelta(days=10)
        )
        assert expired_secret.is_expired()
    
    def test_secret_rotation_needed(self):
        """Test rotation schedule detection."""
        from src.core.security_hardening import SecretMetadata, SecretType
        
        # Needs rotation
        old_secret = SecretMetadata(
            name="OLD_KEY",
            secret_type=SecretType.API_KEY,
            created_at=datetime.utcnow() - timedelta(days=100),
            rotation_schedule_days=90
        )
        assert old_secret.needs_rotation()
        
        # Recently rotated
        fresh_secret = SecretMetadata(
            name="FRESH_KEY",
            secret_type=SecretType.API_KEY,
            created_at=datetime.utcnow() - timedelta(days=100),
            rotated_at=datetime.utcnow() - timedelta(days=10),
            rotation_schedule_days=90
        )
        assert not fresh_secret.needs_rotation()
    
    def test_api_key_scope_validator(self):
        """Test API key scope validation."""
        from src.core.security_hardening import APIKeyScopeValidator
        
        # Valid scopes
        is_valid, issues = APIKeyScopeValidator.validate_scope(
            "OPENAI_API_KEY",
            ["chat", "completions"]
        )
        assert is_valid
        assert len(issues) == 0
        
        # Prohibited scope
        is_valid, issues = APIKeyScopeValidator.validate_scope(
            "OPENAI_API_KEY",
            ["admin", "chat"]  # admin is prohibited
        )
        assert not is_valid
        assert len(issues) > 0
    
    def test_get_recommended_scopes(self):
        """Test getting recommended scopes for API keys."""
        from src.core.security_hardening import APIKeyScopeValidator
        
        scopes = APIKeyScopeValidator.get_recommended_scopes("OPENAI_API_KEY")
        assert "chat" in scopes or "completions" in scopes
    
    @pytest.mark.asyncio
    async def test_local_secrets_manager(self):
        """Test local encrypted secrets manager."""
        from src.core.security_hardening import LocalEncryptedSecretsManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LocalEncryptedSecretsManager(storage_path=Path(tmpdir))
            
            # Store a secret
            success = await manager.set_secret("TEST_SECRET", "secret_value_123")
            assert success
            
            # Retrieve the secret
            value = await manager.get_secret("TEST_SECRET")
            assert value == "secret_value_123"
            
            # Delete the secret
            success = await manager.delete_secret("TEST_SECRET")
            assert success
            
            # Should be gone
            value = await manager.get_secret("TEST_SECRET")
            assert value is None
    
    @pytest.mark.asyncio
    async def test_secret_rotation(self):
        """Test secret rotation."""
        from src.core.security_hardening import LocalEncryptedSecretsManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LocalEncryptedSecretsManager(storage_path=Path(tmpdir))
            
            # Store initial secret
            await manager.set_secret("ROTATING_SECRET", "old_value")
            
            # Rotate
            success = await manager.rotate_secret("ROTATING_SECRET", "new_value")
            assert success
            
            # Should have new value
            value = await manager.get_secret("ROTATING_SECRET")
            assert value == "new_value"
            
            # Metadata should show rotation timestamp
            metadata = await manager.get_metadata("ROTATING_SECRET")
            assert metadata.rotated_at is not None


class TestEnvironmentSecretsAudit:
    """
    Test Suite: Environment secrets auditing.
    """
    
    def test_auditor_initialization(self):
        """Test auditor initialization."""
        from src.core.security_hardening import EnvironmentSecretsAuditor
        
        auditor = EnvironmentSecretsAuditor(Path.cwd())
        assert auditor.project_root == Path.cwd()
    
    def test_audit_clean_file(self):
        """Test auditing a clean file."""
        from src.core.security_hardening import EnvironmentSecretsAuditor
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create clean file
            clean_file = tmpdir_path / "clean.py"
            clean_file.write_text("api_key = os.environ.get('API_KEY')")
            
            auditor = EnvironmentSecretsAuditor(tmpdir_path)
            findings = auditor.audit_file(clean_file)
            
            assert len(findings) == 0
    
    def test_generate_report(self):
        """Test audit report generation."""
        from src.core.security_hardening import EnvironmentSecretsAuditor
        
        auditor = EnvironmentSecretsAuditor(Path.cwd())
        report = auditor.generate_report()
        
        assert "audit_timestamp" in report
        assert "summary" in report
        assert "file_findings" in report
        assert "environment_findings" in report


class TestExpirationMonitoring:
    """
    Test Suite: API key expiration monitoring.
    """
    
    @pytest.mark.asyncio
    async def test_expiration_alert_generation(self):
        """Test expiration alert generation."""
        from src.core.security_hardening import (
            SecretRotationScheduler,
            LocalEncryptedSecretsManager,
            SecretMetadata,
            SecretType
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LocalEncryptedSecretsManager(storage_path=Path(tmpdir))
            
            # Add a secret that expires soon
            expiring_metadata = SecretMetadata(
                name="EXPIRING_KEY",
                secret_type=SecretType.API_KEY,
                created_at=datetime.utcnow() - timedelta(days=85),
                expires_at=datetime.utcnow() + timedelta(days=5)  # 5 days left
            )
            
            await manager.set_secret(
                "EXPIRING_KEY",
                "expiring_value",
                metadata=expiring_metadata
            )
            
            scheduler = SecretRotationScheduler(
                manager,
                warning_days=14,
                critical_days=7
            )
            
            alerts = await scheduler.check_expirations()
            
            assert len(alerts) > 0
            # Alert level depends on days left (5 days is within critical threshold of 7)
            assert alerts[0].alert_level in ["warning", "critical"]
    
    @pytest.mark.asyncio
    async def test_rotation_needed_check(self):
        """Test rotation needed check."""
        from src.core.security_hardening import (
            SecretRotationScheduler,
            LocalEncryptedSecretsManager,
            SecretMetadata,
            SecretType
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LocalEncryptedSecretsManager(storage_path=Path(tmpdir))
            
            # Add secret that needs rotation
            old_metadata = SecretMetadata(
                name="OLD_KEY",
                secret_type=SecretType.API_KEY,
                created_at=datetime.utcnow() - timedelta(days=100),
                rotation_schedule_days=90
            )
            
            await manager.set_secret("OLD_KEY", "old_value", metadata=old_metadata)
            
            scheduler = SecretRotationScheduler(manager)
            needs_rotation = await scheduler.check_rotation_needed()
            
            assert len(needs_rotation) > 0
            assert needs_rotation[0].name == "OLD_KEY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
