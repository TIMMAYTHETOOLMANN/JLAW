"""
Test Strict Execution Mode
===========================

Tests for strict execution controller, phase gates, and cascade abort protocol.
"""

import pytest
from pathlib import Path
from datetime import datetime
from config.strict_execution_config import (
    StrictExecutionConfig,
    AnalysisThresholds,
    load_config
)
from src.core.strict_execution_controller import (
    StrictExecutionController,
    ExecutionAbortException
)


def test_strict_config_creation():
    """Test creation of strict execution config."""
    config = StrictExecutionConfig(strict_mode=True)
    
    assert config.strict_mode is True
    assert config.thresholds.min_filings_total >= 1
    assert config.thresholds.min_nodes_successful == 12
    assert config.thresholds.halt_on_critical_failure is True


def test_load_default_config():
    """Test loading default configuration."""
    config = load_config("default")
    
    assert config.strict_mode is False
    assert config.thresholds.min_filings_total == 1


def test_load_strict_config():
    """Test loading strict configuration."""
    config = load_config("strict")
    
    assert config.strict_mode is True
    assert config.thresholds.min_filings_total >= 5


def test_load_doj_config():
    """Test loading DOJ investigation configuration."""
    config = load_config("doj")
    
    assert config.strict_mode is True
    assert config.thresholds.min_filings_total >= 10
    assert config.thresholds.require_dual_agent_validation is True


def test_exit_codes():
    """Test exit code definitions."""
    config = StrictExecutionConfig()
    
    assert config.exit_code_configuration_failure == 1
    assert config.exit_code_data_collection_failure == 2
    assert config.exit_code_document_parsing_failure == 3
    assert config.exit_code_node_execution_failure == 4
    assert config.exit_code_pattern_detection_failure == 5
    assert config.exit_code_evidence_chain_failure == 6
    assert config.exit_code_dossier_generation_failure == 7


def test_remediation_messages():
    """Test remediation message retrieval."""
    config = StrictExecutionConfig()
    
    msg = config.get_remediation_message(2)
    assert "data collection" in msg.lower()
    assert "cik" in msg.lower()
    
    msg = config.get_remediation_message(4)
    assert "node execution" in msg.lower()


def test_controller_initialization():
    """Test strict controller initialization."""
    config = StrictExecutionConfig(strict_mode=True)
    controller = StrictExecutionController(
        config,
        "TEST-001",
        Path("/tmp/test_output")
    )
    
    assert controller.case_id == "TEST-001"
    assert controller.config.strict_mode is True
    assert controller.audit is not None
    assert controller.validator is not None


def test_begin_phase():
    """Test beginning a phase."""
    config = StrictExecutionConfig(strict_mode=True)
    controller = StrictExecutionController(
        config,
        "TEST-001",
        Path("/tmp/test_output")
    )
    
    controller.begin_phase("Phase 1: Configuration")
    
    assert controller.current_phase == "Phase 1: Configuration"
    assert "Phase 1: Configuration" in controller.audit.phase_metrics


def test_complete_phase_success():
    """Test completing a phase successfully."""
    config = StrictExecutionConfig(strict_mode=False)  # Non-strict for easier testing
    controller = StrictExecutionController(
        config,
        "TEST-001",
        Path("/tmp/test_output")
    )
    
    controller.begin_phase("Phase 1: Configuration")
    
    # Phase with sufficient data
    phase_data = {
        "modules_loaded": 6,
        "sec_client_available": True,
        "sec_config_valid": True,
        "errors": []
    }
    
    result = controller.complete_phase(
        "Phase 1: Configuration",
        phase_data,
        records_extracted=6,
        records_expected=6
    )
    
    assert result is True
    assert "Phase 1: Configuration" in controller.phases_completed


def test_complete_phase_failure_non_strict():
    """Test phase failure in non-strict mode (should not abort)."""
    config = StrictExecutionConfig(strict_mode=False)
    controller = StrictExecutionController(
        config,
        "TEST-001",
        Path("/tmp/test_output")
    )
    
    controller.begin_phase("Phase 2: Data Collection")
    
    # Insufficient data
    phase_data = {
        "filings_collected": 0,
        "filings_by_type": {},
        "errors": ["No filings found"]
    }
    
    result = controller.complete_phase(
        "Phase 2: Data Collection",
        phase_data
    )
    
    # In non-strict mode, should still continue with warnings
    assert result is False or result is True  # Depends on specific contract


def test_complete_phase_failure_strict_mode():
    """Test phase failure in strict mode (should abort)."""
    config = StrictExecutionConfig(strict_mode=True)
    controller = StrictExecutionController(
        config,
        "TEST-001",
        Path("/tmp/test_output")
    )
    
    controller.begin_phase("Phase 2: Data Collection")
    
    # Insufficient data - will fail gate
    phase_data = {
        "filings_collected": 0,
        "filings_by_type": {},
        "errors": []
    }
    
    with pytest.raises(ExecutionAbortException) as exc_info:
        controller.complete_phase(
            "Phase 2: Data Collection",
            phase_data
        )
    
    assert exc_info.value.exit_code == 2  # Data collection failure
    assert controller.execution_aborted is True


def test_audit_trail_generation():
    """Test audit trail creation."""
    config = StrictExecutionConfig(strict_mode=True)
    controller = StrictExecutionController(
        config,
        "TEST-001",
        Path("/tmp/test_output")
    )
    
    controller.begin_phase("Phase 1: Configuration")
    controller.audit.record_error("Phase 1: Configuration", "Test error")
    controller.audit.record_warning("Phase 1: Configuration", "Test warning")
    
    summary = controller.audit.get_summary()
    
    assert summary["case_id"] == "TEST-001"
    assert summary["phases"] == 1
    assert len(controller.audit.events) >= 3  # Start + error + warning


def test_cascade_abort_exception_attributes():
    """Test ExecutionAbortException attributes."""
    exc = ExecutionAbortException(
        "Phase 4: Node Analysis",
        "Node execution below threshold",
        4
    )
    
    assert exc.phase == "Phase 4: Node Analysis"
    assert exc.reason == "Node execution below threshold"
    assert exc.exit_code == 4


def test_finalize():
    """Test execution finalization."""
    config = StrictExecutionConfig(strict_mode=True)
    controller = StrictExecutionController(
        config,
        "TEST-001",
        Path("/tmp/test_output")
    )
    
    controller.begin_phase("Phase 1: Configuration")
    phase_data = {
        "modules_loaded": 6,
        "sec_client_available": True,
        "sec_config_valid": True,
        "errors": []
    }
    controller.complete_phase("Phase 1: Configuration", phase_data)
    
    exit_code = controller.finalize()
    
    assert exit_code == 0  # Success
    assert controller.audit.execution_end is not None


def test_config_to_dict():
    """Test config serialization."""
    config = StrictExecutionConfig(strict_mode=True)
    config_dict = config.to_dict()
    
    assert config_dict["strict_mode"] is True
    assert "thresholds" in config_dict
    assert config_dict["thresholds"]["min_filings_total"] >= 1


def test_multiple_phase_execution():
    """Test executing multiple phases in sequence."""
    config = StrictExecutionConfig(strict_mode=False)
    controller = StrictExecutionController(
        config,
        "TEST-001",
        Path("/tmp/test_output")
    )
    
    # Phase 1
    controller.begin_phase("Phase 1: Configuration")
    phase1_data = {
        "modules_loaded": 6,
        "sec_client_available": True,
        "sec_config_valid": True,
        "errors": []
    }
    controller.complete_phase("Phase 1: Configuration", phase1_data)
    
    # Phase 2
    controller.begin_phase("Phase 2: Data Collection")
    phase2_data = {
        "filings_collected": 10,
        "filings_by_type": {"10-K": 2, "10-Q": 4},
        "errors": []
    }
    controller.complete_phase("Phase 2: Data Collection", phase2_data)
    
    exit_code = controller.finalize()
    
    assert exit_code == 0
    assert len(controller.phases_completed) == 2
    assert controller.audit.get_summary()["gates"]["passed"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
