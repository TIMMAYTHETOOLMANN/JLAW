"""
Context Degradation Prevention for Long-Running Investigations
===============================================================

Implements strategies to prevent the documented 39% average performance
drop in multi-turn LLM interactions. Three primary mitigation mechanisms:

1. **Compaction** — Summarize conversation when token count exceeds a
   configurable threshold (~92% of context window per Claude Code's design).

2. **Structured State Management** — Maintain an ``investigation_state``
   JSON document with current phase, key findings, and outstanding gaps.
   Re-injected at each turn, reducing context from tens of thousands of
   tokens to 500-2,000 tokens.

3. **Fresh Context Design** — Start new conversations with summarized
   state rather than continuing degraded ones. Per Anthropic's research,
   fresh conversations with the same information yield significantly
   better results.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Investigation State
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class InvestigationState:
    """Structured state document for a forensic investigation.

    Tracks the current phase, accumulated findings, outstanding gaps,
    and investigation metadata. Designed to be serialized and re-injected
    into fresh conversation contexts to prevent degradation.

    Attributes:
        investigation_id: Unique identifier for the investigation.
        company_name: Target company name.
        cik: SEC CIK number.
        current_phase: Current analysis phase description.
        findings: Key findings accumulated during analysis.
        violations: Detected violations with metadata.
        gaps: Outstanding investigation gaps to address.
        metadata: Additional investigation metadata.
        token_estimate: Estimated token count when serialized.
    """

    investigation_id: str = ""
    company_name: str = ""
    cik: str = ""
    current_phase: str = "initialization"
    findings: list[str] = field(default_factory=list)
    violations: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    token_estimate: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON storage.

        Returns:
            Dict representation of the investigation state.
        """
        return {
            "investigation_id": self.investigation_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "current_phase": self.current_phase,
            "findings": self.findings,
            "violations": self.violations,
            "gaps": self.gaps,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InvestigationState":
        """Deserialize from dictionary.

        Args:
            data: Dictionary with investigation state fields.

        Returns:
            InvestigationState instance.
        """
        return cls(
            investigation_id=data.get("investigation_id", ""),
            company_name=data.get("company_name", ""),
            cik=data.get("cik", ""),
            current_phase=data.get("current_phase", "initialization"),
            findings=data.get("findings", []),
            violations=data.get("violations", []),
            gaps=data.get("gaps", []),
            metadata=data.get("metadata", {}),
        )

    def add_finding(self, finding: str) -> None:
        """Add a key finding to the state.

        Args:
            finding: Description of the finding.
        """
        if finding not in self.findings:
            self.findings.append(finding)

    def add_violation(self, violation: dict[str, Any]) -> None:
        """Add a detected violation to the state.

        Args:
            violation: Violation details dict.
        """
        self.violations.append(violation)

    def add_gap(self, gap: str) -> None:
        """Add an outstanding investigation gap.

        Args:
            gap: Description of the gap to address.
        """
        if gap not in self.gaps:
            self.gaps.append(gap)

    def to_context_injection(self) -> str:
        """Generate a compact context injection string.

        Creates a concise summary of the investigation state suitable
        for injecting into a fresh conversation context. Targets
        500-2,000 tokens to minimize context window usage.

        Returns:
            Formatted context injection string.
        """
        parts = [
            f"Investigation: {self.company_name} (CIK: {self.cik})",
            f"Current Phase: {self.current_phase}",
        ]

        if self.findings:
            parts.append("Key Findings:")
            for i, f in enumerate(self.findings[-10:], 1):  # Last 10
                parts.append(f"  {i}. {f}")

        if self.violations:
            parts.append(f"Violations Detected: {len(self.violations)}")
            for v in self.violations[-5:]:  # Last 5
                parts.append(
                    f"  - {v.get('type', 'unknown')}: "
                    f"{v.get('description', 'N/A')[:100]}"
                )

        if self.gaps:
            parts.append("Outstanding Gaps:")
            for g in self.gaps:
                parts.append(f"  - {g}")

        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════
# Context Manager
# ═══════════════════════════════════════════════════════════════════════


class ContextManager:
    """Manages conversation context to prevent degradation.

    Monitors token usage and triggers compaction when the context
    approaches the model's window limit. Maintains investigation
    state for re-injection into fresh conversations.

    Args:
        max_context_tokens: Maximum context window size.
        compaction_threshold: Fraction of max_context at which to trigger
            compaction (default 0.92 per Claude Code's design).
        investigation_state: Optional pre-existing investigation state.
    """

    def __init__(
        self,
        max_context_tokens: int = 200_000,
        compaction_threshold: float = 0.92,
        investigation_state: Optional[InvestigationState] = None,
    ) -> None:
        self.max_context_tokens = max_context_tokens
        self.compaction_threshold = compaction_threshold
        self.state = investigation_state or InvestigationState()
        self._message_history: list[dict[str, Any]] = []
        self._total_tokens_used: int = 0
        self._compaction_count: int = 0

    @property
    def needs_compaction(self) -> bool:
        """Check if context has exceeded the compaction threshold.

        Returns:
            True if current token usage exceeds threshold.
        """
        threshold = int(self.max_context_tokens * self.compaction_threshold)
        return self._total_tokens_used >= threshold

    @property
    def utilization(self) -> float:
        """Current context window utilization as a fraction.

        Returns:
            Float between 0.0 and 1.0.
        """
        if self.max_context_tokens == 0:
            return 0.0
        return self._total_tokens_used / self.max_context_tokens

    def update_token_count(self, tokens: int) -> None:
        """Update the running token count.

        Args:
            tokens: Number of tokens from the latest API response.
        """
        self._total_tokens_used += tokens

    def add_message(self, message: dict[str, Any]) -> None:
        """Track a message in the conversation history.

        Args:
            message: Message dict with role and content.
        """
        self._message_history.append(message)

    def compact(self) -> list[dict[str, Any]]:
        """Compact the conversation by replacing history with state summary.

        Replaces the full message history with a single user message
        containing the investigation state context injection. This
        reduces context from tens of thousands of tokens to ~500-2,000.

        Returns:
            New compacted message list to use for the next API call.
        """
        self._compaction_count += 1
        self._total_tokens_used = 0  # Reset after compaction

        context = self.state.to_context_injection()
        compacted_messages = [
            {
                "role": "user",
                "content": (
                    f"[Context compacted — iteration {self._compaction_count}]\n\n"
                    f"{context}\n\n"
                    "Continue the investigation from the current phase. "
                    "Review the findings and gaps above, then proceed "
                    "with the next analysis step."
                ),
            }
        ]

        self._message_history = compacted_messages.copy()
        logger.info(
            "Context compacted (iteration %d). "
            "Reduced to ~%d tokens of state context.",
            self._compaction_count,
            len(context) // 4,  # Rough token estimate
        )
        return compacted_messages

    def get_stats(self) -> dict[str, Any]:
        """Return context management statistics.

        Returns:
            Dict with utilization, compaction count, and state summary.
        """
        return {
            "total_tokens_used": self._total_tokens_used,
            "max_context_tokens": self.max_context_tokens,
            "utilization": round(self.utilization, 3),
            "needs_compaction": self.needs_compaction,
            "compaction_count": self._compaction_count,
            "message_count": len(self._message_history),
            "findings_count": len(self.state.findings),
            "violations_count": len(self.state.violations),
            "gaps_count": len(self.state.gaps),
        }
