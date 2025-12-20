"""
Execution Metrics and Monitoring
================================

Provides instrumentation for:
- Execution time tracking per node
- Memory usage profiling
- API call rate limiting metrics
- Error rate tracking
- Phase duration monitoring
"""

import time
import logging
import psutil
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MetricStatus(Enum):
    """Status of a metric collection."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeMetrics:
    """Metrics for a single node execution."""
    node_id: int
    node_name: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    memory_mb_start: float = 0.0
    memory_mb_end: float = 0.0
    memory_mb_delta: float = 0.0
    api_calls: int = 0
    errors: int = 0
    warnings: int = 0
    findings_count: int = 0
    violations_count: int = 0
    status: MetricStatus = MetricStatus.PENDING
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "duration_seconds": round(self.duration_seconds, 3),
            "memory_mb_delta": round(self.memory_mb_delta, 2),
            "api_calls": self.api_calls,
            "errors": self.errors,
            "findings_count": self.findings_count,
            "status": self.status.value
        }


@dataclass
class PhaseMetrics:
    """Metrics for a single phase execution."""
    phase_name: str
    phase_number: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    items_processed: int = 0
    items_expected: int = 0
    errors: int = 0
    status: MetricStatus = MetricStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_name": self.phase_name,
            "phase_number": self.phase_number,
            "duration_seconds": round(self.duration_seconds, 3),
            "items_processed": self.items_processed,
            "completion_rate": round(self.items_processed / max(self.items_expected, 1) * 100, 1),
            "status": self.status.value
        }


@dataclass
class ExecutionMetrics:
    """Metrics for complete execution."""
    execution_id: str
    cik: str = ""
    company_name: str = ""
    investigation_type: str = "comprehensive"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    
    # Node metrics
    nodes_planned: int = 15
    nodes_executed: int = 0
    nodes_successful: int = 0
    nodes_failed: int = 0
    nodes_skipped: int = 0
    
    # Phase metrics
    phases_total: int = 9
    phases_completed: int = 0
    
    # Findings
    total_findings: int = 0
    total_violations: int = 0
    total_alerts: int = 0
    
    # Resource usage
    peak_memory_mb: float = 0.0
    total_api_calls: int = 0
    
    # Error tracking
    total_errors: int = 0
    total_warnings: int = 0
    error_messages: List[str] = field(default_factory=list)
    
    # Detailed metrics
    node_metrics: Dict[int, NodeMetrics] = field(default_factory=dict)
    phase_metrics: Dict[str, PhaseMetrics] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "cik": self.cik,
            "company_name": self.company_name,
            "investigation_type": self.investigation_type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_seconds": round(self.total_duration_seconds, 2),
            "summary": {
                "nodes_executed": self.nodes_executed,
                "nodes_successful": self.nodes_successful,
                "nodes_failed": self.nodes_failed,
                "nodes_skipped": self.nodes_skipped,
                "phases_completed": self.phases_completed,
                "total_findings": self.total_findings,
                "total_violations": self.total_violations
            },
            "resources": {
                "peak_memory_mb": round(self.peak_memory_mb, 2),
                "total_api_calls": self.total_api_calls
            },
            "errors": {
                "total_errors": self.total_errors,
                "total_warnings": self.total_warnings,
                "messages": self.error_messages[:10]  # Limit to first 10
            },
            "node_details": {
                node_id: m.to_dict() 
                for node_id, m in self.node_metrics.items()
            },
            "phase_details": {
                name: m.to_dict()
                for name, m in self.phase_metrics.items()
            }
        }


class MetricsCollector:
    """
    Collects and reports execution metrics.
    
    Usage:
        collector = MetricsCollector("EXEC-001")
        
        collector.start_phase("Phase 1: Configuration")
        # ... do work ...
        collector.end_phase("Phase 1: Configuration", items_processed=5)
        
        collector.start_node(1, "Form 4 Parser")
        # ... do work ...
        collector.end_node(1, status="success", findings=10)
        
        metrics = collector.finalize()
        print(metrics.to_dict())
    """
    
    # Node ID to name mapping
    NODE_NAMES = {
        1: "Form 4 Insider Trading",
        2: "DEF 14A Compensation",
        3: "10-Q Temporal Consistency",
        4: "10-K SOX Certification",
        5: "IRC §83 Tax Exposure",
        6: "Enforcement Routing",
        7: "13F Holdings",
        8: "13D/13G Ownership",
        9: "8-K Material Events",
        10: "Form 144 Restricted Sales",
        11: "Executive Network",
        12: "Earnings Calls",
        13: "Altman Z-Score",
        14: "Piotroski F-Score",
        15: "Market Correlation"
    }
    
    def __init__(self, execution_id: str, cik: str = "", company_name: str = ""):
        self.metrics = ExecutionMetrics(
            execution_id=execution_id,
            cik=cik,
            company_name=company_name
        )
        self.metrics.start_time = datetime.utcnow()
        self._phase_start_times: Dict[str, float] = {}
        self._node_start_times: Dict[int, float] = {}
        self._initial_memory = self._get_memory_mb()
        
        logger.info(f"MetricsCollector initialized: {execution_id}")
    
    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def set_investigation_type(self, investigation_type: str):
        """Set the investigation type."""
        self.metrics.investigation_type = investigation_type
    
    def set_nodes_planned(self, count: int):
        """Set the number of nodes planned for execution."""
        self.metrics.nodes_planned = count
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE TRACKING
    # ═══════════════════════════════════════════════════════════════
    
    def start_phase(self, phase_name: str, phase_number: int = 0, items_expected: int = 0):
        """Record phase start."""
        self._phase_start_times[phase_name] = time.time()
        
        self.metrics.phase_metrics[phase_name] = PhaseMetrics(
            phase_name=phase_name,
            phase_number=phase_number,
            start_time=datetime.utcnow(),
            items_expected=items_expected,
            status=MetricStatus.RUNNING
        )
        
        logger.debug(f"Phase started: {phase_name}")
    
    def end_phase(
        self, 
        phase_name: str, 
        status: str = "success",
        items_processed: int = 0,
        errors: int = 0
    ):
        """Record phase completion."""
        if phase_name in self.metrics.phase_metrics:
            phase = self.metrics.phase_metrics[phase_name]
            phase.end_time = datetime.utcnow()
            phase.items_processed = items_processed
            phase.errors = errors
            phase.status = MetricStatus.SUCCESS if status == "success" else MetricStatus.FAILED
            
            if phase_name in self._phase_start_times:
                phase.duration_seconds = time.time() - self._phase_start_times[phase_name]
            
            self.metrics.phases_completed += 1
            self.metrics.total_errors += errors
            
            logger.debug(f"Phase completed: {phase_name} in {phase.duration_seconds:.2f}s")
    
    # ═══════════════════════════════════════════════════════════════
    # NODE TRACKING
    # ═══════════════════════════════════════════════════════════════
    
    def start_node(self, node_id: int, node_name: str = ""):
        """Record node start."""
        self._node_start_times[node_id] = time.time()
        
        if not node_name:
            node_name = self.NODE_NAMES.get(node_id, f"Node {node_id}")
        
        self.metrics.node_metrics[node_id] = NodeMetrics(
            node_id=node_id,
            node_name=node_name,
            start_time=datetime.utcnow(),
            memory_mb_start=self._get_memory_mb(),
            status=MetricStatus.RUNNING
        )
        
        logger.debug(f"Node started: {node_id} - {node_name}")
    
    def end_node(
        self,
        node_id: int,
        status: str = "success",
        findings_count: int = 0,
        violations_count: int = 0,
        api_calls: int = 0,
        errors: int = 0,
        warnings: int = 0,
        error_message: str = ""
    ):
        """Record node completion."""
        if node_id in self.metrics.node_metrics:
            node = self.metrics.node_metrics[node_id]
            node.end_time = datetime.utcnow()
            node.memory_mb_end = self._get_memory_mb()
            node.memory_mb_delta = node.memory_mb_end - node.memory_mb_start
            node.findings_count = findings_count
            node.violations_count = violations_count
            node.api_calls = api_calls
            node.errors = errors
            node.warnings = warnings
            node.error_message = error_message
            
            if status == "success":
                node.status = MetricStatus.SUCCESS
                self.metrics.nodes_successful += 1
            elif status == "skipped":
                node.status = MetricStatus.SKIPPED
                self.metrics.nodes_skipped += 1
            else:
                node.status = MetricStatus.FAILED
                self.metrics.nodes_failed += 1
                if error_message:
                    self.metrics.error_messages.append(f"Node {node_id}: {error_message}")
            
            if node_id in self._node_start_times:
                node.duration_seconds = time.time() - self._node_start_times[node_id]
            
            self.metrics.nodes_executed += 1
            self.metrics.total_findings += findings_count
            self.metrics.total_violations += violations_count
            self.metrics.total_api_calls += api_calls
            self.metrics.total_errors += errors
            self.metrics.total_warnings += warnings
            
            # Track peak memory
            if node.memory_mb_end > self.metrics.peak_memory_mb:
                self.metrics.peak_memory_mb = node.memory_mb_end
            
            logger.debug(f"Node completed: {node_id} - {status} in {node.duration_seconds:.2f}s")
    
    def skip_node(self, node_id: int, reason: str = ""):
        """Record a skipped node."""
        node_name = self.NODE_NAMES.get(node_id, f"Node {node_id}")
        
        self.metrics.node_metrics[node_id] = NodeMetrics(
            node_id=node_id,
            node_name=node_name,
            status=MetricStatus.SKIPPED,
            error_message=reason
        )
        
        self.metrics.nodes_skipped += 1
        logger.debug(f"Node skipped: {node_id} - {reason}")
    
    # ═══════════════════════════════════════════════════════════════
    # API CALL TRACKING
    # ═══════════════════════════════════════════════════════════════
    
    def record_api_call(self, node_id: Optional[int] = None):
        """Record an API call."""
        self.metrics.total_api_calls += 1
        
        if node_id and node_id in self.metrics.node_metrics:
            self.metrics.node_metrics[node_id].api_calls += 1
    
    # ═══════════════════════════════════════════════════════════════
    # ERROR TRACKING
    # ═══════════════════════════════════════════════════════════════
    
    def record_error(self, message: str, node_id: Optional[int] = None):
        """Record an error."""
        self.metrics.total_errors += 1
        self.metrics.error_messages.append(message)
        
        if node_id and node_id in self.metrics.node_metrics:
            self.metrics.node_metrics[node_id].errors += 1
    
    def record_warning(self, message: str, node_id: Optional[int] = None):
        """Record a warning."""
        self.metrics.total_warnings += 1
        
        if node_id and node_id in self.metrics.node_metrics:
            self.metrics.node_metrics[node_id].warnings += 1
    
    # ═══════════════════════════════════════════════════════════════
    # FINALIZATION
    # ═══════════════════════════════════════════════════════════════
    
    def finalize(self) -> ExecutionMetrics:
        """Finalize and return metrics."""
        self.metrics.end_time = datetime.utcnow()
        self.metrics.total_duration_seconds = (
            self.metrics.end_time - self.metrics.start_time
        ).total_seconds()
        
        # Calculate totals
        self.metrics.total_alerts = self.metrics.total_findings + self.metrics.total_violations
        
        logger.info(
            f"Execution complete: {self.metrics.execution_id} - "
            f"{self.metrics.total_duration_seconds:.2f}s, "
            f"{self.metrics.nodes_successful}/{self.metrics.nodes_executed} nodes successful, "
            f"{self.metrics.total_findings} findings"
        )
        
        return self.metrics
    
    def get_summary(self) -> str:
        """Generate human-readable summary."""
        m = self.metrics
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "  EXECUTION METRICS SUMMARY",
            "═══════════════════════════════════════════════════════════════",
            f"  Execution ID: {m.execution_id}",
            f"  Target: {m.company_name} (CIK: {m.cik})",
            f"  Investigation Type: {m.investigation_type}",
            f"  Duration: {m.total_duration_seconds:.2f}s",
            "",
            f"  Nodes: {m.nodes_successful}/{m.nodes_executed} successful ({m.nodes_skipped} skipped)",
            f"  Phases: {m.phases_completed}/{m.phases_total} completed",
            f"  Findings: {m.total_findings} | Violations: {m.total_violations}",
            "",
            f"  Peak Memory: {m.peak_memory_mb:.1f} MB",
            f"  API Calls: {m.total_api_calls}",
            f"  Errors: {m.total_errors} | Warnings: {m.total_warnings}",
            "═══════════════════════════════════════════════════════════════",
        ]
        return "\n".join(lines)
