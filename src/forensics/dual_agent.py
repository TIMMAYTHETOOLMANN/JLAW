"""
Dual Agent Coordinator
======================
Coordinates dual-agent analysis using:
 - Primary: OpenAI Agent SDK (AgentSECForensicAnalyzer)
 - Secondary: Anthropic Agent SDK (AnthropicAgentAnalyzer)

This module provides a lightweight, CPU-friendly coordinator that accepts
generic content (text) and returns a merged, provenance-rich summary. It
gracefully degrades when one or both providers are unavailable.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .config_manager import get_config

logger = logging.getLogger(__name__)


class DualAgentCoordinator:
    def __init__(self) -> None:
        cfg = get_config().config
        self._openai_available = bool(cfg.openai.api_key)
        self._anthropic_available = bool(cfg.anthropic.api_key)
        self._init_errors: Dict[str, str] = {}

        self.openai_analyzer = None
        self.anthropic_analyzer = None

        # Try initialize OpenAI analyzer
        if self._openai_available:
            try:
                from .agent_sec_analyzer import AgentSECForensicAnalyzer
                self.openai_analyzer = AgentSECForensicAnalyzer()
            except Exception as e:
                self._init_errors["openai"] = str(e)
                logger.debug("OpenAI analyzer init failed: %s", e)
                self.openai_analyzer = None

        # Try initialize Anthropic analyzer
        if self._anthropic_available:
            try:
                from .anthropic_agent_analyzer import AnthropicAgentAnalyzer
                self.anthropic_analyzer = AnthropicAgentAnalyzer()
            except Exception as e:
                self._init_errors["anthropic"] = str(e)
                logger.debug("Anthropic analyzer init failed: %s", e)
                self.anthropic_analyzer = None

        logger.info(
            "DualAgentCoordinator ready (openai=%s, anthropic=%s)",
            bool(self.openai_analyzer), bool(self.anthropic_analyzer)
        )

    def availability(self) -> Dict[str, bool]:
        return {
            "openai": bool(self.openai_analyzer),
            "anthropic": bool(self.anthropic_analyzer),
        }

    async def analyze_text(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run dual-agent analysis on plain text and merge results.

        Returns a dict with provider subresults, consensus metrics, and provenance.
        """
        context = context or {}
        results: Dict[str, Any] = {
            "openai": {"status": "SKIP", "reason": "unavailable"},
            "anthropic": {"status": "SKIP", "reason": "unavailable"},
            "consensus": {"overlap": 0, "openai_only": 0, "anthropic_only": 0},
            "provenance": {
                "openai_model": None,
                "anthropic_model": None,
            },
        }

        # Enforce BOTH providers available as per policy (no simple fallback)
        if not (self.openai_analyzer and self.anthropic_analyzer):
            avail = self.availability()
            return {
                **results,
                "status": "ERROR",
                "reason": "Dual-agent required: both OpenAI and Anthropic must be configured",
                "availability": avail,
            }

        # Run OpenAI path using internal parse tool on text
        try:
            parse_tool = self.openai_analyzer._create_parse_violations_tool()  # type: ignore[attr-defined]
            parsed = parse_tool(text, context.get("filing_type", "TEXT"), context.get("document_url", "inline://content"), context.get("filing_date"))
            results["openai"] = {
                "status": "success",
                "violations": parsed.get("violations", []),
                "raw": parsed,
            }
            results["provenance"]["openai_model"] = getattr(self.openai_analyzer, "model", None)
        except Exception as e:
            results["openai"] = {"status": "error", "error": str(e), "violations": []}

        # Run Anthropic path via analyze_text
        try:
            anth = await self.anthropic_analyzer.analyze_text(text, context=context)
            results["anthropic"] = anth
            results["provenance"]["anthropic_model"] = getattr(self.anthropic_analyzer, "model", None)
        except Exception as e:
            results["anthropic"] = {"status": "error", "error": str(e), "violations": []}

        # Compute consensus metrics (simple overlap on violation type + statute if present)
        try:
            o_viol = results.get("openai", {}).get("violations") or []
            a_viol = results.get("anthropic", {}).get("violations") or []

            def key(v: Dict[str, Any]) -> str:
                t = v.get("type") or v.get("violation_type") or "?"
                s = v.get("statute") or ""
                d = v.get("description") or ""
                return f"{t}|{s}|{d[:40]}"

            o_keys = {key(v) for v in o_viol}
            a_keys = {key(v) for v in a_viol}
            overlap = len(o_keys & a_keys)
            results["consensus"] = {
                "overlap": overlap,
                "openai_only": len(o_keys - a_keys),
                "anthropic_only": len(a_keys - o_keys),
            }
        except Exception as e:
            logger.debug("Consensus calculation failed: %s", e)

        results["status"] = "OK"
        return results
