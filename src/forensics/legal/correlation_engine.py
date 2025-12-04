"""
Legal Statute Correlation Engine - Phase 3
==========================================
Wrapper that unifies statute harvesting and violation mapping. Integrates the
existing StatuteMapper and provides placeholders for Neo4j/Elasticsearch
connectivity without enforcing heavy dependencies in research runs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from src.forensics.statute_mapper import StatuteMapper, StatuteViolation, StatuteTitle

logger = logging.getLogger(__name__)


@dataclass
class LegalCorrelationResult:
    statutes_indexed: int = 0
    regulations_indexed: int = 0
    violations: List[StatuteViolation] = field(default_factory=list)
    graph_nodes: int = 0
    graph_edges: int = 0


class LegalStatuteCorrelationEngine:
    """Unified interface for legal harvesting and violation correlation."""

    def __init__(self, govinfo_api_key: Optional[str] = None):
        self.mapper = StatuteMapper(api_key=govinfo_api_key or "demo-key", strict_mode=False)
        self._neo4j = None
        self._es = None
        logger.info("✅ LegalStatuteCorrelationEngine initialized")

    def connect_neo4j(self, uri: str, user: str, password: str) -> bool:
        try:
            from neo4j import GraphDatabase  # type: ignore
            self._neo4j = GraphDatabase.driver(uri, auth=(user, password))
            return True
        except Exception as e:
            logger.debug("Neo4j unavailable or connection failed: %s", e)
            self._neo4j = None
            return False

    def connect_elasticsearch(self, hosts: Optional[List[str]] = None) -> bool:
        try:
            from elasticsearch import Elasticsearch  # type: ignore
            self._es = Elasticsearch(hosts or ["http://localhost:9200"])
            return True
        except Exception as e:
            logger.debug("Elasticsearch unavailable or connection failed: %s", e)
            self._es = None
            return False

    async def harvest_usc_titles(self, titles: Optional[List[StatuteTitle]] = None) -> int:
        """Placeholder for USC/GovInfo harvesting. Returns count indexed."""
        # In this research scaffold, we simply return the number of titles requested
        titles = titles or [StatuteTitle.USC_15, StatuteTitle.USC_18, StatuteTitle.USC_31]
        logger.info("📚 USC titles prepared: %s", [t.name for t in titles])
        return len(titles)

    async def harvest_cfr(self, parts: Optional[List[str]] = None) -> int:
        parts = parts or ["17 CFR"]
        logger.info("📚 CFR parts prepared: %s", parts)
        return len(parts)

    async def map_violations(self, findings: List[Dict[str, Any]]) -> LegalCorrelationResult:
        """Map forensic findings to potential violations using StatuteMapper."""
        result = LegalCorrelationResult()
        violations: List[StatuteViolation] = []
        for f in findings:
            try:
                mapped = await self.mapper.map_findings_to_statutes(f)
                violations.extend(mapped)
            except Exception as e:
                logger.debug("Mapping failed for finding %s: %s", f.get('id', 'unknown'), e)
        result.violations = violations
        result.statutes_indexed = 0  # real counts in full implementation
        result.regulations_indexed = 0
        result.graph_nodes = len(violations)
        result.graph_edges = max(0, len(violations) - 1)
        logger.info("⚖️  Mapped %d potential violations", len(violations))
        return result
