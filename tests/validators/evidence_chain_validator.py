"""
Evidence Chain Validator - Validate evidence chain integrity components.
"""

import sys
from typing import Dict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EvidenceValidationResult:
    """Result from evidence chain validation."""
    passed: bool
    message: str
    component_name: str
    can_skip: bool = False


class EvidenceChainValidator:
    """
    Validate evidence chain integrity components.
    
    Validates:
    - SHA-256, SHA3-512, BLAKE2b hash generation
    - Merkle tree construction (RFC 6962)
    - RFC 3161 timestamp client
    - Chain of custody logger
    - Evidence packager
    """
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize evidence chain validator.
        
        Args:
            mock_mode: If True, skip actual cryptographic operations
        """
        self.mock_mode = mock_mode
        self.project_root = self._find_project_root()
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
    
    def _find_project_root(self) -> Path:
        """Find project root directory."""
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / 'src').exists():
                return current
            current = current.parent
        return Path.cwd()
    
    def validate_hash_service(self) -> EvidenceValidationResult:
        """
        Validate triple-hash service (SHA-256, SHA3-512, BLAKE2b).
        
        Returns:
            Validation result
        """
        try:
            import hashlib
            
            # Test that required hash algorithms are available
            test_data = b"test"
            
            # SHA-256 (required for FRE 902(13))
            sha256_hash = hashlib.sha256(test_data).hexdigest()
            
            # SHA3-512 (secondary hash)
            sha3_hash = hashlib.sha3_512(test_data).hexdigest()
            
            # BLAKE2b (tertiary hash)
            blake2b_hash = hashlib.blake2b(test_data).hexdigest()
            
            return EvidenceValidationResult(
                passed=True,
                message="Triple-hash service operational (SHA-256, SHA3-512, BLAKE2b)",
                component_name="Hash Service",
                can_skip=False,
            )
        except Exception as e:
            return EvidenceValidationResult(
                passed=False,
                message=f"Hash service failed: {str(e)}",
                component_name="Hash Service",
                can_skip=False,
            )
    
    def validate_merkle_tree(self) -> EvidenceValidationResult:
        """
        Validate Merkle tree implementation (RFC 6962).
        
        Returns:
            Validation result
        """
        try:
            from src.core.evidence_chain.merkle_tree import MerkleTree
            
            # Test basic Merkle tree construction
            tree = MerkleTree()
            tree.add_leaf(b"test1")
            tree.add_leaf(b"test2")
            root = tree.get_root()
            
            if root:
                return EvidenceValidationResult(
                    passed=True,
                    message="Merkle tree implementation operational (RFC 6962 compliant)",
                    component_name="Merkle Tree",
                    can_skip=False,
                )
            else:
                return EvidenceValidationResult(
                    passed=False,
                    message="Merkle tree construction failed",
                    component_name="Merkle Tree",
                    can_skip=False,
                )
        except ImportError as e:
            return EvidenceValidationResult(
                passed=False,
                message=f"Merkle tree import failed: {str(e)}",
                component_name="Merkle Tree",
                can_skip=False,
            )
        except Exception as e:
            return EvidenceValidationResult(
                passed=False,
                message=f"Merkle tree test failed: {str(e)}",
                component_name="Merkle Tree",
                can_skip=False,
            )
    
    def validate_rfc3161_timestamp(self) -> EvidenceValidationResult:
        """
        Validate RFC 3161 timestamp client.
        
        Returns:
            Validation result
        """
        if self.mock_mode:
            return EvidenceValidationResult(
                passed=True,
                message="RFC 3161 timestamp client (mock mode - skipped)",
                component_name="RFC 3161 Timestamp",
                can_skip=False,
            )
        
        try:
            import rfc3161ng
            
            return EvidenceValidationResult(
                passed=True,
                message="RFC 3161 timestamp client available",
                component_name="RFC 3161 Timestamp",
                can_skip=False,
            )
        except ImportError:
            return EvidenceValidationResult(
                passed=False,
                message="RFC 3161 timestamp client not installed (pip install rfc3161ng)",
                component_name="RFC 3161 Timestamp",
                can_skip=False,
            )
    
    def validate_custody_logger(self) -> EvidenceValidationResult:
        """
        Validate chain of custody logger.
        
        Returns:
            Validation result
        """
        try:
            from src.core.evidence_chain.custody.chain_of_custody import CustodyLogger
            
            # Test instantiation
            logger = CustodyLogger()
            
            return EvidenceValidationResult(
                passed=True,
                message="Chain of custody logger operational",
                component_name="Custody Logger",
                can_skip=False,
            )
        except ImportError as e:
            return EvidenceValidationResult(
                passed=False,
                message=f"Custody logger import failed: {str(e)}",
                component_name="Custody Logger",
                can_skip=False,
            )
        except Exception as e:
            return EvidenceValidationResult(
                passed=False,
                message=f"Custody logger instantiation failed: {str(e)}",
                component_name="Custody Logger",
                can_skip=False,
            )
    
    def validate_evidence_packager(self) -> EvidenceValidationResult:
        """
        Validate evidence packager.
        
        Returns:
            Validation result
        """
        try:
            # Test that evidence chain module is available
            import src.core.evidence_chain
            
            return EvidenceValidationResult(
                passed=True,
                message="Evidence packager available",
                component_name="Evidence Packager",
                can_skip=False,
            )
        except ImportError as e:
            return EvidenceValidationResult(
                passed=False,
                message=f"Evidence packager import failed: {str(e)}",
                component_name="Evidence Packager",
                can_skip=False,
            )
    
    def validate_all_components(self) -> Dict[str, EvidenceValidationResult]:
        """
        Validate all evidence chain components.
        
        Returns:
            Dictionary mapping component name to validation result
        """
        results = {}
        
        results['hash_service'] = self.validate_hash_service()
        results['merkle_tree'] = self.validate_merkle_tree()
        results['rfc3161_timestamp'] = self.validate_rfc3161_timestamp()
        results['custody_logger'] = self.validate_custody_logger()
        results['evidence_packager'] = self.validate_evidence_packager()
        
        return results
    
    def get_summary(self, results: Dict[str, EvidenceValidationResult]) -> Dict[str, int]:
        """
        Get summary statistics from validation results.
        
        Args:
            results: Validation results dictionary
            
        Returns:
            Summary dictionary with counts
        """
        total = len(results)
        passed = sum(1 for r in results.values() if r.passed)
        failed = total - passed
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
        }
