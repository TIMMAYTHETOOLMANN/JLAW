"""
Test Execution Audit Trail
===========================

Tests for execution audit tracking and reporting.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from src.core.execution_audit import (
    ExecutionAudit,
    AuditEvent,
    AuditEventType,
    PhaseMetrics,
    NodeExecutionRecord
)


class TestAuditEvent:
    """Test audit event creation."""
    
    def test_audit_event_creation(self):
        """Test creating an audit event."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.PHASE_START,
            phase="Phase 1",
            message="Starting phase",
            data={"test": "value"}
        )
        
        assert event.event_type == AuditEventType.PHASE_START
        assert event.phase == "Phase 1"
        assert event.message == "Starting phase"
    
    def test_audit_event_to_dict(self):
        """Test converting audit event to dict."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.ERROR,
            phase="Phase 2",
            message="Error occurred",
            data={"error": "test"}
        )
        
        event_dict = event.to_dict()
        
        assert "timestamp" in event_dict
        assert event_dict["event_type"] == "error"
        assert event_dict["phase"] == "Phase 2"


class TestPhaseMetrics:
    """Test phase metrics tracking."""
    
    def test_phase_metrics_creation(self):
        """Test creating phase metrics."""
        metrics = PhaseMetrics(
            phase_name="Phase 1: Configuration",
            start_time=datetime.utcnow()
        )
        
        assert metrics.phase_name == "Phase 1: Configuration"
        assert metrics.duration_seconds == 0.0
    
    def test_phase_metrics_complete(self):
        """Test completing phase metrics."""
        metrics = PhaseMetrics(
            phase_name="Phase 1",
            start_time=datetime.utcnow()
        )
        
        metrics.complete()
        
        assert metrics.end_time is not None
        assert metrics.duration_seconds >= 0
    
    def test_phase_metrics_to_dict(self):
        """Test converting phase metrics to dict."""
        metrics = PhaseMetrics(
            phase_name="Phase 1",
            start_time=datetime.utcnow()
        )
        metrics.records_extracted = 10
        metrics.records_expected = 15
        metrics.operations_attempted = 20
        metrics.operations_successful = 18
        metrics.complete()
        
        metrics_dict = metrics.to_dict()
        
        assert metrics_dict["phase"] == "Phase 1"
        assert metrics_dict["records"]["extracted"] == 10
        assert metrics_dict["records"]["expected"] == 15
        assert "success_rate" in metrics_dict["operations"]


class TestNodeExecutionRecord:
    """Test node execution record."""
    
    def test_node_record_creation(self):
        """Test creating node execution record."""
        start = datetime.utcnow()
        end = datetime.utcnow()
        
        record = NodeExecutionRecord(
            node_id="NODE_1",
            node_name="Form 4 Analysis",
            status="success",
            start_time=start,
            end_time=end,
            duration_seconds=5.0,
            violations_found=3,
            success=True
        )
        
        assert record.node_id == "NODE_1"
        assert record.success is True
        assert record.violations_found == 3
    
    def test_node_record_to_dict(self):
        """Test converting node record to dict."""
        start = datetime.utcnow()
        end = datetime.utcnow()
        
        record = NodeExecutionRecord(
            node_id="NODE_2",
            node_name="Compensation Analysis",
            status="failed",
            start_time=start,
            end_time=end,
            duration_seconds=2.5,
            violations_found=0,
            success=False,
            error_message="Data not available"
        )
        
        record_dict = record.to_dict()
        
        assert record_dict["node_id"] == "NODE_2"
        assert record_dict["success"] is False
        assert record_dict["error"] == "Data not available"


class TestExecutionAudit:
    """Test execution audit trail."""
    
    def test_audit_initialization(self):
        """Test initializing execution audit."""
        audit = ExecutionAudit(
            case_id="TEST-001",
            output_dir=Path("/tmp/test")
        )
        
        assert audit.case_id == "TEST-001"
        assert audit.execution_start is not None
        assert audit.aborted is False
    
    def test_record_event(self):
        """Test recording an event."""
        audit = ExecutionAudit("TEST-001")
        
        audit.record_event(
            AuditEventType.PHASE_START,
            "Phase 1",
            "Starting phase 1",
            {"key": "value"}
        )
        
        assert len(audit.events) == 1
        assert audit.events[0].event_type == AuditEventType.PHASE_START
    
    def test_start_phase(self):
        """Test starting a phase."""
        audit = ExecutionAudit("TEST-001")
        
        audit.start_phase("Phase 1: Configuration")
        
        assert audit.current_phase == "Phase 1: Configuration"
        assert "Phase 1: Configuration" in audit.phase_metrics
        assert len(audit.events) >= 1
    
    def test_complete_phase(self):
        """Test completing a phase."""
        audit = ExecutionAudit("TEST-001")
        
        audit.start_phase("Phase 1")
        audit.complete_phase(
            "Phase 1",
            records_extracted=10,
            records_expected=15,
            bytes_processed=1000
        )
        
        metrics = audit.phase_metrics["Phase 1"]
        assert metrics.end_time is not None
        assert metrics.records_extracted == 10
        assert metrics.records_expected == 15
    
    def test_fail_phase(self):
        """Test failing a phase."""
        audit = ExecutionAudit("TEST-001")
        
        audit.start_phase("Phase 2")
        audit.fail_phase("Phase 2", "Test error")
        
        metrics = audit.phase_metrics["Phase 2"]
        assert metrics.errors_count == 1
    
    def test_record_gate_validation(self):
        """Test recording gate validation."""
        audit = ExecutionAudit("TEST-001")
        
        audit.start_phase("Phase 1")
        audit.record_gate_validation(
            "Phase 1",
            passed=True,
            violations=[]
        )
        
        assert audit.total_gates_validated == 1
        assert audit.gates_passed == 1
        assert audit.gates_failed == 0
    
    def test_record_gate_validation_failure(self):
        """Test recording gate validation failure."""
        audit = ExecutionAudit("TEST-001")
        
        audit.start_phase("Phase 2")
        audit.record_gate_validation(
            "Phase 2",
            passed=False,
            violations=["Insufficient data", "Missing records"]
        )
        
        assert audit.total_gates_validated == 1
        assert audit.gates_passed == 0
        assert audit.gates_failed == 1
    
    def test_record_node_execution(self):
        """Test recording node execution."""
        audit = ExecutionAudit("TEST-001")
        
        record = NodeExecutionRecord(
            node_id="NODE_1",
            node_name="Test Node",
            status="success",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=1.0,
            violations_found=2,
            success=True
        )
        
        audit.record_node_execution(record)
        
        assert len(audit.node_executions) == 1
        assert audit.node_executions[0].node_id == "NODE_1"
    
    def test_record_error(self):
        """Test recording an error."""
        audit = ExecutionAudit("TEST-001")
        audit.start_phase("Phase 1")
        
        audit.record_error("Phase 1", "Test error message")
        
        # Find error event
        error_events = [e for e in audit.events if e.event_type == AuditEventType.ERROR]
        assert len(error_events) == 1
    
    def test_record_warning(self):
        """Test recording a warning."""
        audit = ExecutionAudit("TEST-001")
        audit.start_phase("Phase 1")
        
        audit.record_warning("Phase 1", "Test warning message")
        
        warning_events = [e for e in audit.events if e.event_type == AuditEventType.WARNING]
        assert len(warning_events) == 1
    
    def test_record_abort(self):
        """Test recording execution abort."""
        audit = ExecutionAudit("TEST-001")
        
        audit.record_abort("Phase 3", "Critical failure")
        
        assert audit.aborted is True
        assert audit.abort_reason == "Critical failure"
        assert audit.execution_end is not None
    
    def test_finalize(self):
        """Test finalizing audit."""
        audit = ExecutionAudit("TEST-001")
        
        audit.finalize()
        
        assert audit.execution_end is not None
    
    def test_get_summary(self):
        """Test getting audit summary."""
        audit = ExecutionAudit("TEST-001")
        
        audit.start_phase("Phase 1")
        audit.complete_phase("Phase 1")
        audit.record_gate_validation("Phase 1", True, [])
        
        audit.finalize()
        
        summary = audit.get_summary()
        
        assert summary["case_id"] == "TEST-001"
        assert summary["phases"] == 1
        assert summary["gates"]["total_validated"] == 1
        assert summary["gates"]["passed"] == 1
    
    def test_to_dict(self):
        """Test converting audit to dict."""
        audit = ExecutionAudit("TEST-001")
        
        audit.start_phase("Phase 1")
        audit.complete_phase("Phase 1")
        audit.finalize()
        
        audit_dict = audit.to_dict()
        
        assert "summary" in audit_dict
        assert "phases" in audit_dict
        assert "events" in audit_dict
        assert audit_dict["summary"]["case_id"] == "TEST-001"
    
    def test_save_to_file(self):
        """Test saving audit to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = ExecutionAudit("TEST-001", Path(tmpdir))
            
            audit.start_phase("Phase 1")
            audit.finalize()
            
            filepath = audit.save_to_file()
            
            assert filepath.exists()
            
            # Verify JSON is valid
            with open(filepath, 'r') as f:
                data = json.load(f)
                assert data["summary"]["case_id"] == "TEST-001"
    
    def test_generate_abort_report(self):
        """Test generating abort report."""
        audit = ExecutionAudit("TEST-001")
        
        audit.start_phase("Phase 1")
        audit.record_gate_validation("Phase 1", False, ["Violation 1"])
        audit.record_abort("Phase 1", "Gate validation failed")
        
        report = audit.generate_abort_report()
        
        assert "ABORTED" in report
        assert "TEST-001" in report
        assert "Gate validation failed" in report
    
    def test_abort_report_not_aborted(self):
        """Test abort report when not aborted."""
        audit = ExecutionAudit("TEST-001")
        
        report = audit.generate_abort_report()
        
        assert "not aborted" in report.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
