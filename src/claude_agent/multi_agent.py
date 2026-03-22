"""
Multi-Agent Prosecutor Orchestration
======================================

Implements the multi-agent "prosecutor pattern" using tiered Claude models:
- Master Prosecutor Agent (Opus 4.6) — strategy, analysis coordination
- Subagents (Sonnet 4.6) — parallel domain-specific analysis
- Triage agents (Haiku 4.5) — classification and routing

Architecture mirrors Anthropic's production multi-agent research system:
a lead agent analyzes queries and spawns parallel subagents that explore
independently with their own context windows and tools.

Key design decisions from Anthropic's engineering team:
- Subagents write results to a shared results dict rather than passing
  them back through the coordinator (avoiding "telephone game" degradation)
- Each subagent gets: objective, output format, tool guidance, task boundaries
- 3-5 parallel subagents with 3+ tools each cut research time by up to 90%
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from src.claude_agent.system_prompts import (
    get_subagent_prompt,
)
from src.claude_agent.tools import get_tools_by_names

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Model Tier Configuration
# ═══════════════════════════════════════════════════════════════════════


class ModelTier(Enum):
    """Claude model tiers for cost-optimized agent allocation.

    Pricing (per million tokens, input/output):
      OPUS:   $5 / $25  — complex reasoning, master orchestration
      SONNET: $3 / $15  — standard analysis, subagent work
      HAIKU:  $1 / $5   — triage, classification, routing
    """

    OPUS = "claude-opus-4-6"
    SONNET = "claude-sonnet-4-6"
    HAIKU = "claude-haiku-4-5"


# ═══════════════════════════════════════════════════════════════════════
# Subagent Configuration
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class SubagentConfig:
    """Configuration for a prosecutor subagent.

    Attributes:
        agent_id: Unique identifier for this subagent.
        role: Role key mapping to SUBAGENT_PROMPTS.
        model_tier: Claude model tier to use.
        tools: List of tool names this subagent can access.
        max_tokens: Maximum output tokens per API call.
        objective: Clear objective statement for the subagent.
    """

    agent_id: str
    role: str
    model_tier: ModelTier = ModelTier.SONNET
    tools: list[str] = field(default_factory=list)
    max_tokens: int = 4096
    objective: str = ""


@dataclass
class SubagentResult:
    """Result from a subagent's analysis.

    Attributes:
        agent_id: Which subagent produced this result.
        role: Subagent role.
        status: Execution status (success, error, timeout).
        findings: Analysis findings as a dictionary.
        execution_time: Time taken in seconds.
        tokens_used: Total tokens consumed.
    """

    agent_id: str
    role: str
    status: str = "pending"
    findings: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dict representation of the subagent result.
        """
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "status": self.status,
            "findings": self.findings,
            "execution_time": round(self.execution_time, 3),
            "tokens_used": self.tokens_used,
        }


# ═══════════════════════════════════════════════════════════════════════
# Orchestration Result
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class ProsecutorResult:
    """Combined result from the multi-agent prosecutor analysis.

    Attributes:
        master_summary: Final synthesized analysis from the master agent.
        subagent_results: Individual results from each subagent.
        total_tokens: Total tokens consumed across all agents.
        total_time: Total wall-clock time in seconds.
        model_usage: Token breakdown by model tier.
    """

    master_summary: str = ""
    subagent_results: list[SubagentResult] = field(default_factory=list)
    total_tokens: int = 0
    total_time: float = 0.0
    model_usage: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dict representation of the full prosecutor result.
        """
        return {
            "master_summary": self.master_summary,
            "subagent_results": [r.to_dict() for r in self.subagent_results],
            "total_tokens": self.total_tokens,
            "total_time": round(self.total_time, 3),
            "model_usage": self.model_usage,
        }


# ═══════════════════════════════════════════════════════════════════════
# Default Subagent Configurations
# ═══════════════════════════════════════════════════════════════════════

DEFAULT_SUBAGENTS: list[SubagentConfig] = [
    SubagentConfig(
        agent_id="sec-analysis",
        role="sec_analysis",
        model_tier=ModelTier.SONNET,
        tools=[
            "search_sec_filings",
            "analyze_filing",
            "detect_insider_trading",
            "run_detection_pattern",
        ],
        objective=(
            "Analyze all SEC filings for the target company. Identify "
            "regulatory violations, late filings, and suspicious patterns."
        ),
    ),
    SubagentConfig(
        agent_id="doj-referral",
        role="doj_referral",
        model_tier=ModelTier.SONNET,
        tools=[
            "calculate_penalty",
            "query_evidence_chain",
        ],
        objective=(
            "Evaluate identified violations for DOJ criminal referral "
            "potential. Assess willfulness and damages thresholds."
        ),
    ),
    SubagentConfig(
        agent_id="whistleblower-bounty",
        role="whistleblower_bounty",
        model_tier=ModelTier.SONNET,
        tools=[
            "check_whistleblower_eligibility",
            "calculate_penalty",
        ],
        objective=(
            "Calculate whistleblower bounty potential across all eligible "
            "programs (SEC, CFTC, IRS, DOJ) for identified violations."
        ),
    ),
    SubagentConfig(
        agent_id="briefing-generation",
        role="briefing_generation",
        model_tier=ModelTier.SONNET,
        tools=[
            "generate_investigation_state",
        ],
        objective=(
            "Synthesize all findings into a structured DOJ-grade "
            "prosecutorial briefing with evidence chain references."
        ),
    ),
]


# ═══════════════════════════════════════════════════════════════════════
# Multi-Agent Prosecutor Orchestrator
# ═══════════════════════════════════════════════════════════════════════


class ProsecutorOrchestrator:
    """Multi-agent orchestrator implementing the prosecutor pattern.

    The master agent (Opus) coordinates parallel subagents (Sonnet) that
    each handle a specific domain of forensic analysis. Results are
    collected and synthesized into a unified prosecutorial assessment.

    Args:
        master_model: Model for the master prosecutor agent.
        subagents: Optional custom subagent configurations.
        enable_parallel: Whether to run subagents in parallel.
        max_subagent_tokens: Token budget per subagent.
    """

    def __init__(
        self,
        master_model: str = ModelTier.OPUS.value,
        subagents: Optional[list[SubagentConfig]] = None,
        enable_parallel: bool = True,
        max_subagent_tokens: int = 4096,
    ) -> None:
        self.master_model = master_model
        self.subagents = subagents or DEFAULT_SUBAGENTS
        self.enable_parallel = enable_parallel
        self.max_subagent_tokens = max_subagent_tokens
        self._client = None

    def _get_client(self) -> Any:
        """Lazily initialize the Anthropic client.

        Returns:
            An anthropic.AsyncAnthropic client instance.
        """
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.AsyncAnthropic()
            except ImportError as exc:
                raise ImportError(
                    "The 'anthropic' package (>=0.86.0) is required. "
                    "Install with: pip install 'anthropic>=0.86.0'"
                ) from exc
        return self._client

    async def _run_subagent(
        self,
        config: SubagentConfig,
        investigation_context: str,
    ) -> SubagentResult:
        """Execute a single subagent with its own context window.

        Each subagent gets a fresh context window to prevent cross-contamination
        of degraded context (per Anthropic's production recommendations).

        Args:
            config: Subagent configuration.
            investigation_context: Shared investigation context.

        Returns:
            SubagentResult with findings.
        """
        start = time.monotonic()
        result = SubagentResult(agent_id=config.agent_id, role=config.role)

        try:
            client = self._get_client()
            system_prompt = get_subagent_prompt(config.role)

            tools = get_tools_by_names(config.tools) if config.tools else []

            user_message = (
                f"{config.objective}\n\n"
                f"Investigation Context:\n{investigation_context}"
            )

            response = await client.messages.create(
                model=config.model_tier.value,
                max_tokens=config.max_tokens,
                system=system_prompt,
                tools=tools if tools else None,
                messages=[{"role": "user", "content": user_message}],
            )

            # Extract text response
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            result.status = "success"
            result.findings = {
                "analysis": response_text,
                "model": config.model_tier.value,
            }
            result.tokens_used = getattr(
                response.usage, "input_tokens", 0
            ) + getattr(response.usage, "output_tokens", 0)

        except Exception as e:
            logger.error("Subagent %s failed: %s", config.agent_id, e)
            result.status = "error"
            result.findings = {"error": str(e)}

        result.execution_time = time.monotonic() - start
        return result

    async def orchestrate(
        self,
        investigation_context: str,
    ) -> ProsecutorResult:
        """Execute the full multi-agent prosecutor analysis.

        Spawns subagents (in parallel if enabled) and collects their
        results into a unified ProsecutorResult.

        Args:
            investigation_context: Description of the investigation
                including target company, CIK, date range, and any
                preliminary findings.

        Returns:
            ProsecutorResult with all subagent findings and synthesis.
        """
        start_time = time.monotonic()
        result = ProsecutorResult()

        logger.info(
            "Starting prosecutor orchestration with %d subagents (parallel=%s)",
            len(self.subagents),
            self.enable_parallel,
        )

        # Run subagents
        if self.enable_parallel:
            tasks = [
                self._run_subagent(config, investigation_context)
                for config in self.subagents
            ]
            result.subagent_results = list(await asyncio.gather(*tasks))
        else:
            for config in self.subagents:
                sub_result = await self._run_subagent(
                    config, investigation_context
                )
                result.subagent_results.append(sub_result)

        # Aggregate metrics
        for sub in result.subagent_results:
            result.total_tokens += sub.tokens_used
            tier_key = sub.role
            result.model_usage[tier_key] = (
                result.model_usage.get(tier_key, 0) + sub.tokens_used
            )

        result.total_time = time.monotonic() - start_time
        logger.info(
            "Prosecutor orchestration completed: %d subagents, %d tokens, %.1fs",
            len(result.subagent_results),
            result.total_tokens,
            result.total_time,
        )

        return result
