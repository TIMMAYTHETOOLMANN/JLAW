"""
Test Phase Execution Framework
===============================

Comprehensive tests for phase execution flow, dependency validation,
phase gating, timeout handling, and audit trail generation.
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.core.phase_execution_framework import (
    PhaseExecutionFramework,
    PhaseDefinition,
    PhaseResult,
    PhaseStatus,
    PHASE_REGISTRY,
)
from src.core.exceptions import (
    PhaseDefinitionError,
    PhaseDependencyError,
    PhaseGateFailure,
)


# ═══════════════════════════════════════════════════════════════════════════
# TEST FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def framework():
    """Create phase execution framework instance."""
    return PhaseExecutionFramework(strict_mode=False)


@pytest.fixture
def strict_framework():
    """Create strict mode phase execution framework instance."""
    return PhaseExecutionFramework(strict_mode=True)


@pytest.fixture
async def mock_phase_executor():
    """Create mock phase executor function."""
    async def executor(**kwargs):
        await asyncio.sleep(0.01)  # Simulate work
        return {
            "status": "completed",
            "items_processed": 10,
            "sec_client_available": True,
            "modules_loaded": 8,
            "sec_config_valid": True,
        }
    return executor


@pytest.fixture
async def failing_phase_executor():
    """Create mock failing phase executor."""
    async def executor(**kwargs):
        raise ValueError("Simulated phase failure")
    return executor


@pytest.fixture
async def slow_phase_executor():
    """Create mock slow phase executor that times out."""
    async def executor(**kwargs):
        await asyncio.sleep(10)  # Will timeout
        return {"status": "completed"}
    return executor


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: BASIC PHASE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

class TestBasicPhaseExecution:
    """Test basic phase execution functionality."""
    
    @pytest.mark.asyncio
    async def test_execute_single_phase_success(self, framework, mock_phase_executor):
        """Test successful execution of a single phase."""
        result = await framework.execute_phase(
            "phase_1_initialization",
            executor=mock_phase_executor
        )
        
        assert result.status == PhaseStatus.SUCCESS
        assert result.error is None
        assert result.result is not None
        assert result.execution_time > 0
        assert "phase_1_initialization" in framework.phase_results
    
    @pytest.mark.asyncio
    async def test_execute_phase_with_error(self, framework, failing_phase_executor):
        """Test phase execution with error."""
        result = await framework.execute_phase(
            "phase_1_initialization",
            executor=failing_phase_executor
        )
        
        assert result.status == PhaseStatus.ERROR
        assert result.error is not None
        assert "ValueError" in result.error
        assert result.result is None
    
    @pytest.mark.asyncio
    async def test_phase_not_found(self, framework, mock_phase_executor):
        """Test execution of non-existent phase."""
        with pytest.raises(PhaseDefinitionError, match="Unknown phase"):
            await framework.execute_phase(
                "phase_99_nonexistent",
                executor=mock_phase_executor
            )
    
    @pytest.mark.asyncio
    async def test_execution_log_created(self, framework, mock_phase_executor):
        """Test that execution log is created."""
        await framework.execute_phase(
            "phase_1_initialization",
            executor=mock_phase_executor
        )
        
        assert len(framework.execution_log) == 1
        record = framework.execution_log[0]
        assert record.phase_id == "phase_1_initialization"
        assert record.phase_number == 1
        assert record.status == PhaseStatus.SUCCESS


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: DEPENDENCY VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

class TestDependencyValidation:
    """Test phase dependency validation."""
    
    @pytest.mark.asyncio
    async def test_dependency_not_executed(self, framework, mock_phase_executor):
        """Test that execution fails if dependency not executed."""
        with pytest.raises(PhaseDependencyError, match="requires .* to complete first"):
            await framework.execute_phase(
                "phase_2_data_collection",  # Depends on phase_1
                executor=mock_phase_executor
            )
    
    @pytest.mark.asyncio
    async def test_dependency_failed(self, framework, mock_phase_executor, failing_phase_executor):
        """Test that execution fails if dependency failed."""
        # Execute phase 1 with failure
        await framework.execute_phase(
            "phase_1_initialization",
            executor=failing_phase_executor
        )
        
        # Try to execute phase 2 (depends on phase 1)
        with pytest.raises(PhaseDependencyError, match="failed with status"):
            await framework.execute_phase(
                "phase_2_data_collection",
                executor=mock_phase_executor
            )
    
    @pytest.mark.asyncio
    async def test_dependency_chain_success(self, framework, mock_phase_executor):
        """Test successful execution of dependency chain."""
        # Execute phase 1
        result1 = await framework.execute_phase(
            "phase_1_initialization",
            executor=mock_phase_executor
        )
        assert result1.status == PhaseStatus.SUCCESS
        
        # Execute phase 2 (depends on phase 1)
        async def phase2_executor(**kwargs):
            return {
                "filings_collected": 5,
                "all_filings_have_content": True,
            }
        
        result2 = await framework.execute_phase(
            "phase_2_data_collection",
            executor=phase2_executor
        )
        assert result2.status == PhaseStatus.SUCCESS
        assert len(framework.execution_log) == 2


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: PHASE GATE VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

class TestPhaseGateValidation:
    """Test phase gate validation rules."""
    
    @pytest.mark.asyncio
    async def test_gate_validation_disabled_in_standard_mode(self, framework):
        """Test that gate validation doesn't raise in standard mode."""
        async def bad_executor(**kwargs):
            return {
                "sec_client_available": False,  # Violates rule
                "modules_loaded": 2,  # Violates rule
                "sec_config_valid": False,  # Violates rule
            }
        
        # Should succeed even with bad data in standard mode
        result = await framework.execute_phase(
            "phase_1_initialization",
            executor=bad_executor
        )
        assert result.status == PhaseStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_gate_validation_enforced_in_strict_mode(self, strict_framework):
        """Test that gate validation is enforced in strict mode."""
        async def bad_executor(**kwargs):
            return {
                "sec_client_available": False,  # Violates rule
                "modules_loaded": 2,  # Violates rule
                "sec_config_valid": False,  # Violates rule
            }
        
        # Should fail in strict mode
        with pytest.raises(PhaseGateFailure):
            await strict_framework.execute_phase(
                "phase_1_initialization",
                executor=bad_executor
            )
    
    @pytest.mark.asyncio
    async def test_gate_validation_boolean_rule(self, strict_framework):
        """Test boolean validation rule."""
        async def executor(**kwargs):
            return {
                "sec_client_available": True,  # Passes
                "modules_loaded": 6,
                "sec_config_valid": True,
            }
        
        result = await strict_framework.execute_phase(
            "phase_1_initialization",
            executor=executor
        )
        assert result.status == PhaseStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_gate_validation_comparison_rule(self, strict_framework):
        """Test comparison validation rule (>=)."""
        # First execute phase 1
        async def phase1_executor(**kwargs):
            return {
                "sec_client_available": True,
                "modules_loaded": 6,
                "sec_config_valid": True,
            }
        await strict_framework.execute_phase(
            "phase_1_initialization",
            executor=phase1_executor
        )
        
        # Test phase 2 with comparison rule
        async def phase2_executor(**kwargs):
            return {
                "filings_collected": 5,  # Should pass (>=1)
                "all_filings_have_content": True,
            }
        
        result = await strict_framework.execute_phase(
            "phase_2_data_collection",
            executor=phase2_executor
        )
        assert result.status == PhaseStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_gate_validation_comparison_rule_failure(self, strict_framework):
        """Test comparison validation rule failure."""
        # First execute phase 1
        async def phase1_executor(**kwargs):
            return {
                "sec_client_available": True,
                "modules_loaded": 6,
                "sec_config_valid": True,
            }
        await strict_framework.execute_phase(
            "phase_1_initialization",
            executor=phase1_executor
        )
        
        # Test phase 2 with insufficient filings
        async def phase2_executor(**kwargs):
            return {
                "filings_collected": 0,  # Should fail (>=1)
                "all_filings_have_content": True,
            }
        
        with pytest.raises(PhaseGateFailure, match="filings_collected"):
            await strict_framework.execute_phase(
                "phase_2_data_collection",
                executor=phase2_executor
            )
    
    @pytest.mark.asyncio
    async def test_consensus_score_validation(self, strict_framework):
        """Test consensus score validation (>=0.70)."""
        # Execute prerequisite phases
        for phase_id in ["phase_1_initialization", "phase_2_data_collection", 
                        "phase_3_document_parsing", "phase_4_node_analysis",
                        "phase_5_pattern_detection", "phase_6_dual_agent"]:
            async def executor(**kwargs):
                return {
                    "sec_client_available": True,
                    "modules_loaded": 6,
                    "sec_config_valid": True,
                    "filings_collected": 5,
                    "all_filings_have_content": True,
                    "documents_parsed": 5,
                    "parsing_success_rate": 0.90,
                    "nodes_executed": 13,
                    "node_success_rate": 0.85,
                    "patterns_executed": 15,
                    "pattern_execution_rate": 0.65,
                    "ai_agents_executed": 2,
                    "violations_analyzed": 5,
                }
            await strict_framework.execute_phase(phase_id, executor=executor)
        
        # Test phase 7 with good consensus
        async def phase7_executor(**kwargs):
            return {
                "agents_invoked": 5,
                "consensus_score": 0.75,  # Should pass (>=0.70)
                "orchestration_completed": True,
            }
        
        result = await strict_framework.execute_phase(
            "phase_7_subagent_orchestration",
            executor=phase7_executor
        )
        assert result.status == PhaseStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_consensus_score_validation_failure(self, strict_framework):
        """Test consensus score validation failure."""
        # Execute prerequisite phases
        for phase_id in ["phase_1_initialization", "phase_2_data_collection", 
                        "phase_3_document_parsing", "phase_4_node_analysis",
                        "phase_5_pattern_detection", "phase_6_dual_agent"]:
            async def executor(**kwargs):
                return {
                    "sec_client_available": True,
                    "modules_loaded": 6,
                    "sec_config_valid": True,
                    "filings_collected": 5,
                    "all_filings_have_content": True,
                    "documents_parsed": 5,
                    "parsing_success_rate": 0.90,
                    "nodes_executed": 13,
                    "node_success_rate": 0.85,
                    "patterns_executed": 15,
                    "pattern_execution_rate": 0.65,
                    "ai_agents_executed": 2,
                    "violations_analyzed": 5,
                }
            await strict_framework.execute_phase(phase_id, executor=executor)
        
        # Test phase 7 with low consensus
        async def phase7_executor(**kwargs):
            return {
                "agents_invoked": 3,
                "consensus_score": 0.65,  # Should fail (<0.70)
                "orchestration_completed": True,
            }
        
        with pytest.raises(PhaseGateFailure, match="consensus_score"):
            await strict_framework.execute_phase(
                "phase_7_subagent_orchestration",
                executor=phase7_executor
            )


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: TIMEOUT HANDLING
# ═══════════════════════════════════════════════════════════════════════════

class TestTimeoutHandling:
    """Test phase timeout handling."""
    
    @pytest.mark.asyncio
    async def test_phase_timeout(self, framework, slow_phase_executor):
        """Test that slow phase times out."""
        result = await framework.execute_phase(
            "phase_1_initialization",  # Has 30s timeout
            executor=slow_phase_executor
        )
        
        assert result.status == PhaseStatus.TIMEOUT
        assert result.error is not None
        assert "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_timeout_logged_in_audit(self, framework, slow_phase_executor):
        """Test that timeout is logged in audit trail."""
        await framework.execute_phase(
            "phase_1_initialization",
            executor=slow_phase_executor
        )
        
        assert len(framework.execution_log) == 1
        record = framework.execution_log[0]
        assert record.status == PhaseStatus.TIMEOUT
        assert record.error is not None


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════════════════

class TestAuditTrail:
    """Test audit trail generation and export."""
    
    @pytest.mark.asyncio
    async def test_execution_summary(self, framework, mock_phase_executor):
        """Test execution summary generation."""
        await framework.execute_phase(
            "phase_1_initialization",
            executor=mock_phase_executor
        )
        
        summary = framework.get_execution_summary()
        
        assert summary["total_phases_executed"] == 1
        assert summary["successful_phases"] == 1
        assert summary["failed_phases"] == 0
        assert summary["strict_mode_enabled"] is False
        assert "phases" in summary
        assert len(summary["phases"]) == 1
    
    @pytest.mark.asyncio
    async def test_audit_trail_export(self, framework, mock_phase_executor, tmp_path):
        """Test audit trail export to JSON."""
        await framework.execute_phase(
            "phase_1_initialization",
            executor=mock_phase_executor
        )
        
        audit_path = tmp_path / "audit_trail.json"
        framework.export_audit_trail(audit_path)
        
        # Verify file exists
        assert audit_path.exists()
        
        # Verify JSON structure
        with open(audit_path, 'r') as f:
            audit_data = json.load(f)
        
        assert "audit_trail_version" in audit_data
        assert "generation_timestamp" in audit_data
        assert "strict_mode" in audit_data
        assert "execution_summary" in audit_data
        assert "detailed_phase_log" in audit_data
        assert "phase_registry_snapshot" in audit_data
        assert len(audit_data["detailed_phase_log"]) == 1
    
    @pytest.mark.asyncio
    async def test_multiple_phases_in_audit(self, framework):
        """Test multiple phases in audit trail."""
        # Execute phase 1
        async def phase1_executor(**kwargs):
            return {
                "sec_client_available": True,
                "modules_loaded": 6,
                "sec_config_valid": True,
            }
        await framework.execute_phase("phase_1_initialization", executor=phase1_executor)
        
        # Execute phase 2
        async def phase2_executor(**kwargs):
            return {
                "filings_collected": 5,
                "all_filings_have_content": True,
            }
        await framework.execute_phase("phase_2_data_collection", executor=phase2_executor)
        
        summary = framework.get_execution_summary()
        assert summary["total_phases_executed"] == 2
        assert len(framework.execution_log) == 2


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: PHASE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

class TestPhaseRegistry:
    """Test phase registry and definitions."""
    
    def test_phase_registry_complete(self):
        """Test that all 9 phases are defined."""
        assert len(PHASE_REGISTRY) == 9
        
        expected_phases = [
            "phase_1_initialization",
            "phase_2_data_collection",
            "phase_3_document_parsing",
            "phase_4_node_analysis",
            "phase_5_pattern_detection",
            "phase_6_dual_agent",
            "phase_7_subagent_orchestration",
            "phase_8_evidence_chain",
            "phase_9_report_generation",
        ]
        
        for phase_id in expected_phases:
            assert phase_id in PHASE_REGISTRY
    
    def test_phase_numbers_sequential(self):
        """Test that phase numbers are sequential 1-9."""
        phase_numbers = [
            PHASE_REGISTRY[phase_id].phase_number
            for phase_id in PHASE_REGISTRY
        ]
        
        assert sorted(phase_numbers) == list(range(1, 10))
    
    def test_all_phases_required_in_strict(self):
        """Test that all phases are required in strict mode."""
        for phase_def in PHASE_REGISTRY.values():
            assert phase_def.required_in_strict_mode is True
    
    def test_phase_dependencies_valid(self):
        """Test that all phase dependencies are valid."""
        for phase_id, phase_def in PHASE_REGISTRY.items():
            for dep_id in phase_def.depends_on:
                assert dep_id in PHASE_REGISTRY, f"Invalid dependency: {dep_id}"
    
    def test_phase_dependency_order(self):
        """Test that dependencies are always earlier phases."""
        for phase_id, phase_def in PHASE_REGISTRY.items():
            phase_num = phase_def.phase_number
            for dep_id in phase_def.depends_on:
                dep_num = PHASE_REGISTRY[dep_id].phase_number
                assert dep_num < phase_num, f"Dependency {dep_id} should be before {phase_id}"
    
    def test_phase_order_validation(self, framework):
        """Test phase order validation."""
        # Should not raise
        assert framework.validate_phase_order() is True
    
    def test_dependency_graph_generation(self, framework):
        """Test dependency graph generation."""
        graph = framework.get_phase_dependency_graph()
        
        assert len(graph) == 9
        assert graph["phase_1_initialization"] == []
        assert "phase_1_initialization" in graph["phase_2_data_collection"]


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: STRICT MODE VS STANDARD MODE
# ═══════════════════════════════════════════════════════════════════════════

class TestStrictVsStandardMode:
    """Test differences between strict and standard mode."""
    
    @pytest.mark.asyncio
    async def test_standard_mode_allows_bad_data(self, framework):
        """Test that standard mode allows bad data."""
        async def bad_executor(**kwargs):
            return {
                "sec_client_available": False,
                "modules_loaded": 0,
                "sec_config_valid": False,
            }
        
        result = await framework.execute_phase(
            "phase_1_initialization",
            executor=bad_executor
        )
        
        # Should succeed in standard mode
        assert result.status == PhaseStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_strict_mode_rejects_bad_data(self, strict_framework):
        """Test that strict mode rejects bad data."""
        async def bad_executor(**kwargs):
            return {
                "sec_client_available": False,
                "modules_loaded": 0,
                "sec_config_valid": False,
            }
        
        # Should fail in strict mode
        with pytest.raises(PhaseGateFailure):
            await strict_framework.execute_phase(
                "phase_1_initialization",
                executor=bad_executor
            )
    
    @pytest.mark.asyncio
    async def test_strict_mode_in_summary(self, strict_framework, mock_phase_executor):
        """Test that strict mode flag appears in summary."""
        await strict_framework.execute_phase(
            "phase_1_initialization",
            executor=mock_phase_executor
        )
        
        summary = strict_framework.get_execution_summary()
        assert summary["strict_mode_enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
