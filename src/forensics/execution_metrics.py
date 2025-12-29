"""
Execution Metrics Framework for JLAW
=====================================

Tracks execution metrics for all agent tiers:
- Agent execution times
- Token usage
- Violation counts
- Success/failure status
- Error tracking

Used by UnifiedAgentOrchestrator to profile multi-tier investigations.
"""

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class AgentExecutionMetric:
    """
    Single agent execution metric.
    
    Tracks timing, token usage, violations found, and status for
    a single agent execution.
    """
    agent_name: str
    agent_type: str  # "openai", "anthropic", "subagent", "pattern", "node"
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: float = 0.0
    tokens_used: int = 0
    violations_found: int = 0
    status: str = "pending"  # "pending", "success", "error", "timeout"
    error: Optional[str] = None
    tier: Optional[str] = None  # "primary", "subagent", "pattern", "node"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, status: str = "success", error: Optional[str] = None):
        """Mark metric as complete with status."""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        self.status = status
        if error:
            self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class ExecutionMetricsCollector:
    """
    Collects and exports agent execution metrics.
    
    Provides a centralized way to track all agent executions across
    the unified orchestrator and export metrics for analysis.
    
    Usage:
        collector = ExecutionMetricsCollector()
        
        metric = collector.start_agent("forensic-financial-analyst", "subagent")
        # ... execute agent ...
        metric.tokens_used = 1500
        metric.violations_found = 3
        collector.end_agent(metric, status="success")
        
        collector.export_metrics("output/metrics.json")
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: List[AgentExecutionMetric] = []
        self.active_metrics: Dict[str, AgentExecutionMetric] = {}
        self.start_time = time.time()
        
        logger.debug("ExecutionMetricsCollector initialized")
    
    def start_agent(
        self,
        agent_name: str,
        agent_type: str,
        tier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentExecutionMetric:
        """
        Start tracking an agent execution.
        
        Args:
            agent_name: Name of the agent
            agent_type: Type of agent ("openai", "anthropic", "subagent", "pattern", "node")
            tier: Tier of execution ("primary", "subagent", "pattern", "node")
            metadata: Additional metadata for the execution
            
        Returns:
            AgentExecutionMetric that can be updated and completed
        """
        metric = AgentExecutionMetric(
            agent_name=agent_name,
            agent_type=agent_type,
            start_time=time.time(),
            tier=tier,
            metadata=metadata or {}
        )
        
        self.metrics.append(metric)
        self.active_metrics[agent_name] = metric
        
        logger.debug(f"Started tracking: {agent_name} ({agent_type})")
        
        return metric
    
    def end_agent(
        self,
        metric: AgentExecutionMetric,
        status: str = "success",
        error: Optional[str] = None
    ):
        """
        Mark agent execution as complete.
        
        Args:
            metric: The metric to complete
            status: Execution status ("success", "error", "timeout")
            error: Optional error message if failed
        """
        metric.complete(status=status, error=error)
        
        # Remove from active metrics
        if metric.agent_name in self.active_metrics:
            del self.active_metrics[metric.agent_name]
        
        logger.debug(
            f"Completed tracking: {metric.agent_name} "
            f"({metric.duration_seconds:.2f}s, {metric.tokens_used} tokens, "
            f"{metric.violations_found} violations, status={status})"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all metrics.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.metrics:
            return {
                "total_agents": 0,
                "total_duration": 0.0,
                "total_tokens": 0,
                "total_violations": 0,
                "success_count": 0,
                "error_count": 0,
                "by_tier": {},
                "by_type": {}
            }
        
        total_duration = sum(m.duration_seconds for m in self.metrics)
        total_tokens = sum(m.tokens_used for m in self.metrics)
        total_violations = sum(m.violations_found for m in self.metrics)
        success_count = sum(1 for m in self.metrics if m.status == "success")
        error_count = sum(1 for m in self.metrics if m.status == "error")
        
        # Group by tier
        by_tier: Dict[str, Dict[str, Any]] = {}
        for metric in self.metrics:
            tier = metric.tier or "unknown"
            if tier not in by_tier:
                by_tier[tier] = {
                    "count": 0,
                    "duration": 0.0,
                    "tokens": 0,
                    "violations": 0
                }
            by_tier[tier]["count"] += 1
            by_tier[tier]["duration"] += metric.duration_seconds
            by_tier[tier]["tokens"] += metric.tokens_used
            by_tier[tier]["violations"] += metric.violations_found
        
        # Group by type
        by_type: Dict[str, Dict[str, Any]] = {}
        for metric in self.metrics:
            agent_type = metric.agent_type or "unknown"
            if agent_type not in by_type:
                by_type[agent_type] = {
                    "count": 0,
                    "duration": 0.0,
                    "tokens": 0,
                    "violations": 0
                }
            by_type[agent_type]["count"] += 1
            by_type[agent_type]["duration"] += metric.duration_seconds
            by_type[agent_type]["tokens"] += metric.tokens_used
            by_type[agent_type]["violations"] += metric.violations_found
        
        return {
            "total_agents": len(self.metrics),
            "total_duration": round(total_duration, 2),
            "total_tokens": total_tokens,
            "total_violations": total_violations,
            "success_count": success_count,
            "error_count": error_count,
            "by_tier": by_tier,
            "by_type": by_type,
            "collection_duration": round(time.time() - self.start_time, 2)
        }
    
    def export_metrics(self, filename: str = "agent_metrics.json"):
        """
        Export metrics to JSON file.
        
        Args:
            filename: Output filename (can be relative or absolute path)
        """
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "metrics": [m.to_dict() for m in self.metrics]
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(self.metrics)} metrics to {output_path}")
    
    def get_metrics_by_tier(self, tier: str) -> List[AgentExecutionMetric]:
        """Get all metrics for a specific tier."""
        return [m for m in self.metrics if m.tier == tier]
    
    def get_metrics_by_type(self, agent_type: str) -> List[AgentExecutionMetric]:
        """Get all metrics for a specific agent type."""
        return [m for m in self.metrics if m.agent_type == agent_type]
    
    def get_failed_agents(self) -> List[AgentExecutionMetric]:
        """Get all failed agent executions."""
        return [m for m in self.metrics if m.status in ("error", "timeout")]
