#!/usr/bin/env python3
"""
Zero-Dollar Evidence Integrity Tests
=====================================

Validates the Evidence Integrity & Chain of Custody Protocol implementation
per JLAW Zero-Dollar Transaction Forensic Specification v1.0, Section 9.

Test Coverage:
- Evidence artifact creation and verification
- Merkle tree construction and proof generation
- Chain linking and integrity verification
- Custody record tracking
- Export package generation
"""

import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest


def test_evidence_imports():
    """Test that all evidence modules can be imported."""
    print("Testing evidence module imports...")
    
    try:
        from src.zero_dollar.evidence import (
            EvidenceArtifact,
            create_evidence_artifact,
            verify_artifact_integrity,
            verify_chain_link,
            MerkleEvidenceChain,
            MerkleProof,
            TrustedTimestamp,
            request_trusted_timestamp,
            verify_timestamp_token,
            TimestampError,
            ChainOfCustodyRecord,
            VerificationEvent,
        )
        print("✓ All evidence components imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_evidence_artifact():
    """Test evidence artifact creation with SHA-256 hashing."""
    print("\nTesting evidence artifact creation...")
    
    try:
        from src.zero_dollar.evidence import create_evidence_artifact
        
        # Create test data
        test_data = {
            'transaction_id': 'TXN-001',
            'shares': '10000',
            'price': '0.00',
            'date': '2020-01-15'
        }
        
        # Create artifact
        artifact = create_evidence_artifact(
            artifact_type='TRANSACTION',
            source_data=test_data
        )
        
        # Verify artifact properties
        assert artifact.artifact_id.startswith('EV-'), "Artifact ID should start with 'EV-'"
        assert artifact.artifact_type == 'TRANSACTION', "Artifact type mismatch"
        assert len(artifact.hash_sha256) == 64, "SHA-256 hash should be 64 characters"
        assert artifact.chain_position == 1, "First artifact should have position 1"
        assert artifact.previous_hash == '0' * 64, "Genesis artifact should have null previous hash"
        
        print(f"  ✓ Created artifact: {artifact.artifact_id}")
        print(f"  ✓ SHA-256 hash: {artifact.hash_sha256[:16]}...")
        print(f"  ✓ Chain position: {artifact.chain_position}")
        
        return True
    except Exception as e:
        print(f"  ✗ Artifact creation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_artifact_chain_linking():
    """Test chain linking between artifacts."""
    print("\nTesting artifact chain linking...")
    
    try:
        from src.zero_dollar.evidence import (
            create_evidence_artifact,
            verify_chain_link
        )
        
        # Create first artifact
        artifact1 = create_evidence_artifact(
            artifact_type='TRANSACTION',
            source_data={'id': 1, 'data': 'first'}
        )
        
        # Create second artifact linked to first
        artifact2 = create_evidence_artifact(
            artifact_type='TRANSACTION',
            source_data={'id': 2, 'data': 'second'},
            previous_artifact=artifact1
        )
        
        # Verify chain link
        is_valid = verify_chain_link(artifact2, artifact1)
        assert is_valid, "Chain link should be valid"
        assert artifact2.chain_position == 2, "Second artifact should have position 2"
        assert artifact2.previous_hash == artifact1.hash_sha256, "Previous hash should match"
        
        print(f"  ✓ Artifact 1: {artifact1.artifact_id} (position {artifact1.chain_position})")
        print(f"  ✓ Artifact 2: {artifact2.artifact_id} (position {artifact2.chain_position})")
        print(f"  ✓ Chain link verified")
        
        return True
    except Exception as e:
        print(f"  ✗ Chain linking error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_artifact_integrity_verification():
    """Test artifact integrity verification."""
    print("\nTesting artifact integrity verification...")
    
    try:
        from src.zero_dollar.evidence import (
            create_evidence_artifact,
            verify_artifact_integrity
        )
        
        # Create artifact
        artifact = create_evidence_artifact(
            artifact_type='FLAG',
            source_data={'flag': 'test', 'severity': 'HIGH'}
        )
        
        # Verify integrity (should pass)
        is_valid = verify_artifact_integrity(artifact)
        assert is_valid, "Integrity check should pass for unmodified artifact"
        print(f"  ✓ Unmodified artifact integrity: VERIFIED")
        
        # Tamper with source data
        original_data = artifact.source_data
        artifact.source_data = b'tampered data'
        
        # Verify integrity (should fail)
        is_tampered = not verify_artifact_integrity(artifact)
        assert is_tampered, "Integrity check should fail for tampered artifact"
        print(f"  ✓ Tampered artifact detected: FAILED")
        
        # Restore data
        artifact.source_data = original_data
        is_restored = verify_artifact_integrity(artifact)
        assert is_restored, "Integrity check should pass after restoration"
        print(f"  ✓ Restored artifact integrity: VERIFIED")
        
        return True
    except Exception as e:
        print(f"  ✗ Integrity verification error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_merkle_chain_construction():
    """Test Merkle tree construction from artifacts."""
    print("\nTesting Merkle chain construction...")
    
    try:
        from src.zero_dollar.evidence import (
            create_evidence_artifact,
            MerkleEvidenceChain
        )
        
        # Create chain
        merkle_chain = MerkleEvidenceChain()
        
        # Add 4 artifacts
        for i in range(4):
            artifact = create_evidence_artifact(
                artifact_type='TRANSACTION',
                source_data={'id': i, 'data': f'transaction_{i}'}
            )
            merkle_chain.add_artifact(artifact)
        
        # Verify tree properties
        assert len(merkle_chain.artifacts) == 4, "Should have 4 artifacts"
        assert merkle_chain.root_hash is not None, "Root hash should be computed"
        assert len(merkle_chain.root_hash) == 64, "Root hash should be 64 characters"
        
        print(f"  ✓ Added 4 artifacts to chain")
        print(f"  ✓ Merkle root: {merkle_chain.root_hash[:16]}...")
        print(f"  ✓ Tree depth: {len(merkle_chain.tree)}")
        
        return True
    except Exception as e:
        print(f"  ✗ Merkle chain error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_merkle_proof_generation():
    """Test Merkle proof generation and verification."""
    print("\nTesting Merkle proof generation...")
    
    try:
        from src.zero_dollar.evidence import (
            create_evidence_artifact,
            MerkleEvidenceChain
        )
        
        # Create chain with artifacts
        merkle_chain = MerkleEvidenceChain()
        artifacts = []
        
        for i in range(4):
            artifact = create_evidence_artifact(
                artifact_type='TRANSACTION',
                source_data={'id': i, 'value': i * 100}
            )
            merkle_chain.add_artifact(artifact)
            artifacts.append(artifact)
        
        # Generate proof for artifact at index 2
        proof = merkle_chain.get_proof(2)
        
        # Verify proof properties
        assert proof.artifact_hash == artifacts[2].hash_sha256, "Proof hash should match artifact"
        assert proof.root_hash == merkle_chain.root_hash, "Proof root should match chain root"
        assert len(proof.proof_hashes) > 0, "Proof should have sibling hashes"
        
        # Verify proof
        is_valid = merkle_chain.verify_proof(proof)
        assert is_valid, "Proof should be valid"
        
        print(f"  ✓ Generated proof for artifact {artifacts[2].artifact_id}")
        print(f"  ✓ Proof hashes: {len(proof.proof_hashes)}")
        print(f"  ✓ Proof verified: VALID")
        
        return True
    except Exception as e:
        print(f"  ✗ Merkle proof error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chain_export():
    """Test Merkle chain export."""
    print("\nTesting Merkle chain export...")
    
    try:
        from src.zero_dollar.evidence import (
            create_evidence_artifact,
            MerkleEvidenceChain
        )
        
        # Create chain with artifacts
        merkle_chain = MerkleEvidenceChain()
        
        for i in range(3):
            artifact = create_evidence_artifact(
                artifact_type='CLUSTER',
                source_data={'cluster_id': f'CLU-{i:03d}'}
            )
            merkle_chain.add_artifact(artifact)
        
        # Export chain
        exported = merkle_chain.export_chain()
        
        # Verify export structure
        assert 'artifacts' in exported, "Export should contain artifacts"
        assert 'root_hash' in exported, "Export should contain root hash"
        assert 'tree_depth' in exported, "Export should contain tree depth"
        assert 'artifact_count' in exported, "Export should contain artifact count"
        assert exported['artifact_count'] == 3, "Should have 3 artifacts"
        
        print(f"  ✓ Exported chain with {exported['artifact_count']} artifacts")
        print(f"  ✓ Root hash: {exported['root_hash'][:16]}...")
        print(f"  ✓ Tree depth: {exported['tree_depth']}")
        
        return True
    except Exception as e:
        print(f"  ✗ Chain export error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custody_record_creation():
    """Test chain of custody record creation."""
    print("\nTesting custody record creation...")
    
    try:
        from src.zero_dollar.evidence import (
            create_evidence_artifact,
            MerkleEvidenceChain,
            ChainOfCustodyRecord,
        )
        
        # Create artifacts
        artifacts = []
        for i in range(3):
            artifact = create_evidence_artifact(
                artifact_type='ASSESSMENT',
                source_data={'assessment_id': f'ASS-{i:03d}', 'score': 75 + i}
            )
            artifacts.append(artifact)
        
        # Build Merkle chain
        merkle_chain = MerkleEvidenceChain()
        for artifact in artifacts:
            merkle_chain.add_artifact(artifact)
        
        # Create custody record
        custody = ChainOfCustodyRecord(
            case_id='JLAW-TEST-001',
            created_utc=datetime.now(timezone.utc),
            created_by='JLAW-SYSTEM',
            evidence_artifacts=artifacts,
            merkle_chain=merkle_chain,
            trusted_timestamps=[],
            integrity_status='PENDING',
            last_verified_utc=datetime.now(timezone.utc)
        )
        
        # Verify custody record
        assert custody.case_id == 'JLAW-TEST-001', "Case ID mismatch"
        assert len(custody.evidence_artifacts) == 3, "Should have 3 artifacts"
        assert custody.merkle_chain.root_hash is not None, "Merkle root should exist"
        
        print(f"  ✓ Created custody record for case: {custody.case_id}")
        print(f"  ✓ Artifacts: {len(custody.evidence_artifacts)}")
        print(f"  ✓ Merkle root: {custody.merkle_chain.root_hash[:16]}...")
        
        return True
    except Exception as e:
        print(f"  ✗ Custody record error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custody_integrity_verification():
    """Test custody record integrity verification."""
    print("\nTesting custody integrity verification...")
    
    try:
        from src.zero_dollar.evidence import (
            create_evidence_artifact,
            MerkleEvidenceChain,
            ChainOfCustodyRecord,
        )
        
        # Create chain of artifacts
        artifacts = []
        prev_artifact = None
        
        for i in range(4):
            artifact = create_evidence_artifact(
                artifact_type='TRANSACTION',
                source_data={'txn': f'TXN-{i:04d}'},
                previous_artifact=prev_artifact
            )
            artifacts.append(artifact)
            prev_artifact = artifact
        
        # Build Merkle chain
        merkle_chain = MerkleEvidenceChain()
        for artifact in artifacts:
            merkle_chain.add_artifact(artifact)
        
        # Create custody record
        custody = ChainOfCustodyRecord(
            case_id='JLAW-TEST-002',
            created_utc=datetime.now(timezone.utc),
            created_by='JLAW-SYSTEM',
            evidence_artifacts=artifacts,
            merkle_chain=merkle_chain,
            trusted_timestamps=[],
            integrity_status='PENDING',
            last_verified_utc=datetime.now(timezone.utc)
        )
        
        # Verify integrity
        is_valid = custody.verify_integrity()
        
        assert is_valid, "Custody integrity should be valid"
        assert custody.integrity_status == 'VERIFIED', "Status should be VERIFIED"
        assert len(custody.verification_log) > 0, "Should have verification events"
        
        print(f"  ✓ Custody integrity: {custody.integrity_status}")
        print(f"  ✓ Verification events: {len(custody.verification_log)}")
        
        return True
    except Exception as e:
        print(f"  ✗ Custody verification error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custody_package_export():
    """Test custody package ZIP export."""
    print("\nTesting custody package export...")
    
    try:
        import zipfile
        from io import BytesIO
        from src.zero_dollar.evidence import (
            create_evidence_artifact,
            MerkleEvidenceChain,
            ChainOfCustodyRecord,
        )
        
        # Create artifacts
        artifacts = []
        for i in range(2):
            artifact = create_evidence_artifact(
                artifact_type='FLAG',
                source_data={'flag_id': f'FLAG-{i:03d}', 'severity': 'HIGH'}
            )
            artifacts.append(artifact)
        
        # Build Merkle chain
        merkle_chain = MerkleEvidenceChain()
        for artifact in artifacts:
            merkle_chain.add_artifact(artifact)
        
        # Create custody record
        custody = ChainOfCustodyRecord(
            case_id='JLAW-TEST-003',
            created_utc=datetime.now(timezone.utc),
            created_by='JLAW-SYSTEM',
            evidence_artifacts=artifacts,
            merkle_chain=merkle_chain,
            trusted_timestamps=[],
            integrity_status='PENDING',
            last_verified_utc=datetime.now(timezone.utc)
        )
        
        # Verify integrity first
        custody.verify_integrity()
        
        # Export custody package
        zip_bytes = custody.export_custody_package()
        
        # Verify ZIP structure
        assert len(zip_bytes) > 0, "ZIP should have content"
        
        # Open ZIP and check contents
        zip_buffer = BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            file_list = zf.namelist()
            
            assert 'custody_manifest.json' in file_list, "Should have manifest"
            assert any(f.startswith('artifacts/') for f in file_list), "Should have artifacts"
            assert any(f.startswith('merkle_proofs/') for f in file_list), "Should have proofs"
            assert 'verification_log.json' in file_list, "Should have verification log"
            
            # Read and verify manifest
            manifest_data = json.loads(zf.read('custody_manifest.json'))
            assert manifest_data['case_id'] == 'JLAW-TEST-003', "Case ID in manifest"
            assert manifest_data['artifact_count'] == 2, "Artifact count in manifest"
        
        print(f"  ✓ Exported ZIP package: {len(zip_bytes)} bytes")
        print(f"  ✓ Files in package: {len(file_list)}")
        print(f"  ✓ Package structure: VALID")
        
        return True
    except Exception as e:
        print(f"  ✗ Package export error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timestamp_error_handling():
    """Test timestamp error handling without actual TSA call."""
    print("\nTesting timestamp error handling...")
    
    try:
        from src.zero_dollar.evidence import TimestampError
        
        # Test that TimestampError can be raised
        try:
            raise TimestampError("Test error message")
        except TimestampError as e:
            assert str(e) == "Test error message", "Error message should match"
            print(f"  ✓ TimestampError exception works correctly")
        
        return True
    except Exception as e:
        print(f"  ✗ Timestamp error test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all evidence integrity tests."""
    print("=" * 70)
    print("Zero-Dollar Evidence Integrity Tests")
    print("=" * 70)
    
    tests = [
        ("Import Test", test_evidence_imports),
        ("Evidence Artifact Creation", test_create_evidence_artifact),
        ("Artifact Chain Linking", test_artifact_chain_linking),
        ("Artifact Integrity Verification", test_artifact_integrity_verification),
        ("Merkle Chain Construction", test_merkle_chain_construction),
        ("Merkle Proof Generation", test_merkle_proof_generation),
        ("Chain Export", test_chain_export),
        ("Custody Record Creation", test_custody_record_creation),
        ("Custody Integrity Verification", test_custody_integrity_verification),
        ("Custody Package Export", test_custody_package_export),
        ("Timestamp Error Handling", test_timestamp_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        success = test_func()
        results.append((name, success))
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All evidence integrity tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
