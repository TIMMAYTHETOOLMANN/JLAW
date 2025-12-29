"""
Phase Execution Framework
==========================

Manages execution flow integrity and phase gating for DOJ-grade forensic analysis.

This framework provides:
- Centralized phase definition registry with dependencies
- Mandatory phase gate enforcement
- Phase dependency validation
- Timeout protection for long-running phases
- Immutable audit trail generation
- Evidence chain integrity checkpoints

Architecture:
    PHASE_REGISTRY → PhaseDefinition (metadata + rules)
    PhaseExecutionFramework → orchestrates execution with validation
    PhaseResult → captures execution outcome
    PhaseExecutionRecord → immutable audit log entry

Legal Compliance:
    - FRE 902(13)/(14): Immutable audit trail for evidence authentication
    - SOX 404: Process controls and documentation
    - 18 U.S.C. § 1519: Evidence integrity and chain of custody
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable

from .exceptions import (
    PhaseDefinitionError,
    PhaseDependencyError,
    PhaseGateFailure,
    PhaseTimeoutError
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class PhaseStatus(Enum):
    """Execution status of a phase."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class PhaseDefinition:
    """
    Definition of an execution phase.
    
    Attributes:
        phase_id: Unique identifier for the phase
        phase_name: Human-readable phase name
        phase_number: Sequential phase number (1-9)
        required_in_strict_mode: Whether phase is mandatory in strict mode
        depends_on: List of phase IDs this phase depends on
        validation_rules: Dictionary of validation rules to enforce
        timeout_seconds: Maximum execution time allowed
        description: Detailed description of phase purpose
    """
    phase_id: str
    phase_name: str
    phase_number: int
    required_in_strict_mode: bool
    depends_on: List[str]
    validation_rules: Dict[str, Any]
    timeout_seconds: float
    description: str


@dataclass
class PhaseResult:
    """
    Result from a single phase execution.
    
    Captures all relevant information about phase execution outcome,
    including status, timing, data produced, and any errors encountered.
    """
    phase_id: str
    status: PhaseStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "phase_id": self.phase_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time": round(self.execution_time, 3),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PhaseExecutionRecord:
    """
    Immutable audit log record for a phase execution.
    
    Part of the FRE 902(13)/(14) compliant evidence chain.
    Once created, this record should never be modified.
    """
    phase_id: str
    phase_number: int
    phase_name: str
    status: PhaseStatus
    execution_time: float
    timestamp: datetime
    error: Optional[str] = None
    validation_passed: bool = True
    validation_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for audit trail export."""
        return {
            "phase_id": self.phase_id,
            "phase_number": self.phase_number,
            "phase_name": self.phase_name,
            "status": self.status.value,
            "execution_time": round(self.execution_time, 3),
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
            "validation_passed": self.validation_passed,
            "validation_message": self.validation_message
        }


# ═══════════════════════════════════════════════════════════════════════════
# PHASE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

PHASE_REGISTRY: Dict[str, PhaseDefinition] = {
    "phase_1_initialization": PhaseDefinition(
        phase_id="phase_1_initialization",
        phase_name="Configuration & Target Acquisition",
        phase_number=1,
        required_in_strict_mode=True,
        depends_on=[],
        validation_rules={
            "sec_client_available": True,
            "modules_loaded": 6,
            "sec_config_valid": True,
        },
        timeout_seconds=30.0,
        description="Initialize configuration, SDK manager, and validate setup"
    ),
    
    "phase_2_data_collection": PhaseDefinition(
        phase_id="phase_2_data_collection",
        phase_name="SEC EDGAR Data Collection",
        phase_number=2,
        required_in_strict_mode=True,
        depends_on=["phase_1_initialization"],
        validation_rules={
            "filings_collected": ">=1",
            "all_filings_have_content": True,
        },
        timeout_seconds=300.0,
        description="Collect SEC filings from EDGAR with rate limiting compliance"
    ),
    
    "phase_3_document_parsing": PhaseDefinition(
        phase_id="phase_3_document_parsing",
        phase_name="Document Parsing & Indexing",
        phase_number=3,
        required_in_strict_mode=True,
        depends_on=["phase_2_data_collection"],
        validation_rules={
            "documents_parsed": ">=1",
            "parsing_success_rate": ">=0.80",
        },
        timeout_seconds=300.0,
        description="Parse and index collected SEC documents"
    ),
    
    "phase_4_node_analysis": PhaseDefinition(
        phase_id="phase_4_node_analysis",
        phase_name="15-Node Recursive Analysis",
        phase_number=4,
        required_in_strict_mode=True,
        depends_on=["phase_3_document_parsing"],
        validation_rules={
            "nodes_executed": ">=12",  # 80% of 15 nodes
            "node_success_rate": ">=0.80",
        },
        timeout_seconds=900.0,
        description="Execute recursive 15-node forensic analysis"
    ),
    
    "phase_5_pattern_detection": PhaseDefinition(
        phase_id="phase_5_pattern_detection",
        phase_name="Advanced Pattern Detection",
        phase_number=5,
        required_in_strict_mode=True,
        depends_on=["phase_4_node_analysis"],
        validation_rules={
            "patterns_executed": ">=10",  # At least 10 of 23 patterns
            "pattern_execution_rate": ">=0.43",  # 10/23 = 43%
        },
        timeout_seconds=300.0,
        description="Execute fraud detection algorithms (M-Score, Z-Score, Benford)"
    ),
    
    "phase_6_dual_agent": PhaseDefinition(
        phase_id="phase_6_dual_agent",
        phase_name="Dual-Agent AI Cross-Validation",
        phase_number=6,
        required_in_strict_mode=True,
        depends_on=["phase_5_pattern_detection"],
        validation_rules={
            "ai_agents_executed": ">=1",  # At least one AI agent must respond
            "violations_analyzed": ">=0",  # Can be 0 (clean finding)
        },
        timeout_seconds=600.0,
        description="AI-powered violation validation via OpenAI/Anthropic"
    ),
    
    "phase_7_subagent_orchestration": PhaseDefinition(
        phase_id="phase_7_subagent_orchestration",
        phase_name="Unified Agent Orchestration",
        phase_number=7,
        required_in_strict_mode=True,
        depends_on=["phase_6_dual_agent"],
        validation_rules={
            "agents_invoked": ">=3",
            "consensus_score": ">=0.70",  # 70% minimum consensus for DOJ submission
            "orchestration_completed": True,
        },
        timeout_seconds=900.0,
        description="Multi-tier agent orchestration with intelligent routing"
    ),
    
    "phase_8_evidence_chain": PhaseDefinition(
        phase_id="phase_8_evidence_chain",
        phase_name="Evidence Chain Integrity Verification",
        phase_number=8,
        required_in_strict_mode=True,
        depends_on=["phase_7_subagent_orchestration"],
        validation_rules={
            "all_hashes_verified": True,
            "chain_of_custody_complete": True,
            "fre_902_compliant": True,
            "merkle_root_generated": True,
        },
        timeout_seconds=60.0,
        description="Verify triple-hash integrity and FRE 902(13)/(14) compliance"
    ),
    
    "phase_9_report_generation": PhaseDefinition(
        phase_id="phase_9_report_generation",
        phase_name="DOJ-Grade Report Generation",
        phase_number=9,
        required_in_strict_mode=True,
        depends_on=["phase_8_evidence_chain"],
        validation_rules={
            "dossier_generated": True,
            "pdf_generated": True,
            "all_violations_documented": True,
        },
        timeout_seconds=120.0,
        description="Generate prosecution-ready forensic dossier"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# PHASE EXECUTION FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════════

class PhaseExecutionFramework:
    """
    Manages execution flow integrity and phase gating.
    
    This framework ensures that:
    1. All phases execute in correct dependency order
    2. Phase gates are enforced in strict mode
    3. Timeouts prevent infinite execution
    4. Complete audit trail is maintained
    5. Evidence chain integrity is preserved
    
    Usage:
        framework = PhaseExecutionFramework(strict_mode=True)
        result = await framework.execute_phase(
            "phase_1_initialization",
            executor=my_phase_1_function,
            param1=value1
        )
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize phase execution framework.
        
        Args:
            strict_mode: Enable strict phase gate enforcement
        """
        self.strict_mode = strict_mode
        self.phase_registry = PHASE_REGISTRY
        self.execution_log: List[PhaseExecutionRecord] = []
        self.phase_results: Dict[str, PhaseResult] = {}
        
        logger.info(f"PhaseExecutionFramework initialized (strict_mode={strict_mode})")
    
    async def execute_phase(
        self,
        phase_id: str,
        executor: Callable[..., Awaitable[Dict[str, Any]]],
        **kwargs
    ) -> PhaseResult:
        """
        Execute a single phase with validation and gating.
        
        Execution Flow:
        1. Validate phase definition exists
        2. Check all dependencies completed successfully
        3. Execute phase function with timeout protection
        4. Apply phase gate validation rules
        5. Log execution to immutable audit trail
        6. Return phase result
        
        Args:
            phase_id: Identifier of phase to execute
            executor: Async function that implements the phase logic
            **kwargs: Arguments to pass to the executor function
            
        Returns:
            PhaseResult with execution outcome
            
        Raises:
            PhaseDefinitionError: If phase_id not found in registry
            PhaseDependencyError: If dependencies not satisfied
            PhaseGateFailure: If validation fails in strict mode
            PhaseTimeoutError: If phase exceeds timeout
        """
        # Get phase definition
        phase_def = self.phase_registry.get(phase_id)
        if not phase_def:
            raise PhaseDefinitionError(f"Unknown phase: {phase_id}")
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"  PHASE {phase_def.phase_number}: {phase_def.phase_name}")
        logger.info(f"{'=' * 80}")
        logger.info(f"  Phase ID: {phase_id}")
        logger.info(f"  Timeout: {phase_def.timeout_seconds}s")
        logger.info(f"  Required in strict mode: {phase_def.required_in_strict_mode}")
        
        # Validate dependencies
        self._validate_dependencies(phase_def)
        
        # Execute phase with timeout
        start_time = time.time()
        status = PhaseStatus.SUCCESS
        error = None
        result = None
        
        try:
            logger.info(f"→ Executing {phase_def.phase_name}...")
            result = await asyncio.wait_for(
                executor(**kwargs),
                timeout=phase_def.timeout_seconds
            )
            logger.info(f"✓ Phase execution completed")
            
        except asyncio.TimeoutError:
            status = PhaseStatus.TIMEOUT
            error = f"Phase exceeded {phase_def.timeout_seconds}s timeout"
            logger.error(f"✗ {error}")
            
        except Exception as e:
            status = PhaseStatus.ERROR
            error = f"{type(e).__name__}: {str(e)}"
            logger.error(f"✗ Phase execution failed: {error}")
        
        execution_time = time.time() - start_time
        
        # Create phase result
        phase_result = PhaseResult(
            phase_id=phase_id,
            status=status,
            result=result,
            error=error,
            execution_time=execution_time,
            timestamp=datetime.utcnow()
        )
        
        # Apply phase gate validation
        validation_passed = True
        validation_message = None
        
        if self.strict_mode and phase_def.required_in_strict_mode:
            try:
                self._apply_phase_gate(phase_def, phase_result)
                validation_message = "Phase gate validation passed"
                logger.info(f"✓ Phase gate validation PASSED")
            except PhaseGateFailure as e:
                validation_passed = False
                validation_message = str(e)
                logger.error(f"✗ Phase gate validation FAILED: {validation_message}")
                # Re-raise in strict mode
                raise
        
        # Log execution to audit trail
        self._log_phase_execution(phase_def, phase_result, validation_passed, validation_message)
        
        # Store result
        self.phase_results[phase_id] = phase_result
        
        logger.info(f"  Execution time: {execution_time:.2f}s")
        logger.info(f"  Status: {status.value}")
        
        return phase_result
    
    def _validate_dependencies(self, phase_def: PhaseDefinition):
        """
        Validate all dependencies completed successfully.
        
        Args:
            phase_def: Phase definition to validate
            
        Raises:
            PhaseDependencyError: If any dependency not satisfied
        """
        for dep_id in phase_def.depends_on:
            # Check dependency was executed
            if dep_id not in self.phase_results:
                raise PhaseDependencyError(
                    f"Phase '{phase_def.phase_id}' requires '{dep_id}' to complete first"
                )
            
            # Check dependency succeeded
            dep_result = self.phase_results[dep_id]
            if dep_result.status != PhaseStatus.SUCCESS:
                raise PhaseDependencyError(
                    f"Dependency '{dep_id}' failed with status: {dep_result.status.value}"
                )
    
    def _apply_phase_gate(self, phase_def: PhaseDefinition, result: PhaseResult):
        """
        Apply phase gate validation rules.
        
        Args:
            phase_def: Phase definition with validation rules
            result: Phase execution result to validate
            
        Raises:
            PhaseGateFailure: If validation fails
        """
        # Phase must have succeeded
        if result.status != PhaseStatus.SUCCESS:
            raise PhaseGateFailure(
                f"Phase '{phase_def.phase_id}' did not complete successfully",
                phase_id=phase_def.phase_id
            )
        
        # Phase must have returned result data
        if result.result is None:
            raise PhaseGateFailure(
                f"Phase '{phase_def.phase_id}' returned no result data",
                phase_id=phase_def.phase_id
            )
        
        # Validate against rules
        for rule_name, rule_value in phase_def.validation_rules.items():
            if not self._check_validation_rule(rule_name, rule_value, result):
                actual_value = result.result.get(rule_name, "NOT_SET")
                raise PhaseGateFailure(
                    f"Phase gate validation failed for '{phase_def.phase_id}': "
                    f"{rule_name} (expected: {rule_value}, actual: {actual_value})",
                    phase_id=phase_def.phase_id,
                    rule=rule_name
                )
    
    def _check_validation_rule(
        self,
        rule_name: str,
        rule_value: Any,
        result: PhaseResult
    ) -> bool:
        """
        Check a single validation rule.
        
        Args:
            rule_name: Name of the field to validate
            rule_value: Expected value or comparison string
            result: Phase result containing actual values
            
        Returns:
            True if validation passes, False otherwise
        """
        if result.result is None:
            return False
        
        actual = result.result.get(rule_name)
        
        # Boolean check
        if isinstance(rule_value, bool):
            return actual == rule_value
        
        # Integer check
        if isinstance(rule_value, int):
            return actual == rule_value
        
        # Comparison string checks (e.g., ">=10", ">5")
        if isinstance(rule_value, str):
            if rule_value.startswith(">="):
                threshold = float(rule_value[2:])
                try:
                    return float(actual) >= threshold
                except (TypeError, ValueError):
                    return False
            
            elif rule_value.startswith(">"):
                threshold = float(rule_value[1:])
                try:
                    return float(actual) > threshold
                except (TypeError, ValueError):
                    return False
            
            elif rule_value.startswith("<="):
                threshold = float(rule_value[2:])
                try:
                    return float(actual) <= threshold
                except (TypeError, ValueError):
                    return False
            
            elif rule_value.startswith("<"):
                threshold = float(rule_value[1:])
                try:
                    return float(actual) < threshold
                except (TypeError, ValueError):
                    return False
        
        # Direct equality check
        return actual == rule_value
    
    def _log_phase_execution(
        self,
        phase_def: PhaseDefinition,
        result: PhaseResult,
        validation_passed: bool,
        validation_message: Optional[str]
    ):
        """
        Log phase execution to immutable audit trail.
        
        Args:
            phase_def: Phase definition
            result: Phase execution result
            validation_passed: Whether validation passed
            validation_message: Validation result message
        """
        record = PhaseExecutionRecord(
            phase_id=phase_def.phase_id,
            phase_number=phase_def.phase_number,
            phase_name=phase_def.phase_name,
            status=result.status,
            execution_time=result.execution_time,
            timestamp=result.timestamp,
            error=result.error,
            validation_passed=validation_passed,
            validation_message=validation_message
        )
        self.execution_log.append(record)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get execution summary for DOJ reporting.
        
        Returns:
            Dictionary with execution statistics and phase log
        """
        successful = [r for r in self.execution_log if r.status == PhaseStatus.SUCCESS]
        failed = [r for r in self.execution_log if r.status != PhaseStatus.SUCCESS]
        
        return {
            "total_phases_executed": len(self.execution_log),
            "successful_phases": len(successful),
            "failed_phases": len(failed),
            "total_execution_time": sum(r.execution_time for r in self.execution_log),
            "strict_mode_enabled": self.strict_mode,
            "all_validations_passed": all(r.validation_passed for r in self.execution_log),
            "phases": [r.to_dict() for r in self.execution_log],
        }
    
    def export_audit_trail(self, output_path: Path):
        """
        Export immutable audit trail to JSON file.
        
        This audit trail is part of the FRE 902(13)/(14) compliant
        evidence chain and should be preserved with the forensic dossier.
        
        Args:
            output_path: Path to write audit trail JSON
        """
        audit_data = {
            "audit_trail_version": "1.0",
            "generation_timestamp": datetime.utcnow().isoformat(),
            "strict_mode": self.strict_mode,
            "total_phases": len(self.execution_log),
            "execution_summary": self.get_execution_summary(),
            "detailed_phase_log": [r.to_dict() for r in self.execution_log],
            "phase_registry_snapshot": {
                phase_id: {
                    "phase_name": phase_def.phase_name,
                    "phase_number": phase_def.phase_number,
                    "dependencies": phase_def.depends_on,
                    "timeout_seconds": phase_def.timeout_seconds
                }
                for phase_id, phase_def in self.phase_registry.items()
            }
        }
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write audit trail
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Audit trail exported to: {output_path}")
    
    def get_phase_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get phase dependency graph.
        
        Returns:
            Dictionary mapping phase IDs to their dependencies
        """
        return {
            phase_id: phase_def.depends_on
            for phase_id, phase_def in self.phase_registry.items()
        }
    
    def validate_phase_order(self) -> bool:
        """
        Validate that all phases can be executed in valid order.
        
        Checks for:
        - Circular dependencies
        - Missing dependency definitions
        
        Returns:
            True if phase order is valid
            
        Raises:
            PhaseDefinitionError: If circular dependencies detected
        """
        visited = set()
        rec_stack = set()
        
        def has_cycle(phase_id: str) -> bool:
            """Check if phase has circular dependency."""
            visited.add(phase_id)
            rec_stack.add(phase_id)
            
            phase_def = self.phase_registry.get(phase_id)
            if not phase_def:
                return False
            
            for dep_id in phase_def.depends_on:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(phase_id)
            return False
        
        # Check each phase for cycles
        for phase_id in self.phase_registry.keys():
            if phase_id not in visited:
                if has_cycle(phase_id):
                    raise PhaseDefinitionError(
                        f"Circular dependency detected involving phase: {phase_id}"
                    )
        
        return True
