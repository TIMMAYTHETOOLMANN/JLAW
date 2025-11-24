"""
Universal SEC Extractor - Backward compatibility module.
Re-exports from sec_forensic_extraction_system for legacy imports.
"""

from src.forensics.sec_forensic_extraction_system import (
    DocumentFormat,
    ExtractionResult,
    FinancialMetrics,
    UniversalDocumentExtractor,
    ForensicSECDocumentAnalyzer,
    UniversalSECExtractor,
)

__all__ = [
    'DocumentFormat',
    'ExtractionResult',
    'FinancialMetrics',
    'UniversalDocumentExtractor',
    'ForensicSECDocumentAnalyzer',
    'UniversalSECExtractor',
]
