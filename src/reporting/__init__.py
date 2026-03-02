"""Reporting Module - Court-ready forensic report generation.

This module provides DOJ-level comprehensive forensic reporting capabilities:

- DOJReportGenerator: Generates prosecution-ready reports with per-filing breakdowns
- ForensicPDFGenerator: PDF report generation using ReportLab
- CourtPDFGenerator: FRE 902(13)/(14) compliant court documents
- EvidencePackager: Structures and packages evidence with cryptographic integrity
- StatutoryCitationEngine: GovInfo API integration for statutory references
- ChainOfCustodyLogger: Cryptographic chain of custody tracking

Data Models:
- ViolationEvidence: Complete evidence package for a single violation
- FilingAnalysisReport: Per-filing detailed analysis report
- ForensicReportSummary: Executive summary and statistics
- ChainOfCustodyRecord: Evidence integrity documentation

Constants:
- SeverityTier: Violation severity classification
- ViolationType: Comprehensive SEC violation types
- SEC_STATUTES: Built-in statutory reference database
"""

from .pdf_generator import ForensicPDFGenerator
from .visual_report_generator import ForensicVisualReportGenerator
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
from .constants import (
    SeverityTier,
    ViolationType,
    StatutoryInfo,
    SEC_STATUTES,
    VIOLATION_STATUTE_MAP,
    SEVERITY_PENALTY_MULTIPLIERS,
    REGULATORY_ROUTING,
    PROSECUTORIAL_MERIT_FACTORS,
    NIKE_2019_BASELINE,
    get_statute_for_violation,
    get_all_statutes_for_violation,
    calculate_penalty_range,
    determine_regulatory_routing,
)
from .evidence_packager import (
    EvidenceItem as EvidencePackageItem,
    EvidencePackage,
    EvidencePackager,
)
from .statutory_citation_engine import (
    GovInfoCitation,
    CitationCache,
    StatutoryCitationEngine,
    create_citation_engine,
)
from .chain_of_custody_logger import (
    CustodyAction,
    CustodyEventType,
    CustodyEvent,
    CustodyChain,
    ChainOfCustodyLogger,
    create_custody_logger,
)
from .investigative_article_generator import (
    InvestigativeArticleGenerator,
    InvestigativeArticle,
    ArticleSection,
)
from .public_discrepancy_engine import (
    PublicDiscrepancyEngine,
    DiscrepancyReport,
    Discrepancy,
    PublicStatement,
    SecDisclosure,
)
from .machine_log_generator import (
    MachineLogGenerator,
    MachineLog,
    ForensicLogEntry,
    ProvenanceChain,
)
from .investigation_bundle_generator import (
    InvestigationBundleGenerator,
    BundleManifest,
    GeneratedFile,
)

__all__ = [
    # PDF Generators
    'ForensicPDFGenerator',
    'ForensicVisualReportGenerator',
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
    
    # Constants
    'SeverityTier',
    'ViolationType',
    'StatutoryInfo',
    'SEC_STATUTES',
    'VIOLATION_STATUTE_MAP',
    'SEVERITY_PENALTY_MULTIPLIERS',
    'REGULATORY_ROUTING',
    'PROSECUTORIAL_MERIT_FACTORS',
    'NIKE_2019_BASELINE',
    
    # Evidence Packaging
    'EvidencePackageItem',
    'EvidencePackage',
    'EvidencePackager',
    
    # Statutory Citations
    'GovInfoCitation',
    'CitationCache',
    'StatutoryCitationEngine',
    
    # Chain of Custody
    'CustodyAction',
    'CustodyEventType',
    'CustodyEvent',
    'CustodyChain',
    'ChainOfCustodyLogger',

    # Factory functions
    'create_violation_evidence',
    'get_statute_for_violation',
    'get_all_statutes_for_violation',
    'calculate_penalty_range',
    'determine_regulatory_routing',
    'create_citation_engine',
    'create_custody_logger',

    # Investigative Article Generator
    'InvestigativeArticleGenerator',
    'InvestigativeArticle',
    'ArticleSection',

    # Public Discrepancy Engine
    'PublicDiscrepancyEngine',
    'DiscrepancyReport',
    'Discrepancy',
    'PublicStatement',
    'SecDisclosure',

    # Machine Log Generator
    'MachineLogGenerator',
    'MachineLog',
    'ForensicLogEntry',
    'ProvenanceChain',

    # Investigation Bundle Generator
    'InvestigationBundleGenerator',
    'BundleManifest',
    'GeneratedFile',
]
