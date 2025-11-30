"""
Core forensic architecture with cryptographic integrity management.

Components:
- IntegrityManager: Cryptographic hash chain and Merkle tree management
- InputValidator: Validates all analysis inputs (CIK, dates, filing types)
- SystemLock: Configuration lock to prevent drift and ensure repeatability
"""

from .integrity_manager import (
    IntegrityLevel,
    HashAlgorithm,
    ForensicBlock,
    ForensicHashChain,
    MerkleTree,
    IntegrityError,
    ChainOfCustody
)

from .input_validator import (
    InputValidator,
    ValidationResult
)

from .system_lock import (
    SystemLock,
    SystemState,
    SystemConfiguration,
    AnalysisParameters,
    OutputConfiguration
)

__all__ = [
    # Integrity Management
    "IntegrityLevel",
    "HashAlgorithm",
    "ForensicBlock",
    "ForensicHashChain",
    "MerkleTree",
    "IntegrityError",
    "ChainOfCustody",
    
    # Input Validation
    "InputValidator",
    "ValidationResult",
    
    # System Lock
    "SystemLock",
    "SystemState",
    "SystemConfiguration",
    "AnalysisParameters",
    "OutputConfiguration",
]

