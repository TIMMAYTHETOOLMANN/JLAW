"""
Phase Gate Validator
====================

Implements mandatory phase gate validation with configurable thresholds.
Determines whether execution can proceed to the next phase.
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
import logging

from src.core.data_contracts import (
    create_contract_for_phase,
    ValidationResult,
    DataContract
)

logger = logging.getLogger(__name__)


class GateDecision(Enum):
    """Gate validation decision."""
    PASS = "pass"
    FAIL = "fail"
    OVERRIDE_REQUIRED = "override_required"


class PhaseGateValidator:
    """
    Validates phase completion against data contracts.
    
    Enforces quality gates between analysis phases to ensure
    each phase produces viable data before proceeding.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize validator with configuration.
        
        Args:
            config: Configuration dict with thresholds and settings
        """
        self.config = config
        self.strict_mode = config.get("strict_mode", False)
        self.halt_on_critical_failure = config.get("halt_on_critical_failure", True)
        
        # Track validation history
        self.validation_history: Dict[str, ValidationResult] = {}
    
    def validate_gate(
        self,
        phase_name: str,
        phase_data: Dict[str, Any]
    ) -> Tuple[GateDecision, ValidationResult]:
        """
        Validate phase gate.
        
        Args:
            phase_name: Name of the phase
            phase_data: Data produced by the phase
            
        Returns:
            Tuple of (GateDecision, ValidationResult)
        """
        # Create contract for this phase
        contract = create_contract_for_phase(phase_name, self.config)
        
        # Run validation
        validation_result = contract.validate(phase_data)
        
        # Store in history
        self.validation_history[phase_name] = validation_result
        
        # Determine decision
        if validation_result.passed:
            decision = GateDecision.PASS
            logger.info(f"✓ Gate validation PASSED: {phase_name}")
        else:
            # Check if critical failure
            if self._is_critical_failure(phase_name, validation_result):
                decision = GateDecision.FAIL
                logger.error(f"✗ Gate validation FAILED: {phase_name}")
                logger.error(validation_result.get_error_message())
            else:
                decision = GateDecision.OVERRIDE_REQUIRED
                logger.warning(f"⚠ Gate validation requires override: {phase_name}")
                logger.warning(validation_result.get_error_message())
        
        return decision, validation_result
    
    def _is_critical_failure(self, phase_name: str, result: ValidationResult) -> bool:
        """
        Determine if validation failure is critical.
        
        Critical failures halt execution in strict mode.
        Non-critical failures may allow override.
        """
        if not self.strict_mode:
            return False
        
        if not self.halt_on_critical_failure:
            return False
        
        # All gate failures are critical in strict mode with halt enabled
        return True
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validations performed."""
        return {
            "total_validations": len(self.validation_history),
            "passed": sum(1 for v in self.validation_history.values() if v.passed),
            "failed": sum(1 for v in self.validation_history.values() if not v.passed),
            "phases": {
                phase: {
                    "passed": result.passed,
                    "violations": len(result.violations)
                }
                for phase, result in self.validation_history.items()
            }
        }
    
    def should_halt_execution(self, decision: GateDecision) -> bool:
        """
        Determine if execution should halt based on gate decision.
        
        Args:
            decision: Gate validation decision
            
        Returns:
            True if execution should halt
        """
        if decision == GateDecision.PASS:
            return False
        
        if decision == GateDecision.FAIL:
            return self.strict_mode and self.halt_on_critical_failure
        
        if decision == GateDecision.OVERRIDE_REQUIRED:
            # In strict mode, override not allowed
            return self.strict_mode
        
        return False


def get_phase_order() -> Dict[str, int]:
    """
    Get phase execution order.
    
    Returns:
        Dict mapping phase names to order numbers
    """
    return {
        "Phase 1: Configuration & Target Acquisition": 1,
        "Phase 2: SEC EDGAR Data Collection": 2,
        "Phase 3: DocsGPT Document Parsing & Indexing": 3,
        "Phase 4: 15-Node Recursive Analysis": 4,
        "Phase 5: Advanced Detection Patterns": 5,
        "Phase 6: Dual-Agent AI Cross-Validation": 6,
        "Phase 7: Subagent Orchestration": 7,
        "Phase 8: Evidence Chain Finalization": 8,
        "Phase 9: DOJ-Grade Dossier Generation": 9,
    }


def get_critical_phases() -> set:
    """
    Get set of critical phases that must succeed.
    
    Returns:
        Set of critical phase names
    """
    return {
        "Phase 1: Configuration & Target Acquisition",
        "Phase 2: SEC EDGAR Data Collection",
        "Phase 4: 15-Node Recursive Analysis",
    }
