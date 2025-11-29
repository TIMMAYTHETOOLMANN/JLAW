"""
Legal Statute Correlation Engine - Master Legal Orchestrator
==========================================================

Unified legal intelligence system coordinating:
- GovInfo API: Federal legal document retrieval
- Neo4j Graph: Legal relationship modeling
- ViolationDetector: Multi-strategy violation detection
- Elasticsearch: Full-text legal search

Workflow:
1. Harvest legal corpus (USC/CFR)
2. Build knowledge graph
3. Index for search
4. Detect violations in evidence
5. Map violations to statutes
6. Generate legal analysis report
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import json

from .govinfo_client import GovInfoAPIClient, LegalDocument, USCTitle
from ..neo4j_knowledge_graph import Neo4jKnowledgeGraph, GraphNode
from .violation_detector import ViolationDetector, DetectedViolation
from .legal_search import ElasticsearchLegalIndex, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class LegalAnalysisReport:
    """Comprehensive legal analysis report"""
    target: str
    analysis_date: datetime
    
    # Detected violations
    violations: List[DetectedViolation]
    violations_by_statute: Dict[str, List[DetectedViolation]]
    violations_by_severity: Dict[str, List[DetectedViolation]]
    
    # Related statutes
    applicable_statutes: List[Dict[str, Any]]
    implementing_regulations: List[Dict[str, Any]]
    precedent_cases: List[Dict[str, Any]]
    
    # Statistics
    total_violations: int
    high_severity_count: int
    average_confidence: float
    
    # Legal corpus stats
    statutes_analyzed: int
    regulations_analyzed: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'target': self.target,
            'analysis_date': self.analysis_date.isoformat(),
            'summary': {
                'total_violations': self.total_violations,
                'high_severity': self.high_severity_count,
                'average_confidence': self.average_confidence
            },
            'violations': [v.to_dict() for v in self.violations],
            'by_statute': {
                k: [v.to_dict() for v in vals]
                for k, vals in self.violations_by_statute.items()
            },
            'by_severity': {
                k: len(vals)
                for k, vals in self.violations_by_severity.items()
            },
            'applicable_statutes': self.applicable_statutes,
            'implementing_regulations': self.implementing_regulations,
            'precedent_cases': self.precedent_cases,
            'corpus_stats': {
                'statutes_analyzed': self.statutes_analyzed,
                'regulations_analyzed': self.regulations_analyzed
            }
        }


class LegalStatuteCorrelationEngine:
    """
    Master legal intelligence orchestrator
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Legal Statute Correlation Engine
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config or {}
        
        # Initialize components
        self.govinfo_client: Optional[GovInfoAPIClient] = None
        self.knowledge_graph = Neo4jKnowledgeGraph()
        self.violation_detector = ViolationDetector()
        self.legal_index = ElasticsearchLegalIndex()
        
        # Legal corpus cache
        self._usc_titles: Dict[int, USCTitle] = {}
        self._cfr_titles: Dict[int, Dict[str, LegalDocument]] = {}
        
        # Statistics
        self.stats = {
            'corpus_harvested': False,
            'statutes_indexed': 0,
            'regulations_indexed': 0,
            'graph_nodes': 0,
            'analyses_performed': 0
        }
        
        logger.info("⚖️ Legal Statute Correlation Engine initialized")
    
    async def initialize(self, govinfo_api_key: Optional[str] = None):
        """Initialize async components"""
        api_key = govinfo_api_key or self.config.get('govinfo_api_key')
        self.govinfo_client = GovInfoAPIClient(api_key=api_key)
        
        await self.govinfo_client.__aenter__()
        
        logger.info("✓ Engine initialized with GovInfo API client")
    
    async def shutdown(self):
        """Cleanup async resources"""
        if self.govinfo_client:
            await self.govinfo_client.__aexit__(None, None, None)
    
    async def harvest_legal_corpus(
        self,
        titles: Optional[List[int]] = None,
        include_cfr: bool = True
    ):
        """
        Harvest federal legal corpus from GovInfo
        
        Args:
            titles: List of USC titles to harvest (None = priority titles)
            include_cfr: Whether to include CFR regulations
        """
        logger.info("🌾 Beginning legal corpus harvest...")
        
        if not self.govinfo_client:
            await self.initialize()
        
        # Harvest USC titles
        if titles:
            for title_num in titles:
                title = await self.govinfo_client.get_usc_title(title_num)
                self._usc_titles[title_num] = title
                
                # Index statutes
                for section, doc in title.sections.items():
                    self._index_statute(doc)
                
                # Add to knowledge graph
                for section, doc in title.sections.items():
                    self._add_statute_to_graph(doc)
                
                await asyncio.sleep(1)  # Rate limiting
        else:
            # Harvest priority titles
            self._usc_titles = await self.govinfo_client.harvest_priority_titles()
            
            # Index and graph all
            for title in self._usc_titles.values():
                for section, doc in title.sections.items():
                    self._index_statute(doc)
                    self._add_statute_to_graph(doc)
        
        # Harvest CFR if requested
        if include_cfr:
            self._cfr_titles = await self.govinfo_client.harvest_priority_cfr()
            
            # Index regulations
            for title_num, sections in self._cfr_titles.items():
                for section_num, doc in sections.items():
                    self._index_regulation(doc)
                    self._add_regulation_to_graph(doc)
        
        self.stats['corpus_harvested'] = True
        self.stats['statutes_indexed'] = sum(
            len(t.sections) for t in self._usc_titles.values()
        )
        self.stats['regulations_indexed'] = sum(
            len(sections) for sections in self._cfr_titles.values()
        )
        self.stats['graph_nodes'] = len(self.knowledge_graph._nodes)
        
        logger.info(f"✓ Corpus harvest complete:")
        logger.info(f"  - USC titles: {len(self._usc_titles)}")
        logger.info(f"  - Statutes: {self.stats['statutes_indexed']}")
        logger.info(f"  - CFR titles: {len(self._cfr_titles)}")
        logger.info(f"  - Regulations: {self.stats['regulations_indexed']}")
        logger.info(f"  - Graph nodes: {self.stats['graph_nodes']}")
    
    def _index_statute(self, doc: LegalDocument):
        """Index statute in Elasticsearch"""
        citation = f"{doc.title_number} USC § {doc.section}"
        
        self.legal_index.index_document(
            document_id=f"usc_{doc.title_number}_{doc.section}",
            document_type="statute",
            title=f"{citation} - {doc.title}",
            full_text=doc.full_text,
            metadata={
                'title_number': doc.title_number,
                'section': doc.section,
                'citation': citation
            }
        )
    
    def _index_regulation(self, doc: LegalDocument):
        """Index regulation in Elasticsearch"""
        citation = f"{doc.title_number} CFR § {doc.section}"
        
        self.legal_index.index_document(
            document_id=f"cfr_{doc.title_number}_{doc.section}",
            document_type="regulation",
            title=f"{citation} - {doc.title}",
            full_text=doc.full_text,
            metadata={
                'cfr_title': doc.title_number,
                'section': doc.section,
                'citation': citation
            }
        )
    
    def _add_statute_to_graph(self, doc: LegalDocument):
        """Add statute to knowledge graph"""
        citation = f"{doc.title_number} USC § {doc.section}"
        
        self.knowledge_graph.create_statute_node(
            citation=citation,
            title=doc.title_number,
            section=doc.section,
            text=doc.full_text[:1000],  # Truncate for storage
            effective_date=doc.publication_date
        )
    
    def _add_regulation_to_graph(self, doc: LegalDocument):
        """Add regulation to knowledge graph"""
        citation = f"{doc.title_number} CFR § {doc.section}"
        
        # Extract part number from section if available
        part = doc.section.split('.')[0] if '.' in doc.section else doc.section
        
        self.knowledge_graph.create_regulation_node(
            cfr_citation=citation,
            cfr_title=doc.title_number,
            part=part,
            section=doc.section,
            text=doc.full_text[:1000]
        )
    
    async def analyze_evidence(
        self,
        evidence: str,
        source: str = "investigation",
        context: Optional[Dict[str, Any]] = None
    ) -> LegalAnalysisReport:
        """
        Analyze evidence for legal violations
        
        Args:
            evidence: Evidence text to analyze
            source: Source identifier
            context: Additional context
        
        Returns:
            Comprehensive legal analysis report
        """
        logger.info(f"⚖️ Analyzing evidence from: {source}")
        
        self.stats['analyses_performed'] += 1
        
        # Detect violations
        violations = self.violation_detector.detect_violations(
            text=evidence,
            source=source,
            context=context
        )
        
        logger.info(f"✓ Detected {len(violations)} potential violations")
        
        # Group violations
        by_statute = self._group_by_statute(violations)
        by_severity = self._group_by_severity(violations)
        
        # Get applicable statutes
        applicable_statutes = await self._get_applicable_statutes(violations)
        
        # Get implementing regulations
        implementing_regs = await self._get_implementing_regulations(violations)
        
        # Get precedent cases (placeholder)
        precedent_cases = []
        
        # Calculate statistics
        total = len(violations)
        high_severity = len(by_severity.get('high', []))
        avg_confidence = (
            sum(v.confidence for v in violations) / total
            if total > 0 else 0.0
        )
        
        # Create report
        report = LegalAnalysisReport(
            target=source,
            analysis_date=datetime.now(),
            violations=violations,
            violations_by_statute=by_statute,
            violations_by_severity=by_severity,
            applicable_statutes=applicable_statutes,
            implementing_regulations=implementing_regs,
            precedent_cases=precedent_cases,
            total_violations=total,
            high_severity_count=high_severity,
            average_confidence=avg_confidence,
            statutes_analyzed=len(applicable_statutes),
            regulations_analyzed=len(implementing_regs)
        )
        
        # Add violations to knowledge graph
        for violation in violations:
            self._add_violation_to_graph(violation)
        
        logger.info(f"✓ Analysis complete: {total} violations, {high_severity} high severity")
        
        return report
    
    def _group_by_statute(
        self,
        violations: List[DetectedViolation]
    ) -> Dict[str, List[DetectedViolation]]:
        """Group violations by statute"""
        from collections import defaultdict
        
        grouped = defaultdict(list)
        for v in violations:
            grouped[v.statute_citation].append(v)
        
        return dict(grouped)
    
    def _group_by_severity(
        self,
        violations: List[DetectedViolation]
    ) -> Dict[str, List[DetectedViolation]]:
        """Group violations by severity"""
        from collections import defaultdict
        
        grouped = defaultdict(list)
        for v in violations:
            grouped[v.severity].append(v)
        
        return dict(grouped)
    
    async def _get_applicable_statutes(
        self,
        violations: List[DetectedViolation]
    ) -> List[Dict[str, Any]]:
        """Get full statute text for violations"""
        statutes = []
        seen = set()
        
        for violation in violations:
            if violation.statute_citation in seen:
                continue
            
            seen.add(violation.statute_citation)
            
            # Search for statute
            results = self.legal_index.search_by_citation(violation.statute_citation)
            
            if results:
                statutes.append({
                    'citation': violation.statute_citation,
                    'title': results[0].title,
                    'text': results[0].full_text[:1000],
                    'violations_count': len([
                        v for v in violations
                        if v.statute_citation == violation.statute_citation
                    ])
                })
        
        return statutes
    
    async def _get_implementing_regulations(
        self,
        violations: List[DetectedViolation]
    ) -> List[Dict[str, Any]]:
        """Get regulations implementing violated statutes"""
        regulations = []
        
        # Placeholder - would query knowledge graph for IMPLEMENTS relationships
        
        return regulations
    
    def _add_violation_to_graph(self, violation: DetectedViolation):
        """Add detected violation to knowledge graph"""
        # Create violation node
        node_id = self.knowledge_graph.create_violation_node(
            violation_type=violation.violation_type,
            description=violation.description,
            severity=violation.severity,
            evidence={
                'text': violation.evidence_text[:500],
                'source': violation.evidence_source,
                'confidence': violation.confidence
            }
        )
        
        # Link to statute
        statute_node_id = f"statute:{violation.statute_citation}"
        self.knowledge_graph.create_relationship(
            from_node_id=node_id,
            to_node_id=statute_node_id,
            relationship_type='VIOLATES',
            properties={
                'confidence': violation.confidence,
                'detected_at': violation.detected_at.isoformat()
            }
        )
    
    def search_statutes(
        self,
        query: str,
        max_results: int = 50
    ) -> List[SearchResult]:
        """Search legal corpus"""
        return self.legal_index.search(
            query=query,
            document_types=['statute'],
            max_results=max_results
        )
    
    def search_regulations(
        self,
        query: str,
        max_results: int = 50
    ) -> List[SearchResult]:
        """Search regulations"""
        return self.legal_index.search(
            query=query,
            document_types=['regulation'],
            max_results=max_results
        )
    
    def get_statute_network(
        self,
        statute_citation: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Get complete network around a statute"""
        statute_id = f"statute:{statute_citation}"
        return self.knowledge_graph.get_statute_network(statute_id, depth=depth)
    
    def export_report(
        self,
        report: LegalAnalysisReport,
        format: str = 'json'
    ) -> str:
        """Export analysis report"""
        if format == 'json':
            return json.dumps(report.to_dict(), indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            **self.stats,
            'govinfo': self.govinfo_client.get_statistics() if self.govinfo_client else {},
            'detector': self.violation_detector.get_statistics(),
            'index': self.legal_index.get_statistics(),
            'graph': self.knowledge_graph.get_statistics()
        }


if __name__ == "__main__":
    # Demo usage
    async def demo():
        engine = LegalStatuteCorrelationEngine()
        
        await engine.initialize()
        
        # Harvest small corpus (demo)
        logger.info("Harvesting legal corpus (demo mode)...")
        # await engine.harvest_legal_corpus(titles=[18], include_cfr=False)
        
        # Analyze evidence
        test_evidence = """
        The company made false statements to federal investigators regarding
        offshore accounts. Additionally, insider trading was conducted based
        on material non-public information about pending acquisitions.
        """
        
        report = await engine.analyze_evidence(
            evidence=test_evidence,
            source="test_investigation"
        )
        
        print(f"\n📊 Legal Analysis Report:")
        print(f"  Total violations: {report.total_violations}")
        print(f"  High severity: {report.high_severity_count}")
        print(f"  Average confidence: {report.average_confidence:.2%}")
        print(f"\n  Violations by statute:")
        for statute, violations in report.violations_by_statute.items():
            print(f"    {statute}: {len(violations)} violation(s)")
        
        # Statistics
        stats = engine.get_statistics()
        print(f"\n  Engine statistics:")
        print(f"    Analyses performed: {stats['analyses_performed']}")
        
        await engine.shutdown()
    
    asyncio.run(demo())

