"""
Test Phase Gate Validation
===========================

Tests for phase gate validators and data contract enforcement.
"""

import pytest
from src.core.data_contracts import (
    Phase1ConfigurationContract,
    Phase2DataCollectionContract,
    Phase3DocumentParsingContract,
    Phase4NodeAnalysisContract,
    Phase5PatternDetectionContract,
    Phase8EvidenceChainContract,
    ContractViolationType,
    create_contract_for_phase
)
from src.core.phase_gate_validator import (
    PhaseGateValidator,
    GateDecision
)


class TestDataContracts:
    """Test individual data contracts."""
    
    def test_phase1_configuration_success(self):
        """Test Phase 1 contract with valid data."""
        contract = Phase1ConfigurationContract(strict_mode=False)
        
        data = {
            "sec_client_available": True,
            "modules_loaded": 6,
            "sec_config_valid": True
        }
        
        result = contract.validate(data)
        assert result.passed is True
        assert len(result.violations) == 0
    
    def test_phase1_configuration_failure(self):
        """Test Phase 1 contract with invalid data."""
        contract = Phase1ConfigurationContract(strict_mode=True)
        
        data = {
            "sec_client_available": False,
            "modules_loaded": 2,
            "sec_config_valid": False
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert len(result.violations) > 0
        assert any(v.violation_type == ContractViolationType.MISSING_REQUIRED_FIELD for v in result.violations)
    
    def test_phase2_data_collection_success(self):
        """Test Phase 2 contract with sufficient filings."""
        contract = Phase2DataCollectionContract(min_filings_total=5, strict_mode=False)
        
        data = {
            "filings_collected": 10,
            "filings_by_type": {"10-K": 2, "10-Q": 4, "8-K": 4},
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is True
    
    def test_phase2_data_collection_failure(self):
        """Test Phase 2 contract with insufficient filings."""
        contract = Phase2DataCollectionContract(min_filings_total=5, strict_mode=True)
        
        data = {
            "filings_collected": 2,
            "filings_by_type": {"10-K": 2},
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any(v.violation_type == ContractViolationType.INSUFFICIENT_RECORDS for v in result.violations)
    
    def test_phase2_per_type_minimums(self):
        """Test Phase 2 contract with per-type minimum requirements."""
        min_per_type = {"10-K": 1, "10-Q": 3, "DEF 14A": 1}
        contract = Phase2DataCollectionContract(
            min_filings_total=1,
            min_filings_per_type=min_per_type,
            strict_mode=True
        )
        
        # Missing 10-Q filings
        data = {
            "filings_collected": 10,
            "filings_by_type": {"10-K": 2, "10-Q": 1, "DEF 14A": 1, "8-K": 6},
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any("10-Q" in v.message for v in result.violations)
    
    def test_phase3_document_parsing_success(self):
        """Test Phase 3 contract with parsed documents."""
        contract = Phase3DocumentParsingContract(min_parsed=5, strict_mode=False)
        
        data = {
            "parsed": 10,
            "indexed": 50,
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is True
    
    def test_phase3_document_parsing_failure(self):
        """Test Phase 3 contract with no parsed documents."""
        contract = Phase3DocumentParsingContract(min_parsed=1, strict_mode=True)
        
        data = {
            "parsed": 0,
            "indexed": 0,
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is False
    
    def test_phase4_node_analysis_success(self):
        """Test Phase 4 contract with sufficient nodes."""
        contract = Phase4NodeAnalysisContract(
            min_nodes_successful=12,
            min_success_rate=0.80,
            strict_mode=True
        )
        
        data = {
            "nodes_executed": 15,
            "nodes_successful": 14,
            "node_results": {"phase1": [], "phase2": []},
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is True
    
    def test_phase4_node_analysis_failure_count(self):
        """Test Phase 4 contract with insufficient successful nodes."""
        contract = Phase4NodeAnalysisContract(
            min_nodes_successful=12,
            min_success_rate=0.80,
            strict_mode=True
        )
        
        data = {
            "nodes_executed": 15,
            "nodes_successful": 10,  # Below threshold
            "node_results": {"phase1": []},
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is False
    
    def test_phase4_node_analysis_failure_rate(self):
        """Test Phase 4 contract with low success rate."""
        contract = Phase4NodeAnalysisContract(
            min_nodes_successful=10,
            min_success_rate=0.80,
            strict_mode=True
        )
        
        data = {
            "nodes_executed": 15,
            "nodes_successful": 10,  # 66% success rate
            "node_results": {"phase1": []},
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any("success rate" in v.message.lower() for v in result.violations)
    
    def test_phase5_pattern_detection_success(self):
        """Test Phase 5 contract with sufficient patterns."""
        contract = Phase5PatternDetectionContract(min_patterns_executed=20, strict_mode=True)
        
        data = {
            "patterns_executed": 22,
            "total_alerts": 15,
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is True
    
    def test_phase5_pattern_detection_failure(self):
        """Test Phase 5 contract with insufficient patterns."""
        contract = Phase5PatternDetectionContract(min_patterns_executed=20, strict_mode=True)
        
        data = {
            "patterns_executed": 15,
            "total_alerts": 5,
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is False
    
    def test_phase8_evidence_chain_success(self):
        """Test Phase 8 contract with evidence chain."""
        contract = Phase8EvidenceChainContract(require_evidence_chain=True, strict_mode=True)
        
        data = {
            "custody_records": 10,
            "evidence_chain_hash": "abc123def456",
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is True
    
    def test_phase8_evidence_chain_failure(self):
        """Test Phase 8 contract without evidence chain."""
        contract = Phase8EvidenceChainContract(require_evidence_chain=True, strict_mode=True)
        
        data = {
            "custody_records": 0,
            "evidence_chain_hash": None,
            "errors": []
        }
        
        result = contract.validate(data)
        assert result.passed is False


class TestPhaseGateValidator:
    """Test phase gate validator."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        config = {
            "strict_mode": True,
            "halt_on_critical_failure": True,
            "min_filings_total": 5
        }
        
        validator = PhaseGateValidator(config)
        
        assert validator.strict_mode is True
        assert validator.halt_on_critical_failure is True
    
    def test_validate_gate_pass(self):
        """Test gate validation that passes."""
        config = {
            "strict_mode": False,
            "halt_on_critical_failure": True,
            "min_filings_total": 1
        }
        
        validator = PhaseGateValidator(config)
        
        phase_data = {
            "filings_collected": 10,
            "filings_by_type": {"10-K": 2},
            "errors": []
        }
        
        decision, result = validator.validate_gate(
            "Phase 2: SEC EDGAR Data Collection",
            phase_data
        )
        
        assert decision == GateDecision.PASS
        assert result.passed is True
    
    def test_validate_gate_fail_non_strict(self):
        """Test gate validation failure in non-strict mode."""
        config = {
            "strict_mode": False,
            "halt_on_critical_failure": False,
            "min_filings_total": 5
        }
        
        validator = PhaseGateValidator(config)
        
        phase_data = {
            "filings_collected": 2,
            "filings_by_type": {},
            "errors": []
        }
        
        decision, result = validator.validate_gate(
            "Phase 2: SEC EDGAR Data Collection",
            phase_data
        )
        
        # In non-strict mode, might allow override
        assert decision in [GateDecision.OVERRIDE_REQUIRED, GateDecision.PASS]
    
    def test_validate_gate_fail_strict(self):
        """Test gate validation failure in strict mode."""
        config = {
            "strict_mode": True,
            "halt_on_critical_failure": True,
            "min_filings_total": 5
        }
        
        validator = PhaseGateValidator(config)
        
        phase_data = {
            "filings_collected": 2,
            "filings_by_type": {},
            "errors": []
        }
        
        decision, result = validator.validate_gate(
            "Phase 2: SEC EDGAR Data Collection",
            phase_data
        )
        
        assert decision == GateDecision.FAIL
        assert result.passed is False
    
    def test_validation_history(self):
        """Test validation history tracking."""
        config = {
            "strict_mode": False,
            "min_filings_total": 1
        }
        
        validator = PhaseGateValidator(config)
        
        # Validate phase 1
        validator.validate_gate(
            "Phase 1: Configuration",
            {
                "modules_loaded": 6,
                "sec_client_available": True,
                "sec_config_valid": True
            }
        )
        
        # Validate phase 2
        validator.validate_gate(
            "Phase 2: Data Collection",
            {
                "filings_collected": 10,
                "filings_by_type": {},
                "errors": []
            }
        )
        
        summary = validator.get_validation_summary()
        
        assert summary["total_validations"] == 2
        assert len(summary["phases"]) == 2
    
    def test_should_halt_execution(self):
        """Test halt execution decision logic."""
        config = {
            "strict_mode": True,
            "halt_on_critical_failure": True
        }
        
        validator = PhaseGateValidator(config)
        
        assert validator.should_halt_execution(GateDecision.PASS) is False
        assert validator.should_halt_execution(GateDecision.FAIL) is True
        assert validator.should_halt_execution(GateDecision.OVERRIDE_REQUIRED) is True


class TestContractFactory:
    """Test contract factory function."""
    
    def test_create_phase1_contract(self):
        """Test creating Phase 1 contract."""
        config = {"strict_mode": True}
        contract = create_contract_for_phase("Phase 1: Configuration", config)
        
        assert isinstance(contract, Phase1ConfigurationContract)
    
    def test_create_phase2_contract(self):
        """Test creating Phase 2 contract."""
        config = {
            "strict_mode": True,
            "min_filings_total": 5
        }
        contract = create_contract_for_phase("Phase 2: Data Collection", config)
        
        assert isinstance(contract, Phase2DataCollectionContract)
    
    def test_create_phase4_contract(self):
        """Test creating Phase 4 contract."""
        config = {
            "strict_mode": True,
            "min_nodes_successful": 12
        }
        contract = create_contract_for_phase("Phase 4: Node Analysis", config)
        
        assert isinstance(contract, Phase4NodeAnalysisContract)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
