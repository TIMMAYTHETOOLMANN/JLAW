"""
Phase Execution Exceptions
===========================

Custom exceptions for phase execution flow control and error handling.
These exceptions enable precise error reporting and enforcement of
DOJ-grade execution standards.
"""

from typing import Optional


class PhaseExecutionError(Exception):
    """
    Base exception for phase execution errors.
    
    All phase-related exceptions inherit from this class to enable
    unified exception handling for phase execution failures.
    """
    pass


class PhaseDefinitionError(PhaseExecutionError):
    """
    Phase definition not found or invalid.
    
    Raised when:
    - Attempting to execute a phase that doesn't exist in the registry
    - Phase definition is malformed or missing required fields
    """
    pass


class PhaseDependencyError(PhaseExecutionError):
    """
    Phase dependency not satisfied.
    
    Raised when:
    - A required dependency phase has not been executed
    - A dependency phase failed and cannot proceed
    - Circular dependencies detected in phase graph
    """
    pass


class PhaseGateFailure(PhaseExecutionError):
    """
    Phase gate validation failed.
    
    Raised when a phase completes but fails to meet the quality
    thresholds defined in its validation rules. This is critical
    for DOJ-grade output integrity.
    
    Attributes:
        phase_id: Identifier of the failed phase
        rule: Specific validation rule that failed
    """
    
    def __init__(self, message: str, phase_id: Optional[str] = None, rule: Optional[str] = None):
        """
        Initialize phase gate failure.
        
        Args:
            message: Human-readable error message
            phase_id: ID of the phase that failed validation
            rule: Name of the validation rule that was violated
        """
        super().__init__(message)
        self.phase_id = phase_id
        self.rule = rule


class EvidenceChainIntegrityError(PhaseExecutionError):
    """
    Evidence chain integrity compromised.
    
    Raised when:
    - Hash verification fails (triple-hash mismatch)
    - Merkle tree construction fails
    - Chain of custody is broken
    - RFC 3161 timestamp validation fails
    - FRE 902(13)/(14) compliance cannot be established
    
    This is a CRITICAL error that MUST halt execution immediately
    as it compromises the admissibility of all evidence.
    """
    pass


class PhaseTimeoutError(PhaseExecutionError):
    """
    Phase execution exceeded timeout.
    
    Raised when a phase takes longer than its configured timeout
    threshold. This prevents infinite execution and ensures
    timely forensic analysis completion.
    """
    pass


class NodeExecutionError(PhaseExecutionError):
    """
    A node in the recursive analysis engine failed to produce valid results.

    Raised when:
    - A node's ``analyze`` method returns ``None``, an empty list, or an
      empty dict instead of meaningful output.
    - A node catches an internal exception and cannot proceed.
    - The FailLoud mixin detects that a node produced no results.

    Attributes:
        node_id: Identifier of the failing node (e.g. ``"NODE_5"``).
    """

    def __init__(self, message: str, node_id: Optional[str] = None):
        """
        Initialize node execution error.

        Args:
            message: Human-readable error message.
            node_id: Identifier of the node that failed.
        """
        super().__init__(message)
        self.node_id = node_id
