"""
DocsGPT Integration Module
==========================

Provides advanced document parsing and semantic search for SEC forensic analysis.

Components:
- DocumentParser: Multi-format document parsing (PDF, HTML, XBRL, etc.)
- SECDocumentAnalyzer: SEC-specific filing analysis
- FAISSVectorStore: Vector storage and similarity search
- SECVectorSearchEngine: Semantic search across filings
"""

from .document_parser import (
    DocumentParser,
    SECDocumentAnalyzer,
    DocumentFormat,
    SECFilingType,
    ParsedDocument,
    DocumentChunk,
    ChunkingStrategy
)

from .vector_store import (
    FAISSVectorStore,
    SECVectorSearchEngine,
    EmbeddingGenerator,
    VectorDocument,
    SearchResult
)

__all__ = [
    # Parser classes
    'DocumentParser',
    'SECDocumentAnalyzer',
    'DocumentFormat',
    'SECFilingType',
    'ParsedDocument',
    'DocumentChunk',
    'ChunkingStrategy',
    
    # Vector store classes
    'FAISSVectorStore',
    'SECVectorSearchEngine',
    'EmbeddingGenerator',
    'VectorDocument',
    'SearchResult'
]

