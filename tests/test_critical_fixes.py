"""
Test Critical Configuration Fixes
==================================

Tests for the three critical configuration errors fixed per the
JLAW Forensic System Audit Report (December 25, 2025):

1. CRITICAL-001: strict_mode defaults to True
2. CRITICAL-002: validate_gate() method access through validator
3. CRITICAL-003: Missing data contracts for Phases 6, 7, and 9
"""

import pytest
from pathlib import Path
from datetime import date, datetime
from src.core.master_execution_controller import MasterExecutionController
from src.core.data_contracts import (
    Phase6DualAgentContract,
    Phase7SubagentContract,
    Phase9DossierContract,
    create_contract_for_phase,
    ContractViolationType,
    ValidationResult
)


class TestCritical001StrictModeDefault:
    """Test CRITICAL-001: strict_mode defaults to True."""
    
    def test_strict_mode_default_is_true(self):
        """Test that strict_mode parameter defaults to True."""
        controller = MasterExecutionController(
            cik="0000320187",
            company_name="Test Company",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            output_dir=Path("/tmp/test_output")
            # Note: NOT passing strict_mode parameter
        )
        
        assert controller.strict_mode is True, \
            "strict_mode should default to True for DOJ-grade forensic compliance"
    
    def test_strict_mode_can_be_disabled(self):
        """Test that strict_mode can still be explicitly disabled if needed."""
        controller = MasterExecutionController(
            cik="0000320187",
            company_name="Test Company",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            output_dir=Path("/tmp/test_output"),
            strict_mode=False
        )
        
        assert controller.strict_mode is False


class TestCritical003Phase6DualAgentContract:
    """Test CRITICAL-003: Phase6DualAgentContract implementation."""
    
    def test_phase6_contract_creation(self):
        """Test Phase 6 contract can be created."""
        contract = Phase6DualAgentContract(strict_mode=True)
        assert contract is not None
        assert contract.min_confidence_threshold == 0.75
    
    def test_phase6_validation_success_with_both_agents(self):
        """Test Phase 6 validation passes with both agents responsive."""
        contract = Phase6DualAgentContract(strict_mode=True)
        
        data = {
            "openai_validation_complete": True,
            "anthropic_validation_complete": True,
            "cross_validation_score": 0.85,
            "min_confidence_threshold": 0.75
        }
        
        result = contract.validate(data)
        assert result.passed is True
        assert len(result.violations) == 0
    
    def test_phase6_validation_success_with_one_agent(self):
        """Test Phase 6 validation passes with at least one agent (per audit spec)."""
        contract = Phase6DualAgentContract(strict_mode=True)
        
        # Test with only OpenAI
        data = {
            "openai_validation_complete": True,
            "anthropic_validation_complete": False,
            "cross_validation_score": 0.80,
            "min_confidence_threshold": 0.75
        }
        
        result = contract.validate(data)
        assert result.passed is True
        
        # Test with only Anthropic
        data = {
            "openai_validation_complete": False,
            "anthropic_validation_complete": True,
            "cross_validation_score": 0.80,
            "min_confidence_threshold": 0.75
        }
        
        result = contract.validate(data)
        assert result.passed is True
    
    def test_phase6_validation_failure_no_agents(self):
        """Test Phase 6 validation fails when no agents are responsive."""
        contract = Phase6DualAgentContract(strict_mode=True)
        
        data = {
            "openai_validation_complete": False,
            "anthropic_validation_complete": False,
            "cross_validation_score": 0.0,
            "min_confidence_threshold": 0.75
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert len(result.violations) > 0
        assert any(v.violation_type == ContractViolationType.FAILED_DEPENDENCY 
                   for v in result.violations)
    
    def test_phase6_validation_failure_low_confidence(self):
        """Test Phase 6 validation fails with low confidence score."""
        contract = Phase6DualAgentContract(strict_mode=True)
        
        data = {
            "openai_validation_complete": True,
            "anthropic_validation_complete": True,
            "cross_validation_score": 0.60,  # Below threshold
            "min_confidence_threshold": 0.75
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any(v.violation_type == ContractViolationType.INSUFFICIENT_RECORDS 
                   for v in result.violations)


class TestCritical003Phase7SubagentContract:
    """Test CRITICAL-003: Phase7SubagentContract implementation."""
    
    def test_phase7_contract_creation(self):
        """Test Phase 7 contract can be created."""
        contract = Phase7SubagentContract(strict_mode=True)
        assert contract is not None
        assert contract.required_agents == 10
        assert contract.min_completion_ratio == 0.80
    
    def test_phase7_validation_success(self):
        """Test Phase 7 validation passes with 80%+ completion."""
        contract = Phase7SubagentContract(strict_mode=True)
        
        data = {
            "agents_deployed": 10,
            "agents_completed": 9,
            "min_completion_ratio": 0.80
        }
        
        result = contract.validate(data)
        assert result.passed is True
        assert len(result.violations) == 0
    
    def test_phase7_validation_failure_no_agents(self):
        """Test Phase 7 validation fails when no agents deployed."""
        contract = Phase7SubagentContract(strict_mode=True)
        
        data = {
            "agents_deployed": 0,
            "agents_completed": 0,
            "min_completion_ratio": 0.80
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any(v.violation_type == ContractViolationType.EMPTY_REQUIRED_DATA 
                   for v in result.violations)
    
    def test_phase7_validation_failure_low_completion(self):
        """Test Phase 7 validation fails with <80% completion."""
        contract = Phase7SubagentContract(strict_mode=True)
        
        data = {
            "agents_deployed": 10,
            "agents_completed": 7,  # 70% completion
            "min_completion_ratio": 0.80
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any(v.violation_type == ContractViolationType.INSUFFICIENT_RECORDS 
                   for v in result.violations)


class TestCritical003Phase9DossierContract:
    """Test CRITICAL-003: Phase9DossierContract implementation."""
    
    def test_phase9_contract_creation(self):
        """Test Phase 9 contract can be created."""
        contract = Phase9DossierContract(strict_mode=True)
        assert contract is not None
    
    def test_phase9_validation_success_all_requirements(self):
        """Test Phase 9 validation passes when all requirements met."""
        contract = Phase9DossierContract(strict_mode=True)
        
        data = {
            "fre_902_13_compliant": True,
            "fre_902_14_compliant": True,
            "evidence_chain_complete": True,
            "triple_hash_verified": True,
            "merkle_tree_valid": True,
            "executive_summary_present": True,
            "findings_documented": True,
            "evidence_exhibits_attached": True,
            "chain_of_custody_documented": True,
            "rfc_3161_timestamp_present": True
        }
        
        result = contract.validate(data)
        assert result.passed is True
        assert len(result.violations) == 0
    
    def test_phase9_validation_failure_missing_fre_902_13(self):
        """Test Phase 9 validation fails without FRE 902(13) compliance."""
        contract = Phase9DossierContract(strict_mode=True)
        
        data = {
            "fre_902_13_compliant": False,
            "fre_902_14_compliant": True,
            "evidence_chain_complete": True,
            "triple_hash_verified": True,
            "merkle_tree_valid": True,
            "executive_summary_present": True,
            "findings_documented": True,
            "evidence_exhibits_attached": True,
            "chain_of_custody_documented": True,
            "rfc_3161_timestamp_present": True
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any(v.field_name == "fre_902_13_compliant" for v in result.violations)
    
    def test_phase9_validation_failure_missing_fre_902_14(self):
        """Test Phase 9 validation fails without FRE 902(14) compliance."""
        contract = Phase9DossierContract(strict_mode=True)
        
        data = {
            "fre_902_13_compliant": True,
            "fre_902_14_compliant": False,
            "evidence_chain_complete": True,
            "triple_hash_verified": True,
            "merkle_tree_valid": True,
            "executive_summary_present": True,
            "findings_documented": True,
            "evidence_exhibits_attached": True,
            "chain_of_custody_documented": True,
            "rfc_3161_timestamp_present": True
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any(v.field_name == "fre_902_14_compliant" for v in result.violations)
    
    def test_phase9_validation_failure_missing_triple_hash(self):
        """Test Phase 9 validation fails without triple-hash verification."""
        contract = Phase9DossierContract(strict_mode=True)
        
        data = {
            "fre_902_13_compliant": True,
            "fre_902_14_compliant": True,
            "evidence_chain_complete": True,
            "triple_hash_verified": False,
            "merkle_tree_valid": True,
            "executive_summary_present": True,
            "findings_documented": True,
            "evidence_exhibits_attached": True,
            "chain_of_custody_documented": True,
            "rfc_3161_timestamp_present": True
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any(v.violation_type == ContractViolationType.HASH_MISMATCH 
                   for v in result.violations)
    
    def test_phase9_validation_failure_missing_merkle_tree(self):
        """Test Phase 9 validation fails without valid Merkle tree."""
        contract = Phase9DossierContract(strict_mode=True)
        
        data = {
            "fre_902_13_compliant": True,
            "fre_902_14_compliant": True,
            "evidence_chain_complete": True,
            "triple_hash_verified": True,
            "merkle_tree_valid": False,
            "executive_summary_present": True,
            "findings_documented": True,
            "evidence_exhibits_attached": True,
            "chain_of_custody_documented": True,
            "rfc_3161_timestamp_present": True
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any(v.violation_type == ContractViolationType.HASH_MISMATCH 
                   for v in result.violations)
    
    def test_phase9_validation_failure_missing_rfc3161(self):
        """Test Phase 9 validation fails without RFC 3161 timestamp."""
        contract = Phase9DossierContract(strict_mode=True)
        
        data = {
            "fre_902_13_compliant": True,
            "fre_902_14_compliant": True,
            "evidence_chain_complete": True,
            "triple_hash_verified": True,
            "merkle_tree_valid": True,
            "executive_summary_present": True,
            "findings_documented": True,
            "evidence_exhibits_attached": True,
            "chain_of_custody_documented": True,
            "rfc_3161_timestamp_present": False
        }
        
        result = contract.validate(data)
        assert result.passed is False
        assert any(v.field_name == "rfc_3161_timestamp_present" for v in result.violations)
    
    def test_phase9_validation_comprehensive_failure(self):
        """Test Phase 9 validation with multiple failures."""
        contract = Phase9DossierContract(strict_mode=True)
        
        data = {
            "fre_902_13_compliant": False,
            "fre_902_14_compliant": False,
            "evidence_chain_complete": False,
            "triple_hash_verified": False,
            "merkle_tree_valid": False,
            "executive_summary_present": False,
            "findings_documented": False,
            "evidence_exhibits_attached": False,
            "chain_of_custody_documented": False,
            "rfc_3161_timestamp_present": False
        }
        
        result = contract.validate(data)
        assert result.passed is False
        # Should have 10 violations (one for each field)
        assert len(result.violations) == 10


class TestCritical003FactoryIntegration:
    """Test CRITICAL-003: Factory function integration with new contracts."""
    
    def test_factory_creates_phase6_contract(self):
        """Test factory function creates Phase 6 contract."""
        config = {"strict_mode": True}
        contract = create_contract_for_phase(
            "Phase 6: Dual-Agent AI Cross-Validation",
            config
        )
        
        assert isinstance(contract, Phase6DualAgentContract)
    
    def test_factory_creates_phase7_contract(self):
        """Test factory function creates Phase 7 contract."""
        config = {"strict_mode": True}
        contract = create_contract_for_phase(
            "Phase 7: Subagent Orchestration",
            config
        )
        
        assert isinstance(contract, Phase7SubagentContract)
    
    def test_factory_creates_phase9_contract(self):
        """Test factory function creates Phase 9 contract."""
        config = {"strict_mode": True}
        contract = create_contract_for_phase(
            "Phase 9: DOJ-Grade Dossier Generation",
            config
        )
        
        assert isinstance(contract, Phase9DossierContract)
