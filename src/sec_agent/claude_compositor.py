"""
Claude Compositor — AI Agent Composition and Orchestration Bridge
===================================================================

Bridges JLAW's multi-agent AI infrastructure (Anthropic + OpenAI) with
the SEC-AGENT deployment platform. Composes Claude forensic agents for
specialized analysis tasks across the unified pipeline.

Architecture:
    - Wraps JLAW's UnifiedSDKManager for centralized API access
    - Exposes JLAW's AnthropicAgentAnalyzer for Claude-powered analysis
    - Orchestrates multi-agent workflows via UnifiedAgentOrchestrator
    - Integrates Claude Agent layer (Tool Runner, MCP, multi-agent prosecutor)
    - Manages agent lifecycle, rate limiting, and cost tracking

Source Integration:
    JLAW anthropic_agent_analyzer.py (389 LOC) → Claude forensic analysis
    JLAW sdk_manager.py (563 LOC) → Unified SDK management (singleton)
    JLAW unified_agent_orchestrator.py (1,003 LOC) → Multi-tier orchestration
    JLAW claude_agent/ → Tool Runner, MCP servers, multi-agent prosecutor
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.claude_agent import (
    ContextManager,
    ForensicToolRunner,
    InvestigationState,
    MCPConfiguration,
    ModelTier,
    ProsecutorOrchestrator,
    ToolExecutor,
    get_default_mcp_config,
    get_forensic_tools,
)
from src.forensics.anthropic_agent_analyzer import AnthropicAgentAnalyzer
from src.forensics.sdk_manager import (
    UnifiedSDKManager,
    get_sdk_manager,
    get_sdk_manager_sync,
)
from src.core.unified_agent_orchestrator import (
    UnifiedAgentOrchestrator,
    UnifiedResult,
    AgentTier,
)

logger = logging.getLogger(__name__)


class CompositorMode(Enum):
    """Operating mode for the Claude Compositor."""

    SINGLE_AGENT = "single_agent"       # Single Claude agent analysis
    MULTI_AGENT = "multi_agent"         # Multiple specialized agents
    FULL_PIPELINE = "full_pipeline"     # Complete JLAW orchestration
    VALIDATION_ONLY = "validation_only" # Cross-validation without analysis


class AnalysisScope(Enum):
    """Scope of forensic analysis."""

    FILING_LEVEL = "filing_level"       # Single filing analysis
    ENTITY_LEVEL = "entity_level"       # Entity/company-wide analysis
    CROSS_ENTITY = "cross_entity"       # Multi-entity correlation
    TEMPORAL = "temporal"               # Time-series analysis


@dataclass
class AgentConfig:
    """Configuration for a Claude forensic agent."""

    agent_id: str
    agent_name: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: float = 0.1
    system_prompt: Optional[str] = None
    specialization: Optional[str] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "specialization": self.specialization,
            "enabled": self.enabled,
        }


# Default agent configurations for JLAW forensic analysis
DEFAULT_AGENT_CONFIGS: List[AgentConfig] = [
    AgentConfig(
        agent_id="insider-trading-analyst",
        agent_name="Insider Trading Analyst",
        specialization="Form 4, Section 16(a)/(b), short-swing profit detection",
        system_prompt=(
            "You are an SEC enforcement specialist focused on insider trading "
            "violations. Analyze Form 4 filings for Section 16(a) late filing, "
            "Section 16(b) short-swing profit, and suspicious trading patterns."
        ),
    ),
    AgentConfig(
        agent_id="compensation-analyst",
        agent_name="Executive Compensation Analyst",
        specialization="DEF 14A, proxy statement, say-on-pay, golden parachute",
        system_prompt=(
            "You are a corporate governance expert specializing in executive "
            "compensation analysis. Review DEF 14A proxy statements for excessive "
            "compensation, say-on-pay failures, and golden parachute provisions."
        ),
    ),
    AgentConfig(
        agent_id="financial-statement-analyst",
        agent_name="Financial Statement Analyst",
        specialization="10-K/10-Q, SOX compliance, restatements, revenue recognition",
        system_prompt=(
            "You are a forensic accountant specializing in financial statement "
            "analysis. Review 10-K and 10-Q filings for SOX compliance issues, "
            "restatement indicators, and revenue recognition anomalies."
        ),
    ),
    AgentConfig(
        agent_id="beneficial-ownership-analyst",
        agent_name="Beneficial Ownership Analyst",
        specialization="Schedule 13D/13G, Section 13(d) compliance, wolf pack detection",
        system_prompt=(
            "You are a securities law expert focused on beneficial ownership "
            "reporting. Analyze Schedule 13D/13G filings for late filings, "
            "passive-to-activist shifts, and coordinated wolf pack activity."
        ),
    ),
    AgentConfig(
        agent_id="material-event-analyst",
        agent_name="Material Event Analyst",
        specialization="8-K current reports, material omissions, insider timing",
        system_prompt=(
            "You are an SEC enforcement specialist focused on material event "
            "disclosure. Review 8-K filings for late disclosure, material "
            "omissions, and suspicious insider trading timing around events."
        ),
    ),
    AgentConfig(
        agent_id="institutional-holdings-analyst",
        agent_name="Institutional Holdings Analyst",
        specialization="13F-HR, institutional ownership changes, accumulation patterns",
        system_prompt=(
            "You are a market structure analyst specializing in institutional "
            "holdings. Analyze 13F-HR filings for unusual accumulation/distribution "
            "patterns and institutional coordination signals."
        ),
    ),
    AgentConfig(
        agent_id="network-intelligence-analyst",
        agent_name="Network Intelligence Analyst",
        specialization="Executive networks, board interlocks, related party transactions",
        system_prompt=(
            "You are a corporate intelligence analyst specializing in network "
            "analysis. Map executive relationships, board interlocks, and "
            "related party transactions for evidence of coordinated activity."
        ),
    ),
    AgentConfig(
        agent_id="quantitative-forensics-analyst",
        agent_name="Quantitative Forensics Analyst",
        specialization="Z-Score, F-Score, Beneish M-Score, Benford's Law",
        system_prompt=(
            "You are a quantitative forensic analyst specializing in financial "
            "health metrics. Apply Altman Z-Score, Piotroski F-Score, Beneish "
            "M-Score, and Benford's Law analysis to detect financial anomalies."
        ),
    ),
    AgentConfig(
        agent_id="market-correlation-analyst",
        agent_name="Market Correlation Analyst",
        specialization="Price-volume correlation, event-driven anomalies, isolation forest",
        system_prompt=(
            "You are a market microstructure analyst specializing in correlation "
            "analysis. Detect unusual price-volume patterns around SEC filings "
            "and corporate events using statistical anomaly detection."
        ),
    ),
    AgentConfig(
        agent_id="cross-validation-analyst",
        agent_name="Cross-Validation Analyst",
        specialization="Dual-agent consensus, contradiction detection, evidence synthesis",
        system_prompt=(
            "You are a forensic synthesis analyst responsible for cross-validating "
            "findings from multiple analysis agents. Identify contradictions, "
            "consensus patterns, and synthesize evidence for prosecution readiness."
        ),
    ),
]


@dataclass
class CompositorResult:
    """Result from Claude Compositor analysis."""

    compositor_id: str
    mode: CompositorMode
    scope: AnalysisScope
    status: str  # "success", "partial", "error"
    agents_invoked: int = 0
    agents_succeeded: int = 0
    agents_failed: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    execution_time_seconds: float = 0.0
    findings: Dict[str, Any] = field(default_factory=dict)
    violations_detected: int = 0
    agent_results: Dict[str, Any] = field(default_factory=dict)
    consensus_score: float = 0.0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "compositor_id": self.compositor_id,
            "mode": self.mode.value,
            "scope": self.scope.value,
            "status": self.status,
            "agents_invoked": self.agents_invoked,
            "agents_succeeded": self.agents_succeeded,
            "agents_failed": self.agents_failed,
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "execution_time_seconds": round(self.execution_time_seconds, 2),
            "violations_detected": self.violations_detected,
            "consensus_score": round(self.consensus_score, 3),
            "error_count": len(self.errors),
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


class ClaudeCompositor:
    """
    Orchestrate Claude forensic agents for SEC filing analysis.

    Bridges JLAW's multi-agent AI infrastructure with the SEC-AGENT
    platform, providing unified agent composition, lifecycle management,
    and cost tracking.

    Args:
        agent_configs: List of agent configurations. Uses defaults if None.
        max_tokens_budget: Maximum total tokens across all agents.
        max_cost_usd: Maximum total cost in USD.
        mode: Operating mode (single_agent, multi_agent, full_pipeline).
        enable_cross_validation: Enable dual-agent cross-validation.
    """

    def __init__(
        self,
        agent_configs: Optional[List[AgentConfig]] = None,
        max_tokens_budget: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        mode: CompositorMode = CompositorMode.MULTI_AGENT,
        enable_cross_validation: bool = True,
    ) -> None:
        self.agent_configs = agent_configs or DEFAULT_AGENT_CONFIGS
        self.max_tokens_budget = max_tokens_budget
        self.max_cost_usd = max_cost_usd or 2.0  # Default $2 per investigation
        self.mode = mode
        self.enable_cross_validation = enable_cross_validation

        # JLAW integration components (lazy-loaded)
        self._anthropic_analyzer: Optional[AnthropicAgentAnalyzer] = None
        self._orchestrator: Optional[UnifiedAgentOrchestrator] = None
        self._sdk_manager: Optional[UnifiedSDKManager] = None

        # Claude Agent layer components (lazy-loaded)
        self._tool_runner: Optional[ForensicToolRunner] = None
        self._mcp_config: Optional[MCPConfiguration] = None
        self._context_manager: Optional[ContextManager] = None
        self._prosecutor: Optional[ProsecutorOrchestrator] = None

        # Tracking
        self._total_tokens_used = 0
        self._total_cost_usd = 0.0
        self._invocation_count = 0

        logger.info(
            "ClaudeCompositor initialized: mode=%s, agents=%d, budget=$%.2f",
            mode.value,
            len(self.agent_configs),
            self.max_cost_usd,
        )

    @property
    def anthropic_analyzer(self) -> AnthropicAgentAnalyzer:
        """Lazy-load the Anthropic agent analyzer."""
        if self._anthropic_analyzer is None:
            self._anthropic_analyzer = AnthropicAgentAnalyzer()
        return self._anthropic_analyzer

    @property
    def orchestrator(self) -> UnifiedAgentOrchestrator:
        """Lazy-load the unified agent orchestrator."""
        if self._orchestrator is None:
            self._orchestrator = UnifiedAgentOrchestrator(
                max_tokens=self.max_tokens_budget,
                max_cost_usd=self.max_cost_usd,
                enable_profiling=True,
            )
        return self._orchestrator

    @property
    def tool_runner(self) -> ForensicToolRunner:
        """Lazy-load the Claude forensic tool runner.

        Provides the agentic loop with forensic tool definitions for
        Claude to invoke during analysis.
        """
        if self._tool_runner is None:
            self._tool_runner = ForensicToolRunner(
                model=ModelTier.SONNET.value,
                max_tokens=4096,
                enable_prompt_caching=True,
            )
        return self._tool_runner

    @property
    def mcp_config(self) -> MCPConfiguration:
        """Lazy-load MCP server configuration.

        Returns configuration for SEC EDGAR, anomaly database,
        and evidence chain MCP servers.
        """
        if self._mcp_config is None:
            self._mcp_config = get_default_mcp_config()
        return self._mcp_config

    @property
    def context_manager(self) -> ContextManager:
        """Lazy-load the context degradation prevention manager."""
        if self._context_manager is None:
            self._context_manager = ContextManager(
                max_context_tokens=200_000,
                compaction_threshold=0.92,
            )
        return self._context_manager

    @property
    def prosecutor(self) -> ProsecutorOrchestrator:
        """Lazy-load the multi-agent prosecutor orchestrator.

        Configures the prosecutor pattern with Opus master agent
        and Sonnet subagents for parallel domain analysis.
        """
        if self._prosecutor is None:
            self._prosecutor = ProsecutorOrchestrator(
                master_model=ModelTier.OPUS.value,
                enable_parallel=True,
            )
        return self._prosecutor

    def get_claude_agent_capabilities(self) -> Dict[str, Any]:
        """Return available Claude agent layer capabilities.

        Provides a summary of all integrated Claude agent features
        including tool runner, MCP servers, multi-agent orchestration,
        and context management.

        Returns:
            Dict describing available capabilities and their status.
        """
        return {
            "tool_runner": {
                "available": True,
                "model": self.tool_runner.model,
                "tools_count": len(get_forensic_tools()),
                "prompt_caching": self.tool_runner.enable_prompt_caching,
            },
            "mcp_servers": {
                "available": True,
                "servers": {
                    name: {"enabled": cfg.enabled}
                    for name, cfg in self.mcp_config.servers.items()
                },
            },
            "multi_agent": {
                "available": True,
                "master_model": self.prosecutor.master_model,
                "subagent_count": len(self.prosecutor.subagents),
                "parallel_enabled": self.prosecutor.enable_parallel,
            },
            "context_management": {
                "available": True,
                "max_tokens": self.context_manager.max_context_tokens,
                "compaction_threshold": self.context_manager.compaction_threshold,
            },
        }

    def get_enabled_agents(self) -> List[AgentConfig]:
        """Get list of enabled agent configurations."""
        return [a for a in self.agent_configs if a.enabled]

    def get_agent_by_id(self, agent_id: str) -> Optional[AgentConfig]:
        """Look up agent configuration by ID."""
        for agent in self.agent_configs:
            if agent.agent_id == agent_id:
                return agent
        return None

    async def analyze_filing(
        self,
        content: str,
        filing_type: str,
        document_url: str,
        filing_date: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
    ) -> CompositorResult:
        """
        Analyze a single filing using Claude forensic agents.

        In SINGLE_AGENT mode, uses the specified agent or best-match agent.
        In MULTI_AGENT mode, routes to all relevant agents for the filing type.

        Args:
            content: Filing text content.
            filing_type: SEC form type (e.g., "4", "10-K", "DEF 14A").
            document_url: Source document URL.
            filing_date: Filing date string.
            context: Additional analysis context.
            agent_id: Specific agent to use (overrides auto-routing).

        Returns:
            CompositorResult with analysis findings.
        """
        compositor_id = f"comp-{int(time.time())}-{self._invocation_count}"
        self._invocation_count += 1
        start_time = time.time()

        result = CompositorResult(
            compositor_id=compositor_id,
            mode=self.mode,
            scope=AnalysisScope.FILING_LEVEL,
            status="error",
            started_at=datetime.utcnow(),
        )

        try:
            # Budget check
            if self._total_cost_usd >= self.max_cost_usd:
                result.errors.append(
                    f"Budget exceeded: ${self._total_cost_usd:.2f} >= ${self.max_cost_usd:.2f}"
                )
                result.status = "error"
                return result

            if self.mode == CompositorMode.SINGLE_AGENT:
                await self._run_single_agent(
                    result, content, filing_type, document_url,
                    filing_date, context, agent_id,
                )
            elif self.mode == CompositorMode.MULTI_AGENT:
                await self._run_multi_agent(
                    result, content, filing_type, document_url,
                    filing_date, context,
                )
            elif self.mode == CompositorMode.FULL_PIPELINE:
                await self._run_full_pipeline(
                    result, content, filing_type, document_url,
                    filing_date, context,
                )
            elif self.mode == CompositorMode.VALIDATION_ONLY:
                await self._run_validation(
                    result, content, filing_type, context,
                )

        except Exception as e:
            logger.error("Compositor analysis failed: %s", e, exc_info=True)
            result.errors.append(str(e))
            result.status = "error"

        result.execution_time_seconds = time.time() - start_time
        result.completed_at = datetime.utcnow()
        return result

    async def analyze_corpus(
        self,
        filings: List[Dict[str, Any]],
        investigation_type: str = "forensic",
        output_dir: Optional[Path] = None,
    ) -> CompositorResult:
        """
        Analyze a corpus of filings using the full orchestration pipeline.

        Routes through JLAW's UnifiedAgentOrchestrator for multi-tier
        analysis including all 10 Claude agents, 23 detection patterns,
        and cross-validation.

        Args:
            filings: List of filing dictionaries with content and metadata.
            investigation_type: Type of investigation ("forensic", "compliance", etc.).
            output_dir: Optional output directory for results.

        Returns:
            CompositorResult with corpus-wide analysis.
        """
        compositor_id = f"corpus-{int(time.time())}-{self._invocation_count}"
        self._invocation_count += 1
        start_time = time.time()

        result = CompositorResult(
            compositor_id=compositor_id,
            mode=CompositorMode.FULL_PIPELINE,
            scope=AnalysisScope.ENTITY_LEVEL,
            status="error",
            started_at=datetime.utcnow(),
        )

        try:
            context = {
                "compositor_mode": self.mode.value,
                "agent_count": len(self.get_enabled_agents()),
                "filing_count": len(filings),
                "investigation_type": investigation_type,
            }

            orchestrator_result: UnifiedResult = (
                await self.orchestrator.execute_investigation(
                    investigation_type=investigation_type,
                    filings=filings,
                    context=context,
                    enable_subagents=True,
                    enable_patterns=True,
                    enable_nodes=True,
                    output_dir=output_dir,
                )
            )

            result.status = orchestrator_result.status
            result.agents_invoked = orchestrator_result.agents_invoked
            result.total_tokens_used = orchestrator_result.tokens_used
            result.violations_detected = len(
                orchestrator_result.aggregated_violations
            )
            result.consensus_score = orchestrator_result.consensus_score
            result.findings = {
                "tier_results": orchestrator_result.tier_results,
                "violations": orchestrator_result.aggregated_violations,
            }
            result.agent_results = orchestrator_result.tier_results

            # Update tracking
            self._total_tokens_used += orchestrator_result.tokens_used
            result.agents_succeeded = result.agents_invoked  # Simplified

        except Exception as e:
            logger.error("Corpus analysis failed: %s", e, exc_info=True)
            result.errors.append(str(e))

        result.execution_time_seconds = time.time() - start_time
        result.completed_at = datetime.utcnow()
        return result

    async def get_sdk_availability(self) -> Dict[str, bool]:
        """
        Check availability of AI SDK clients.

        Returns:
            Dictionary mapping SDK name to availability status.
        """
        try:
            sdk = get_sdk_manager_sync()
            return sdk.get_availability()
        except Exception as e:
            logger.error("SDK availability check failed: %s", e)
            return {
                "openai": False,
                "anthropic": False,
                "openrouter": False,
            }

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get compositor usage statistics.

        Returns:
            Dictionary with token usage, cost, and invocation counts.
        """
        return {
            "total_tokens_used": self._total_tokens_used,
            "total_cost_usd": round(self._total_cost_usd, 4),
            "invocation_count": self._invocation_count,
            "budget_remaining_usd": round(
                max(0, self.max_cost_usd - self._total_cost_usd), 4
            ),
            "budget_utilization_pct": round(
                (self._total_cost_usd / self.max_cost_usd * 100)
                if self.max_cost_usd > 0
                else 0,
                1,
            ),
            "enabled_agents": len(self.get_enabled_agents()),
            "mode": self.mode.value,
        }

    async def close(self) -> None:
        """Release resources and close connections."""
        if self._sdk_manager:
            await self._sdk_manager.close()
        logger.info(
            "ClaudeCompositor closed: %d invocations, %d tokens, $%.4f",
            self._invocation_count,
            self._total_tokens_used,
            self._total_cost_usd,
        )

    # ── Private methods ─────────────────────────────────────────────────

    def _get_agents_for_filing_type(
        self, filing_type: str
    ) -> List[AgentConfig]:
        """Route filing type to relevant agent configurations."""
        filing_upper = filing_type.upper().strip()
        enabled = self.get_enabled_agents()

        # Mapping of filing types to relevant agent specializations
        routing: Dict[str, List[str]] = {
            "4": ["insider-trading-analyst"],
            "3": ["insider-trading-analyst"],
            "5": ["insider-trading-analyst"],
            "DEF 14A": ["compensation-analyst"],
            "10-K": ["financial-statement-analyst", "quantitative-forensics-analyst"],
            "10-Q": ["financial-statement-analyst", "quantitative-forensics-analyst"],
            "8-K": ["material-event-analyst"],
            "13F-HR": ["institutional-holdings-analyst"],
            "SC 13D": ["beneficial-ownership-analyst"],
            "SC 13G": ["beneficial-ownership-analyst"],
            "144": ["insider-trading-analyst"],
        }

        target_ids = routing.get(filing_upper, [])

        # Always include cross-validation if enabled
        if self.enable_cross_validation:
            target_ids.append("cross-validation-analyst")

        return [a for a in enabled if a.agent_id in target_ids]

    async def _run_single_agent(
        self,
        result: CompositorResult,
        content: str,
        filing_type: str,
        document_url: str,
        filing_date: Optional[str],
        context: Optional[Dict[str, Any]],
        agent_id: Optional[str],
    ) -> None:
        """Run analysis with a single Claude agent."""
        result.agents_invoked = 1

        try:
            analysis = await self.anthropic_analyzer.analyze_filing_deep(
                content=content,
                filing_type=filing_type,
                document_url=document_url,
                filing_date=filing_date,
                context=context,
            )

            result.findings = analysis
            result.violations_detected = len(analysis.get("violations", []))
            result.status = "success"
            result.agents_succeeded = 1

        except Exception as e:
            result.errors.append(f"Single agent analysis failed: {e}")
            result.agents_failed = 1

    async def _run_multi_agent(
        self,
        result: CompositorResult,
        content: str,
        filing_type: str,
        document_url: str,
        filing_date: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> None:
        """Run analysis with multiple relevant agents."""
        agents = self._get_agents_for_filing_type(filing_type)
        result.agents_invoked = len(agents)

        if not agents:
            # Fallback to single agent
            await self._run_single_agent(
                result, content, filing_type, document_url,
                filing_date, context, None,
            )
            return

        all_findings: Dict[str, Any] = {}
        total_violations = 0

        for agent_config in agents:
            try:
                enriched_context = {
                    **(context or {}),
                    "agent_specialization": agent_config.specialization,
                    "agent_id": agent_config.agent_id,
                }

                analysis = await self.anthropic_analyzer.analyze_filing_deep(
                    content=content,
                    filing_type=filing_type,
                    document_url=document_url,
                    filing_date=filing_date,
                    context=enriched_context,
                )

                all_findings[agent_config.agent_id] = analysis
                total_violations += len(analysis.get("violations", []))
                result.agents_succeeded += 1

            except Exception as e:
                logger.warning(
                    "Agent %s failed: %s", agent_config.agent_id, e
                )
                result.agents_failed += 1
                result.errors.append(
                    f"Agent {agent_config.agent_id}: {e}"
                )

        result.findings = all_findings
        result.agent_results = all_findings
        result.violations_detected = total_violations
        result.status = (
            "success" if result.agents_succeeded > 0 else "error"
        )

    async def _run_full_pipeline(
        self,
        result: CompositorResult,
        content: str,
        filing_type: str,
        document_url: str,
        filing_date: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> None:
        """Run full JLAW orchestration pipeline."""
        filings = [
            {
                "content": content,
                "filing_type": filing_type,
                "document_url": document_url,
                "filing_date": filing_date,
                **(context or {}),
            }
        ]

        corpus_result = await self.analyze_corpus(
            filings=filings,
            investigation_type="forensic",
        )

        # Copy results
        result.status = corpus_result.status
        result.agents_invoked = corpus_result.agents_invoked
        result.agents_succeeded = corpus_result.agents_succeeded
        result.agents_failed = corpus_result.agents_failed
        result.total_tokens_used = corpus_result.total_tokens_used
        result.violations_detected = corpus_result.violations_detected
        result.consensus_score = corpus_result.consensus_score
        result.findings = corpus_result.findings
        result.agent_results = corpus_result.agent_results
        result.errors.extend(corpus_result.errors)

    async def _run_validation(
        self,
        result: CompositorResult,
        content: str,
        filing_type: str,
        context: Optional[Dict[str, Any]],
    ) -> None:
        """Run cross-validation only (no primary analysis)."""
        result.agents_invoked = 1
        try:
            analysis = await self.anthropic_analyzer.analyze_text(
                content=content,
                context={
                    **(context or {}),
                    "mode": "validation_only",
                    "filing_type": filing_type,
                },
            )
            result.findings = {"validation": analysis}
            result.status = "success"
            result.agents_succeeded = 1
        except Exception as e:
            result.errors.append(f"Validation failed: {e}")
            result.agents_failed = 1
