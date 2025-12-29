"""
Intelligent Subagent Router for JLAW Forensic System
====================================================

Intelligent routing system that plans multi-agent execution, performs
top-K agent selection, creates parallel execution stages, and aggregates
results with consensus tracking.

Key Features:
- Intelligent agent selection based on capability scoring
- Parallel execution planning with dependency tracking
- Result fusion and consensus computation
- Cost estimation for token usage optimization
- Conflict detection and manual review flagging

Usage:
    from src.forensics.intelligent_router import IntelligentSubagentRouter
    from src.forensics.agent_registry import DynamicAgentRegistry
    
    registry = DynamicAgentRegistry()
    router = IntelligentSubagentRouter(registry)
    
    decision = router.plan_execution(violations, max_agents=5)
    result = await router.execute(decision, violations, context)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from collections import Counter

from src.forensics.agent_registry import DynamicAgentRegistry, AgentCapability

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """
    Execution plan for multi-agent orchestration.
    
    Attributes:
        selected_agents: List of agents selected for execution
        execution_plan: List of agent name lists (stages for parallel execution)
        estimated_cost: Estimated token cost (placeholder)
        confidence_threshold: Minimum confidence for consensus
        agent_scores: Relevance scores for each agent
    """
    selected_agents: List[AgentCapability]
    execution_plan: List[List[str]]  # Stages of agent names
    estimated_cost: float = 0.0
    confidence_threshold: float = 0.7
    agent_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class AgentResult:
    """
    Result from single agent execution.
    
    Attributes:
        agent_name: Name of agent that produced result
        status: Execution status ('success', 'error', 'timeout')
        findings: Findings dict from agent
        recommendations: Recommendations from agent
        severity: Severity assessment
        execution_time: Time taken in seconds
        error: Error message if failed
    """
    agent_name: str
    status: str
    findings: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    severity: str = ""
    execution_time: float = 0.0
    error: Optional[str] = None


class IntelligentSubagentRouter:
    """
    Intelligent routing system for multi-agent orchestration.
    
    Plans execution strategy, selects top-K agents, creates parallel
    stages, and aggregates results with consensus tracking.
    """
    
    def __init__(self, registry: Optional[DynamicAgentRegistry] = None):
        """
        Initialize intelligent router.
        
        Args:
            registry: DynamicAgentRegistry instance (creates new if None)
        """
        self.registry = registry or DynamicAgentRegistry()
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info(f"🧠 IntelligentSubagentRouter initialized with {len(self.registry.agents)} agents")
    
    def plan_execution(
        self,
        violations: List[Dict[str, Any]],
        max_agents: int = 5,
        parallel_stages: int = 3,
        confidence_threshold: float = 0.7
    ) -> RoutingDecision:
        """
        Create intelligent execution plan for violations.
        
        Steps:
        1. Score agents based on violation type relevance
        2. Select top-K agents (max_agents)
        3. Sort by priority and API availability
        4. Create parallel execution stages
        
        Args:
            violations: List of violation dicts
            max_agents: Maximum agents to select (default: 5)
            parallel_stages: Number of parallel stages (default: 3)
            confidence_threshold: Minimum confidence for consensus (default: 0.7)
            
        Returns:
            RoutingDecision with execution plan
        """
        if not violations:
            logger.warning("No violations provided for execution planning")
            return RoutingDecision(
                selected_agents=[],
                execution_plan=[],
                estimated_cost=0.0,
                confidence_threshold=confidence_threshold
            )
        
        # Get top-K agents from registry
        selected_agents = self.registry.get_agents_for_violations(
            violations=violations,
            top_k=max_agents
        )
        
        if not selected_agents:
            logger.warning(f"No agents found for violations: {[v.get('type', 'unknown') for v in violations]}")
            # Fallback: use forensic-compliance-auditor if available
            fallback = self.registry.get_agent('forensic-compliance-auditor')
            if fallback:
                selected_agents = [fallback]
        
        # Calculate agent scores for tracking
        agent_scores = {}
        violation_types = [v.get('type') or v.get('violation_type', '') for v in violations if v.get('type') or v.get('violation_type')]
        for agent in selected_agents:
            agent_scores[agent.agent_name] = agent.score_for_violations(violation_types)
        
        # Create parallel execution stages
        execution_plan = self._create_parallel_stages(selected_agents, parallel_stages)
        
        # Estimate token cost (simple heuristic)
        estimated_cost = self._estimate_cost(selected_agents, violations)
        
        decision = RoutingDecision(
            selected_agents=selected_agents,
            execution_plan=execution_plan,
            estimated_cost=estimated_cost,
            confidence_threshold=confidence_threshold,
            agent_scores=agent_scores
        )
        
        logger.info(f"Execution plan created:")
        logger.info(f"  - Selected agents: {len(selected_agents)}")
        logger.info(f"  - Parallel stages: {len(execution_plan)}")
        logger.info(f"  - Estimated cost: ${estimated_cost:.2f}")
        for i, stage in enumerate(execution_plan):
            logger.info(f"  - Stage {i+1}: {', '.join(stage)}")
        
        return decision
    
    def _create_parallel_stages(
        self,
        agents: List[AgentCapability],
        num_stages: int
    ) -> List[List[str]]:
        """
        Create parallel execution stages from agent list.
        
        Groups agents into stages based on priority. Higher priority
        agents execute first. Agents in same stage execute in parallel.
        
        Args:
            agents: List of AgentCapability objects
            num_stages: Desired number of stages
            
        Returns:
            List of agent name lists (one list per stage)
        """
        if not agents:
            return []
        
        if num_stages <= 1:
            # All agents in single stage
            return [[agent.agent_name for agent in agents]]
        
        # Sort agents by priority (highest first)
        sorted_agents = sorted(agents, key=lambda a: (-a.priority, a.agent_name))
        
        # Distribute agents across stages
        stages: List[List[str]] = [[] for _ in range(num_stages)]
        
        for i, agent in enumerate(sorted_agents):
            stage_idx = min(i // max(1, len(sorted_agents) // num_stages), num_stages - 1)
            stages[stage_idx].append(agent.agent_name)
        
        # Remove empty stages
        stages = [stage for stage in stages if stage]
        
        return stages
    
    def _estimate_cost(
        self,
        agents: List[AgentCapability],
        violations: List[Dict[str, Any]]
    ) -> float:
        """
        Estimate token cost for agent execution.
        
        Simple heuristic: $0.01 per agent per violation.
        Real implementation would use actual token counting.
        
        Args:
            agents: List of agents to execute
            violations: List of violations to analyze
            
        Returns:
            Estimated cost in USD
        """
        # Placeholder: $0.01 per agent per violation
        return len(agents) * len(violations) * 0.01
    
    async def execute(
        self,
        decision: RoutingDecision,
        violations: List[Dict[str, Any]],
        context: Dict[str, Any],
        orchestrator: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute routing decision with multi-stage parallel execution.
        
        Args:
            decision: RoutingDecision from plan_execution()
            violations: List of violation dicts
            context: Additional context for agents
            orchestrator: Optional SubagentOrchestrator for actual execution
            
        Returns:
            Aggregated results dict with:
            - status: Overall status
            - agents_executed: Number of agents executed
            - stage_results: Results from each stage
            - combined_findings: Aggregated findings
            - consensus_score: Agent agreement metric
            - conflicts: List of conflicting findings
        """
        start_time = datetime.now()
        
        if not decision.execution_plan:
            logger.warning("Empty execution plan, nothing to execute")
            return {
                "status": "no_agents",
                "agents_executed": 0,
                "stage_results": [],
                "combined_findings": [],
                "consensus_score": 0.0,
                "conflicts": [],
                "execution_time": 0.0
            }
        
        # Execute stages sequentially (agents within stage execute in parallel)
        all_stage_results = []
        
        for stage_idx, agent_names in enumerate(decision.execution_plan):
            logger.info(f"Executing stage {stage_idx + 1}/{len(decision.execution_plan)}: {', '.join(agent_names)}")
            
            stage_results = await self._execute_stage(
                agent_names=agent_names,
                violations=violations,
                context=context,
                orchestrator=orchestrator
            )
            
            all_stage_results.append(stage_results)
        
        # Aggregate results from all stages
        combined_findings = self._aggregate_findings(all_stage_results)
        consensus_score = self._compute_consensus(all_stage_results)
        conflicts = self._detect_conflicts(all_stage_results)
        
        # Count successful executions
        agents_executed = sum(
            sum(1 for r in stage.values() if r.status == 'success')
            for stage in all_stage_results
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "status": "completed" if agents_executed > 0 else "failed",
            "agents_executed": agents_executed,
            "total_agents_planned": len(decision.selected_agents),
            "stage_results": all_stage_results,
            "combined_findings": combined_findings,
            "consensus_score": consensus_score,
            "conflicts": conflicts,
            "execution_time": execution_time,
            "agent_scores": decision.agent_scores
        }
        
        # Record in history
        self.execution_history.append({
            "timestamp": start_time.isoformat(),
            "violations_count": len(violations),
            "agents_executed": agents_executed,
            "consensus_score": consensus_score,
            "conflicts_found": len(conflicts)
        })
        
        logger.info(f"Execution completed: {agents_executed}/{len(decision.selected_agents)} agents succeeded")
        logger.info(f"Consensus score: {consensus_score:.2%}")
        logger.info(f"Conflicts detected: {len(conflicts)}")
        
        return result
    
    async def _execute_stage(
        self,
        agent_names: List[str],
        violations: List[Dict[str, Any]],
        context: Dict[str, Any],
        orchestrator: Optional[Any] = None
    ) -> Dict[str, AgentResult]:
        """
        Execute single stage (agents in parallel).
        
        Args:
            agent_names: List of agent names to execute
            violations: Violations to analyze
            context: Context dict
            orchestrator: Optional orchestrator for execution
            
        Returns:
            Dict mapping agent name to AgentResult
        """
        # Execute agents in parallel
        tasks = []
        for agent_name in agent_names:
            task = self._execute_single_agent(
                agent_name=agent_name,
                violations=violations,
                context=context,
                orchestrator=orchestrator
            )
            tasks.append((agent_name, task))
        
        # Wait for all agents in stage
        results = {}
        for agent_name, task in tasks:
            try:
                result = await task
                results[agent_name] = result
            except Exception as e:
                logger.error(f"Agent {agent_name} execution failed: {e}")
                results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    status="error",
                    error=str(e)
                )
        
        return results
    
    async def _execute_single_agent(
        self,
        agent_name: str,
        violations: List[Dict[str, Any]],
        context: Dict[str, Any],
        orchestrator: Optional[Any] = None
    ) -> AgentResult:
        """
        Execute single agent.
        
        Args:
            agent_name: Name of agent to execute
            violations: Violations to analyze
            context: Context dict
            orchestrator: Optional orchestrator instance
            
        Returns:
            AgentResult with execution outcome
        """
        start_time = datetime.now()
        
        try:
            # Get agent capability
            capability = self.registry.get_agent(agent_name)
            if not capability:
                raise ValueError(f"Agent {agent_name} not found in registry")
            
            # If orchestrator provided, use it to spawn agent
            if orchestrator:
                result = await orchestrator.spawn_subagent(
                    agent_name=agent_name,
                    task_description=f"Analyze {len(violations)} violations",
                    input_data={
                        "violations": violations,
                        **context
                    }
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return AgentResult(
                    agent_name=agent_name,
                    status="success" if result.get("status") == "success" else "error",
                    findings=result.get("findings", {}),
                    recommendations=result.get("recommendations", []),
                    severity=result.get("severity", ""),
                    execution_time=execution_time,
                    error=result.get("error")
                )
            else:
                # Placeholder execution (no actual API call)
                logger.debug(f"Agent {agent_name} executed (placeholder mode)")
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return AgentResult(
                    agent_name=agent_name,
                    status="success",
                    findings={"message": f"Agent {agent_name} placeholder execution"},
                    recommendations=[],
                    severity="medium",
                    execution_time=execution_time
                )
        
        except Exception as e:
            logger.error(f"Error executing agent {agent_name}: {e}", exc_info=True)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_name=agent_name,
                status="error",
                error=str(e),
                execution_time=execution_time
            )
    
    def _aggregate_findings(
        self,
        stage_results: List[Dict[str, AgentResult]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate findings from all stages.
        
        Args:
            stage_results: List of stage result dicts
            
        Returns:
            List of combined findings
        """
        all_findings = []
        
        for stage in stage_results:
            for agent_name, result in stage.items():
                if result.status == "success" and result.findings:
                    finding = {
                        "agent": agent_name,
                        "findings": result.findings,
                        "recommendations": result.recommendations,
                        "severity": result.severity,
                        "execution_time": result.execution_time
                    }
                    all_findings.append(finding)
        
        return all_findings
    
    def _compute_consensus(
        self,
        stage_results: List[Dict[str, AgentResult]]
    ) -> float:
        """
        Compute consensus score (agent agreement).
        
        Measures how often agents agree on findings. Simple heuristic:
        - Count successful executions
        - Count consistent severity assessments
        
        Args:
            stage_results: List of stage result dicts
            
        Returns:
            Consensus score (0.0-1.0)
        """
        all_results = []
        for stage in stage_results:
            all_results.extend(stage.values())
        
        if not all_results:
            return 0.0
        
        # Count successful executions
        successful = sum(1 for r in all_results if r.status == "success")
        if successful == 0:
            return 0.0
        
        # Count severity assessments
        severities = [r.severity for r in all_results if r.status == "success" and r.severity]
        
        if not severities:
            return float(successful) / len(all_results)
        
        # Most common severity
        severity_counts = Counter(severities)
        most_common_count = severity_counts.most_common(1)[0][1]
        
        # Consensus = (most common count) / (total successful)
        consensus = most_common_count / successful
        
        return consensus
    
    def _detect_conflicts(
        self,
        stage_results: List[Dict[str, AgentResult]]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicting findings between agents.
        
        Args:
            stage_results: List of stage result dicts
            
        Returns:
            List of conflict dicts
        """
        conflicts = []
        
        # Collect all severity assessments
        severities_by_agent = {}
        for stage in stage_results:
            for agent_name, result in stage.items():
                if result.status == "success" and result.severity:
                    severities_by_agent[agent_name] = result.severity
        
        if len(severities_by_agent) < 2:
            return conflicts
        
        # Check for severity conflicts
        severity_values = list(severities_by_agent.values())
        unique_severities = set(severity_values)
        
        if len(unique_severities) > 1:
            conflicts.append({
                "type": "severity_conflict",
                "description": f"Agents disagree on severity: {dict(severities_by_agent)}",
                "agents_involved": list(severities_by_agent.keys())
            })
        
        return conflicts
    
    def build_agent_prompt(
        self,
        agent: AgentCapability,
        violations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """
        Build prompt for agent execution.
        
        Args:
            agent: AgentCapability object
            violations: Violations to analyze
            context: Additional context
            
        Returns:
            Formatted prompt string
        """
        # Start with agent's prompt template
        prompt = agent.prompt_template
        
        # Append task-specific information
        prompt += f"\n\n## Task: Analyze Violations\n\n"
        prompt += f"You are being invoked to analyze {len(violations)} violation(s):\n\n"
        
        for i, violation in enumerate(violations, 1):
            vtype = violation.get('type') or violation.get('violation_type', 'unknown')
            prompt += f"{i}. **{vtype}**\n"
            for key, value in violation.items():
                if key not in ['type', 'violation_type']:
                    prompt += f"   - {key}: {value}\n"
        
        # Add context
        if context:
            prompt += f"\n## Context\n\n"
            for key, value in context.items():
                if key != 'violations':
                    prompt += f"- **{key}**: {value}\n"
        
        return prompt
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get execution history.
        
        Returns:
            List of execution records
        """
        return self.execution_history


__all__ = [
    'IntelligentSubagentRouter',
    'RoutingDecision',
    'AgentResult'
]
