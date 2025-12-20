"""
Execution Audit Trail
====================

Real-time tracking and auditing of forensic analysis execution.
Provides detailed metrics, timestamps, and validation results.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from enum import Enum


class AuditEventType(Enum):
    """Types of audit events."""
    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"
    PHASE_FAILED = "phase_failed"
    GATE_VALIDATION = "gate_validation"
    NODE_EXECUTION = "node_execution"
    PATTERN_DETECTION = "pattern_detection"
    ERROR = "error"
    WARNING = "warning"
    ABORT = "abort"


@dataclass
class AuditEvent:
    """Single audit trail event."""
    timestamp: datetime
    event_type: AuditEventType
    phase: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "phase": self.phase,
            "message": self.message,
            "data": self.data
        }


@dataclass
class PhaseMetrics:
    """Metrics for a single phase execution."""
    phase_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Data metrics
    bytes_processed: int = 0
    records_extracted: int = 0
    records_expected: int = 0
    
    # Execution metrics
    operations_attempted: int = 0
    operations_successful: int = 0
    errors_count: int = 0
    
    # Validation
    gate_validation_passed: bool = False
    gate_violations: List[str] = field(default_factory=list)
    
    def complete(self):
        """Mark phase as complete."""
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase": self.phase_name,
            "start": self.start_time.isoformat() if self.start_time else None,
            "end": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "bytes_processed": self.bytes_processed,
            "records": {
                "extracted": self.records_extracted,
                "expected": self.records_expected,
                "rate": f"{self.records_extracted}/{self.records_expected}" if self.records_expected > 0 else "N/A"
            },
            "operations": {
                "attempted": self.operations_attempted,
                "successful": self.operations_successful,
                "success_rate": f"{self.operations_successful/self.operations_attempted:.1%}" if self.operations_attempted > 0 else "N/A"
            },
            "errors": self.errors_count,
            "validation": {
                "passed": self.gate_validation_passed,
                "violations": self.gate_violations
            }
        }


@dataclass
class NodeExecutionRecord:
    """Record of node execution for audit trail."""
    node_id: str
    node_name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    violations_found: int
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "status": self.status,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat(),
            "duration_seconds": round(self.duration_seconds, 2),
            "violations_found": self.violations_found,
            "success": self.success,
            "error": self.error_message
        }


class ExecutionAudit:
    """
    Real-time execution audit trail tracker.
    
    Tracks all phases, gates, nodes, and validation events
    for complete forensic analysis accountability.
    """
    
    def __init__(self, case_id: str, output_dir: Optional[Path] = None):
        self.case_id = case_id
        self.output_dir = output_dir or Path("output")
        self.execution_start = datetime.utcnow()
        self.execution_end: Optional[datetime] = None
        
        # Audit data
        self.events: List[AuditEvent] = []
        self.phase_metrics: Dict[str, PhaseMetrics] = {}
        self.node_executions: List[NodeExecutionRecord] = []
        
        # Current state
        self.current_phase: Optional[str] = None
        self.aborted: bool = False
        self.abort_reason: Optional[str] = None
        
        # Summary stats
        self.total_gates_validated: int = 0
        self.gates_passed: int = 0
        self.gates_failed: int = 0
    
    def record_event(
        self,
        event_type: AuditEventType,
        phase: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Record an audit event."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            phase=phase,
            message=message,
            data=data or {}
        )
        self.events.append(event)
    
    def start_phase(self, phase_name: str):
        """Record phase start."""
        self.current_phase = phase_name
        self.phase_metrics[phase_name] = PhaseMetrics(
            phase_name=phase_name,
            start_time=datetime.utcnow()
        )
        self.record_event(
            AuditEventType.PHASE_START,
            phase_name,
            f"Starting phase: {phase_name}"
        )
    
    def complete_phase(
        self,
        phase_name: str,
        records_extracted: int = 0,
        records_expected: int = 0,
        bytes_processed: int = 0
    ):
        """Record phase completion."""
        if phase_name in self.phase_metrics:
            metrics = self.phase_metrics[phase_name]
            metrics.complete()
            metrics.records_extracted = records_extracted
            metrics.records_expected = records_expected
            metrics.bytes_processed = bytes_processed
            
            self.record_event(
                AuditEventType.PHASE_COMPLETE,
                phase_name,
                f"Completed phase: {phase_name}",
                data=metrics.to_dict()
            )
    
    def fail_phase(self, phase_name: str, error: str):
        """Record phase failure."""
        if phase_name in self.phase_metrics:
            metrics = self.phase_metrics[phase_name]
            metrics.complete()
            metrics.errors_count += 1
        
        self.record_event(
            AuditEventType.PHASE_FAILED,
            phase_name,
            f"Phase failed: {phase_name}",
            data={"error": error}
        )
    
    def record_gate_validation(
        self,
        phase_name: str,
        passed: bool,
        violations: List[str]
    ):
        """Record gate validation result."""
        self.total_gates_validated += 1
        if passed:
            self.gates_passed += 1
        else:
            self.gates_failed += 1
        
        if phase_name in self.phase_metrics:
            metrics = self.phase_metrics[phase_name]
            metrics.gate_validation_passed = passed
            metrics.gate_violations = violations
        
        self.record_event(
            AuditEventType.GATE_VALIDATION,
            phase_name,
            f"Gate validation {'PASSED' if passed else 'FAILED'}",
            data={"passed": passed, "violations": violations}
        )
    
    def record_node_execution(self, node_record: NodeExecutionRecord):
        """Record node execution."""
        self.node_executions.append(node_record)
        self.record_event(
            AuditEventType.NODE_EXECUTION,
            "Phase 4: Node Analysis",
            f"Node {node_record.node_id} executed",
            data=node_record.to_dict()
        )
    
    def record_error(self, phase: str, error: str):
        """Record an error."""
        self.record_event(
            AuditEventType.ERROR,
            phase,
            f"Error: {error}",
            data={"error": error}
        )
    
    def record_warning(self, phase: str, warning: str):
        """Record a warning."""
        self.record_event(
            AuditEventType.WARNING,
            phase,
            f"Warning: {warning}",
            data={"warning": warning}
        )
    
    def record_abort(self, phase: str, reason: str):
        """Record execution abort."""
        self.aborted = True
        self.abort_reason = reason
        self.execution_end = datetime.utcnow()
        
        self.record_event(
            AuditEventType.ABORT,
            phase,
            f"EXECUTION ABORTED: {reason}",
            data={"reason": reason, "phase": phase}
        )
    
    def finalize(self):
        """Finalize audit trail."""
        self.execution_end = datetime.utcnow()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get audit summary."""
        duration = 0.0
        if self.execution_start and self.execution_end:
            duration = (self.execution_end - self.execution_start).total_seconds()
        
        return {
            "case_id": self.case_id,
            "execution_start": self.execution_start.isoformat(),
            "execution_end": self.execution_end.isoformat() if self.execution_end else None,
            "total_duration_seconds": round(duration, 2),
            "aborted": self.aborted,
            "abort_reason": self.abort_reason,
            "gates": {
                "total_validated": self.total_gates_validated,
                "passed": self.gates_passed,
                "failed": self.gates_failed,
                "pass_rate": f"{self.gates_passed/self.total_gates_validated:.1%}" if self.total_gates_validated > 0 else "N/A"
            },
            "nodes": {
                "total_executed": len(self.node_executions),
                "successful": sum(1 for n in self.node_executions if n.success),
                "failed": sum(1 for n in self.node_executions if not n.success)
            },
            "phases": len(self.phase_metrics),
            "events": len(self.events)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export complete audit trail."""
        return {
            "summary": self.get_summary(),
            "phases": {name: metrics.to_dict() for name, metrics in self.phase_metrics.items()},
            "nodes": [n.to_dict() for n in self.node_executions],
            "events": [e.to_dict() for e in self.events]
        }
    
    def save_to_file(self, filename: Optional[str] = None):
        """Save audit trail to JSON file."""
        if filename is None:
            filename = f"audit_trail_{self.case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        return filepath
    
    def generate_abort_report(self) -> str:
        """Generate detailed abort report."""
        if not self.aborted:
            return "Execution not aborted"
        
        lines = [
            "=" * 80,
            "FORENSIC ANALYSIS EXECUTION ABORTED",
            "=" * 80,
            "",
            f"Case ID: {self.case_id}",
            f"Abort Time: {self.execution_end.isoformat() if self.execution_end else 'Unknown'}",
            f"Abort Phase: {self.current_phase or 'Unknown'}",
            f"Abort Reason: {self.abort_reason or 'Unknown'}",
            "",
            "=" * 80,
            "EXECUTION SUMMARY",
            "=" * 80,
            "",
            f"Total Duration: {(self.execution_end - self.execution_start).total_seconds():.2f}s" if self.execution_end else "Unknown",
            f"Phases Completed: {len([m for m in self.phase_metrics.values() if m.end_time])} / {len(self.phase_metrics)}",
            f"Gates Validated: {self.total_gates_validated} ({self.gates_passed} passed, {self.gates_failed} failed)",
            "",
            "=" * 80,
            "PHASE STATUS",
            "=" * 80,
            ""
        ]
        
        for phase_name, metrics in self.phase_metrics.items():
            status = "✓ COMPLETE" if metrics.end_time else "✗ INCOMPLETE"
            gate = "✓ PASSED" if metrics.gate_validation_passed else "✗ FAILED" if metrics.gate_violations else "- NOT VALIDATED"
            lines.append(f"  {phase_name}")
            lines.append(f"    Status: {status}")
            lines.append(f"    Gate: {gate}")
            if metrics.gate_violations:
                lines.append(f"    Violations: {len(metrics.gate_violations)}")
                for v in metrics.gate_violations[:3]:  # Show first 3
                    lines.append(f"      - {v}")
            lines.append("")
        
        lines.extend([
            "=" * 80,
            "PARTIAL RESULTS PRESERVED",
            "=" * 80,
            "",
            f"Audit trail saved to: {self.output_dir}",
            f"Partial dossier may be available in output directory",
            "",
            "=" * 80
        ])
        
        return "\n".join(lines)
