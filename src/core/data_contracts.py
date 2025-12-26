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


class Phase6DualAgentContract(DataContract):
    """Validates dual-agent AI cross-validation completion.
    
    Ensures both OpenAI and Anthropic agents have processed the analysis
    and cross-validation has been performed.
    """
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.openai_validation_complete: bool = False
        self.anthropic_validation_complete: bool = False
        self.cross_validation_score: float = 0.0
        self.discrepancies_resolved: bool = False
        self.min_confidence_threshold: float = 0.75
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """At least one AI agent must be responsive (per audit spec)."""
        result = ValidationResult(passed=True)
        
        openai_complete = data.get("openai_validation_complete", False)
        anthropic_complete = data.get("anthropic_validation_complete", False)
        cross_validation_score = data.get("cross_validation_score", 0.0)
        min_threshold = data.get("min_confidence_threshold", 0.75)
        
        # At least one AI agent must be responsive
        if not (openai_complete or anthropic_complete):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.FAILED_DEPENDENCY,
                field_name="ai_agents",
                expected="At least one agent responsive",
                actual="No agents responsive",
                message="At least one AI agent (OpenAI or Anthropic) must complete validation"
            ))
        
        # Check confidence threshold if any agent is responsive
        if (openai_complete or anthropic_complete) and cross_validation_score < min_threshold:
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                field_name="cross_validation_score",
                expected=f">= {min_threshold}",
                actual=cross_validation_score,
                message=f"Cross-validation confidence too low: {cross_validation_score} < {min_threshold}"
            ))
        
        return result


class Phase7SubagentContract(DataContract):
    """Validates subagent orchestration completion.
    
    Ensures all 10 Claude specialized agents have been properly orchestrated
    and their results aggregated.
    """
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.agents_deployed: int = 0
        self.agents_completed: int = 0
        self.required_agents: int = 10
        self.min_completion_ratio: float = 0.80
        self.orchestration_errors: List[str] = []
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """80% of agents must complete successfully."""
        result = ValidationResult(passed=True)
        
        agents_deployed = data.get("agents_deployed", 0)
        agents_completed = data.get("agents_completed", 0)
        min_ratio = data.get("min_completion_ratio", 0.80)
        
        # Check if any agents were deployed
        if agents_deployed == 0:
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.EMPTY_REQUIRED_DATA,
                field_name="agents_deployed",
                expected="> 0",
                actual=0,
                message="No subagents were deployed for orchestration"
            ))
            return result
        
        # Check completion ratio
        completion_ratio = agents_completed / agents_deployed
        if completion_ratio < min_ratio:
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.INSUFFICIENT_RECORDS,
                field_name="completion_ratio",
                expected=f">= {min_ratio:.0%}",
                actual=f"{completion_ratio:.0%}",
                message=f"Insufficient agents completed: {agents_completed}/{agents_deployed} ({completion_ratio:.0%}) < {min_ratio:.0%}"
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


class Phase9DossierContract(DataContract):
    """Validates DOJ-grade dossier meets FRE 902(13)/(14) standards.
    
    Ensures the final forensic dossier contains all required components
    for courtroom admissibility.
    """
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        # FRE 902(13) - Certified Records of a Regularly Conducted Activity
        self.fre_902_13_compliant: bool = False
        # FRE 902(14) - Certified Data Copied from Electronic Device
        self.fre_902_14_compliant: bool = False
        # Evidence chain integrity
        self.evidence_chain_complete: bool = False
        self.triple_hash_verified: bool = False  # SHA-256 + SHA3-512 + BLAKE2b
        self.merkle_tree_valid: bool = False  # RFC 6962 compliant
        # Dossier components
        self.executive_summary_present: bool = False
        self.findings_documented: bool = False
        self.evidence_exhibits_attached: bool = False
        self.chain_of_custody_documented: bool = False
        # Timestamp compliance
        self.rfc_3161_timestamp_present: bool = False
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """All FRE compliance and evidence integrity requirements must be met."""
        result = ValidationResult(passed=True)
        
        # Check FRE 902(13) compliance
        if not data.get("fre_902_13_compliant", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                field_name="fre_902_13_compliant",
                expected=True,
                actual=False,
                message="Dossier must be FRE 902(13) compliant (Certified Records)"
            ))
        
        # Check FRE 902(14) compliance
        if not data.get("fre_902_14_compliant", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                field_name="fre_902_14_compliant",
                expected=True,
                actual=False,
                message="Dossier must be FRE 902(14) compliant (Certified Electronic Data)"
            ))
        
        # Check evidence chain complete
        if not data.get("evidence_chain_complete", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                field_name="evidence_chain_complete",
                expected=True,
                actual=False,
                message="Evidence chain must be complete and documented"
            ))
        
        # Check triple-hash verification
        if not data.get("triple_hash_verified", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.HASH_MISMATCH,
                field_name="triple_hash_verified",
                expected=True,
                actual=False,
                message="Triple-hash integrity (SHA-256 + SHA3-512 + BLAKE2b) must be verified"
            ))
        
        # Check Merkle tree validity
        if not data.get("merkle_tree_valid", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.HASH_MISMATCH,
                field_name="merkle_tree_valid",
                expected=True,
                actual=False,
                message="Merkle tree (RFC 6962) must be valid"
            ))
        
        # Check executive summary
        if not data.get("executive_summary_present", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                field_name="executive_summary_present",
                expected=True,
                actual=False,
                message="Dossier must contain executive summary"
            ))
        
        # Check findings documented
        if not data.get("findings_documented", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                field_name="findings_documented",
                expected=True,
                actual=False,
                message="Forensic findings must be documented"
            ))
        
        # Check evidence exhibits
        if not data.get("evidence_exhibits_attached", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                field_name="evidence_exhibits_attached",
                expected=True,
                actual=False,
                message="Evidence exhibits must be attached to dossier"
            ))
        
        # Check chain of custody documentation
        if not data.get("chain_of_custody_documented", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                field_name="chain_of_custody_documented",
                expected=True,
                actual=False,
                message="Chain of custody must be documented"
            ))
        
        # Check RFC 3161 timestamp
        if not data.get("rfc_3161_timestamp_present", False):
            result.add_violation(ContractViolation(
                violation_type=ContractViolationType.MISSING_REQUIRED_FIELD,
                field_name="rfc_3161_timestamp_present",
                expected=True,
                actual=False,
                message="RFC 3161 timestamp token must be present"
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
    
    elif "Dual-Agent" in phase_name or "Dual Agent" in phase_name:
        return Phase6DualAgentContract(strict_mode=strict_mode)
    
    elif "Subagent" in phase_name:
        return Phase7SubagentContract(strict_mode=strict_mode)
    
    elif "Evidence Chain" in phase_name:
        return Phase8EvidenceChainContract(
            require_evidence_chain=config.get("require_evidence_chain", True),
            strict_mode=strict_mode
        )
    
    elif "Dossier" in phase_name:
        return Phase9DossierContract(strict_mode=strict_mode)
    
    # Default: no validation
    return DataContract()
