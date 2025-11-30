"""
JLAW Phase 7: Comprehensive Reporting Engine
===========================================

Advanced reporting and visualization system for forensic investigations.

Components:
- ReportingEngine: Master report orchestrator
- PDFReportGenerator: Professional PDF reports with templates
- InteractiveDashboard: Web-based interactive dashboards
- EvidencePackager: Evidence compilation and export
- CustodyReporter: Chain of custody documentation
- ExecutiveSummaryGenerator: High-level executive summaries
"""

try:
    from .reporting_engine import ReportingEngine
    from .pdf_generator import PDFReportGenerator
    from .custody_reporter import CustodyReporter
    from .dashboard import InteractiveDashboard
    from .evidence_packager import EvidencePackager
    from .executive_summary import ExecutiveSummaryGenerator, ExecutiveSummary
    
    # Aliases for backward compatibility
    ChainOfCustodyReporter = CustodyReporter
    
except ImportError as e:
    # Fallback imports
    ReportingEngine = None
    PDFReportGenerator = None
    CustodyReporter = None
    InteractiveDashboard = None
    EvidencePackager = None
    ExecutiveSummaryGenerator = None
    ExecutiveSummary = None
    ChainOfCustodyReporter = None

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

