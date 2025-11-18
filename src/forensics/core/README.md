# Forensic Integrity Manager

## Overview
NIST-compliant cryptographic integrity management system implementing blockchain-style immutable audit trails for courtroom admissibility.

## Components Implemented

### 1. IntegrityLevel (Enum)
FIPS 140-2 compliance levels:
- `GENESIS` - Chain initialization
- `CRITICAL` - Financial statements, material contracts
- `HIGH` - SEC filings, regulatory documents
- `MEDIUM` - Supporting documentation
- `LOW` - Public information

### 2. HashAlgorithm (Enum)
NIST-approved algorithms per FIPS 180-4:
- SHA256, SHA384, SHA512
- SHA3_256, SHA3_512

### 3. ForensicBlock (dataclass)
Immutable evidence block with:
- Sequence number
- ISO 8601 timestamp
- Data payload
- Previous/current hash linkage
- Merkle root (optional)
- Digital signatures
- Evidence ID (UUID)

### 4. ForensicHashChain
Blockchain-style chain implementing:
- Genesis block initialization
- Atomic evidence addition with verification
- Full chain integrity verification
- Merkle tree checkpoints (every 1000 blocks)
- External anchoring support
- Chain export for legal proceedings

### 5. MerkleTree
Efficient batch verification:
- Tree building from leaf hashes
- Proof generation
- Proof verification

### 6. ChainOfCustody
Chain of custody documentation per NIST IR 8387:
- Collection initialization
- Custody transfers with hash verification
- Access logging
- Complete documentation export

### 7. IntegrityError (Exception)
Critical integrity violation exception

## Usage Example

```python
from forensics.core.integrity_manager import (
    ForensicHashChain,
    ChainOfCustody,
    IntegrityLevel
)

# Create chain
chain = ForensicHashChain()

# Add evidence
await chain.add_evidence(
    {"type": "financial_statement", "amount": 1000000},
    integrity_level=IntegrityLevel.CRITICAL
)

# Verify chain
is_valid = await chain.verify_chain()
```

## Standards Compliance
- NIST IR 8387 - Forensic evidence handling
- FIPS 140-2 - Cryptographic module security
- FIPS 180-4 - Secure hash algorithms
- FRE 902(13)/(14) - Federal Rules of Evidence
- DOJ Requirements - Chain of custody

## File Location
`src/forensics/core/integrity_manager.py`

## Status
✅ **IMPLEMENTED** - Module created and validated
- All classes operational
- Import tests passing
- No dependencies on other pending modules

