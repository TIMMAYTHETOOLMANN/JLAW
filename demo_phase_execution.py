#!/usr/bin/env python3
"""
Phase Execution Framework Demonstration
========================================

Demonstrates the Phase Execution Framework in action with a simple
mock analysis that shows phase dependencies, validation, and audit trail.

This script shows:
1. Phase execution with dependencies
2. Phase gate validation (strict mode)
3. Timeout handling
4. Immutable audit trail generation
5. Execution summary reporting
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from src.core.phase_execution_framework import (
    PhaseExecutionFramework,
    PhaseStatus,
    PHASE_REGISTRY
)
from src.core.exceptions import PhaseGateFailure, PhaseDependencyError


# ═══════════════════════════════════════════════════════════════════════════
# MOCK PHASE EXECUTORS
# ═══════════════════════════════════════════════════════════════════════════

async def mock_phase_1_executor(**kwargs):
    """Mock Phase 1: Configuration & Target Acquisition."""
    print("  → Loading configuration...")
    await asyncio.sleep(0.5)  # Simulate work
    print("  → Initializing SEC client...")
    await asyncio.sleep(0.3)
    print("  ✓ Configuration complete")
    
    return {
        "sec_client_available": True,
        "modules_loaded": 6,  # Exact match required
        "sec_config_valid": True
    }


async def mock_phase_2_executor(**kwargs):
    """Mock Phase 2: SEC EDGAR Data Collection."""
    print("  → Fetching SEC filings...")
    await asyncio.sleep(0.8)
    print("  → Downloaded 15 filings")
    print("  ✓ Data collection complete")
    
    return {
        "filings_collected": 15,
        "all_filings_have_content": True
    }


async def mock_phase_3_executor(**kwargs):
    """Mock Phase 3: Document Parsing & Indexing."""
    print("  → Parsing documents...")
    await asyncio.sleep(0.6)
    print("  → Parsed 12 of 15 documents (80%)")
    print("  ✓ Parsing complete")
    
    return {
        "documents_parsed": 12,
        "parsing_success_rate": 0.80
    }


async def mock_phase_4_executor(**kwargs):
    """Mock Phase 4: 15-Node Recursive Analysis."""
    print("  → Executing node analysis...")
    await asyncio.sleep(1.0)
    print("  → Completed 13 of 15 nodes (87%)")
    print("  ✓ Node analysis complete")
    
    return {
        "nodes_executed": 13,
        "node_success_rate": 0.87
    }


async def mock_phase_5_executor(**kwargs):
    """Mock Phase 5: Advanced Pattern Detection."""
    print("  → Running fraud detection algorithms...")
    await asyncio.sleep(0.7)
    print("  → Executed 15 of 23 patterns (65%)")
    print("  ✓ Pattern detection complete")
    
    return {
        "patterns_executed": 15,
        "pattern_execution_rate": 0.65
    }


async def mock_phase_6_executor(**kwargs):
    """Mock Phase 6: Dual-Agent AI Cross-Validation."""
    print("  → Running AI validation...")
    await asyncio.sleep(0.9)
    print("  → 2 AI agents executed")
    print("  ✓ AI validation complete")
    
    return {
        "ai_agents_executed": 2,
        "violations_analyzed": 5
    }


async def mock_phase_7_executor(**kwargs):
    """Mock Phase 7: Unified Agent Orchestration."""
    print("  → Orchestrating agents...")
    await asyncio.sleep(1.2)
    print("  → 5 agents invoked, 75% consensus")
    print("  ✓ Orchestration complete")
    
    return {
        "agents_invoked": 5,
        "consensus_score": 0.75,  # Passes 70% threshold
        "orchestration_completed": True
    }


async def mock_phase_8_executor(**kwargs):
    """Mock Phase 8: Evidence Chain Integrity Verification."""
    print("  → Verifying evidence chain...")
    await asyncio.sleep(0.4)
    print("  → All hashes verified")
    print("  → Chain of custody complete")
    print("  ✓ Evidence chain verified")
    
    return {
        "all_hashes_verified": True,
        "chain_of_custody_complete": True,
        "fre_902_compliant": True,
        "merkle_root_generated": True
    }


async def mock_phase_9_executor(**kwargs):
    """Mock Phase 9: DOJ-Grade Report Generation."""
    print("  → Generating forensic dossier...")
    await asyncio.sleep(0.6)
    print("  → Generated JSON dossier")
    print("  → Generated PDF report")
    print("  ✓ Report generation complete")
    
    return {
        "dossier_generated": True,
        "pdf_generated": True,
        "all_violations_documented": True
    }


# ═══════════════════════════════════════════════════════════════════════════
# DEMONSTRATION SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════

async def scenario_1_successful_execution():
    """Scenario 1: Complete successful execution in strict mode."""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Successful 9-Phase Execution (Strict Mode)")
    print("=" * 80)
    
    framework = PhaseExecutionFramework(strict_mode=True)
    
    # Execute all 9 phases in order
    phases = [
        ("phase_1_initialization", mock_phase_1_executor),
        ("phase_2_data_collection", mock_phase_2_executor),
        ("phase_3_document_parsing", mock_phase_3_executor),
        ("phase_4_node_analysis", mock_phase_4_executor),
        ("phase_5_pattern_detection", mock_phase_5_executor),
        ("phase_6_dual_agent", mock_phase_6_executor),
        ("phase_7_subagent_orchestration", mock_phase_7_executor),
        ("phase_8_evidence_chain", mock_phase_8_executor),
        ("phase_9_report_generation", mock_phase_9_executor),
    ]
    
    for phase_id, executor in phases:
        result = await framework.execute_phase(phase_id, executor)
        if result.status != PhaseStatus.SUCCESS:
            print(f"✗ Phase {phase_id} failed: {result.error}")
            break
    
    # Get execution summary
    summary = framework.get_execution_summary()
    
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total phases executed: {summary['total_phases_executed']}")
    print(f"Successful phases: {summary['successful_phases']}")
    print(f"Failed phases: {summary['failed_phases']}")
    print(f"Total execution time: {summary['total_execution_time']:.2f}s")
    print(f"All validations passed: {summary['all_validations_passed']}")
    print(f"Strict mode enabled: {summary['strict_mode_enabled']}")
    
    # Export audit trail
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    audit_path = output_dir / "demo_audit_trail.json"
    framework.export_audit_trail(audit_path)
    print(f"\n✓ Audit trail exported to: {audit_path}")
    
    return framework


async def scenario_2_dependency_failure():
    """Scenario 2: Dependency violation (trying to skip Phase 1)."""
    print("\n" + "=" * 80)
    print("SCENARIO 2: Dependency Violation")
    print("=" * 80)
    print("Attempting to execute Phase 2 without executing Phase 1...")
    
    framework = PhaseExecutionFramework(strict_mode=True)
    
    try:
        # Try to execute Phase 2 without Phase 1
        await framework.execute_phase(
            "phase_2_data_collection",
            mock_phase_2_executor
        )
        print("✗ Should have raised PhaseDependencyError!")
    except PhaseDependencyError as e:
        print(f"✓ Correctly caught dependency error: {e}")
    
    return framework


async def scenario_3_gate_failure():
    """Scenario 3: Phase gate validation failure (strict mode)."""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Phase Gate Validation Failure")
    print("=" * 80)
    print("Executing Phase 7 with low consensus score...")
    
    framework = PhaseExecutionFramework(strict_mode=True)
    
    # Execute prerequisite phases
    phases = [
        ("phase_1_initialization", mock_phase_1_executor),
        ("phase_2_data_collection", mock_phase_2_executor),
        ("phase_3_document_parsing", mock_phase_3_executor),
        ("phase_4_node_analysis", mock_phase_4_executor),
        ("phase_5_pattern_detection", mock_phase_5_executor),
        ("phase_6_dual_agent", mock_phase_6_executor),
    ]
    
    for phase_id, executor in phases:
        await framework.execute_phase(phase_id, executor)
    
    # Execute Phase 7 with low consensus
    async def bad_phase_7_executor(**kwargs):
        return {
            "agents_invoked": 3,
            "consensus_score": 0.65,  # Below 70% threshold
            "orchestration_completed": True
        }
    
    try:
        await framework.execute_phase(
            "phase_7_subagent_orchestration",
            bad_phase_7_executor
        )
        print("✗ Should have raised PhaseGateFailure!")
    except PhaseGateFailure as e:
        print(f"✓ Correctly caught gate failure: {e}")
    
    return framework


async def main():
    """Run all demonstration scenarios."""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "PHASE EXECUTION FRAMEWORK DEMONSTRATION" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Show phase registry
    print("\nREGISTERED PHASES:")
    print("-" * 80)
    for phase_id, phase_def in PHASE_REGISTRY.items():
        deps = ", ".join(phase_def.depends_on) if phase_def.depends_on else "None"
        print(f"  {phase_def.phase_number}. {phase_def.phase_name}")
        print(f"     Dependencies: {deps}")
        print(f"     Timeout: {phase_def.timeout_seconds}s")
    
    # Run scenarios
    await scenario_1_successful_execution()
    await scenario_2_dependency_failure()
    await scenario_3_gate_failure()
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  ✓ Phase dependencies are enforced")
    print("  ✓ Phase gates validate output quality in strict mode")
    print("  ✓ Consensus threshold (70%) is validated for DOJ submission")
    print("  ✓ Immutable audit trail is generated automatically")
    print("  ✓ All phases must succeed for DOJ-grade output")


if __name__ == "__main__":
    asyncio.run(main())
