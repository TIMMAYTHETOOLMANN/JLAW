"""
JLAW Phase 7: Comprehensive Reporting Engine
===========================================

Advanced reporting and visualization system for forensic investigations.

Components:
- ReportingEngine: Master report orchestrator
- PDFReportGenerator: Professional PDF reports with templates
- InteractiveDashboard: Web-based interactive dashboards
- EvidencePackager: Evidence compilation and export
- ChainOfCustodyReporter: Chain of custody documentation
- ExecutiveSummaryGenerator: High-level executive summaries
"""

try:
    from .reporting_engine import (
        ReportingEngine,
        ExecutiveSummary,
        EvidencePackager,
        CustodyReporter
    )
    from .pdf_generator import PDFReportGenerator
    
    # Aliases for backward compatibility
    ExecutiveSummaryGenerator = ExecutiveSummary
    ChainOfCustodyReporter = CustodyReporter
    InteractiveDashboard = ReportingEngine
except ImportError as e:
    # Fallback imports
    ReportingEngine = None
    PDFReportGenerator = None

__all__ = [
    'ReportingEngine',
    'PDFReportGenerator',
    'InteractiveDashboard',
    'EvidencePackager',
    'CustodyReporter',
    'ChainOfCustodyReporter',
    'ExecutiveSummary',
    'ExecutiveSummaryGenerator',
]

__version__ = '7.0.0'
__phase__ = 7

