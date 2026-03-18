"""
Forensic Meta-Orchestrator
==========================

Dynamic agent spawning and orchestration system for complex forensic
investigations requiring specialized analysis and parallel execution.

Features:
- Dynamic agent spawning based on investigation type
- Parallel execution with dependency tracking
- Circuit breaker integration for fault tolerance
- Result aggregation with conflict resolution
- Intelligent agent selection based on violation patterns

Architecture:
    ForensicMetaOrchestrator
        ├── Agent Registry (available specialized agents)
        ├── Dependency Graph (agent execution order)
        ├── Circuit Breaker Registry (fault tolerance)
        └── Result Aggregator (merge & deduplicate)

Example:
    orchestrator = ForensicMetaOrchestrator()
    
    # Register specialized agents
    orchestrator.register_agent("options_backdating", OptionsBackdatingAgent())
    orchestrator.register_agent("channel_stuffing", ChannelStuffingAgent())
    
    # Execute investigation
    results = await orchestrator.investigate(
        violation_types=["insider_trading", "accounting_fraud"],
        filings=[...],
        parallel=True
    )
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum
import logging

from .circuit_breaker import CircuitBreaker, CircuitBreakerRegistry, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of forensic agents."""
    PATTERN_DETECTOR = "pattern_detector"
    FINANCIAL_ANALYZER = "financial_analyzer"
    NETWORK_ANALYZER = "network_analyzer"
    DOCUMENT_PARSER = "document_parser"
    COMPLIANCE_CHECKER = "compliance_checker"
    CROSS_VALIDATOR = "cross_validator"


class AgentPriority(Enum):
    """Agent execution priority levels."""
    CRITICAL = 1  # Must execute first
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class AgentConfig:
    """Configuration for a forensic agent."""
    name: str
    agent_type: AgentType
    priority: AgentPriority
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: float = 300.0
    retry_on_failure: bool = True
    max_retries: int = 3
    requires_circuit_breaker: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "timeout_seconds": self.timeout_seconds,
            "retry_on_failure": self.retry_on_failure,
            "max_retries": self.max_retries,
            "requires_circuit_breaker": self.requires_circuit_breaker
        }


@dataclass
class AgentResult:
    """Result from agent execution."""
    agent_name: str
    success: bool
    execution_time_seconds: float
    findings: Dict[str, Any]
    violations: List[Dict[str, Any]] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "success": self.success,
            "execution_time_seconds": self.execution_time_seconds,
            "findings": self.findings,
            "violations": self.violations,
            "alerts": self.alerts,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class InvestigationResult:
    """Complete investigation result from meta-orchestrator."""
    investigation_id: str
    started_at: datetime
    completed_at: datetime
    agents_executed: int
    agents_successful: int
    agents_failed: int
    total_violations: int
    total_alerts: int
    agent_results: List[AgentResult]
    aggregated_findings: Dict[str, Any]
    conflict_resolutions: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "investigation_id": self.investigation_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": (self.completed_at - self.started_at).total_seconds(),
            "agents_executed": self.agents_executed,
            "agents_successful": self.agents_successful,
            "agents_failed": self.agents_failed,
            "total_violations": self.total_violations,
            "total_alerts": self.total_alerts,
            "agent_results": [r.to_dict() for r in self.agent_results],
            "aggregated_findings": self.aggregated_findings,
            "conflict_resolutions": self.conflict_resolutions
        }


class ForensicMetaOrchestrator:
    """
    Meta-orchestrator for dynamic forensic agent spawning and coordination.

    .. deprecated::
        Use :class:`UnifiedForensicOrchestrator` from
        ``src.core.unified_orchestrator`` instead.  This class is retained
        for backward compatibility and will be removed in a future version.
    
    Provides:
    - Dynamic agent selection based on violation patterns
    - Parallel execution with dependency resolution
    - Circuit breaker protection for external services
    - Result aggregation with conflict resolution
    - Intelligent retry logic
    
    Example:
        orchestrator = ForensicMetaOrchestrator()
        
        # Register agents
        orchestrator.register_agent(
            name="options_backdating",
            agent_type=AgentType.PATTERN_DETECTOR,
            handler=analyze_options_backdating,
            priority=AgentPriority.HIGH
        )
        
        # Execute investigation
        result = await orchestrator.investigate(
            investigation_type="insider_trading",
            data={"filings": [...], "cik": "..."}
        )
    """
    
    def __init__(
        self,
        enable_circuit_breakers: bool = True,
        default_timeout: float = 300.0,
        auto_register_agents: bool = True
    ):
        """
        Initialize meta-orchestrator.
        
        Args:
            enable_circuit_breakers: Enable circuit breaker protection
            default_timeout: Default timeout for agent execution (seconds)
            auto_register_agents: Automatically register default agents
        """
        # DEPRECATION WARNING
        import warnings
        warnings.warn(
            "ForensicMetaOrchestrator is deprecated. "
            "Use UnifiedForensicOrchestrator from src.core.unified_orchestrator for DOJ-grade compliance. "
            "This class will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.enable_circuit_breakers = enable_circuit_breakers
        self.default_timeout = default_timeout
        
        # Agent registry
        self._agents: Dict[str, Tuple[AgentConfig, Callable]] = {}
        
        # Circuit breaker registry
        self._circuit_breakers = CircuitBreakerRegistry() if enable_circuit_breakers else None
        
        # Execution tracking
        self._execution_history: List[InvestigationResult] = []
        
        logger.info(f"ForensicMetaOrchestrator initialized (circuit_breakers={'enabled' if enable_circuit_breakers else 'disabled'})")
        
        # Auto-register default agents
        if auto_register_agents:
            try:
                from .agent_registry import register_default_agents
                agent_count = register_default_agents(self)
                logger.info(f"✓ Auto-registered {agent_count} default agents")
            except ImportError as e:
                logger.warning(f"Agent registry not available: {e}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agents: {e}")
    
    def register_agent(
        self,
        name: str,
        agent_type: AgentType,
        handler: Callable,
        priority: AgentPriority = AgentPriority.MEDIUM,
        dependencies: Optional[List[str]] = None,
        timeout_seconds: Optional[float] = None,
        requires_circuit_breaker: bool = True
    ):
        """
        Register a forensic agent.
        
        Args:
            name: Unique agent name
            agent_type: Type of agent
            handler: Async function to execute agent logic
            priority: Execution priority
            dependencies: List of agent names that must execute first
            timeout_seconds: Execution timeout (None = use default)
            requires_circuit_breaker: Whether to use circuit breaker
        """
        config = AgentConfig(
            name=name,
            agent_type=agent_type,
            priority=priority,
            dependencies=dependencies or [],
            timeout_seconds=timeout_seconds or self.default_timeout,
            requires_circuit_breaker=requires_circuit_breaker and self.enable_circuit_breakers
        )
        
        self._agents[name] = (config, handler)
        
        # Register circuit breaker if needed
        # Note: Circuit breaker registration is deferred to first use to avoid
        # requiring an event loop during initialization
        if config.requires_circuit_breaker and self._circuit_breakers:
            # Circuit breaker will be registered on-demand during first execution
            pass
        
        logger.info(f"Registered agent: {name} (type={agent_type.value}, priority={priority.value})")
    
    async def investigate(
        self,
        investigation_type: str,
        data: Dict[str, Any],
        agent_filter: Optional[List[str]] = None,
        parallel: bool = True,
        investigation_id: Optional[str] = None
    ) -> InvestigationResult:
        """
        Execute forensic investigation with dynamic agent spawning.
        
        Args:
            investigation_type: Type of investigation (e.g., "insider_trading")
            data: Investigation data (filings, CIK, etc.)
            agent_filter: Optional list of agent names to execute (None = all)
            parallel: Execute agents in parallel when possible
            investigation_id: Optional investigation ID (auto-generated if None)
            
        Returns:
            InvestigationResult with aggregated findings
        """
        started_at = datetime.utcnow()
        investigation_id = investigation_id or f"INV-{started_at.strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting investigation {investigation_id}: {investigation_type}")
        
        # Select agents based on investigation type
        selected_agents = self._select_agents(investigation_type, agent_filter)
        
        if not selected_agents:
            logger.warning(f"No agents selected for investigation type: {investigation_type}")
            return self._create_empty_result(investigation_id, started_at)
        
        # Build dependency graph and execution plan
        execution_plan = self._build_execution_plan(selected_agents)
        
        logger.info(f"Execution plan: {len(execution_plan)} stages, {sum(len(stage) for stage in execution_plan)} total agents")
        
        # Execute agents in stages
        agent_results: List[AgentResult] = []
        completed_agents: Set[str] = set()
        
        for stage_idx, stage_agents in enumerate(execution_plan):
            logger.info(f"Executing stage {stage_idx + 1}/{len(execution_plan)}: {len(stage_agents)} agents")
            
            if parallel and len(stage_agents) > 1:
                # Execute agents in parallel
                stage_results = await self._execute_agents_parallel(
                    stage_agents,
                    data,
                    completed_agents
                )
            else:
                # Execute agents sequentially
                stage_results = await self._execute_agents_sequential(
                    stage_agents,
                    data,
                    completed_agents
                )
            
            agent_results.extend(stage_results)
            completed_agents.update(r.agent_name for r in stage_results if r.success)
        
        # Aggregate results
        completed_at = datetime.utcnow()
        aggregated_findings, conflicts = self._aggregate_results(agent_results)
        
        result = InvestigationResult(
            investigation_id=investigation_id,
            started_at=started_at,
            completed_at=completed_at,
            agents_executed=len(agent_results),
            agents_successful=sum(1 for r in agent_results if r.success),
            agents_failed=sum(1 for r in agent_results if not r.success),
            total_violations=sum(len(r.violations) for r in agent_results),
            total_alerts=sum(len(r.alerts) for r in agent_results),
            agent_results=agent_results,
            aggregated_findings=aggregated_findings,
            conflict_resolutions=conflicts
        )
        
        self._execution_history.append(result)
        
        logger.info(
            f"Investigation {investigation_id} completed: "
            f"{result.agents_successful}/{result.agents_executed} agents successful, "
            f"{result.total_violations} violations, {result.total_alerts} alerts"
        )
        
        return result
    
    def _select_agents(
        self,
        investigation_type: str,
        agent_filter: Optional[List[str]]
    ) -> List[Tuple[AgentConfig, Callable]]:
        """Select agents based on investigation type."""
        # If filter provided, use only those agents
        if agent_filter:
            return [
                self._agents[name]
                for name in agent_filter
                if name in self._agents
            ]
        
        # Otherwise, select all registered agents
        # In production, would have sophisticated mapping of investigation types to agents
        return list(self._agents.values())
    
    def _build_execution_plan(
        self,
        agents: List[Tuple[AgentConfig, Callable]]
    ) -> List[List[Tuple[AgentConfig, Callable]]]:
        """
        Build execution plan respecting dependencies and priorities.
        
        Returns list of stages, where each stage contains agents that can
        execute in parallel.
        """
        # Sort by priority first
        sorted_agents = sorted(agents, key=lambda x: x[0].priority.value)
        
        # Build dependency graph
        dependency_graph: Dict[str, Set[str]] = {}
        agent_map: Dict[str, Tuple[AgentConfig, Callable]] = {}
        
        for config, handler in sorted_agents:
            dependency_graph[config.name] = set(config.dependencies)
            agent_map[config.name] = (config, handler)
        
        # Topological sort to create execution stages
        stages: List[List[Tuple[AgentConfig, Callable]]] = []
        completed: Set[str] = set()
        
        while len(completed) < len(agent_map):
            # Find agents whose dependencies are satisfied
            ready_agents = [
                agent_map[name]
                for name, deps in dependency_graph.items()
                if name not in completed and deps.issubset(completed)
            ]
            
            if not ready_agents:
                # Circular dependency or unsatisfiable dependencies
                logger.error("Circular dependency detected in agent execution plan")
                break
            
            stages.append(ready_agents)
            completed.update(config.name for config, _ in ready_agents)
        
        return stages
    
    async def _execute_agents_parallel(
        self,
        agents: List[Tuple[AgentConfig, Callable]],
        data: Dict[str, Any],
        completed_agents: Set[str]
    ) -> List[AgentResult]:
        """Execute agents in parallel."""
        tasks = [
            self._execute_agent(config, handler, data, completed_agents)
            for config, handler in agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        agent_results = []
        for (config, _), result in zip(agents, results):
            if isinstance(result, Exception):
                agent_results.append(AgentResult(
                    agent_name=config.name,
                    success=False,
                    execution_time_seconds=0.0,
                    findings={},
                    error_message=str(result)
                ))
            else:
                agent_results.append(result)
        
        return agent_results
    
    async def _execute_agents_sequential(
        self,
        agents: List[Tuple[AgentConfig, Callable]],
        data: Dict[str, Any],
        completed_agents: Set[str]
    ) -> List[AgentResult]:
        """Execute agents sequentially."""
        results = []
        for config, handler in agents:
            result = await self._execute_agent(config, handler, data, completed_agents)
            results.append(result)
        
        return results
    
    async def _execute_agent(
        self,
        config: AgentConfig,
        handler: Callable,
        data: Dict[str, Any],
        completed_agents: Set[str]
    ) -> AgentResult:
        """Execute a single agent with circuit breaker and retry logic."""
        start_time = datetime.utcnow()
        retry_count = 0
        
        for attempt in range(config.max_retries + 1):
            try:
                # Get circuit breaker if needed
                breaker = None
                if config.requires_circuit_breaker and self._circuit_breakers:
                    breaker = self._circuit_breakers.get(f"agent_{config.name}")
                    # Register circuit breaker on-demand if not already registered
                    if breaker is None:
                        await self._circuit_breakers.register(
                            name=f"agent_{config.name}",
                            failure_threshold=3,
                            recovery_timeout=60.0
                        )
                        breaker = self._circuit_breakers.get(f"agent_{config.name}")
                
                # Execute with timeout
                if breaker:
                    result = await asyncio.wait_for(
                        breaker.call(handler, data, completed_agents),
                        timeout=config.timeout_seconds
                    )
                else:
                    result = await asyncio.wait_for(
                        handler(data, completed_agents),
                        timeout=config.timeout_seconds
                    )
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                return AgentResult(
                    agent_name=config.name,
                    success=True,
                    execution_time_seconds=execution_time,
                    findings=result.get('findings', {}),
                    violations=result.get('violations', []),
                    alerts=result.get('alerts', []),
                    retry_count=retry_count
                )
            
            except (CircuitBreakerOpenError, asyncio.TimeoutError, Exception) as e:
                retry_count += 1
                error_msg = f"{e.__class__.__name__}: {e}"
                
                if attempt < config.max_retries and config.retry_on_failure:
                    logger.warning(
                        f"Agent {config.name} failed (attempt {attempt + 1}/{config.max_retries + 1}): {error_msg}"
                    )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
                # Final failure
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.error(f"Agent {config.name} failed after {retry_count} retries: {error_msg}")
                
                return AgentResult(
                    agent_name=config.name,
                    success=False,
                    execution_time_seconds=execution_time,
                    findings={},
                    error_message=error_msg,
                    retry_count=retry_count
                )
        
        # Should never reach here
        return AgentResult(
            agent_name=config.name,
            success=False,
            execution_time_seconds=0.0,
            findings={},
            error_message="Unknown error"
        )
    
    def _aggregate_results(
        self,
        agent_results: List[AgentResult]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Aggregate results from multiple agents with conflict resolution.
        
        Returns:
            (aggregated_findings, conflict_resolutions)
        """
        aggregated = {
            "total_findings": 0,
            "by_agent": {},
            "merged_violations": [],
            "merged_alerts": []
        }
        
        conflicts = []
        violation_hashes: Set[str] = set()
        
        for result in agent_results:
            if not result.success:
                continue
            
            aggregated["by_agent"][result.agent_name] = result.findings
            aggregated["total_findings"] += 1
            
            # Deduplicate violations by content hash
            for violation in result.violations:
                v_hash = self._hash_violation(violation)
                if v_hash not in violation_hashes:
                    violation_hashes.add(v_hash)
                    aggregated["merged_violations"].append(violation)
                else:
                    # Conflict detected - same violation from multiple agents
                    conflicts.append({
                        "type": "duplicate_violation",
                        "violation": violation,
                        "source_agent": result.agent_name
                    })
            
            # Merge alerts
            aggregated["merged_alerts"].extend(result.alerts)
        
        return aggregated, conflicts
    
    def _hash_violation(self, violation: Dict[str, Any]) -> str:
        """Generate hash for violation deduplication."""
        import hashlib
        import json
        
        # Use stable fields for hashing
        hash_fields = {
            "type": violation.get("type", ""),
            "description": violation.get("description", ""),
            "entity": violation.get("entity", "")
        }
        
        content = json.dumps(hash_fields, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _create_empty_result(
        self,
        investigation_id: str,
        started_at: datetime
    ) -> InvestigationResult:
        """Create empty result for failed investigation."""
        return InvestigationResult(
            investigation_id=investigation_id,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            agents_executed=0,
            agents_successful=0,
            agents_failed=0,
            total_violations=0,
            total_alerts=0,
            agent_results=[],
            aggregated_findings={}
        )
    
    def get_execution_history(self) -> List[InvestigationResult]:
        """Get history of all investigations."""
        return self._execution_history.copy()
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered agents and executions."""
        return {
            "total_agents_registered": len(self._agents),
            "agents_by_type": {
                agent_type.value: sum(
                    1 for config, _ in self._agents.values()
                    if config.agent_type == agent_type
                )
                for agent_type in AgentType
            },
            "total_investigations": len(self._execution_history),
            "circuit_breakers_enabled": self.enable_circuit_breakers,
            "circuit_breaker_metrics": (
                self._circuit_breakers.get_all_metrics()
                if self._circuit_breakers else {}
            )
        }


__all__ = [
    'ForensicMetaOrchestrator',
    'AgentType',
    'AgentPriority',
    'AgentConfig',
    'AgentResult',
    'InvestigationResult'
]
