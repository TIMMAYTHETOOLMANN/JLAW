"""
SEC EDGAR Integration Module
============================

Production-grade SEC EDGAR API client with comprehensive features:
- Rate limiting (9 req/sec with 60s cooldown on 403)
- Triple-hash integrity verification (SHA-256 + SHA3-512 + BLAKE2b)
- Document completeness validation
- Connection pooling and retry strategy
- CIK/accession number normalization
- Structured acquisition results
- Comprehensive SEC Data Resources integration

Key Components:
- edgar_client.SECEdgarClient: Main API client
- sec_data_resources.SECDataResourcesClient: Comprehensive SEC Data Resources client
- document_validator.SECDocumentValidator: Document validation engine
- rate_limiter.RateLimiter: Shared rate limiter with cooldown
- models: Data structures (AcquisitionResult, IntegrityHashes, etc.)
- utils: CIK/accession normalization utilities
- session_manager: HTTP session management

SEC Data Resources (https://www.sec.gov/data-research/sec-data-resources):
- Financial Statement Data Sets (quarterly XBRL-extracted data)
- Company Facts/Concept APIs (per-CIK XBRL data)
- Fails-to-Deliver Data (settlement statistics)
- Investment Adviser Data (IAPD/Form ADV)
- Mutual Fund Data (N-PORT holdings)
- Market Structure Data
- SEC Enforcement Actions
- EDGAR Full-Text Search
- Real-time RSS Feeds
"""

from .edgar_client import SECEdgarClient, FormType, SECFiling, XBRLFact
from .document_validator import SECDocumentValidator, DocumentType, ValidationResult
from .rate_limiter import RateLimiter, get_shared_rate_limiter
from .models import (
    AcquisitionResult,
    AcquisitionStatus,
    IntegrityHashes,
    XBRLContext,
    Form4TransactionCode,
    FORM4_TRANSACTION_CODES
)
from .utils import (
    normalize_cik,
    strip_cik_leading_zeros,
    format_accession_number,
    build_edgar_document_url,
    build_edgar_index_url,
    build_submissions_url,
    build_xbrl_companyfacts_url,
    extract_cik_from_url,
    validate_cik,
    validate_accession_number
)

# SEC Data Resources - Comprehensive SEC data access
from .sec_data_resources import (
    SECDataResourcesClient,
    SECDataEndpoint,
    FinancialStatementFact,
    FailsToDeliverRecord,
    InvestmentAdviser,
    MutualFundHolding,
    EnforcementAction,
    MarketStructureMetric,
    FullTextSearchResult,
    RSSFilingEntry,
    CrowdfundingOffering,
    FormDOffering,
    InsiderTransactionRecord,
    get_sec_data_client
)

# Cross-Analysis Engine - Dynamic research and multi-source correlation
from .cross_analysis_engine import (
    SECCrossAnalysisEngine,
    AnalysisType,
    AlertSeverity,
    ForensicAlert,
    DataAcquisitionReport,
    CrossAnalysisResult,
    run_forensic_analysis
)

__all__ = [
    # Main client
    'SECEdgarClient',
    'FormType',
    'SECFiling',
    'XBRLFact',
    
    # SEC Data Resources Client
    'SECDataResourcesClient',
    'SECDataEndpoint',
    'FinancialStatementFact',
    'FailsToDeliverRecord',
    'InvestmentAdviser',
    'MutualFundHolding',
    'EnforcementAction',
    'MarketStructureMetric',
    'FullTextSearchResult',
    'RSSFilingEntry',
    'CrowdfundingOffering',
    'FormDOffering',
    'InsiderTransactionRecord',
    'get_sec_data_client',
    
    # Cross-Analysis Engine
    'SECCrossAnalysisEngine',
    'AnalysisType',
    'AlertSeverity',
    'ForensicAlert',
    'DataAcquisitionReport',
    'CrossAnalysisResult',
    'run_forensic_analysis',
    
    # Document validation
    'SECDocumentValidator',
    'DocumentType',
    'ValidationResult',
    
    # Rate limiting
    'RateLimiter',
    'get_shared_rate_limiter',
    
    # Models
    'AcquisitionResult',
    'AcquisitionStatus',
    'IntegrityHashes',
    'XBRLContext',
    'Form4TransactionCode',
    'FORM4_TRANSACTION_CODES',
    
    # Utilities
    'normalize_cik',
    'strip_cik_leading_zeros',
    'format_accession_number',
    'build_edgar_document_url',
    'build_edgar_index_url',
    'build_submissions_url',
    'build_xbrl_companyfacts_url',
    'extract_cik_from_url',
    'validate_cik',
    'validate_accession_number',
]
