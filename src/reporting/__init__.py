"""Reporting Module - Court-ready forensic report generation.

This module provides DOJ-level comprehensive forensic reporting capabilities:

- DOJReportGenerator: Generates prosecution-ready reports with per-filing breakdowns
- ForensicPDFGenerator: PDF report generation using ReportLab
- CourtPDFGenerator: FRE 902(13)/(14) compliant court documents

Data Models:
- ViolationEvidence: Complete evidence package for a single violation
- FilingAnalysisReport: Per-filing detailed analysis report
- ForensicReportSummary: Executive summary and statistics
- ChainOfCustodyRecord: Evidence integrity documentation
"""

from .pdf_generator import ForensicPDFGenerator
from .court_pdf_generator import (
    CourtPDFGenerator,
    CaseCaption,
    ViolationDetail,
    Exhibit,
    EvidenceItem
)
from .models import (
    SeverityLevel,
    ProsecutorialMerit,
    AgentSource,
    StatutoryReference,
    ExactQuote,
    DamageEstimate,
    RedFlag,
    ViolationEvidence,
    DualAgentConsensus,
    FilingAnalysisReport,
    SubagentFinding,
    ChainOfCustodyRecord,
    ForensicReportSummary,
)
from .doj_report_generator import (
    DOJReportGenerator,
    create_violation_evidence,
)

__all__ = [
    # PDF Generators
    'ForensicPDFGenerator',
    'CourtPDFGenerator',
    'DOJReportGenerator',
    
    # Court PDF types
    'CaseCaption',
    'ViolationDetail',
    'Exhibit',
    'EvidenceItem',
    
    # DOJ Report Models
    'SeverityLevel',
    'ProsecutorialMerit',
    'AgentSource',
    'StatutoryReference',
    'ExactQuote',
    'DamageEstimate',
    'RedFlag',
    'ViolationEvidence',
    'DualAgentConsensus',
    'FilingAnalysisReport',
    'SubagentFinding',
    'ChainOfCustodyRecord',
    'ForensicReportSummary',
    
    # Factory functions
    'create_violation_evidence',
]
