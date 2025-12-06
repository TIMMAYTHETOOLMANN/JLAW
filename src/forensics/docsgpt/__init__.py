"""
DocsGPT Integration Module for JLAW SEC Forensic System
========================================================

This module integrates DocsGPT's advanced document parsing, chunking,
and embedding capabilities with JLAW's forensic analysis infrastructure.

Key Components:
- ParserFactory: Unified document parsing for all SEC filing formats
- SECChunker: Intelligent chunking optimized for SEC documents
- Adapters: Format-specific parsing adapters

Usage:
    from src.forensics.docsgpt import ParserFactory, SECChunker
    
    parser = ParserFactory.get_parser("10-K.pdf")
    documents = parser.parse()
    chunks = SECChunker().chunk(documents)
"""

from .parser_factory import ParserFactory
from .sec_chunking import SECChunker, SECChunkingStrategy
from .config import DocsGPTConfig

__all__ = [
    'ParserFactory',
    'SECChunker',
    'SECChunkingStrategy',
    'DocsGPTConfig',
]

__version__ = "1.0.0"

