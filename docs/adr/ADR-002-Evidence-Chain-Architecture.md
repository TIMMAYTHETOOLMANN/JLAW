# ADR-002: Evidence Chain Architecture

**Status:** Accepted

**Date:** 2025-12-23

**Decision Makers:** JLAW Engineering Team

---

## Context

JLAW produces DOJ-grade forensic dossiers that must meet Federal Rules of Evidence (FRE) 902(13) and 902(14) requirements for self-authenticating evidence. The system needed a robust evidence chain architecture to ensure:

1. **Integrity**: Evidence cannot be tampered with after collection
2. **Authenticity**: Evidence provenance is verifiable
3. **Chain of Custody**: Complete tracking from collection to courtroom
4. **Court Admissibility**: Meets FRE 902(13)/(14) standards

Initial implementation used single SHA-256 hashing, which while secure, lacked redundancy and advanced cryptographic verification features required for high-stakes prosecutorial cases.

## Decision

Implement a **triple-hash integrity system** with **RFC 6962 compliant Merkle trees** for maximum evidence security:

### Architecture Components

1. **Triple-Hash Integrity**
   - **SHA-256**: Primary hash (FRE 902(13) compliant, FIPS 180-4)
   - **SHA3-512**: Secondary hash (enhanced security, FIPS 202)
   - **BLAKE2b**: Tertiary hash (performance + security, RFC 7693)

2. **Merkle Tree Construction**
   - RFC 6962 compliant (Certificate Transparency standard)
   - Binary tree structure with cryptographic leaf/node hashing
   - Single root hash representing entire evidence corpus
   - Enables efficient partial verification

3. **RFC 3161 Timestamp Tokens**
   - Trusted timestamp authority (TSA) integration
   - Proves evidence existed at specific time
   - Non-repudiable temporal proof

4. **Chain of Custody Tracking**
   - Automated logging of all evidence interactions
   - Action types: COLLECTION, ANALYSIS, TRANSFER, STORAGE
   - Custodian tracking with timestamps
   - Immutable audit log

### Implementation

**Evidence Hash Service (`src/core/evidence_chain/hash_service.py`):**
```python
class HashService:
    def compute_triple_hash(self, data: bytes) -> Dict[str, str]:
        return {
            'sha256': hashlib.sha256(data).hexdigest(),
            'sha3_512': hashlib.sha3_512(data).hexdigest(),
            'blake2b': hashlib.blake2b(data).hexdigest()
        }
```

**Merkle Tree (`src/core/evidence_chain/merkle_tree.py`):**
```python
class MerkleTree:
    def __init__(self):
        self.leaves = []
    
    def add_leaf(self, leaf_hash: bytes):
        self.leaves.append(leaf_hash)
    
    def get_root(self) -> str:
        # RFC 6962 compliant Merkle tree construction
        return self._compute_merkle_root(self.leaves)
```

**Custody Logger (`src/core/evidence_chain/custody/chain_of_custody.py`):**
```python
class CustodyLogger:
    def log_acquisition(self, document_url: str, sha256_hash: str, timestamp: datetime):
        self.custody_chain.append({
            "action": "COLLECTION",
            "document_url": document_url,
            "sha256": sha256_hash,
            "timestamp": timestamp.isoformat(),
            "custodian": "JLAW Forensic System"
        })
```

## Consequences

### Positive

- **Defense Against Attacks**: Triple-hashing provides redundancy if one algorithm is compromised
- **Court Admissibility**: Meets FRE 902(13)/(14) requirements for self-authenticating evidence
- **Cryptographic Proof**: Merkle root provides single verifiable proof of entire evidence corpus
- **Efficient Verification**: Can verify individual documents without re-hashing entire corpus
- **Temporal Proof**: RFC 3161 timestamps prove evidence existed at collection time
- **Audit Trail**: Complete chain of custody from SEC EDGAR to courtroom

### Negative

- **Computational Overhead**: Triple-hashing adds ~30% CPU time vs single hash
- **Storage Overhead**: Three hashes per document (96 bytes vs 32 bytes for SHA-256 only)
- **Complexity**: More moving parts to maintain and test
- **TSA Dependency**: RFC 3161 timestamps require external trusted timestamp authority

### Neutral

- **Standard Compliance**: Following RFC 6962 and RFC 3161 ensures interoperability
- **Migration Impact**: Existing evidence chains need re-hashing with new system
- **Performance vs Security**: Trade accepted for prosecutorial-grade requirements

## Alternatives Considered

### Alternative 1: Single SHA-256 Hash Only

- **Description**: Continue with SHA-256 only (original implementation)
- **Pros**: Simple, fast, widely accepted
- **Cons**: No redundancy if SHA-256 compromised, minimal for DOJ-grade
- **Reason for rejection**: Insufficient for high-stakes prosecutorial cases

### Alternative 2: SHA-256 + SHA3-512 Dual Hash

- **Description**: Two-hash system without BLAKE2b
- **Pros**: Good redundancy, both NIST standards
- **Cons**: SHA3-512 slower than BLAKE2b for verification
- **Reason for rejection**: BLAKE2b adds performance without sacrificing security

### Alternative 3: Blockchain-Based Evidence Chain

- **Description**: Store evidence hashes on blockchain (e.g., Ethereum)
- **Pros**: Immutable, distributed, publicly verifiable
- **Cons**: Transaction costs, external dependency, privacy concerns
- **Reason for rejection**: Overkill for current needs, privacy issues with public filings

### Alternative 4: ZKP (Zero-Knowledge Proofs)

- **Description**: Use ZKPs to verify evidence without revealing content
- **Pros**: Privacy-preserving verification
- **Cons**: Complex, computationally expensive, unclear legal precedent
- **Reason for rejection**: Too experimental for courtroom use, legal uncertainty

## Implementation Notes

### Phase 8: Evidence Chain Finalization

During Phase 8 of the 9-phase execution:

1. **Compute Triple Hashes** for all collected evidence:
   - SEC EDGAR documents (HTML/XBRL)
   - Node analysis results (JSON)
   - Detection pattern outputs
   - AI validation results

2. **Build Merkle Tree**:
   - Add all SHA-256 hashes as leaves
   - Compute Merkle root (single hash representing all evidence)

3. **Request RFC 3161 Timestamp**:
   - Send Merkle root to TSA
   - Receive signed timestamp token
   - Store token with evidence chain

4. **Log Chain of Custody**:
   - Collection: SEC EDGAR → JLAW System
   - Analysis: JLAW System → Node Processors
   - Storage: Analysis Results → Dossier

5. **Gate Validation** (Strict Mode):
   - Verify all hashes match
   - Confirm Merkle root integrity
   - Check timestamp token validity
   - **ABORT** execution if any hash mismatch (exit code 6)

### FRE 902(13)/(14) Compliance

**FRE 902(13)** - Certified Records Generated by Electronic Process:
- ✅ Triple-hash integrity proves data authenticity
- ✅ Chain of custody shows electronic generation
- ✅ Certificate (dossier) describes process

**FRE 902(14)** - Certified Data Copied from Electronic Device:
- ✅ Triple-hash proves data unchanged from source
- ✅ Merkle tree verifies corpus integrity
- ✅ RFC 3161 timestamp proves temporal authenticity

### Migration Path

**Phase 1** (Immediate):
- Deploy triple-hash system for new analyses
- Existing evidence chains remain SHA-256 only (backward compatible)

**Phase 2** (Month 1):
- Background job to re-hash legacy evidence with triple-hash
- Merkle trees constructed for historical analyses

**Phase 3** (Quarter 1):
- All evidence chains upgraded to triple-hash + Merkle
- Legacy SHA-256-only support deprecated

### Rollback Strategy

If critical issues discovered:
1. Disable triple-hashing, revert to SHA-256 only
2. Merkle tree construction made optional
3. RFC 3161 timestamps remain optional (nice-to-have)
4. Chain of custody continues unchanged

## References

- **Related ADRs:**
  - ADR-001: Orchestration Hierarchy Design
  - ADR-003: Node Execution Strategy

- **Code References:**
  - `src/core/evidence_chain/hash_service.py` - Triple-hash implementation
  - `src/core/evidence_chain/merkle_tree.py` - RFC 6962 Merkle tree
  - `src/core/custody/chain_of_custody.py` - Custody tracking

- **Legal Framework:**
  - Federal Rules of Evidence (FRE) 902(13)
  - Federal Rules of Evidence (FRE) 902(14)
  - FIPS 180-4 (SHA-256 standard)
  - FIPS 202 (SHA-3 standard)

- **Cryptographic Standards:**
  - RFC 6962 - Certificate Transparency (Merkle trees)
  - RFC 3161 - Time-Stamp Protocol (TSP)
  - RFC 7693 - BLAKE2 Cryptographic Hash and MAC
  - NIST SP 800-107 - Recommendation for Applications Using Approved Hash Algorithms

- **Documentation:**
  - `STRICT_EXECUTION_MODE.md` - Phase gate validation including evidence chain
  - `HOLY_GRAIL_PIPELINE.md` - Complete pipeline including Phase 8

---

## Metadata

- **ADR Number:** 002
- **Created:** 2025-12-23
- **Last Updated:** 2025-12-23
- **Authors:** JLAW Engineering Team
- **Reviewers:** Legal Advisory (FRE compliance)
