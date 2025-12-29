"""
Performance Metrics Collector with Cost Tracking
=================================================

Enhanced metrics collection with comprehensive cost tracking for
OpenAI and Anthropic API usage. Extends the basic ExecutionMetricsCollector
with detailed cost analysis and optimization capabilities.

Features:
- Token usage tracking per agent (input/output separation)
- Cost calculation per agent using current API pricing
- Phase-based metrics aggregation
- Tier-based breakdown (primary, subagent, pattern, node)
- Agent ranking by cost and effectiveness
- Detailed performance reports

Usage:
    collector = PerformanceMetricsCollector()
    
    # Start tracking a phase
    phase = collector.start_phase("unified_orchestration", "Unified Agent Orchestration")
    
    # Start tracking an agent
    agent = collector.start_agent("forensic-analyst", "anthropic", "subagent")
    
    # ... execute agent ...
    
    # End tracking with token usage
    collector.end_agent(
        "forensic-analyst",
        input_tokens=5000,
        output_tokens=1500,
        model="claude-sonnet-3.5",
        violations_found=3
    )
    
    # End phase
    collector.end_phase("unified_orchestration")
    
    # Export detailed report
    collector.export_detailed_report(Path("output/performance_metrics.json"))
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """
    Metrics for a single agent execution.
    
    Tracks comprehensive performance and cost metrics for each agent invocation,
    including timing, token usage (input/output separated), cost breakdown,
    and effectiveness metrics.
    """
    agent_name: str
    agent_type: str  # "openai", "anthropic", "subagent", "pattern", "node"
    tier: str  # "primary", "subagent", "pattern", "node"
    
    # Timing
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: float = 0.0
    
    # Token usage (separated for accurate cost calculation)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # Cost (USD)
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    
    # Results
    violations_found: int = 0
    consensus_contribution: float = 0.0
    status: str = "pending"  # "pending", "success", "error", "timeout"
    error: Optional[str] = None
    
    # Metadata
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class PhaseMetrics:
    """
    Metrics for a single phase execution.
    
    Aggregates metrics for all agents executed within a phase,
    providing phase-level summary statistics.
    """
    phase_id: str
    phase_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: float = 0.0
    agent_metrics: List[AgentMetrics] = field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
    status: str = "pending"  # "pending", "success", "error"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "status": self.status,
            "agents_count": len(self.agent_metrics),
            "agent_metrics": [a.to_dict() for a in self.agent_metrics]
        }


class PerformanceMetricsCollector:
    """
    Collects comprehensive performance metrics during execution.
    
    Provides enhanced metrics collection with detailed cost tracking,
    phase-based aggregation, and optimization recommendations preparation.
    
    Key Features:
    - Track token usage with input/output separation
    - Calculate costs using current OpenAI/Anthropic pricing
    - Organize metrics by phase and tier
    - Generate detailed performance reports
    - Rank agents by cost and effectiveness
    """
    
    # Token pricing (as of December 2024)
    # Prices are per 1K tokens (input/output)
    PRICING = {
        "openai": {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.0025, "output": 0.01},  # GPT-4o
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        },
        "anthropic": {
            "claude-opus-4": {"input": 0.015, "output": 0.075},
            "claude-sonnet-3.5": {"input": 0.003, "output": 0.015},
            "claude-haiku-3": {"input": 0.00025, "output": 0.00125},
        }
    }
    
    def __init__(self):
        """Initialize performance metrics collector."""
        self.investigation_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.phase_metrics: List[PhaseMetrics] = []
        self.agent_metrics: List[AgentMetrics] = []
        self._active_agents: Dict[str, AgentMetrics] = {}
        
        logger.info(f"PerformanceMetricsCollector initialized: {self.investigation_id}")
    
    def start_phase(self, phase_id: str, phase_name: str) -> PhaseMetrics:
        """
        Start tracking a phase.
        
        Args:
            phase_id: Unique identifier for the phase
            phase_name: Human-readable phase name
            
        Returns:
            PhaseMetrics object for this phase
        """
        metrics = PhaseMetrics(
            phase_id=phase_id,
            phase_name=phase_name,
            start_time=time.time()
        )
        self.phase_metrics.append(metrics)
        
        logger.debug(f"Started phase tracking: {phase_name} ({phase_id})")
        
        return metrics
    
    def end_phase(self, phase_id: str, status: str = "success"):
        """
        End tracking a phase.
        
        Args:
            phase_id: Unique identifier for the phase
            status: Phase completion status ("success", "error", "partial")
        """
        for metrics in self.phase_metrics:
            if metrics.phase_id == phase_id:
                metrics.end_time = time.time()
                metrics.duration_seconds = metrics.end_time - metrics.start_time
                metrics.status = status
                
                # Aggregate agent metrics
                metrics.total_tokens = sum(
                    a.total_tokens for a in metrics.agent_metrics
                )
                metrics.total_cost = sum(
                    a.total_cost for a in metrics.agent_metrics
                )
                
                logger.debug(
                    f"Ended phase tracking: {metrics.phase_name} "
                    f"({metrics.duration_seconds:.2f}s, "
                    f"{metrics.total_tokens} tokens, "
                    f"${metrics.total_cost:.4f})"
                )
                break
    
    def start_agent(
        self,
        agent_name: str,
        agent_type: str,
        tier: str,
        model: Optional[str] = None
    ) -> AgentMetrics:
        """
        Start tracking an agent execution.
        
        Args:
            agent_name: Name of the agent
            agent_type: Type of agent ("openai", "anthropic", "subagent", "pattern", "node")
            tier: Tier of execution ("primary", "subagent", "pattern", "node")
            model: Optional model name for cost calculation
            
        Returns:
            AgentMetrics object for this agent
        """
        metrics = AgentMetrics(
            agent_name=agent_name,
            agent_type=agent_type,
            tier=tier,
            start_time=time.time(),
            model=model
        )
        
        self.agent_metrics.append(metrics)
        self._active_agents[agent_name] = metrics
        
        logger.debug(f"Started agent tracking: {agent_name} ({agent_type}, {tier})")
        
        return metrics
    
    def end_agent(
        self,
        agent_name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: Optional[str] = None,
        violations_found: int = 0,
        consensus_contribution: float = 0.0,
        status: str = "success",
        error: Optional[str] = None
    ):
        """
        End tracking an agent execution.
        
        Args:
            agent_name: Name of the agent
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            model: Model name for cost calculation (overrides value from start_agent)
            violations_found: Number of violations detected
            consensus_contribution: Agent's contribution to consensus (0.0-1.0)
            status: Execution status ("success", "error", "timeout")
            error: Optional error message if failed
        """
        # Find the most recent matching agent metric
        agent_metric = None
        for metrics in reversed(self.agent_metrics):
            if metrics.agent_name == agent_name and metrics.end_time is None:
                agent_metric = metrics
                break
        
        if not agent_metric:
            logger.warning(f"No active agent metric found for: {agent_name}")
            return
        
        # Update timing
        agent_metric.end_time = time.time()
        agent_metric.duration_seconds = agent_metric.end_time - agent_metric.start_time
        
        # Update tokens
        agent_metric.input_tokens = input_tokens
        agent_metric.output_tokens = output_tokens
        agent_metric.total_tokens = input_tokens + output_tokens
        
        # Update results
        agent_metric.violations_found = violations_found
        agent_metric.consensus_contribution = consensus_contribution
        agent_metric.status = status
        agent_metric.error = error
        
        # Update model if provided
        if model:
            agent_metric.model = model
        
        # Calculate cost
        if agent_metric.agent_type in self.PRICING and agent_metric.model:
            pricing = self._get_pricing(agent_metric.agent_type, agent_metric.model)
            agent_metric.input_cost = (input_tokens / 1000) * pricing["input"]
            agent_metric.output_cost = (output_tokens / 1000) * pricing["output"]
            agent_metric.total_cost = agent_metric.input_cost + agent_metric.output_cost
        
        # Associate with current phase
        if self.phase_metrics:
            current_phase = self.phase_metrics[-1]
            if agent_metric not in current_phase.agent_metrics:
                current_phase.agent_metrics.append(agent_metric)
        
        # Remove from active agents
        if agent_name in self._active_agents:
            del self._active_agents[agent_name]
        
        logger.debug(
            f"Ended agent tracking: {agent_name} "
            f"({agent_metric.duration_seconds:.2f}s, "
            f"{agent_metric.total_tokens} tokens, "
            f"${agent_metric.total_cost:.4f}, "
            f"{violations_found} violations)"
        )
    
    def _get_pricing(self, agent_type: str, model: str) -> Dict[str, float]:
        """
        Get pricing for a model.
        
        Args:
            agent_type: Type of agent ("openai" or "anthropic")
            model: Model name
            
        Returns:
            Dictionary with "input" and "output" pricing per 1K tokens
        """
        if agent_type == "openai":
            if "gpt-4o" in model.lower():
                return self.PRICING["openai"]["gpt-4o"]
            elif "gpt-4-turbo" in model.lower() or "turbo" in model.lower():
                return self.PRICING["openai"]["gpt-4-turbo"]
            elif "gpt-4" in model.lower():
                return self.PRICING["openai"]["gpt-4"]
            else:
                return self.PRICING["openai"]["gpt-3.5-turbo"]
        elif agent_type == "anthropic":
            if "opus" in model.lower():
                return self.PRICING["anthropic"]["claude-opus-4"]
            elif "sonnet" in model.lower():
                return self.PRICING["anthropic"]["claude-sonnet-3.5"]
            elif "haiku" in model.lower():
                return self.PRICING["anthropic"]["claude-haiku-3"]
            else:
                # Default to Sonnet pricing
                return self.PRICING["anthropic"]["claude-sonnet-3.5"]
        
        # Default fallback
        return {"input": 0, "output": 0}
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Returns:
            Dictionary with comprehensive summary statistics
        """
        total_duration = time.time() - self.start_time
        total_tokens = sum(a.total_tokens for a in self.agent_metrics)
        total_cost = sum(a.total_cost for a in self.agent_metrics)
        total_violations = sum(a.violations_found for a in self.agent_metrics)
        
        # Count by status
        success_count = sum(1 for a in self.agent_metrics if a.status == "success")
        error_count = sum(1 for a in self.agent_metrics if a.status == "error")
        
        # Group by tier
        tier_breakdown = {}
        for agent in self.agent_metrics:
            tier = agent.tier or "unknown"
            if tier not in tier_breakdown:
                tier_breakdown[tier] = {
                    "agents": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "violations": 0
                }
            tier_breakdown[tier]["agents"] += 1
            tier_breakdown[tier]["tokens"] += agent.total_tokens
            tier_breakdown[tier]["cost"] += agent.total_cost
            tier_breakdown[tier]["violations"] += agent.violations_found
        
        # Round cost values
        for tier in tier_breakdown.values():
            tier["cost"] = round(tier["cost"], 4)
        
        return {
            "investigation_id": self.investigation_id,
            "total_duration_seconds": round(total_duration, 2),
            "total_phases": len(self.phase_metrics),
            "total_agents_invoked": len(self.agent_metrics),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "cost_per_token": round(total_cost / max(total_tokens, 1) * 1000, 6),
            "total_violations_found": total_violations,
            "success_count": success_count,
            "error_count": error_count,
            "tier_breakdown": tier_breakdown,
            "phase_breakdown": [
                {
                    "phase": p.phase_name,
                    "duration": round(p.duration_seconds, 2),
                    "tokens": p.total_tokens,
                    "cost": round(p.total_cost, 4)
                }
                for p in self.phase_metrics
            ]
        }
    
    def export_detailed_report(self, output_path: Path):
        """
        Export detailed performance report to JSON.
        
        Args:
            output_path: Path for the output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "investigation_id": self.investigation_id,
            "export_timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "phases": [p.to_dict() for p in self.phase_metrics],
            "agent_ranking": self._get_agent_ranking()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Exported detailed performance report to {output_path}")
    
    def _get_agent_ranking(self) -> List[Dict[str, Any]]:
        """
        Rank agents by token usage and cost.
        
        Returns:
            List of top 10 agents ranked by cost
        """
        sorted_agents = sorted(
            self.agent_metrics,
            key=lambda a: a.total_cost,
            reverse=True
        )
        
        return [
            {
                "rank": i + 1,
                "agent_name": a.agent_name,
                "agent_type": a.agent_type,
                "tier": a.tier,
                "total_tokens": a.total_tokens,
                "total_cost": round(a.total_cost, 4),
                "violations_found": a.violations_found,
                "cost_per_violation": round(
                    a.total_cost / max(a.violations_found, 1), 4
                ),
                "duration_seconds": round(a.duration_seconds, 2)
            }
            for i, a in enumerate(sorted_agents[:10])  # Top 10
        ]
