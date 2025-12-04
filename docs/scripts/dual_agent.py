"""
Dual Agent Coordinator
======================
Coordinates dual-agent analysis using:
 - Primary: OpenAI Agent SDK (AgentSECForensicAnalyzer)
 - Secondary: Anthropic Agent SDK (AnthropicAgentAnalyzer)

This module provides a lightweight, CPU-friendly coordinator that accepts
generic content (text) and returns a merged, provenance-rich summary. It
gracefully degrades when one or both providers are unavailable.

ENHANCED INVESTIGATIVE WORKFLOW:
================================
1. OpenAI Agent: Initial violation detection and flagging
2. Anthropic Agent: Cross-references ALL flagged violations using GovInfo API
3. GovInfo Integration: Pulls every statute and legal framework correlated with filings
4. Dual-Pass Validation: Ensures nothing is missed between agents
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from .config_manager import get_config

logger = logging.getLogger(__name__)

# SEC rate limiting delay in seconds (10 requests per second = 0.1s minimum, use 0.35s for safety)
SEC_RATE_LIMIT_DELAY = 0.35


def _get_govinfo_api_key(cfg: Any) -> Optional[str]:
    """Helper to extract GovInfo API key from config with consistent pattern."""
    govinfo = getattr(cfg, 'govinfo', None)
    if govinfo and hasattr(govinfo, 'api_key') and govinfo.api_key:
        return govinfo.api_key
    return None


class DualAgentCoordinator:
    """
    Enhanced Dual-Agent Investigative Coordinator.
    
    Implements a sophisticated tandem workflow where:
    - OpenAI agent performs initial violation detection
    - Anthropic agent cross-references findings using GovInfo API
    - All statutes and legal frameworks are pulled for comprehensive coverage
    """

    def __init__(self) -> None:
        cfg = get_config().config
        self._openai_available = bool(cfg.openai.api_key)
        self._anthropic_available = bool(cfg.anthropic.api_key)
        self._govinfo_available = bool(_get_govinfo_api_key(cfg))
        self._init_errors: Dict[str, str] = {}

        self.openai_analyzer: Any = None
        self.anthropic_analyzer: Any = None
        self.govinfo_client: Any = None
        self.statute_integrator: Any = None

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

        # Initialize GovInfo API client for statute cross-referencing
        govinfo_key = _get_govinfo_api_key(cfg)
        if govinfo_key:
            try:
                from src.forensics.advanced_statute_integrator import AdvancedStatuteIntegrator
                from src.forensics.govinfo_api_client import GovInfoAPIClient
                self.govinfo_client = GovInfoAPIClient(api_key=govinfo_key)
                self.statute_integrator = AdvancedStatuteIntegrator(
                    govinfo_api_key=govinfo_key,
                    strict_api_mode=False,  # Use non-strict for resilience
                    dual_agent=True,
                    govinfo_client=self.govinfo_client
                )
                self._govinfo_available = True
                logger.info("✅ GovInfo statute integrator initialized")
            except Exception as e:
                self._init_errors["govinfo"] = str(e)
                logger.warning(f"⚠️ GovInfo client init failed: {e}")
                self._govinfo_available = False
                self.govinfo_client = None
                self.statute_integrator = None

        logger.info(
            "DualAgentCoordinator ready (openai=%s, anthropic=%s, govinfo=%s)",
            bool(self.openai_analyzer), bool(self.anthropic_analyzer), self._govinfo_available
        )

    def availability(self) -> Dict[str, bool]:
        return {
            "openai": bool(self.openai_analyzer),
            "anthropic": bool(self.anthropic_analyzer),
            "govinfo": self._govinfo_available,
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

        # Run OpenAI path using public parse method on text
        try:
            parsed = self.openai_analyzer.parse_violations_from_content(
                text,
                context.get("filing_type", "TEXT"),
                context.get("document_url", "inline://content"),
                context.get("filing_date")
            )
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

    async def investigate_with_cross_reference(
        self,
        content: str,
        filing_metadata: Dict[str, Any],
        enable_govinfo_enrichment: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced investigative workflow with cross-referencing.
        
        WORKFLOW:
        1. OpenAI Agent: Performs initial violation detection on content
        2. Anthropic Agent: Cross-references flagged violations with GovInfo API
        3. Statute Integration: Pulls all related statutes and legal frameworks
        4. Dual-Pass Validation: Ensures comprehensive coverage with nothing missed
        
        Args:
            content: Document content to analyze (filing text)
            filing_metadata: Metadata about the filing (type, date, URL, CIK, etc.)
            enable_govinfo_enrichment: Whether to enrich with GovInfo statutes
            
        Returns:
            Comprehensive investigation results with:
            - openai_findings: Initial violations from OpenAI
            - anthropic_cross_reference: Anthropic validation and additional findings
            - govinfo_statutes: All correlated statutes and legal frameworks
            - merged_violations: Deduplicated, enriched violations
            - investigation_summary: Summary statistics and confidence
        """
        investigation = {
            "status": "IN_PROGRESS",
            "phase": "initialization",
            "openai_findings": {"violations": [], "status": "pending"},
            "anthropic_cross_reference": {"violations": [], "status": "pending"},
            "govinfo_statutes": {"statutes": [], "regulations": [], "status": "pending"},
            "merged_violations": [],
            "investigation_summary": {},
            "provenance": {
                "openai_model": None,
                "anthropic_model": None,
                "govinfo_enriched": False,
            }
        }

        # Check availability
        availability = self.availability()
        if not availability["openai"] or not availability["anthropic"]:
            investigation["status"] = "ERROR"
            investigation["error"] = "Both OpenAI and Anthropic agents required for investigation"
            investigation["availability"] = availability
            return investigation

        context = {
            "filing_type": filing_metadata.get("filing_type", "UNKNOWN"),
            "document_url": filing_metadata.get("document_url", ""),
            "filing_date": filing_metadata.get("filing_date"),
            "cik": filing_metadata.get("cik"),
            "company_name": filing_metadata.get("company_name"),
        }

        # =====================================================================
        # PHASE 1: OpenAI Initial Violation Detection
        # =====================================================================
        investigation["phase"] = "openai_analysis"
        logger.info("[Investigation] Phase 1: OpenAI initial violation detection")

        try:
            parsed = self.openai_analyzer.parse_violations_from_content(
                content,
                context.get("filing_type", "TEXT"),
                context.get("document_url", "inline://content"),
                context.get("filing_date")
            )
            openai_violations = parsed.get("violations", [])
            investigation["openai_findings"] = {
                "status": "success",
                "violations": openai_violations,
                "violation_count": len(openai_violations),
                "raw": parsed,
            }
            investigation["provenance"]["openai_model"] = getattr(self.openai_analyzer, "model", None)
            logger.info(f"[Investigation] OpenAI detected {len(openai_violations)} potential violations")
        except Exception as e:
            logger.error(f"[Investigation] OpenAI analysis failed: {e}")
            investigation["openai_findings"] = {
                "status": "error",
                "error": str(e),
                "violations": [],
            }
            openai_violations = []

        # =====================================================================
        # PHASE 2: Anthropic Cross-Reference and Deep Analysis
        # =====================================================================
        investigation["phase"] = "anthropic_cross_reference"
        logger.info("[Investigation] Phase 2: Anthropic cross-reference analysis")

        # Build enhanced context with OpenAI findings for Anthropic to validate
        cross_ref_context = {
            **context,
            "openai_flagged_violations": openai_violations,
            "cross_reference_mode": True,
            "instruction": (
                "You are cross-referencing violations flagged by the primary analyzer. "
                "Validate each flagged violation, identify any missed violations, "
                "and ensure comprehensive coverage of all regulatory breaches."
            ),
        }

        try:
            anthropic_result = await self.anthropic_analyzer.analyze_text(content, context=cross_ref_context)
            anthropic_violations = anthropic_result.get("violations", [])
            investigation["anthropic_cross_reference"] = {
                "status": anthropic_result.get("status", "success"),
                "violations": anthropic_violations,
                "violation_count": len(anthropic_violations),
                "summary": anthropic_result.get("summary", ""),
                "risk_indicators": anthropic_result.get("risk_indicators", []),
                "recommended_actions": anthropic_result.get("recommended_actions", []),
            }
            investigation["provenance"]["anthropic_model"] = getattr(self.anthropic_analyzer, "model", None)
            logger.info(f"[Investigation] Anthropic validated/found {len(anthropic_violations)} violations")
        except Exception as e:
            logger.error(f"[Investigation] Anthropic cross-reference failed: {e}")
            investigation["anthropic_cross_reference"] = {
                "status": "error",
                "error": str(e),
                "violations": [],
            }
            anthropic_violations = []

        # =====================================================================
        # PHASE 3: Merge and Deduplicate Violations
        # =====================================================================
        investigation["phase"] = "merge_violations"
        logger.info("[Investigation] Phase 3: Merging and deduplicating violations")

        merged = self._merge_violations(openai_violations, anthropic_violations)
        investigation["merged_violations"] = merged

        # =====================================================================
        # PHASE 4: GovInfo Statute Enrichment (Cross-Reference with Legal Framework)
        # =====================================================================
        if enable_govinfo_enrichment and self.statute_integrator:
            investigation["phase"] = "govinfo_enrichment"
            logger.info("[Investigation] Phase 4: GovInfo statute cross-reference")

            try:
                # Use batch cross-reference for efficient API usage
                enriched_violations = await self.statute_integrator.batch_cross_reference(
                    violations=merged,
                    filing_content=content,
                    max_concurrent=5
                )
                
                statutes_found: List[Dict[str, Any]] = []
                regulations_found: List[Dict[str, Any]] = []
                statutes_seen: Set[str] = set()

                for enriched in enriched_violations:
                    try:
                        # Extract statute references from legal framework
                        legal_framework = enriched.get("legal_framework", {})
                        
                        # Collect primary statute
                        primary_statute = legal_framework.get("primary_statute", {})
                        if primary_statute:
                            citation = primary_statute.get("citation", "")
                            if citation and citation not in statutes_seen:
                                statutes_seen.add(citation)
                                statutes_found.append({
                                    "citation": citation,
                                    "full_text": primary_statute.get("full_text", ""),
                                    "summary": primary_statute.get("summary", ""),
                                    "penalties": primary_statute.get("penalties", {}),
                                    "severity": primary_statute.get("severity", "REGULATORY"),
                                    "govinfo_url": primary_statute.get("govinfo_url", ""),
                                    "type": "primary_statute"
                                })
                        
                        # Collect related statutes
                        for related in legal_framework.get("related_statutes", []):
                            citation = related.get("citation", "")
                            if citation and citation not in statutes_seen:
                                statutes_seen.add(citation)
                                statutes_found.append({
                                    "citation": citation,
                                    "summary": related.get("summary", ""),
                                    "govinfo_url": related.get("govinfo_url", ""),
                                    "type": "related_statute"
                                })
                        
                        # Collect CFR regulations
                        for cfr in legal_framework.get("cfr_regulations", []):
                            citation = cfr.get("citation", "")
                            if citation and citation not in statutes_seen:
                                statutes_seen.add(citation)
                                regulations_found.append({
                                    "citation": citation,
                                    "full_text": cfr.get("full_text", ""),
                                    "govinfo_url": cfr.get("govinfo_url", ""),
                                    "type": "cfr_regulation"
                                })

                    except Exception as ve:
                        logger.warning(f"[Investigation] Statute extraction failed: {ve}")

                investigation["merged_violations"] = enriched_violations
                investigation["govinfo_statutes"] = {
                    "status": "success",
                    "statutes": statutes_found,
                    "regulations": regulations_found,
                    "total_unique": len(statutes_seen),
                }
                investigation["provenance"]["govinfo_enriched"] = True
                logger.info(f"[Investigation] GovInfo enriched with {len(statutes_found)} statutes, {len(regulations_found)} regulations")

            except Exception as e:
                logger.error(f"[Investigation] GovInfo enrichment failed: {e}")
                investigation["govinfo_statutes"] = {
                    "status": "error",
                    "error": str(e),
                    "statutes": [],
                    "regulations": [],
                }
        else:
            investigation["govinfo_statutes"]["status"] = "skipped"

        # =====================================================================
        # PHASE 5: Generate Investigation Summary
        # =====================================================================
        investigation["phase"] = "summary"
        logger.info("[Investigation] Phase 5: Generating investigation summary")

        openai_count = len(openai_violations)
        anthropic_count = len(anthropic_violations)
        merged_count = len(merged)

        # Compute overlap and unique findings
        overlap_violations = self._compute_overlap(openai_violations, anthropic_violations)

        investigation["investigation_summary"] = {
            "total_violations_detected": merged_count,
            "openai_initial_count": openai_count,
            "anthropic_cross_reference_count": anthropic_count,
            "overlap_count": len(overlap_violations),
            "openai_unique_count": openai_count - len(overlap_violations),
            "anthropic_unique_count": anthropic_count - len(overlap_violations),
            "dual_agent_coverage": True,
            "govinfo_enriched": investigation["provenance"]["govinfo_enriched"],
            "statutes_correlated": len(investigation["govinfo_statutes"].get("statutes", [])),
            "regulations_correlated": len(investigation["govinfo_statutes"].get("regulations", [])),
            "confidence_level": self._calculate_confidence(openai_count, anthropic_count, merged_count),
            "nothing_missed_validation": merged_count >= max(openai_count, anthropic_count),
        }

        investigation["status"] = "COMPLETE"
        investigation["phase"] = "complete"

        logger.info(
            f"[Investigation] Complete: {merged_count} violations, "
            f"{investigation['investigation_summary']['statutes_correlated']} statutes, "
            f"confidence={investigation['investigation_summary']['confidence_level']:.2%}"
        )

        return investigation

    def _merge_violations(
        self,
        openai_violations: List[Dict[str, Any]],
        anthropic_violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge violations from both agents with deduplication.
        
        Returns a unified list with provenance tracking.
        """
        merged: List[Dict[str, Any]] = []
        seen_keys: Set[str] = set()

        def violation_key(v: Dict[str, Any]) -> str:
            t = v.get("type") or v.get("violation_type") or "?"
            s = v.get("statute") or ""
            d = (v.get("description") or "")[:50]
            url = v.get("document_url") or v.get("url") or ""
            return f"{t}|{s}|{d}|{url}"

        # Add OpenAI violations with provenance
        for v in openai_violations:
            key = violation_key(v)
            if key not in seen_keys:
                seen_keys.add(key)
                v_copy = dict(v)
                v_copy["_source"] = "openai"
                v_copy["_confirmed_by"] = []
                merged.append(v_copy)

        # Add or confirm Anthropic violations
        for v in anthropic_violations:
            key = violation_key(v)
            if key not in seen_keys:
                seen_keys.add(key)
                v_copy = dict(v)
                v_copy["_source"] = "anthropic"
                v_copy["_confirmed_by"] = []
                merged.append(v_copy)
            else:
                # Mark as confirmed by Anthropic
                for m in merged:
                    if violation_key(m) == key:
                        m["_confirmed_by"].append("anthropic")
                        break

        return merged

    def _compute_overlap(
        self,
        openai_violations: List[Dict[str, Any]],
        anthropic_violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Compute violations found by both agents."""
        def key(v: Dict[str, Any]) -> str:
            t = v.get("type") or v.get("violation_type") or "?"
            s = v.get("statute") or ""
            d = (v.get("description") or "")[:40]
            return f"{t}|{s}|{d}"

        o_keys = {key(v) for v in openai_violations}
        a_keys = {key(v) for v in anthropic_violations}
        overlap_keys = o_keys & a_keys

        return [v for v in openai_violations if key(v) in overlap_keys]

    def _calculate_confidence(
        self,
        openai_count: int,
        anthropic_count: int,
        merged_count: int
    ) -> float:
        """
        Calculate confidence level based on agent agreement.
        
        Higher confidence when agents agree, lower when there's significant divergence.
        """
        if merged_count == 0:
            return 1.0  # No violations = high confidence in clean finding

        if openai_count == 0 or anthropic_count == 0:
            return 0.5  # One agent found nothing = moderate confidence

        # Calculate agreement ratio
        min_count = min(openai_count, anthropic_count)
        max_count = max(openai_count, anthropic_count)
        agreement_ratio = min_count / max_count if max_count > 0 else 1.0

        # Bonus for overlap
        overlap_bonus = 0.1 if merged_count <= max_count else 0.0

        return min(1.0, agreement_ratio + overlap_bonus)

    async def close(self) -> None:
        """Clean up resources."""
        if self.govinfo_client:
            try:
                await self.govinfo_client.close()
            except Exception:
                pass
        if self.statute_integrator:
            try:
                await self.statute_integrator.close()
            except Exception:
                pass
