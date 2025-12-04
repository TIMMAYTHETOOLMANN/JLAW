"""
Enhanced Document Parsing Module - Phase 1
==========================================
Advanced multi-modal document processing with forensic precision
"""

from .document_processor import EnhancedDocumentProcessor
from .table_extractor import ForensicTableExtractor
from .financial_parser import FinancialDataParser
from .metadata_extractor import MetadataEnhancer
from .ocr_cascade import OCRCascade
from .universal_document_processor import UniversalDocumentProcessor, ProcessingResult

# Aliases for blueprint compatibility
DocumentProcessor = EnhancedDocumentProcessor
FinancialParser = FinancialDataParser

__all__ = [
    'EnhancedDocumentProcessor',
    'DocumentProcessor',
    'ForensicTableExtractor',
    'FinancialDataParser',
    'FinancialParser',
    'MetadataEnhancer',
    'OCRCascade',
    'UniversalDocumentProcessor',
    'ProcessingResult'
]

