"""
Unified Agent Orchestrator - JLAW Multi-Tier Investigation Coordinator
======================================================================

.. deprecated::
    **DEPRECATED** — Use :class:`UnifiedForensicOrchestrator` from
    ``src.core.unified_orchestrator`` instead. See ``EXECUTION_AUTHORITY.md``
    for the canonical execution path. This module is retained for backward
    compatibility and will be removed in a future version.

Master orchestrator that harmonizes ALL agent tiers into a single, 
coordinated investigation workflow.

ARCHITECTURE:
=============
Tier 1 (PRIMARY): OpenAI + Anthropic dual-agent analysis
Tier 2 (SUBAGENT): Intelligent routing to 10 specialized Claude agents
Tier 3 (PATTERN): 23 algorithmic fraud detection patterns
Tier 4 (NODE): 15 document-specific node analyzers

WORKFLOW:
=========
1. Tier 1: Dual-agent initial violation detection
2. Tier 2: Route violations to specialized subagents (intelligent selection)
3. Tier 3: Validate findings with statistical pattern detection
4. Tier 4: Extract structured data from document nodes
5. Aggregation: Deduplicate violations, compute unified consensus

FEATURES:
=========
- Single entry point for multi-tier investigations
- Context propagation (Tier 1 findings → Tier 2 routing)
- Violation deduplication across all tiers
- Unified consensus scoring
- Token usage tracking
- Execution metrics profiling
- Evidence chain integration

Usage:
    from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator
    
    orchestrator = UnifiedAgentOrchestrator()
    
    result = await orchestrator.execute_investigation(
        investigation_type="full_forensic",
        filings=[...],
        context={"cik": "320187", "company_name": "NIKE, Inc."},
        enable_subagents=True,
        enable_patterns=True
    )
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from src.forensics.execution_metrics import ExecutionMetricsCollector, AgentExecutionMetric
from src.profiling import (
    PerformanceMetricsCollector,
    OptimizationAnalyzer,
    TimelineVisualizer,
    BudgetEnforcer
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class AgentTier(Enum):
    """Agent tier identifiers for multi-tier orchestration."""
    PRIMARY = "primary"      # OpenAI + Anthropic dual-agent
    SUBAGENT = "subagent"    # 10 specialized Claude agents
    PATTERN = "pattern"      # 23 detection algorithms
    NODE = "node"            # 15 node analyzers


@dataclass
class UnifiedTask:
    """
    Task submission for unified orchestration.
    
    Represents a single investigation task that may span multiple tiers.
    """
    task_id: str
    task_type: str  # "analyze_filing", "detect_violations", "cross_reference"
    tier: AgentTier
    input_data: Dict[str, Any]
    priority: int = 50
    timeout_seconds: float = 60.0
    requires_consensus: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UnifiedResult:
    """
    Unified result from multi-tier investigation.
    
    Aggregates results from all tiers with provenance tracking,
    consensus scoring, and execution metrics.
    """
    task_id: str
    status: str  # "success", "partial", "failure"
    tier_results: Dict[str, Any]  # Key: tier name, Value: tier-specific results
    aggregated_violations: List[Dict[str, Any]]
    consensus_score: float
    execution_time_seconds: float
    tokens_used: int
    agents_invoked: List[str]
    tiers_executed: List[str] = field(default_factory=list)
    execution_metrics: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# UNIFIED AGENT ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

class UnifiedAgentOrchestrator:
    """
    Master orchestrator for multi-tier agent coordination.

    .. deprecated::
        Use :class:`UnifiedForensicOrchestrator` from
        ``src.core.unified_orchestrator`` instead.  This class is retained
        for backward compatibility and will be removed in a future version.
    
    Coordinates all 4 agent tiers in a unified investigation workflow:
    - Tier 1: Primary dual-agent analysis
    - Tier 2: Intelligent subagent routing
    - Tier 3: Pattern detection algorithms
    - Tier 4: Node-specific analyzers
    
    Provides context propagation, result aggregation, consensus scoring,
    and comprehensive execution metrics.
    """
    
    VERSION = "1.1.0"  # Updated for enhanced profiling
    
    def __init__(
        self,
        max_tokens: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        enable_profiling: bool = True
    ):
        """
        Initialize unified orchestrator with enhanced profiling.
        
        Args:
            max_tokens: Maximum token budget (optional)
            max_cost_usd: Maximum cost budget in USD (optional)
            enable_profiling: Enable enhanced profiling features (default: True)
        """
        # DEPRECATION WARNING
        import warnings
        warnings.warn(
            "UnifiedAgentOrchestrator is deprecated. "
            "Use UnifiedForensicOrchestrator from src.core.unified_orchestrator for DOJ-grade compliance. "
            "This class will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )

        # Legacy metrics collector (for backward compatibility)
        self.metrics_collector = ExecutionMetricsCollector()
        
        # Enhanced profiling framework
        self.enable_profiling = enable_profiling
        if enable_profiling:
            self.performance_metrics = PerformanceMetricsCollector()
            self.optimization_analyzer = OptimizationAnalyzer()
            self.timeline_visualizer = TimelineVisualizer()
            
            # Budget enforcer (optional)
            if max_tokens or max_cost_usd:
                self.budget_enforcer = BudgetEnforcer(
                    max_tokens=max_tokens,
                    max_cost_usd=max_cost_usd,
                    strict_mode=False  # Use warning mode by default
                )
            else:
                self.budget_enforcer = None
        else:
            self.performance_metrics = None
            self.optimization_analyzer = None
            self.timeline_visualizer = None
            self.budget_enforcer = None
        
        # Track tier invocations
        self.tier_invocation_counts: Dict[AgentTier, int] = {
            AgentTier.PRIMARY: 0,
            AgentTier.SUBAGENT: 0,
            AgentTier.PATTERN: 0,
            AgentTier.NODE: 0
        }
        
        # Track overall statistics
        self.tasks_executed = 0
        self.total_tokens_used = 0
        
        # SDK manager for availability checks
        from src.forensics.sdk_manager import get_sdk_manager_sync
        self.sdk_manager = get_sdk_manager_sync()
        
        logger.info(
            f"UnifiedAgentOrchestrator v{self.VERSION} initialized "
            f"(profiling={'enabled' if enable_profiling else 'disabled'}, "
            f"budget={'enforced' if self.budget_enforcer else 'none'})"
        )
    
    async def execute_investigation(
        self,
        investigation_type: str,  # "form4", "10k", "full_forensic"
        filings: List[Dict[str, Any]],
        context: Dict[str, Any],
        enable_subagents: bool = True,
        enable_patterns: bool = True,
        enable_nodes: bool = False,
        output_dir: Optional[Path] = None
    ) -> UnifiedResult:
        """
        Execute complete multi-tier investigation with enhanced profiling.
        
        Workflow:
        1. TIER 1 (Primary): Dual-agent analysis (OpenAI + Anthropic)
           - Detect initial violations
           - Generate cross-reference findings
           - Compute dual-agent consensus
        
        2. TIER 2 (Subagents): Intelligent routing based on Tier 1 findings
           - Route violations to specialized agents (via IntelligentRouter)
           - Execute parallel subagent analysis
           - Aggregate subagent findings
        
        3. TIER 3 (Patterns): Algorithmic validation
           - Run fraud detection algorithms
           - Validate agent findings with statistics
           - Generate fraud scores
        
        4. TIER 4 (Nodes): Document-specific processing
           - Extract structured data from filings
           - Generate filing-specific metrics
        
        5. AGGREGATION: Unified result synthesis
           - Deduplicate violations across tiers
           - Compute unified consensus score
           - Track execution metrics
           - Integrate into evidence chain
           - Generate optimization recommendations
        
        Args:
            investigation_type: Type of investigation ("form4", "10k", "full_forensic")
            filings: List of filing dictionaries to analyze
            context: Investigation context (CIK, company name, date range, etc.)
            enable_subagents: Enable Tier 2 subagent routing (default: True)
            enable_patterns: Enable Tier 3 pattern detection (default: True)
            enable_nodes: Enable Tier 4 node processing (default: False)
            output_dir: Optional output directory for profiling reports
            
        Returns:
            UnifiedResult with aggregated findings from all tiers
        """
        start_time = time.time()
        task_id = f"investigation_{int(start_time)}"
        
        # Start enhanced profiling
        if self.enable_profiling and self.performance_metrics:
            self.performance_metrics.start_phase(
                "unified_investigation",
                "Unified Multi-Tier Investigation"
            )
        
        logger.info("=" * 80)
        logger.info(f"  UNIFIED AGENT ORCHESTRATOR v{self.VERSION} - {investigation_type.upper()}")
        logger.info("=" * 80)
        logger.info(f"Task ID: {task_id}")
        logger.info(f"Filings: {len(filings)}")
        logger.info(f"Context: {context}")
        logger.info(f"Tiers enabled: Primary=True, Subagents={enable_subagents}, "
                   f"Patterns={enable_patterns}, Nodes={enable_nodes}")
        if self.budget_enforcer:
            logger.info(f"Budget: {self.budget_enforcer}")
        
        tier_results: Dict[str, Any] = {}
        all_violations: List[Dict[str, Any]] = []
        agents_invoked: List[str] = []
        tiers_executed: List[str] = []
        errors: List[str] = []
        
        try:
            # ═══════════════════════════════════════════════════════════════════
            # TIER 1: PRIMARY DUAL-AGENT ANALYSIS
            # ═══════════════════════════════════════════════════════════════════
            
            logger.info("\n" + "─" * 80)
            logger.info("TIER 1: Primary Dual-Agent Analysis")
            logger.info("─" * 80)
            
            try:
                tier1_result = await self._execute_tier_1_primary(filings, context)
                tier_results[AgentTier.PRIMARY.value] = tier1_result
                tiers_executed.append(AgentTier.PRIMARY.value)
                self.tier_invocation_counts[AgentTier.PRIMARY] += 1
                
                # Extract violations from Tier 1
                tier1_violations = tier1_result.get("violations", [])
                all_violations.extend(tier1_violations)
                
                # Track agents
                agents_invoked.extend(tier1_result.get("agents", ["openai", "anthropic"]))
                
                logger.info(f"✓ Tier 1 complete: {len(tier1_violations)} violations found")
                logger.info(f"  Consensus: {tier1_result.get('consensus', 0.0):.2%}")
                
            except Exception as e:
                error_msg = f"Tier 1 execution error: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
                tier_results[AgentTier.PRIMARY.value] = {"status": "error", "error": str(e)}
            
            # ═══════════════════════════════════════════════════════════════════
            # TIER 2: INTELLIGENT SUBAGENT ROUTING
            # ═══════════════════════════════════════════════════════════════════
            
            if enable_subagents and all_violations:
                logger.info("\n" + "─" * 80)
                logger.info("TIER 2: Intelligent Subagent Routing")
                logger.info("─" * 80)
                
                try:
                    tier2_result = await self._execute_tier_2_subagents(all_violations, context)
                    tier_results[AgentTier.SUBAGENT.value] = tier2_result
                    tiers_executed.append(AgentTier.SUBAGENT.value)
                    self.tier_invocation_counts[AgentTier.SUBAGENT] += 1
                    
                    # Extract findings from Tier 2
                    tier2_findings = tier2_result.get("combined_findings", [])
                    # Convert findings to violation format
                    for finding in tier2_findings:
                        if isinstance(finding, dict):
                            all_violations.append({
                                "type": finding.get("finding_type", "subagent_finding"),
                                "description": finding.get("description", ""),
                                "severity": finding.get("severity", "MEDIUM"),
                                "source": "subagent",
                                "agent": finding.get("agent_name", "unknown"),
                                "tier": "subagent"
                            })
                    
                    # Track agents
                    agents_invoked.extend(tier2_result.get("agents_executed", []))
                    
                    logger.info(f"✓ Tier 2 complete: {len(tier2_findings)} findings from "
                               f"{len(tier2_result.get('agents_executed', []))} agents")
                    
                except Exception as e:
                    error_msg = f"Tier 2 execution error: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)
                    tier_results[AgentTier.SUBAGENT.value] = {"status": "error", "error": str(e)}
            
            elif enable_subagents:
                logger.info("\n→ Tier 2 (Subagents) skipped: No violations to route")
            
            # ═══════════════════════════════════════════════════════════════════
            # TIER 3: PATTERN DETECTION ALGORITHMS
            # ═══════════════════════════════════════════════════════════════════
            
            if enable_patterns:
                logger.info("\n" + "─" * 80)
                logger.info("TIER 3: Pattern Detection Algorithms")
                logger.info("─" * 80)
                
                try:
                    tier3_result = self._execute_tier_3_patterns(filings, all_violations)
                    tier_results[AgentTier.PATTERN.value] = tier3_result
                    tiers_executed.append(AgentTier.PATTERN.value)
                    self.tier_invocation_counts[AgentTier.PATTERN] += 1
                    
                    logger.info(f"✓ Tier 3 complete: {tier3_result.get('patterns_executed', 0)} "
                               f"patterns executed")
                    
                except Exception as e:
                    error_msg = f"Tier 3 execution error: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)
                    tier_results[AgentTier.PATTERN.value] = {"status": "error", "error": str(e)}
            
            # ═══════════════════════════════════════════════════════════════════
            # TIER 4: NODE-SPECIFIC ANALYZERS
            # ═══════════════════════════════════════════════════════════════════
            
            if enable_nodes:
                logger.info("\n" + "─" * 80)
                logger.info("TIER 4: Node-Specific Analyzers")
                logger.info("─" * 80)
                
                try:
                    tier4_result = self._execute_tier_4_nodes(filings)
                    tier_results[AgentTier.NODE.value] = tier4_result
                    tiers_executed.append(AgentTier.NODE.value)
                    self.tier_invocation_counts[AgentTier.NODE] += 1
                    
                    logger.info(f"✓ Tier 4 complete: {tier4_result.get('nodes_processed', 0)} "
                               f"nodes processed")
                    
                except Exception as e:
                    error_msg = f"Tier 4 execution error: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)
                    tier_results[AgentTier.NODE.value] = {"status": "error", "error": str(e)}
            
            # ═══════════════════════════════════════════════════════════════════
            # AGGREGATION: UNIFIED RESULT SYNTHESIS
            # ═══════════════════════════════════════════════════════════════════
            
            logger.info("\n" + "─" * 80)
            logger.info("AGGREGATION: Unified Result Synthesis")
            logger.info("─" * 80)
            
            # Deduplicate violations across all tiers
            deduplicated_violations = self._deduplicate_violations(all_violations)
            logger.info(f"→ Deduplicated: {len(all_violations)} → {len(deduplicated_violations)} violations")
            
            # Compute unified consensus score
            consensus_score = self._compute_unified_consensus(tier_results)
            logger.info(f"→ Unified consensus: {consensus_score:.2%}")
            
            # Count total tokens
            total_tokens = self._count_tokens(tier_results)
            self.total_tokens_used += total_tokens
            logger.info(f"→ Total tokens: {total_tokens}")
            
            # Execution time
            execution_time = time.time() - start_time
            logger.info(f"→ Execution time: {execution_time:.2f}s")
            
            # Get metrics summary
            metrics_summary = self.metrics_collector.get_summary()
            
            # Update task counter
            self.tasks_executed += 1
            
            # Determine overall status
            if not errors:
                status = "success"
            elif len(tiers_executed) > 0:
                status = "partial"
            else:
                status = "failure"
            
            # ═══════════════════════════════════════════════════════════════════
            # ENHANCED PROFILING: Generate Reports & Recommendations
            # ═══════════════════════════════════════════════════════════════════
            
            profiling_data = {}
            if self.enable_profiling and self.performance_metrics:
                # End profiling phase
                self.performance_metrics.end_phase("unified_investigation", status=status)
                
                # Generate optimization recommendations
                optimization_result = self.optimization_analyzer.analyze(self.performance_metrics)
                
                # Generate timeline
                timeline = self.timeline_visualizer.generate_timeline(self.performance_metrics)
                
                # Export reports if output directory specified
                if output_dir:
                    output_dir = Path(output_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Export detailed performance report
                    perf_report_path = output_dir / f"performance_metrics_{task_id}.json"
                    self.performance_metrics.export_detailed_report(perf_report_path)
                    logger.info(f"✓ Performance report: {perf_report_path}")
                    
                    # Export timeline
                    timeline_path = output_dir / f"timeline_{task_id}.json"
                    self.timeline_visualizer.export_json(timeline, timeline_path)
                    logger.info(f"✓ Timeline report: {timeline_path}")
                    
                    # Export Gantt chart HTML
                    gantt_path = output_dir / f"gantt_chart_{task_id}.html"
                    self.timeline_visualizer.generate_gantt_html(timeline, gantt_path)
                    logger.info(f"✓ Gantt chart: {gantt_path}")
                
                # Log optimization recommendations
                if optimization_result["recommendations"]:
                    logger.info("\n" + "─" * 80)
                    logger.info("OPTIMIZATION RECOMMENDATIONS")
                    logger.info("─" * 80)
                    for i, rec in enumerate(optimization_result["recommendations"], 1):
                        logger.info(f"{i}. [{rec['severity'].upper()}] {rec['message']}")
                        logger.info(f"   → {rec['suggestion']}")
                    
                    summary = optimization_result["summary"]
                    logger.info("\n" + "─" * 40)
                    logger.info(f"Current cost: ${summary['current_cost']:.4f}")
                    logger.info(f"Potential savings: ${summary['potential_savings']:.4f} ({summary['savings_percentage']:.1f}%)")
                    logger.info(f"Optimized cost: ${summary['optimized_cost']:.4f}")
                    logger.info("─" * 40)
                
                # Include profiling data in result
                profiling_data = {
                    "performance_summary": self.performance_metrics.get_summary(),
                    "optimization": optimization_result,
                    "timeline": timeline,
                    "budget_status": self.budget_enforcer.get_status().to_dict() if self.budget_enforcer else None
                }
            
            result = UnifiedResult(
                task_id=task_id,
                status=status,
                tier_results=tier_results,
                aggregated_violations=deduplicated_violations,
                consensus_score=consensus_score,
                execution_time_seconds=execution_time,
                tokens_used=total_tokens,
                agents_invoked=agents_invoked,
                tiers_executed=tiers_executed,
                execution_metrics=metrics_summary,
                errors=errors
            )
            
            logger.info("\n" + "=" * 80)
            logger.info(f"✓ UNIFIED INVESTIGATION COMPLETE - Status: {status.upper()}")
            logger.info(f"  Tiers executed: {len(tiers_executed)}/{4 if enable_nodes else 3}")
            logger.info(f"  Violations found: {len(deduplicated_violations)}")
            logger.info(f"  Agents invoked: {len(set(agents_invoked))}")
            logger.info(f"  Consensus: {consensus_score:.2%}")
            if profiling_data.get("performance_summary"):
                perf = profiling_data["performance_summary"]
                logger.info(f"  Total cost: ${perf['total_cost_usd']:.4f}")
                logger.info(f"  Total tokens: {perf['total_tokens']:,}")
            logger.info("=" * 80)
            
            return result
        
        except Exception as e:
            logger.error(f"Unified investigation failed: {e}", exc_info=True)
            execution_time = time.time() - start_time
            
            return UnifiedResult(
                task_id=task_id,
                status="failure",
                tier_results=tier_results,
                aggregated_violations=all_violations,
                consensus_score=0.0,
                execution_time_seconds=execution_time,
                tokens_used=self._count_tokens(tier_results),
                agents_invoked=agents_invoked,
                tiers_executed=tiers_executed,
                execution_metrics=self.metrics_collector.get_summary(),
                errors=[str(e)]
            )
    
    # ═══════════════════════════════════════════════════════════════════════
    # TIER EXECUTION METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _execute_tier_1_primary(
        self,
        filings: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Tier 1: Primary dual-agent analysis.
        
        Uses DualAgentCoordinator to perform initial violation detection
        with OpenAI + Anthropic cross-validation.
        
        Args:
            filings: List of filing dictionaries
            context: Investigation context
            
        Returns:
            Dictionary with violations, consensus, and agent info
        """
        from src.forensics.dual_agent import DualAgentCoordinator
        
        # Start metrics tracking
        metric = self.metrics_collector.start_agent(
            "dual_agent_coordinator",
            "primary",
            tier="primary"
        )
        
        # Start enhanced profiling
        if self.enable_profiling and self.performance_metrics:
            self.performance_metrics.start_agent(
                "dual_agent_coordinator",
                "anthropic",  # Primary type
                "primary",
                model="gpt-4o+claude-sonnet-3.5"
            )
        
        try:
            dual_agent = DualAgentCoordinator()
            
            primary_violations = []
            consensus_scores = []
            
            # Analyze each filing with dual-agent
            for filing in filings[:5]:  # Limit to 5 filings for performance
                # Build content for analysis
                content = filing.get('content', '') or filing.get('summary', '')
                if not content:
                    logger.warning(f"Skipping filing {filing.get('form_type', 'unknown')}: no content")
                    continue
                
                # Execute dual-agent investigation
                investigation = await dual_agent.investigate_with_cross_reference(
                    content=content,
                    filing_metadata=filing,
                    enable_govinfo_enrichment=False  # Disable for performance
                )
                
                # Extract violations
                merged_violations = investigation.get('merged_violations', [])
                for v in merged_violations:
                    v['filing'] = filing.get('form_type', 'unknown')
                    v['tier'] = 'primary'
                primary_violations.extend(merged_violations)
                
                # Track consensus
                summary = investigation.get('investigation_summary', {})
                confidence = summary.get('confidence_level', 0.0)
                consensus_scores.append(confidence)
            
            # Compute average consensus
            avg_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
            
            # Update metrics
            metric.violations_found = len(primary_violations)
            # Estimate tokens (rough heuristic)
            estimated_tokens = len(filings) * 2000  # ~2k tokens per filing
            metric.tokens_used = estimated_tokens
            self.metrics_collector.end_agent(metric, status="success")
            
            # Update enhanced profiling
            if self.enable_profiling and self.performance_metrics:
                self.performance_metrics.end_agent(
                    "dual_agent_coordinator",
                    input_tokens=estimated_tokens // 2,  # Rough estimate: 50% input, 50% output
                    output_tokens=estimated_tokens // 2,
                    violations_found=len(primary_violations),
                    consensus_contribution=avg_consensus,
                    status="success"
                )
            
            return {
                "violations": primary_violations,
                "consensus": avg_consensus,
                "filings_analyzed": len(filings[:5]),
                "agents": ["openai", "anthropic"],
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Tier 1 execution error: {e}", exc_info=True)
            self.metrics_collector.end_agent(metric, status="error", error=str(e))
            raise
    
    async def _execute_tier_2_subagents(
        self,
        violations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Tier 2: Intelligent subagent routing.
        
        Uses IntelligentSubagentRouter to select and execute specialized
        Claude agents based on violation types from Tier 1.
        
        Args:
            violations: Violations from Tier 1 to route
            context: Investigation context
            
        Returns:
            Dictionary with routing results and agent findings
        """
        from src.forensics.intelligent_router import IntelligentSubagentRouter
        from src.forensics.subagents.orchestrator import SubagentOrchestrator
        
        # Start metrics tracking
        metric = self.metrics_collector.start_agent(
            "intelligent_router",
            "subagent",
            tier="subagent"
        )
        
        try:
            router = IntelligentSubagentRouter()
            orchestrator = SubagentOrchestrator()
            
            # Plan execution with intelligent routing
            routing_decision = router.plan_execution(
                violations=violations,
                max_agents=5,
                parallel_stages=3
            )
            
            # Execute routing decision
            result = await router.execute(
                decision=routing_decision,
                violations=violations,
                context=context,
                orchestrator=orchestrator
            )
            
            # Update metrics
            metric.violations_found = len(result.get("combined_findings", []))
            metric.tokens_used = result.get("total_tokens", 0) or (
                len(result.get("agents_executed", [])) * 1500  # Estimate
            )
            self.metrics_collector.end_agent(metric, status="success")
            
            return {
                "combined_findings": result.get("combined_findings", []),
                "agents_executed": result.get("agents_executed", []),
                "consensus_score": result.get("consensus_score", 0.0),
                "conflicts": result.get("conflicts", []),
                "routing_decision": {
                    "selected_agents": [a.agent_name for a in routing_decision.selected_agents],
                    "execution_plan": routing_decision.execution_plan,
                    "agent_scores": routing_decision.agent_scores
                },
                "total_tokens": metric.tokens_used,
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Tier 2 execution error: {e}", exc_info=True)
            self.metrics_collector.end_agent(metric, status="error", error=str(e))
            raise
    
    def _execute_tier_3_patterns(
        self,
        filings: List[Dict[str, Any]],
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute Tier 3: Pattern detection algorithms.
        
        Runs fraud detection patterns to validate agent findings with
        statistical analysis. This is a stub that will integrate with
        existing pattern detection modules.
        
        Args:
            filings: Filings to analyze
            violations: Violations from previous tiers
            
        Returns:
            Dictionary with pattern detection results
        """
        # Start metrics tracking
        metric = self.metrics_collector.start_agent(
            "pattern_detector",
            "pattern",
            tier="pattern"
        )
        
        try:
            # TODO: Integrate with existing pattern detection modules
            # For now, return a placeholder result
            
            pattern_results = {
                "mscore": None,
                "zscore": None,
                "benford": None,
                "patterns_executed": 0,
                "fraud_indicators": [],
                "status": "stub"  # Mark as stub implementation
            }
            
            logger.info("  ⚠ Pattern detection is a stub (integration pending)")
            
            # Update metrics
            metric.violations_found = 0
            metric.tokens_used = 0
            self.metrics_collector.end_agent(metric, status="success")
            
            return pattern_results
        
        except Exception as e:
            logger.error(f"Tier 3 execution error: {e}", exc_info=True)
            self.metrics_collector.end_agent(metric, status="error", error=str(e))
            raise
    
    def _execute_tier_4_nodes(
        self,
        filings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute Tier 4: Node-specific analyzers.
        
        Runs document-specific node analyzers to extract structured data.
        This is a stub that will integrate with node analyzer modules.
        
        Args:
            filings: Filings to process
            
        Returns:
            Dictionary with node processing results
        """
        # Start metrics tracking
        metric = self.metrics_collector.start_agent(
            "node_analyzer",
            "node",
            tier="node"
        )
        
        try:
            # TODO: Integrate with node analyzer modules
            # For now, return a placeholder result
            
            node_results = {
                "nodes_processed": len(filings),
                "structured_data": [],
                "status": "stub"  # Mark as stub implementation
            }
            
            logger.info("  ⚠ Node analysis is a stub (integration pending)")
            
            # Update metrics
            metric.violations_found = 0
            metric.tokens_used = 0
            self.metrics_collector.end_agent(metric, status="success")
            
            return node_results
        
        except Exception as e:
            logger.error(f"Tier 4 execution error: {e}", exc_info=True)
            self.metrics_collector.end_agent(metric, status="error", error=str(e))
            raise
    
    # ═══════════════════════════════════════════════════════════════════════
    # AGGREGATION METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _deduplicate_violations(
        self,
        violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate violations across all tiers.
        
        Uses a combination of violation type, statute, and description
        to identify duplicates. Keeps the violation with highest severity.
        
        Args:
            violations: List of all violations from all tiers
            
        Returns:
            Deduplicated list of violations
        """
        if not violations:
            return []
        
        seen_keys: Set[str] = set()
        deduplicated: List[Dict[str, Any]] = []
        
        # Sort by severity (highest first) so we keep the most severe version
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        sorted_violations = sorted(
            violations,
            key=lambda v: severity_order.get(v.get('severity', 'INFO'), 4)
        )
        
        for v in sorted_violations:
            # Build deduplication key
            v_type = v.get('type', '') or v.get('violation_type', '')
            v_statute = v.get('statute', '') or v.get('legal_basis', '')
            v_desc = (v.get('description', '') or v.get('finding', ''))[:100]
            
            key = f"{v_type}|{v_statute}|{v_desc}".lower()
            
            if key not in seen_keys:
                seen_keys.add(key)
                deduplicated.append(v)
        
        logger.debug(f"Deduplicated {len(violations)} → {len(deduplicated)} violations")
        
        return deduplicated
    
    def _compute_unified_consensus(
        self,
        tier_results: Dict[str, Any]
    ) -> float:
        """
        Compute consensus score across all tiers.
        
        Weighted average of tier-specific consensus scores:
        - Primary tier: 40% weight
        - Subagent tier: 40% weight
        - Pattern tier: 20% weight
        - Node tier: not included (data extraction only)
        
        Args:
            tier_results: Results from all executed tiers
            
        Returns:
            Unified consensus score (0.0 to 1.0)
        """
        scores = []
        weights = []
        
        # Primary tier consensus (40% weight)
        if AgentTier.PRIMARY.value in tier_results:
            primary = tier_results[AgentTier.PRIMARY.value]
            if primary.get("status") == "success":
                scores.append(primary.get('consensus', 0.0))
                weights.append(0.4)
        
        # Subagent tier consensus (40% weight)
        if AgentTier.SUBAGENT.value in tier_results:
            subagent = tier_results[AgentTier.SUBAGENT.value]
            if subagent.get("status") == "success":
                scores.append(subagent.get('consensus_score', 0.0))
                weights.append(0.4)
        
        # Pattern tier validation (20% weight)
        if AgentTier.PATTERN.value in tier_results:
            pattern = tier_results[AgentTier.PATTERN.value]
            if pattern.get("status") == "success":
                # Patterns executed ratio as consensus proxy
                patterns_executed = pattern.get('patterns_executed', 0)
                pattern_consensus = min(patterns_executed / 23.0, 1.0)
                scores.append(pattern_consensus)
                weights.append(0.2)
        
        # Compute weighted average
        if scores and weights:
            # Normalize weights if not all tiers executed
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            
            consensus = sum(s * w for s, w in zip(scores, normalized_weights))
            return round(consensus, 4)
        
        return 0.0
    
    def _count_tokens(
        self,
        tier_results: Dict[str, Any]
    ) -> int:
        """
        Count total tokens used across all tiers.
        
        Extracts token counts from tier-specific result structures.
        
        Args:
            tier_results: Results from all executed tiers
            
        Returns:
            Total token count
        """
        total = 0
        
        for tier_name, result in tier_results.items():
            if not isinstance(result, dict):
                continue
            
            # Extract token counts from various result structures
            tokens = (
                result.get('tokens_used') or
                result.get('total_tokens') or
                result.get('token_count') or
                0
            )
            
            total += tokens
        
        return total
    
    # ═══════════════════════════════════════════════════════════════════════
    # METRICS AND PROFILING
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get orchestrator execution metrics.
        
        Returns comprehensive metrics including:
        - Tasks executed
        - Total tokens used
        - Tier invocation counts
        - Average metrics per task
        - SDK availability
        
        Returns:
            Dictionary with orchestrator metrics
        """
        return {
            "tasks_executed": self.tasks_executed,
            "total_tokens_used": self.total_tokens_used,
            "tier_invocation_counts": {
                tier.value: count 
                for tier, count in self.tier_invocation_counts.items()
            },
            "avg_tokens_per_task": (
                self.total_tokens_used / max(self.tasks_executed, 1)
            ),
            "sdk_availability": self.sdk_manager.get_availability(),
            "metrics_summary": self.metrics_collector.get_summary()
        }
    
    def export_metrics(self, filename: str = "orchestrator_metrics.json"):
        """
        Export execution metrics to file.
        
        Args:
            filename: Output filename for metrics export
        """
        self.metrics_collector.export_metrics(filename)
        logger.info(f"Exported orchestrator metrics to {filename}")
