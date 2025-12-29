"""
Optimization Analyzer
=====================

Analyzes performance metrics and generates actionable optimization
recommendations to reduce costs and improve execution efficiency.

Features:
- Identifies token-heavy agents (>10K tokens)
- Identifies cost-heavy agents (>$0.50)
- Identifies slow agents (>60 seconds)
- Identifies low-value agents (high cost, few violations)
- Estimates potential cost savings
- Provides specific optimization suggestions

Usage:
    from src.profiling import PerformanceMetricsCollector, OptimizationAnalyzer
    
    # After collecting metrics
    analyzer = OptimizationAnalyzer()
    recommendations = analyzer.analyze(metrics_collector)
    
    print(f"Potential savings: ${recommendations['potential_savings']['total']:.2f}")
    for rec in recommendations['recommendations']:
        print(f"- {rec['message']}")
"""

import logging
from typing import Dict, List, Any

from .performance_metrics import PerformanceMetricsCollector, AgentMetrics

logger = logging.getLogger(__name__)


class OptimizationAnalyzer:
    """
    Analyzes performance metrics and suggests optimizations.
    
    Provides actionable recommendations to reduce costs, improve
    execution speed, and optimize agent selection.
    """
    
    # Thresholds for optimization recommendations
    TOKEN_HEAVY_THRESHOLD = 10000  # >10K tokens
    COST_HEAVY_THRESHOLD = 0.50    # >$0.50
    SLOW_AGENT_THRESHOLD = 60.0    # >60 seconds
    LOW_VALUE_COST_THRESHOLD = 0.20  # >$0.20
    LOW_VALUE_VIOLATIONS_THRESHOLD = 2  # <2 violations
    
    def __init__(self):
        """Initialize optimization analyzer."""
        logger.debug("OptimizationAnalyzer initialized")
    
    def analyze(self, metrics: PerformanceMetricsCollector) -> Dict[str, Any]:
        """
        Generate optimization recommendations.
        
        Args:
            metrics: PerformanceMetricsCollector with collected metrics
            
        Returns:
            Dictionary with recommendations and potential savings
        """
        recommendations = []
        
        # Check for token-heavy agents
        token_heavy = self._identify_token_heavy_agents(metrics)
        if token_heavy:
            recommendations.append({
                "type": "token_reduction",
                "severity": "high",
                "priority": 1,
                "message": f"{len(token_heavy)} agents using >{self.TOKEN_HEAVY_THRESHOLD} tokens",
                "agents": token_heavy,
                "suggestion": "Truncate input content or use cheaper models",
                "actions": [
                    "Implement content truncation for large documents",
                    "Use summarization before sending to agents",
                    "Consider using streaming for long content"
                ]
            })
        
        # Check for cost-heavy agents
        cost_heavy = self._identify_cost_heavy_agents(metrics)
        if cost_heavy:
            recommendations.append({
                "type": "cost_reduction",
                "severity": "high",
                "priority": 1,
                "message": f"{len(cost_heavy)} agents costing >${self.COST_HEAVY_THRESHOLD}",
                "agents": cost_heavy,
                "suggestion": "Use cheaper models (GPT-4o, Claude Haiku)",
                "actions": [
                    "Switch from GPT-4 to GPT-4o (75% cost reduction)",
                    "Switch from Claude Opus to Claude Sonnet (80% cost reduction)",
                    "Use Claude Haiku for simple classification tasks (91% cost reduction)"
                ]
            })
        
        # Check for slow agents
        slow_agents = self._identify_slow_agents(metrics)
        if slow_agents:
            recommendations.append({
                "type": "performance",
                "severity": "medium",
                "priority": 2,
                "message": f"{len(slow_agents)} agents taking >{self.SLOW_AGENT_THRESHOLD}s",
                "agents": slow_agents,
                "suggestion": "Consider parallelization or caching",
                "actions": [
                    "Implement caching for repeated queries",
                    "Parallelize independent agent executions",
                    "Use async execution patterns"
                ]
            })
        
        # Check for low-value agents (high cost, few violations)
        low_value = self._identify_low_value_agents(metrics)
        if low_value:
            recommendations.append({
                "type": "agent_selection",
                "severity": "medium",
                "priority": 2,
                "message": f"{len(low_value)} agents with low ROI",
                "agents": low_value,
                "suggestion": "Consider excluding from future investigations or adjusting thresholds",
                "actions": [
                    "Review agent effectiveness metrics",
                    "Adjust violation detection thresholds",
                    "Consider conditional agent invocation based on document type"
                ]
            })
        
        # Check for duplicate work patterns
        duplicate_work = self._identify_duplicate_work(metrics)
        if duplicate_work:
            recommendations.append({
                "type": "duplicate_work",
                "severity": "low",
                "priority": 3,
                "message": f"Found {len(duplicate_work)} potential duplicate analysis patterns",
                "patterns": duplicate_work,
                "suggestion": "Implement result caching and deduplication",
                "actions": [
                    "Cache agent results by content hash",
                    "Deduplicate similar content before analysis",
                    "Share context between related agents"
                ]
            })
        
        # Estimate potential savings
        potential_savings = self._estimate_savings(
            recommendations,
            metrics
        )
        
        # Generate summary
        summary = self._generate_summary(
            metrics,
            recommendations,
            potential_savings
        )
        
        return {
            "recommendations": recommendations,
            "potential_savings": potential_savings,
            "summary": summary
        }
    
    def _identify_token_heavy_agents(
        self,
        metrics: PerformanceMetricsCollector
    ) -> List[Dict[str, Any]]:
        """Identify agents using >TOKEN_HEAVY_THRESHOLD tokens."""
        return [
            {
                "agent": a.agent_name,
                "tokens": a.total_tokens,
                "cost": round(a.total_cost, 4),
                "tier": a.tier
            }
            for a in metrics.agent_metrics
            if a.total_tokens > self.TOKEN_HEAVY_THRESHOLD
        ]
    
    def _identify_cost_heavy_agents(
        self,
        metrics: PerformanceMetricsCollector
    ) -> List[Dict[str, Any]]:
        """Identify agents costing >COST_HEAVY_THRESHOLD."""
        return [
            {
                "agent": a.agent_name,
                "cost": round(a.total_cost, 4),
                "tokens": a.total_tokens,
                "model": a.model,
                "tier": a.tier
            }
            for a in metrics.agent_metrics
            if a.total_cost > self.COST_HEAVY_THRESHOLD
        ]
    
    def _identify_slow_agents(
        self,
        metrics: PerformanceMetricsCollector
    ) -> List[Dict[str, Any]]:
        """Identify agents taking >SLOW_AGENT_THRESHOLD seconds."""
        return [
            {
                "agent": a.agent_name,
                "duration": round(a.duration_seconds, 2),
                "cost": round(a.total_cost, 4),
                "tier": a.tier
            }
            for a in metrics.agent_metrics
            if a.duration_seconds > self.SLOW_AGENT_THRESHOLD
        ]
    
    def _identify_low_value_agents(
        self,
        metrics: PerformanceMetricsCollector
    ) -> List[Dict[str, Any]]:
        """Identify agents with cost >LOW_VALUE_COST_THRESHOLD but <LOW_VALUE_VIOLATIONS_THRESHOLD violations."""
        return [
            {
                "agent": a.agent_name,
                "cost": round(a.total_cost, 4),
                "violations": a.violations_found,
                "cost_per_violation": round(
                    a.total_cost / max(a.violations_found, 1), 4
                ),
                "tier": a.tier
            }
            for a in metrics.agent_metrics
            if a.total_cost > self.LOW_VALUE_COST_THRESHOLD 
            and a.violations_found < self.LOW_VALUE_VIOLATIONS_THRESHOLD
        ]
    
    def _identify_duplicate_work(
        self,
        metrics: PerformanceMetricsCollector
    ) -> List[Dict[str, Any]]:
        """
        Identify potential duplicate work patterns.
        
        Looks for:
        - Multiple agents with similar names analyzing same tier
        - Agents with very similar token counts (potential duplicate content)
        """
        duplicates = []
        
        # Group agents by tier
        agents_by_tier: Dict[str, List[AgentMetrics]] = {}
        for agent in metrics.agent_metrics:
            tier = agent.tier or "unknown"
            if tier not in agents_by_tier:
                agents_by_tier[tier] = []
            agents_by_tier[tier].append(agent)
        
        # Check for similar token counts in same tier (potential duplicate content)
        for tier, agents in agents_by_tier.items():
            if len(agents) < 2:
                continue
            
            for i, agent1 in enumerate(agents):
                for agent2 in agents[i+1:]:
                    # If token counts are within 10% of each other
                    if agent1.total_tokens > 0 and agent2.total_tokens > 0:
                        ratio = min(agent1.total_tokens, agent2.total_tokens) / max(agent1.total_tokens, agent2.total_tokens)
                        if ratio > 0.90:
                            duplicates.append({
                                "agent1": agent1.agent_name,
                                "agent2": agent2.agent_name,
                                "tier": tier,
                                "tokens1": agent1.total_tokens,
                                "tokens2": agent2.total_tokens,
                                "similarity": f"{ratio:.1%}"
                            })
        
        return duplicates
    
    def _estimate_savings(
        self,
        recommendations: List[Dict],
        metrics: PerformanceMetricsCollector
    ) -> Dict[str, float]:
        """
        Estimate potential cost savings from recommendations.
        
        Args:
            recommendations: List of optimization recommendations
            metrics: Performance metrics collector
            
        Returns:
            Dictionary with savings estimates by category
        """
        savings = {
            "token_reduction": 0.0,
            "model_downgrade": 0.0,
            "agent_exclusion": 0.0,
            "caching": 0.0,
            "total": 0.0
        }
        
        for rec in recommendations:
            if rec["type"] == "token_reduction":
                # Assume 30% token reduction possible
                for agent in rec["agents"]:
                    savings["token_reduction"] += agent["cost"] * 0.3
            
            elif rec["type"] == "cost_reduction":
                # Assume 50-75% cost reduction with cheaper models
                for agent in rec["agents"]:
                    # Different savings based on current model
                    if agent.get("model"):
                        model = agent["model"].lower()
                        if "opus" in model:
                            savings["model_downgrade"] += agent["cost"] * 0.80  # 80% savings
                        elif "gpt-4" in model and "turbo" not in model:
                            savings["model_downgrade"] += agent["cost"] * 0.75  # 75% savings
                        else:
                            savings["model_downgrade"] += agent["cost"] * 0.50  # 50% savings
                    else:
                        savings["model_downgrade"] += agent["cost"] * 0.50
            
            elif rec["type"] == "agent_selection":
                # Exclude low-value agents entirely
                for agent in rec["agents"]:
                    savings["agent_exclusion"] += agent["cost"]
            
            elif rec["type"] == "duplicate_work":
                # Assume 25% savings from caching
                total_cost = sum(a.total_cost for a in metrics.agent_metrics)
                savings["caching"] += total_cost * 0.25
        
        # Calculate total
        savings["total"] = sum(
            v for k, v in savings.items() if k != "total"
        )
        
        # Round all values
        for k in savings:
            savings[k] = round(savings[k], 4)
        
        return savings
    
    def _generate_summary(
        self,
        metrics: PerformanceMetricsCollector,
        recommendations: List[Dict],
        savings: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate optimization summary.
        
        Args:
            metrics: Performance metrics collector
            recommendations: List of recommendations
            savings: Estimated savings
            
        Returns:
            Summary dictionary
        """
        summary_data = metrics.get_summary()
        current_cost = summary_data["total_cost_usd"]
        
        return {
            "current_cost": current_cost,
            "potential_savings": savings["total"],
            "optimized_cost": round(current_cost - savings["total"], 4),
            "savings_percentage": round(
                (savings["total"] / max(current_cost, 0.0001)) * 100, 1
            ),
            "recommendations_count": len(recommendations),
            "high_priority_count": sum(
                1 for r in recommendations if r.get("severity") == "high"
            ),
            "total_agents_analyzed": summary_data["total_agents_invoked"],
            "total_tokens_analyzed": summary_data["total_tokens"]
        }
