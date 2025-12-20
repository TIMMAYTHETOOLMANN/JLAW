"""
Strict Execution Controller
============================

Orchestrates forensic analysis in strict mode with mandatory gate validation,
cascade abort protocol, and comprehensive audit trails.
"""

import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from config.strict_execution_config import StrictExecutionConfig
from src.core.phase_gate_validator import PhaseGateValidator, GateDecision
from src.core.execution_audit import ExecutionAudit, AuditEventType

logger = logging.getLogger(__name__)


class ExecutionAbortException(Exception):
    """Exception raised when execution must abort."""
    
    def __init__(self, phase: str, reason: str, exit_code: int):
        self.phase = phase
        self.reason = reason
        self.exit_code = exit_code
        super().__init__(f"Execution aborted at {phase}: {reason}")


class StrictExecutionController:
    """
    Strict mode orchestrator for DOJ-grade forensic analysis.
    
    Enforces:
    - Mandatory phase gate validation
    - Data contract compliance
    - Cascade abort on critical failures
    - Comprehensive audit trails
    - Non-zero exit codes on failures
    """
    
    def __init__(
        self,
        config: StrictExecutionConfig,
        case_id: str,
        output_dir: Path
    ):
        """
        Initialize strict execution controller.
        
        Args:
            config: Strict execution configuration
            case_id: Unique case identifier
            output_dir: Output directory for artifacts
        """
        self.config = config
        self.case_id = case_id
        self.output_dir = output_dir
        
        # Initialize validator and audit
        config_dict = self._config_to_dict()
        self.validator = PhaseGateValidator(config_dict)
        self.audit = ExecutionAudit(case_id, output_dir)
        
        # State tracking
        self.current_phase: Optional[str] = None
        self.phases_completed: set = set()
        self.execution_aborted = False
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert config to dict for validator."""
        config_dict = {
            "strict_mode": self.config.strict_mode,
            "halt_on_critical_failure": self.config.thresholds.halt_on_critical_failure,
            "min_filings_total": self.config.thresholds.min_filings_total,
            "min_filings_per_type": self.config.thresholds.min_filings_per_type,
            "min_documents_parsed": self.config.thresholds.min_documents_parsed,
            "min_chunks_indexed": self.config.thresholds.min_chunks_indexed,
            "min_nodes_successful": self.config.thresholds.min_nodes_successful,
            "min_node_success_rate": self.config.thresholds.min_node_success_rate,
            "min_patterns_executed": self.config.thresholds.min_patterns_executed,
            "require_evidence_chain": self.config.thresholds.require_evidence_chain,
        }
        return config_dict
    
    def begin_phase(self, phase_name: str):
        """
        Begin a new phase.
        
        Args:
            phase_name: Name of the phase
        """
        self.current_phase = phase_name
        self.audit.start_phase(phase_name)
        logger.info(f"\n{'═' * 70}")
        logger.info(f"  STRICT MODE: {phase_name}")
        logger.info(f"{'═' * 70}")
    
    def complete_phase(
        self,
        phase_name: str,
        phase_data: Dict[str, Any],
        records_extracted: int = 0,
        records_expected: int = 0,
        bytes_processed: int = 0
    ) -> bool:
        """
        Complete a phase and validate its gate.
        
        Args:
            phase_name: Name of the phase
            phase_data: Data produced by the phase
            records_extracted: Number of records extracted
            records_expected: Number of records expected
            bytes_processed: Bytes processed in phase
            
        Returns:
            True if validation passed and execution can continue
            
        Raises:
            ExecutionAbortException: If gate fails in strict mode
        """
        # Mark phase complete in audit
        self.audit.complete_phase(
            phase_name,
            records_extracted=records_extracted,
            records_expected=records_expected,
            bytes_processed=bytes_processed
        )
        
        # Validate phase gate
        logger.info(f"\n  Validating phase gate...")
        decision, validation_result = self.validator.validate_gate(phase_name, phase_data)
        
        # Record validation in audit
        violations = [v.message for v in validation_result.violations]
        self.audit.record_gate_validation(phase_name, validation_result.passed, violations)
        
        # Check decision
        if decision == GateDecision.PASS:
            logger.info(f"  ✓ Gate validation PASSED")
            self.phases_completed.add(phase_name)
            return True
        
        elif decision == GateDecision.FAIL:
            # Critical failure in strict mode
            exit_code = self._get_exit_code_for_phase(phase_name)
            error_msg = validation_result.get_error_message()
            
            logger.error(f"  ✗ GATE VALIDATION FAILED")
            logger.error(f"  {error_msg}")
            
            # Trigger cascade abort
            self._trigger_cascade_abort(phase_name, error_msg, exit_code)
            
            # Should not reach here
            return False
        
        elif decision == GateDecision.OVERRIDE_REQUIRED:
            # Non-critical failure
            if self.config.strict_mode:
                # No overrides in strict mode
                exit_code = self._get_exit_code_for_phase(phase_name)
                error_msg = "Gate validation failed; override not allowed in strict mode"
                logger.error(f"  ✗ {error_msg}")
                self._trigger_cascade_abort(phase_name, error_msg, exit_code)
                return False
            else:
                # Allow continuation in non-strict mode
                logger.warning(f"  ⚠ Gate validation had warnings but continuing")
                self.phases_completed.add(phase_name)
                return True
        
        return False
    
    def fail_phase(self, phase_name: str, error: str):
        """
        Mark a phase as failed.
        
        Args:
            phase_name: Name of the phase
            error: Error message
            
        Raises:
            ExecutionAbortException: If in strict mode
        """
        self.audit.fail_phase(phase_name, error)
        logger.error(f"  ✗ Phase failed: {error}")
        
        if self.config.strict_mode:
            exit_code = self._get_exit_code_for_phase(phase_name)
            self._trigger_cascade_abort(phase_name, f"Phase execution failed: {error}", exit_code)
    
    def _get_exit_code_for_phase(self, phase_name: str) -> int:
        """Get appropriate exit code for phase failure."""
        phase_lower = phase_name.lower()
        
        if "configuration" in phase_lower:
            return self.config.exit_code_configuration_failure
        elif "data collection" in phase_lower:
            return self.config.exit_code_data_collection_failure
        elif "document parsing" in phase_lower or "docsgpt" in phase_lower:
            return self.config.exit_code_document_parsing_failure
        elif "node analysis" in phase_lower or "15-node" in phase_lower or "recursive" in phase_lower:
            return self.config.exit_code_node_execution_failure
        elif "pattern detection" in phase_lower or "detection pattern" in phase_lower:
            return self.config.exit_code_pattern_detection_failure
        elif "evidence chain" in phase_lower or "chain finalization" in phase_lower:
            return self.config.exit_code_evidence_chain_failure
        elif "dossier generation" in phase_lower or "doj-grade" in phase_lower:
            return self.config.exit_code_dossier_generation_failure
        else:
            return 1  # Generic failure
    
    def _trigger_cascade_abort(self, phase: str, reason: str, exit_code: int):
        """
        Trigger cascade abort protocol.
        
        1. Preserve all evidence collected to that point
        2. Generate partial dossier with INCOMPLETE markers
        3. Log detailed failure forensics
        4. Create abort report
        5. Raise exception with exit code
        """
        logger.critical(f"\n{'═' * 70}")
        logger.critical(f"  EXECUTION ABORT TRIGGERED")
        logger.critical(f"{'═' * 70}")
        logger.critical(f"  Phase: {phase}")
        logger.critical(f"  Reason: {reason}")
        logger.critical(f"  Exit Code: {exit_code}")
        
        # Record abort in audit
        self.audit.record_abort(phase, reason)
        self.execution_aborted = True
        
        # Save audit trail
        try:
            audit_file = self.audit.save_to_file()
            logger.info(f"  Audit trail saved: {audit_file}")
        except Exception as e:
            logger.error(f"  Failed to save audit trail: {e}")
        
        # Generate abort report
        try:
            abort_report = self.audit.generate_abort_report()
            report_file = self.output_dir / f"ABORT_REPORT_{self.case_id}.txt"
            with open(report_file, 'w') as f:
                f.write(abort_report)
            logger.info(f"  Abort report saved: {report_file}")
            
            # Print abort report to console
            print("\n" + abort_report)
        except Exception as e:
            logger.error(f"  Failed to generate abort report: {e}")
        
        # Print remediation guidance
        remediation = self.config.get_remediation_message(exit_code)
        logger.info(f"\n  REMEDIATION GUIDANCE:")
        logger.info(f"  {remediation}")
        
        # Raise exception
        raise ExecutionAbortException(phase, reason, exit_code)
    
    def finalize(self) -> int:
        """
        Finalize execution and return exit code.
        
        Returns:
            Exit code (0 for success, non-zero for failures)
        """
        self.audit.finalize()
        
        # Save final audit trail
        try:
            audit_file = self.audit.save_to_file()
            logger.info(f"\n  Final audit trail: {audit_file}")
        except Exception as e:
            logger.error(f"  Failed to save final audit: {e}")
        
        # Print summary
        summary = self.audit.get_summary()
        logger.info(f"\n{'═' * 70}")
        logger.info(f"  EXECUTION SUMMARY")
        logger.info(f"{'═' * 70}")
        logger.info(f"  Phases Completed: {len(self.phases_completed)}")
        logger.info(f"  Gates Validated: {summary['gates']['total_validated']}")
        logger.info(f"  Gates Passed: {summary['gates']['passed']}")
        logger.info(f"  Gates Failed: {summary['gates']['failed']}")
        logger.info(f"  Execution Time: {summary['total_duration_seconds']:.2f}s")
        
        if self.execution_aborted:
            logger.critical(f"  STATUS: ABORTED")
            return 1  # Generic abort exit code
        else:
            logger.info(f"  STATUS: COMPLETED")
            return 0
    
    def record_error(self, error: str):
        """Record an error in audit trail."""
        self.audit.record_error(self.current_phase or "Unknown", error)
    
    def record_warning(self, warning: str):
        """Record a warning in audit trail."""
        self.audit.record_warning(self.current_phase or "Unknown", warning)
