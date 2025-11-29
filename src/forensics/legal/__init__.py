"""
JLAW Phase 3: Legal Statute Correlation Engine
==============================================

Advanced legal intelligence system for forensic investigations.

Components:
- LegalStatuteCorrelationEngine: Master legal orchestrator
- GovInfoAPIClient: Federal legal document retrieval
- Neo4jKnowledgeGraph: Legal relationship database
- ViolationDetector: Multi-strategy violation detection
- ElasticsearchLegalIndex: Full-text legal search
- CitationParser: Legal citation extraction and validation
- PrecedentAnalyzer: Case law pattern analysis
"""

from .legal_engine import LegalStatuteCorrelationEngine
from .govinfo_client import GovInfoAPIClient
from ..neo4j_knowledge_graph import Neo4jKnowledgeGraph
from .violation_detector import ViolationDetector
from .legal_search import ElasticsearchLegalIndex

# Optional - requires eyecite
try:
    from .citation_parser import CitationParser
    _citation_available = True
except ImportError:
    CitationParser = None
    _citation_available = False

__all__ = [
    'LegalStatuteCorrelationEngine',
    'GovInfoAPIClient',
    'Neo4jKnowledgeGraph',
    'ViolationDetector',
    'ElasticsearchLegalIndex',
]

if _citation_available:
    __all__.append('CitationParser')

__version__ = '3.0.0'
__phase__ = 3

