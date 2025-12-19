"""
Data Contracts for Phase-to-Phase Validation
==============================================

Defines strict data contracts that each phase must satisfy before
the next phase can begin. Ensures data integrity and completeness
throughout the forensic pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class ContractViolationType(Enum):
    """Types of data contract violations."""
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INSUFFICIENT_RECORDS = "insufficient_records"
    INVALID_DATA_TYPE = "invalid_data_type"
    HASH_MISMATCH = "hash_mismatch"
    EMPTY_REQUIRED_DATA = "empty_required_data"
    FAILED_DEPENDENCY = "failed_dependency"


@dataclass
class ContractViolation:
    """Represents a single contract violation."""
    violation_type: ContractViolationType
    field_name: str
    expected: Any
    actual: Any
    message: str


@dataclass
class ValidationResult:
    """Result of data contract validation."""
    passed: bool
    violations: List[ContractViolation] = field(default_factory=list)
    
    def add_violation(self, violation: ContractViolation):
        """Add a contract violation."""
        self.violations.append(violation)
        self.passed = False
    
    def get_error_message(self) -> str:
        """Get formatted error message."""
        if self.passed:
            return "Validation passed"
        
        messages = [f"Data contract validation failed with {len(self.violations)} violation(s):"]
        for i, v in enumerate(self.violations, 1):
            messages.append(f"  {i}. {v.message}")
        return "\n".join(messages)


class DataContract:
    """Base class for phase data contracts."""
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate data against contract requirements.
        
        Args:
            data: Phase output data to validate
            
        Returns:
            ValidationResult with violations if any
        """
        raise NotImplementedError("Subclasses must implement validate()")


class Phase1ConfigurationContract(DataContract):
    """Contract for Phase 1: Configuration & Target Acquisition."""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate configuration phase output."""
        result = ValidationResult(passed=True)
        
        # Check SEC client initialized
        if not data.get("sec_client_available"):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                field_name="sec_client_available",
                expected=True,
                actual=False,
                message="SEC EDGAR Client must be initialized and available"
            ))
        
        # Check modules loaded
        modules_loaded = data.get("modules_loaded", 0)
        min_required = 6 if self.strict_mode else 3
        if modules_loaded < min_required:
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                field_name="modules_loaded",
                expected=f">= {min_required}",
                actual=modules_loaded,
                message=f"Insufficient modules loaded: {modules_loaded} < {min_required}"
            ))
        
        # Check SEC API configuration valid
        if self.strict_mode and not data.get("sec_config_valid"):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.INVALID_DATA_TYPE,
                field_name="sec_config_valid",
                expected=True,
                actual=data.get("sec_config_valid", False),
                message="SEC API configuration must be valid in strict mode"
            ))
        
        return result


class Phase2DataCollectionContract(DataContract):
    """Contract for Phase 2: SEC EDGAR Data Collection."""
    
    def __init__(
        self,
        min_filings_total: int = 1,
        min_filings_per_type: Optional[Dict[str, int]] = None,
        strict_mode: bool = False
    ):
        self.min_filings_total = min_filings_total
        self.min_filings_per_type = min_filings_per_type or {}
        self.strict_mode = strict_mode
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data collection phase output."""
        result = ValidationResult(passed=True)
        
        # Check minimum total filings
        filings_collected = data.get("filings_collected", 0)
        if filings_collected < self.min_filings_total:
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                field_name="filings_collected",
                expected=f">= {self.min_filings_total}",
                actual=filings_collected,
                message=f"Insufficient filings collected: {filings_collected} < {self.min_filings_total}"
            ))
        
        # Check per-type minimums (if specified)
        if self.strict_mode and self.min_filings_per_type:
            filings_by_type = data.get("filings_by_type", {})
            for filing_type, min_count in self.min_filings_per_type.items():
                actual_count = filings_by_type.get(filing_type, 0)
                if actual_count < min_count:
                    result.add_violation(ContractViolation(
                        violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                        field_name=f"filings_by_type[{filing_type}]",
                        expected=f">= {min_count}",
                        actual=actual_count,
                        message=f"Insufficient {filing_type} filings: {actual_count} < {min_count}"
                    ))
        
        # Check for errors in strict mode
        if self.strict_mode:
            errors = data.get("errors", [])
            if errors:
                result.add_violation(ContractViolation(
                    violation_type=ContractViolationType.FAILED_DEPENDENCY,
                    field_name="errors",
                    expected="[]",
                    actual=errors,
                    message=f"Data collection had {len(errors)} error(s): {errors[0] if errors else ''}"
                ))
        
        return result


class Phase3DocumentParsingContract(DataContract):
    """Contract for Phase 3: DocsGPT Document Parsing & Indexing."""
    
    def __init__(self, min_parsed: int = 1, min_indexed: int = 0, strict_mode: bool = False):
        self.min_parsed = min_parsed
        self.min_indexed = min_indexed
        self.strict_mode = strict_mode
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate document parsing phase output."""
        result = ValidationResult(passed=True)
        
        # Check minimum parsed documents
        parsed_count = data.get("parsed", 0)
        if parsed_count < self.min_parsed:
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                field_name="parsed",
                expected=f">= {self.min_parsed}",
                actual=parsed_count,
                message=f"Insufficient documents parsed: {parsed_count} < {self.min_parsed}"
            ))
        
        # Check indexed chunks in strict mode
        if self.strict_mode and self.min_indexed > 0:
            indexed_count = data.get("indexed", 0)
            if indexed_count < self.min_indexed:
                result.add_violation(ContractViolation(
                    violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                    field_name="indexed",
                    expected=f">= {self.min_indexed}",
                    actual=indexed_count,
                    message=f"Insufficient document chunks indexed: {indexed_count} < {self.min_indexed}"
                ))
        
        return result


class Phase4NodeAnalysisContract(DataContract):
    """Contract for Phase 4: 15-Node Recursive Analysis."""
    
    def __init__(
        self,
        min_nodes_successful: int = 12,
        min_success_rate: float = 0.80,
        strict_mode: bool = False
    ):
        self.min_nodes_successful = min_nodes_successful
        self.min_success_rate = min_success_rate
        self.strict_mode = strict_mode
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate node analysis phase output."""
        result = ValidationResult(passed=True)
        
        # Get node execution stats
        nodes_executed = data.get("nodes_executed", 0)
        nodes_successful = data.get("nodes_successful", 0)
        
        # Check minimum successful nodes
        if nodes_successful < self.min_nodes_successful:
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                field_name="nodes_successful",
                expected=f">= {self.min_nodes_successful}",
                actual=nodes_successful,
                message=f"Insufficient successful nodes: {nodes_successful} < {self.min_nodes_successful}"
            ))
        
        # Check success rate in strict mode
        if self.strict_mode and nodes_executed > 0:
            success_rate = nodes_successful / nodes_executed
            if success_rate < self.min_success_rate:
                result.add_violation(ContractViolation(
                    violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                    field_name="success_rate",
                    expected=f">= {self.min_success_rate:.0%}",
                    actual=f"{success_rate:.0%}",
                    message=f"Node success rate too low: {success_rate:.0%} < {self.min_success_rate:.0%}"
                ))
        
        # Check for node data presence
        if not data.get("node_results"):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.EMPTY_REQUIRED_DATA,
                field_name="node_results",
                expected="non-empty dict",
                actual="empty or None",
                message="Node analysis must produce results data"
            ))
        
        return result


class Phase5PatternDetectionContract(DataContract):
    """Contract for Phase 5: Advanced Detection Patterns."""
    
    def __init__(
        self,
        min_patterns_executed: int = 20,
        strict_mode: bool = False
    ):
        self.min_patterns_executed = min_patterns_executed
        self.strict_mode = strict_mode
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate pattern detection phase output."""
        result = ValidationResult(passed=True)
        
        # Check minimum patterns executed
        patterns_executed = data.get("patterns_executed", 0)
        if patterns_executed < self.min_patterns_executed:
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                field_name="patterns_executed",
                expected=f">= {self.min_patterns_executed}",
                actual=patterns_executed,
                message=f"Insufficient patterns executed: {patterns_executed} < {self.min_patterns_executed}"
            ))
        
        return result


class Phase8EvidenceChainContract(DataContract):
    """Contract for Phase 8: Evidence Chain & Custody Finalization."""
    
    def __init__(self, require_evidence_chain: bool = True, strict_mode: bool = False):
        self.require_evidence_chain = require_evidence_chain
        self.strict_mode = strict_mode
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate evidence chain phase output."""
        result = ValidationResult(passed=True)
        
        if self.require_evidence_chain or self.strict_mode:
            # Check custody records exist
            custody_count = data.get("custody_records", 0)
            if custody_count == 0:
                result.add_violation(ContractViolation(
                    violation_type=ContractViolationType.EMPTY_REQUIRED_DATA,
                    field_name="custody_records",
                    expected="> 0",
                    actual=custody_count,
                    message="Evidence chain must contain custody records"
                ))
            
            # Check evidence hash exists
            if not data.get("evidence_chain_hash"):
                result.add_violation(ContractViolation(
                    violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                    field_name="evidence_chain_hash",
                    expected="SHA-256 hash",
                    actual="None or empty",
                    message="Evidence chain hash must be computed"
                ))
        
        return result


def create_contract_for_phase(phase_name: str, config: Dict[str, Any]) -> DataContract:
    """
    Factory function to create appropriate contract for a phase.
    
    Args:
        phase_name: Name of the analysis phase
        config: Configuration dict with thresholds
        
    Returns:
        DataContract instance for the phase
    """
    strict_mode = config.get("strict_mode", False)
    
    if "Configuration" in phase_name:
        return Phase1ConfigurationContract(strict_mode=strict_mode)
    
    elif "Data Collection" in phase_name:
        return Phase2DataCollectionContract(
            min_filings_total=config.get("min_filings_total", 1),
            min_filings_per_type=config.get("min_filings_per_type"),
            strict_mode=strict_mode
        )
    
    elif "Document Parsing" in phase_name:
        return Phase3DocumentParsingContract(
            min_parsed=config.get("min_documents_parsed", 1),
            min_indexed=config.get("min_chunks_indexed", 0),
            strict_mode=strict_mode
        )
    
    elif "Node Analysis" in phase_name:
        return Phase4NodeAnalysisContract(
            min_nodes_successful=config.get("min_nodes_successful", 12),
            min_success_rate=config.get("min_node_success_rate", 0.80),
            strict_mode=strict_mode
        )
    
    elif "Pattern Detection" in phase_name:
        return Phase5PatternDetectionContract(
            min_patterns_executed=config.get("min_patterns_executed", 20),
            strict_mode=strict_mode
        )
    
    elif "Evidence Chain" in phase_name:
        return Phase8EvidenceChainContract(
            require_evidence_chain=config.get("require_evidence_chain", True),
            strict_mode=strict_mode
        )
    
    # Default: no validation
    return DataContract()
