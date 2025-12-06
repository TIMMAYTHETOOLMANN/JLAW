"""
Semantic Search Module for SEC Filings
=======================================

Provides advanced semantic search capabilities across SEC filings,
including cross-filing analysis, contradiction detection, and
temporal consistency checking.
"""

from .semantic_engine import SECSemanticSearchEngine, CrossFilingAnalyzer
from .contradiction_finder import SemanticContradictionFinder

__all__ = [
    'SECSemanticSearchEngine',
    'CrossFilingAnalyzer',
    'SemanticContradictionFinder',
]

