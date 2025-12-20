"""
Integration Test for Strict Execution Mode
===========================================

End-to-end test demonstrating strict mode workflow.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import date
from config.strict_execution_config import load_config, StrictExecutionConfig
from src.core.strict_execution_controller import (
    StrictExecutionController,
    ExecutionAbortException
)


def test_strict_mode_complete_success():
    """Test complete successful execution in strict mode."""
    config = load_config("strict")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        controller = StrictExecutionController(
            config,
            "INTEGRATION-TEST-001",
            Path(tmpdir)
        )
        
        # Phase 1: Configuration - Success
        controller.begin_phase("Phase 1: Configuration & Target Acquisition")
        phase1_data = {
            "modules_loaded": 6,
            "sec_client_available": True,
            "sec_config_valid": True,
            "errors": []
        }
        result = controller.complete_phase(
            "Phase 1: Configuration & Target Acquisition",
            phase1_data,
            records_extracted=6,
            records_expected=6
        )
        assert result is True
        
        # Phase 2: Data Collection - Success
        controller.begin_phase("Phase 2: SEC EDGAR Data Collection")
        phase2_data = {
            "filings_collected": 30,
            "filings_by_type": {
                "10-K": 2,
                "10-Q": 4,
                "DEF 14A": 2,
                "4": 12,
                "8-K": 10
            },
            "errors": []
        }
        result = controller.complete_phase(
            "Phase 2: SEC EDGAR Data Collection",
            phase2_data,
            records_extracted=30
        )
        assert result is True
        
        # Finalize (skip phases that don't have contracts)
        exit_code = controller.finalize()
        assert exit_code == 0
        
        # Check audit trail
        summary = controller.audit.get_summary()
        assert summary["gates"]["passed"] == 2
        assert summary["gates"]["failed"] == 0


def test_strict_mode_data_collection_failure():
    """Test cascade abort on data collection failure."""
    config = load_config("strict")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        controller = StrictExecutionController(
            config,
            "INTEGRATION-TEST-002",
            Path(tmpdir)
        )
        
        # Phase 1: Success
        controller.begin_phase("Phase 1: Configuration")
        phase1_data = {
            "modules_loaded": 6,
            "sec_client_available": True,
            "sec_config_valid": True,
            "errors": []
        }
        controller.complete_phase("Phase 1: Configuration", phase1_data)
        
        # Phase 2: Failure - Insufficient filings
        controller.begin_phase("Phase 2: SEC EDGAR Data Collection")
        phase2_data = {
            "filings_collected": 2,  # Below threshold of 5
            "filings_by_type": {"10-K": 2},
            "errors": []
        }
        
        # Should raise ExecutionAbortException
        with pytest.raises(ExecutionAbortException) as exc_info:
            controller.complete_phase(
                "Phase 2: SEC EDGAR Data Collection",
                phase2_data
            )
        
        # Verify abort details
        assert exc_info.value.exit_code == 2  # Data collection failure
        assert exc_info.value.phase == "Phase 2: SEC EDGAR Data Collection"
        assert controller.execution_aborted is True
        
        # Verify audit trail
        summary = controller.audit.get_summary()
        assert summary["aborted"] is True
        assert summary["gates"]["failed"] >= 1


def test_strict_mode_node_execution_failure():
    """Test cascade abort on node execution failure."""
    config = load_config("strict")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        controller = StrictExecutionController(
            config,
            "INTEGRATION-TEST-003",
            Path(tmpdir)
        )
        
        # Phases 1 & 2: Success
        controller.begin_phase("Phase 1: Configuration")
        controller.complete_phase("Phase 1: Configuration", {
            "modules_loaded": 6,
            "sec_client_available": True,
            "sec_config_valid": True,
            "errors": []
        })
        
        controller.begin_phase("Phase 2: Data Collection")
        controller.complete_phase("Phase 2: Data Collection", {
            "filings_collected": 20,
            "filings_by_type": {
                "10-K": 2,
                "10-Q": 4,
                "DEF 14A": 2,
                "4": 12,
                "8-K": 10
            },
            "errors": []
        })
        
        # Phase 4: Failure - Too many node failures
        controller.begin_phase("Phase 4: Node Analysis")
        phase4_data = {
            "nodes_executed": 15,
            "nodes_successful": 8,  # Below threshold of 12
            "node_results": {},
            "errors": []
        }
        
        with pytest.raises(ExecutionAbortException) as exc_info:
            controller.complete_phase("Phase 4: Node Analysis", phase4_data)
        
        assert exc_info.value.exit_code == 4  # Node execution failure


def test_non_strict_mode_continues_on_warnings():
    """Test that non-strict mode continues with warnings."""
    config = StrictExecutionConfig(strict_mode=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        controller = StrictExecutionController(
            config,
            "INTEGRATION-TEST-004",
            Path(tmpdir)
        )
        
        # Phase with warnings but not critical
        controller.begin_phase("Phase 2: Data Collection")
        phase2_data = {
            "filings_collected": 3,  # Below strict threshold but may pass
            "filings_by_type": {},
            "errors": []
        }
        
        # In non-strict mode, should not abort
        # May return True or False depending on contract, but won't raise
        try:
            result = controller.complete_phase(
                "Phase 2: Data Collection",
                phase2_data
            )
            # If it gets here, no abort occurred
            assert controller.execution_aborted is False
        except ExecutionAbortException:
            # Should not happen in non-strict mode
            pytest.fail("Non-strict mode should not abort")


def test_abort_report_generation():
    """Test that abort report is generated on failure."""
    config = load_config("strict")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        controller = StrictExecutionController(
            config,
            "INTEGRATION-TEST-005",
            Path(tmpdir)
        )
        
        controller.begin_phase("Phase 1: Configuration")
        phase1_data = {
            "modules_loaded": 2,  # Insufficient
            "sec_client_available": False,
            "sec_config_valid": False,
            "errors": ["Module load failed"]
        }
        
        try:
            controller.complete_phase("Phase 1: Configuration", phase1_data)
        except ExecutionAbortException:
            pass
        
        # Generate abort report
        report = controller.audit.generate_abort_report()
        
        assert "ABORTED" in report
        assert "INTEGRATION-TEST-005" in report
        assert "Phase 1" in report
        
        # Check that audit trail file exists
        audit_files = list(Path(tmpdir).glob("audit_trail_*.json"))
        assert len(audit_files) > 0


def test_exit_code_mapping():
    """Test that different phases produce correct exit codes."""
    test_cases = [
        ("Phase 1: Configuration", 1),
        ("Phase 2: SEC EDGAR Data Collection", 2),
        ("Phase 3: DocsGPT Document Parsing", 3),
        ("Phase 4: 15-Node Recursive Analysis", 4),
        ("Phase 5: Advanced Detection Patterns", 5),
        ("Phase 8: Evidence Chain Finalization", 6),
        ("Phase 9: DOJ-Grade Dossier Generation", 7),
    ]
    
    config = load_config("strict")
    
    for phase_name, expected_exit_code in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            controller = StrictExecutionController(
                config,
                f"EXIT-CODE-TEST-{expected_exit_code}",
                Path(tmpdir)
            )
            
            exit_code = controller._get_exit_code_for_phase(phase_name)
            assert exit_code == expected_exit_code, \
                f"Phase '{phase_name}' should have exit code {expected_exit_code}, got {exit_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
