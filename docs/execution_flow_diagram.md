# Execution Flow Diagram

## Overview

This document visualizes the JLAW execution flow architecture, showing the 9-phase forensic analysis pipeline with dependencies, validation gates, and evidence chain checkpoints.

## Phase Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         JLAW Execution Flow                                  │
│                  9-Phase DOJ-Grade Forensic Analysis                         │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 1: Configuration & Target Acquisition
│   ├─ Timeout: 30s
│   ├─ Validation Rules:
│   │   • sec_client_available = True
│   │   • modules_loaded = 6
│   │   • sec_config_valid = True
│   └─ Dependencies: None
    │
    ▼
Phase 2: SEC EDGAR Data Collection
│   ├─ Timeout: 300s (5 minutes)
│   ├─ Validation Rules:
│   │   • filings_collected >= 1
│   │   • all_filings_have_content = True
│   └─ Dependencies: phase_1_initialization
    │
    ▼
Phase 3: Document Parsing & Indexing
│   ├─ Timeout: 300s (5 minutes)
│   ├─ Validation Rules:
│   │   • documents_parsed >= 1
│   │   • parsing_success_rate >= 0.80
│   └─ Dependencies: phase_2_data_collection
    │
    ▼
Phase 4: 15-Node Recursive Analysis
│   ├─ Timeout: 900s (15 minutes)
│   ├─ Validation Rules:
│   │   • nodes_executed >= 12 (80% of 15)
│   │   • node_success_rate >= 0.80
│   └─ Dependencies: phase_3_document_parsing
    │
    ▼
Phase 5: Advanced Pattern Detection
│   ├─ Timeout: 300s (5 minutes)
│   ├─ Validation Rules:
│   │   • patterns_executed >= 10 (of 23 patterns)
│   │   • pattern_execution_rate >= 0.43
│   └─ Dependencies: phase_4_node_analysis
    │
    ▼
Phase 6: Dual-Agent AI Cross-Validation
│   ├─ Timeout: 600s (10 minutes)
│   ├─ Validation Rules:
│   │   • ai_agents_executed >= 1
│   │   • violations_analyzed >= 0
│   └─ Dependencies: phase_5_pattern_detection
    │
    ▼
Phase 7: Unified Agent Orchestration
│   ├─ Timeout: 900s (15 minutes)
│   ├─ Validation Rules:
│   │   • agents_invoked >= 3
│   │   • consensus_score >= 0.70 ◄─ DOJ SUBMISSION THRESHOLD
│   │   • orchestration_completed = True
│   └─ Dependencies: phase_6_dual_agent
    │
    ▼
Phase 8: Evidence Chain Integrity Verification
│   ├─ Timeout: 60s (1 minute)
│   ├─ Validation Rules:
│   │   • all_hashes_verified = True
│   │   • chain_of_custody_complete = True
│   │   • fre_902_compliant = True ◄─ COURT ADMISSIBILITY
│   │   • merkle_root_generated = True
│   └─ Dependencies: phase_7_subagent_orchestration
    │
    ▼
Phase 9: DOJ-Grade Report Generation
│   ├─ Timeout: 120s (2 minutes)
│   ├─ Validation Rules:
│   │   • dossier_generated = True
│   │   • pdf_generated = True
│   │   • all_violations_documented = True
│   └─ Dependencies: phase_8_evidence_chain
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Forensic Dossier                                    │
│                    FRE 902(13)/(14) Compliant                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Phase Gate Validation Points

### Strict Mode Enforcement

In **Strict Mode** (DOJ-grade), each phase gate MUST pass validation before proceeding:

```
┌──────────────┐
│  Phase N     │
│  Executes    │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌─────────────────┐
│ Phase Gate   │─NO──▶│ PhaseGateFailure│─────▶ ABORT
│ Validation   │      │ Exception Raised│
└──────┬───────┘      └─────────────────┘
       │
       YES
       │
       ▼
┌──────────────┐
│  Phase N+1   │
│  Proceeds    │
└──────────────┘
```

### Standard Mode Behavior

In **Standard Mode**, phase gates log warnings but do not halt execution:

```
┌──────────────┐
│  Phase N     │
│  Executes    │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌─────────────────┐
│ Phase Gate   │─NO──▶│ Warning Logged  │
│ Validation   │      │ Execution Continues
└──────┬───────┘      └─────────────────┘
       │
       YES
       │
       ▼
┌──────────────┐
│  Phase N+1   │
│  Proceeds    │
└──────────────┘
```

## Error Handling Flow

### Exception Hierarchy

```
PhaseExecutionError (Base)
├── PhaseDefinitionError
│   └── Raised when: Phase ID not found in registry
│
├── PhaseDependencyError
│   └── Raised when: Dependency not satisfied or failed
│
├── PhaseGateFailure
│   └── Raised when: Validation rules not met (strict mode only)
│
├── PhaseTimeoutError
│   └── Raised when: Phase exceeds timeout threshold
│
└── EvidenceChainIntegrityError
    └── Raised when: Triple-hash verification fails (CRITICAL)
```

### Error Propagation

```
┌──────────────────────────────────────────────────────────────┐
│                     Phase Execution                          │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Try Execute    │
              │ with Timeout   │
              └────────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌──────────┐
   │SUCCESS  │   │ ERROR   │   │ TIMEOUT  │
   └────┬────┘   └────┬────┘   └────┬─────┘
        │             │              │
        ▼             ▼              ▼
   ┌─────────────────────────────────────┐
   │    Log to Audit Trail               │
   │    (Immutable Append-Only)          │
   └─────────────┬───────────────────────┘
                 │
                 ▼
   ┌─────────────────────────────────────┐
   │  Strict Mode Enabled?               │
   └─────────────┬───────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
       YES               NO
        │                 │
        ▼                 ▼
   ┌─────────┐      ┌──────────┐
   │ ABORT   │      │ CONTINUE │
   │ Raise   │      │ Log Warn │
   └─────────┘      └──────────┘
```

## Evidence Chain Checkpoints

Evidence integrity is verified at multiple checkpoints:

```
Phase 2: Data Collection
    ↓
    [Checkpoint 1: Document Hash Generation]
    • SHA-256 (primary)
    • SHA3-512 (secondary)
    • BLAKE2b (tertiary)
    ↓
Phase 4-7: Analysis Phases
    ↓
    [Checkpoint 2: Violation Evidence Collection]
    • Timestamp each finding
    • Link to source document hash
    ↓
Phase 8: Evidence Chain Finalization
    ↓
    [Checkpoint 3: Triple-Hash Verification]
    • Verify all hashes match original
    • Build Merkle tree (RFC 6962)
    • Generate Merkle root
    ↓
    [Checkpoint 4: Chain of Custody Validation]
    • Verify custody records complete
    • Check for gaps or modifications
    ↓
    [Checkpoint 5: FRE 902(13)/(14) Compliance]
    • RFC 3161 timestamp tokens
    • Self-authenticating evidence markers
    • Court admissibility validation
    ↓
    [PASS] → Phase 9: Report Generation
    [FAIL] → EvidenceChainIntegrityError → ABORT
```

## Audit Trail Format

The immutable audit trail is exported as JSON with the following structure:

```json
{
  "audit_trail_version": "1.0",
  "generation_timestamp": "2025-12-29T16:00:00Z",
  "strict_mode": true,
  "total_phases": 9,
  "execution_summary": {
    "total_phases_executed": 9,
    "successful_phases": 9,
    "failed_phases": 0,
    "total_execution_time": 3245.67,
    "strict_mode_enabled": true,
    "all_validations_passed": true,
    "phases": [
      {
        "phase_id": "phase_1_initialization",
        "phase_number": 1,
        "phase_name": "Configuration & Target Acquisition",
        "status": "success",
        "execution_time": 2.145,
        "timestamp": "2025-12-29T16:00:01Z",
        "error": null,
        "validation_passed": true,
        "validation_message": "Phase gate validation passed"
      }
      // ... remaining phases ...
    ]
  },
  "detailed_phase_log": [
    // Same as phases array above
  ],
  "phase_registry_snapshot": {
    "phase_1_initialization": {
      "phase_name": "Configuration & Target Acquisition",
      "phase_number": 1,
      "dependencies": [],
      "timeout_seconds": 30.0
    }
    // ... remaining phases ...
  }
}
```

## Critical Phase Gates

### Phase 7: Consensus Score Validation

The **70% consensus threshold** is critical for DOJ submission:

```
Consensus Score Calculation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Agents Invoked: 5
Agents in Agreement: 4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Consensus Score = 4/5 = 0.80 (80%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ PASS: 0.80 >= 0.70 (Meets DOJ threshold)

If consensus score < 0.70:
  → PhaseGateFailure raised (strict mode)
  → Analysis NOT suitable for DOJ submission
```

### Phase 8: Evidence Chain Integrity

The **100% hash match** requirement is absolute:

```
Triple-Hash Verification:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documents Verified: 127
Hash Matches: 127
Hash Mismatches: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Match Rate = 127/127 = 100%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ PASS: All hashes verified

If ANY hash mismatch detected:
  → EvidenceChainIntegrityError raised
  → Entire analysis ABORTED
  → Evidence inadmissible in court
```

## Performance Metrics

### Phase Timeout Thresholds

| Phase | Timeout | Typical Duration | Headroom |
|-------|---------|------------------|----------|
| Phase 1 | 30s | 2-5s | 6-15x |
| Phase 2 | 300s | 60-120s | 2.5-5x |
| Phase 3 | 300s | 30-90s | 3-10x |
| Phase 4 | 900s | 300-600s | 1.5-3x |
| Phase 5 | 300s | 60-180s | 1.7-5x |
| Phase 6 | 600s | 120-300s | 2-5x |
| Phase 7 | 900s | 240-600s | 1.5-3.75x |
| Phase 8 | 60s | 10-30s | 2-6x |
| Phase 9 | 120s | 30-60s | 2-4x |

**Total Maximum Execution Time**: 64 minutes (3840s)
**Typical Execution Time**: 15-30 minutes

## Usage Examples

### Basic Phase Execution

```python
from src.core.phase_execution_framework import PhaseExecutionFramework

# Initialize framework
framework = PhaseExecutionFramework(strict_mode=True)

# Define phase executor
async def my_phase_executor(**kwargs):
    # Perform phase logic
    return {
        "sec_client_available": True,
        "modules_loaded": 6,
        "sec_config_valid": True
    }

# Execute phase with validation
result = await framework.execute_phase(
    "phase_1_initialization",
    executor=my_phase_executor
)

# Check result
if result.status == PhaseStatus.SUCCESS:
    print("Phase completed successfully")
else:
    print(f"Phase failed: {result.error}")
```

### Exporting Audit Trail

```python
from pathlib import Path

# After all phases complete
framework.export_audit_trail(
    Path("output/audit_trail.json")
)

# Audit trail is now immutable and court-admissible
```

### Dependency Graph Inspection

```python
# Get dependency graph
graph = framework.get_phase_dependency_graph()

# Validate no circular dependencies
is_valid = framework.validate_phase_order()  # True if valid

# Get execution summary
summary = framework.get_execution_summary()
print(f"Successful phases: {summary['successful_phases']}/9")
print(f"Total execution time: {summary['total_execution_time']:.2f}s")
```

## Legal Compliance References

### Federal Rules of Evidence

- **FRE 902(13)**: Certified records generated by electronic process
- **FRE 902(14)**: Certified data copied from electronic device

### Technical Standards

- **RFC 6962**: Certificate Transparency (Merkle tree structure)
- **RFC 3161**: Time-Stamp Protocol (TSP)
- **FIPS 180-4**: Secure Hash Standard (SHA-256, SHA3-512)
- **RFC 7693**: BLAKE2 Cryptographic Hash and MAC

### Regulatory Framework

- **17 CFR § 240.10b-5**: Securities fraud
- **SOX Section 404**: Internal controls assessment
- **18 U.S.C. § 1348**: Securities and commodities fraud
- **18 U.S.C. § 1519**: Evidence tampering and obstruction

## Conclusion

The Phase Execution Framework ensures:

1. ✅ **Mandatory phase sequencing** via dependency validation
2. ✅ **Quality gates** enforced in strict mode
3. ✅ **Timeout protection** prevents infinite execution
4. ✅ **Immutable audit trail** for court admissibility
5. ✅ **Evidence chain integrity** with triple-hash verification
6. ✅ **DOJ-grade consensus** (≥70% threshold)
7. ✅ **FRE 902 compliance** for self-authenticating evidence

This architecture guarantees that forensic dossiers produced by JLAW meet the highest prosecutorial standards and are admissible in federal court.
