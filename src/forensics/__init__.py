"""
JLAW Forensic Analysis System
==============================

Comprehensive forensic analysis platform with NIST-compliant cryptographic integrity.

All 9 Phases:
- Phase 1: Document Parsing & Extraction
- Phase 2: Intelligence Gathering  
- Phase 3: Legal Statute Mapping
- Phase 4: Temporal Analysis & Timeline Reconstruction
- Phase 5: Decision Engine & Prosecution Path Builder
- Phase 6: Advanced Contradiction Detection
- Phase 7: Comprehensive Reporting & Visualization
- Phase 8: Master Forensic Controller & Integration
- Phase 9: Deployment & Optimization

Usage:
    from src.forensics import MasterForensicController, SystemConfiguration
    
    config = SystemConfiguration(phases_enabled=[1, 2, 3, 4, 5, 6, 7])
    controller = MasterForensicController()
    result = await controller.run_full_pipeline(document_path)
"""

__version__ = "1.0.0"

import logging

logger = logging.getLogger(__name__)

# =============================================================================
# PHASE 1-3: Core Analysis Modules
# =============================================================================

from .sec_edgar_analyzer import SECForensicAnalyzer, FilingAnalysis
from .sec_edgar_api import SECEdgarAPI, FilingMetadata, fetch_nike_2019_filings, get_filings_sync
from .statute_mapper import StatuteMapper, StatuteViolation, StatuteTitle
from .api_resilience import (
    CircuitBreaker, CircuitBreakerConfig, CircuitState,
    ResilientAPIClient, RetryConfig, FailureType,
    ExponentialBackoff, QueueManager,
    CircuitBreakerOpenError, MaxRetriesExceededError,
    TokenBucket, create_sec_rate_limiter, create_govinfo_rate_limiter
)
from .immutable_storage import (
    ImmutableStorage, StorageConfig, AppendOnlyLog
)
from .forensic_orchestrator import (
    ForensicOrchestrator, ForensicCase, InvestigationStatus
)
from .insider_form4_analyzer import (
    InsiderForm4Analyzer, Form4ViolationRecord
)
from .ml_fraud_detector import (
    AdvancedFraudDetector, FraudPrediction,
    FinancialFeatureExtractor, TextFeatureExtractor, TemporalFeatureExtractor
)
from .sec_forensic_extraction_system import (
    UniversalDocumentExtractor, ForensicSECDocumentAnalyzer,
    ExtractionResult, DocumentFormat,
    ForensicSECAnalyzer, EnhancedDocumentFormat,
    ComprehensiveExtractionResult, SECPatternMatch
)
from .multi_pass_compliance_analyzer import (
    MultiPassComplianceAnalyzer, ComplianceViolation,
    ComplianceAnalysisResult, ComplianceSeverity, RiskLevel
)
from .nist_integrated_compliance_analyzer import (
    NISTIntegratedComplianceAnalyzer, XBRLParser, TransformerNLP,
    XGBoostAnomalyDetector, SECBulkDataFeed, CachedEDGARPipeline,
    IndustryPeerComparator, WhistleblowerEvidenceMatcher, ForensicAnalysisReport,
    XBRLFinancialData, PeerComparisonResult, WhistleblowerMatch,
    TemporalConsistencyResult
)
from .forensic_statutory_mapper import (
    ForensicStatutoryMapper, StatuteJurisdiction, ViolationSeverity,
    StatuteReference, ForensicIndicatorResult, StatuteViolationMatch,
    ComprehensiveStatutoryAnalysis
)
from .linguistic_deception_analyzer import (
    LinguisticDeceptionAnalyzer, DeceptionType, LinguisticCategory,
    CognitiveComplexityMetrics, PsychologicalDistancingMetrics,
    TemporalIndicators, ObfuscationMetrics, EmotionalToneMetrics,
    NarrativeStructureMetrics, DeceptionAnalysisResult
)
from .temporal_forensic_reconciliation import (
    TemporalForensicReconciliation, ReconciliationSeverity, RestatementType,
    RatioAnomalyType, ReconciliationTest, RestatementEvent,
    RatioAnomaly, TemporalForensicAnalysis
)
from .forensic_evidence_authenticator import (
    ForensicEvidenceAuthenticator, EvidenceType, AuthenticationMethod,
    HearsayException, ChainOfCustody, AuthenticationResult
)
from .quantitative_forensic_analyzer import (
    QuantitativeForensicAnalyzer, FraudClassification, FinancialHealthStatus,
    BenfordAnalysis, AltmanZScore, PiotroskiFScore, ComprehensiveForensicScore
)
from .whistleblower_evidence_correlator import (
    WhistleblowerEvidenceCorrelator, WhistleblowerProtection, ContradictionType,
    EvidenceStrength, WhistleblowerClaim, ContradictionMatch, CorrelationMatrix
)
from .forensic_dossier_generator import (
    ForensicDossierGenerator, ForensicDossier, ExecutiveSummary,
    DetailedFindings, EvidentExhibits, LegalFramework,
    MaterialityLevel, ScienterStrength
)
from .advanced_forensic_analytics import (
    SemanticContradictionGraph, EnhancedFinancialForensics,
    AdvancedForensicAnalyzer, ContradictionDetection,
    BeneishMScore, AdvancedForensicResult
)
from .config_manager import (
    ConfigurationManager, SECConfig, GovInfoConfig, SystemConfig,
    get_config, reload_config
)

# =============================================================================
# PHASE 4: Temporal Analysis & Timeline Reconstruction
# =============================================================================

from .temporal_analysis import (
    ForensicTimelineReconstructor, TemporalEvent, ForensicTimeline,
    TemporalContradiction, TemporalAnomaly, NarrativeSequence,
    EventCorrelator, EventCorrelation, CausalChain,
    TemporalParser, TemporalExtractor, DateExtractionResult,
    TemporalAnomalyDetector, GapAnomaly, ClusterAnomaly, PatternBreak
)

# =============================================================================
# PHASE 5: Decision Engine & Prosecution Path Builder
# =============================================================================

from .decision_engine import (
    ProsecutionPathBuilder, ProsecutionPath, DecisionPath, ProsecutionStrategy,
    ForensicEvidenceEvaluator, EvaluatedEvidence, Admissibility, EvidenceStrength,
    DecisionTree, DecisionNode, DecisionBranch, PathScore,
    Evidence, EvidenceType, ProsecutionObjective, EnforcementAction
)

# =============================================================================
# PHASE 6: Advanced Contradiction Detection
# =============================================================================

from .contradiction_detection import (
    OmniscientContradictionDetector, ContradictionReport, Contradiction,
    ContradictionNetwork, ContradictionType, Severity
)

# =============================================================================
# PHASE 7: Comprehensive Reporting & Visualization (NOW ENABLED)
# =============================================================================

try:
    from .reporting import (
        ReportingEngine,
        ProsecutionReportGenerator,
        PDFReportGenerator,
        CustodyReporter,
        InteractiveDashboard,
        EvidencePackager,
        ExecutiveSummaryGenerator,
    )
    _reporting_available = True
    logger.info("Phase 7: Reporting module loaded successfully")
except ImportError as e:
    logger.warning(f"Phase 7: Reporting module partially available: {e}")
    ReportingEngine = None
    ProsecutionReportGenerator = None
    PDFReportGenerator = None
    CustodyReporter = None
    InteractiveDashboard = None
    EvidencePackager = None
    ExecutiveSummaryGenerator = None
    _reporting_available = False

# =============================================================================
# PHASE 8: Master Forensic Controller & Integration (NOW ENABLED)
# =============================================================================

try:
    from .orchestrator import (
        MasterForensicController,
        InvestigationConfig,
        InvestigationResult,
        FullSpectrumAnalysis,
        SystemConfiguration,
        PhaseConfig,
        OutputConfig,
        IntegrationTestSuite,
        TestResult,
        SystemHealth,
    )
    _orchestrator_available = True
    logger.info("Phase 8: Orchestrator module loaded successfully")
except ImportError as e:
    logger.warning(f"Phase 8: Orchestrator module partially available: {e}")
    MasterForensicController = None
    InvestigationConfig = None
    InvestigationResult = None
    FullSpectrumAnalysis = None
    SystemConfiguration = None
    PhaseConfig = None
    OutputConfig = None
    IntegrationTestSuite = None
    TestResult = None
    SystemHealth = None
    _orchestrator_available = False

# =============================================================================
# PHASE 9: Deployment & Optimization (NOW ENABLED)
# =============================================================================

try:
    from .deployment import (
        HealthChecker,
        DeploymentManager,
        SystemOptimizer,
    )
    _deployment_available = True
    logger.info("Phase 9: Deployment module loaded successfully")
except ImportError as e:
    logger.warning(f"Phase 9: Deployment module partially available: {e}")
    HealthChecker = None
    DeploymentManager = None
    SystemOptimizer = None
    _deployment_available = False

# =============================================================================
# Multi-Agent AI Components (Optional - require additional SDKs)
# =============================================================================
try:
    from .agent_sec_analyzer import AgentSECForensicAnalyzer
except ImportError:
    AgentSECForensicAnalyzer = None

try:
    from .anthropic_agent_analyzer import AnthropicAgentAnalyzer
except ImportError:
    AnthropicAgentAnalyzer = None

try:
    from .multipass_strategy import MultiPassAnalysisStrategy, MultiPassResult
except ImportError:
    MultiPassAnalysisStrategy = None
    MultiPassResult = None

# =============================================================================
# Enhancement Modules: Entity Resolution & Narrative Analysis
# =============================================================================

try:
    from .triangulation import (
        EntityResolver, EntityMention, ResolvedEntity, ResolutionResult,
        EntityType, SourceType
    )
    _triangulation_available = True
except ImportError:
    EntityResolver = None
    EntityMention = None
    ResolvedEntity = None
    ResolutionResult = None
    EntityType = None
    SourceType = None
    _triangulation_available = False

try:
    from .analysis import (
        NarrativeAnalyzer, NarrativeSegment, NarrativeShift,
        NarrativeAnalysisResult, LinguisticMetrics, ShiftSeverity, NarrativeCategory
    )
    _analysis_available = True
except ImportError:
    NarrativeAnalyzer = None
    NarrativeSegment = None
    NarrativeShift = None
    NarrativeAnalysisResult = None
    LinguisticMetrics = None
    ShiftSeverity = None
    NarrativeCategory = None
    _analysis_available = False

# =============================================================================
# System Status Function
# =============================================================================

def get_system_status() -> dict:
    """
    Get the operational status of all forensic system phases.

    Returns:
        Dictionary with phase availability and status information.
    """
    return {
        "version": __version__,
        "phases": {
            "phase_1_parsing": True,
            "phase_2_intelligence": True,
            "phase_3_legal": True,
            "phase_4_temporal": True,
            "phase_5_decision": True,
            "phase_6_contradiction": True,
            "phase_7_reporting": _reporting_available,
            "phase_8_orchestrator": _orchestrator_available,
            "phase_9_deployment": _deployment_available,
        },
        "enhancements": {
            "triangulation": _triangulation_available,
            "narrative_analysis": _analysis_available,
        },
        "all_phases_operational": all([
            _reporting_available,
            _orchestrator_available,
            _deployment_available,
        ]),
    }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "__version__",
    "get_system_status",
    # Core analyzers
    "SECForensicAnalyzer",
    "FilingAnalysis",
    "StatuteMapper",
    "StatuteViolation",
    "StatuteTitle",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "ResilientAPIClient",
    "RetryConfig",
    "FailureType",
    "ExponentialBackoff",
    "QueueManager",
    "CircuitBreakerOpenError",
    "MaxRetriesExceededError",
    "TokenBucket",
    "create_sec_rate_limiter",
    "create_govinfo_rate_limiter",
    "ImmutableStorage",
    "StorageConfig",
    "AppendOnlyLog",
    "ForensicOrchestrator",
    "ForensicCase",
    "InvestigationStatus",
    "AdvancedFraudDetector",
    "FraudPrediction",
    "FinancialFeatureExtractor",
    "TextFeatureExtractor",
    "TemporalFeatureExtractor",
    "UniversalDocumentExtractor",
    "ForensicSECDocumentAnalyzer",
    "ExtractionResult",
    "DocumentFormat",
    "ForensicSECAnalyzer",
    "EnhancedDocumentFormat",
    "ComprehensiveExtractionResult",
    "SECPatternMatch",
    "MultiPassComplianceAnalyzer",
    "ComplianceViolation",
    "ComplianceAnalysisResult",
    "ComplianceSeverity",
    "RiskLevel",
    "SemanticContradictionGraph",
    "EnhancedFinancialForensics",
    "AdvancedForensicAnalyzer",
    "ContradictionDetection",
    "BeneishMScore",
    "AdvancedForensicResult",
    "NISTIntegratedComplianceAnalyzer",
    "XBRLParser",
    "TransformerNLP",
    "XGBoostAnomalyDetector",
    "SECBulkDataFeed",
    "CachedEDGARPipeline",
    "IndustryPeerComparator",
    "WhistleblowerEvidenceMatcher",
    "ForensicAnalysisReport",
    "XBRLFinancialData",
    "PeerComparisonResult",
    "WhistleblowerMatch",
    "TemporalConsistencyResult",
    "ForensicStatutoryMapper",
    "StatuteJurisdiction",
    "ViolationSeverity",
    "StatuteReference",
    "ForensicIndicatorResult",
    "StatuteViolationMatch",
    "ComprehensiveStatutoryAnalysis",
    "LinguisticDeceptionAnalyzer",
    "DeceptionType",
    "LinguisticCategory",
    "CognitiveComplexityMetrics",
    "PsychologicalDistancingMetrics",
    "DeceptionAnalysisResult",
    "TemporalForensicReconciliation",
    "ReconciliationSeverity",
    "RestatementType",
    "RatioAnomalyType",
    "ReconciliationTest",
    "RestatementEvent",
    "RatioAnomaly",
    "TemporalForensicAnalysis",
    "ForensicEvidenceAuthenticator",
    "EvidenceType",
    "AuthenticationMethod",
    "HearsayException",
    "ChainOfCustody",
    "AuthenticationResult",
    "QuantitativeForensicAnalyzer",
    "FraudClassification",
    "FinancialHealthStatus",
    "BenfordAnalysis",
    "AltmanZScore",
    "PiotroskiFScore",
    "ComprehensiveForensicScore",
    "WhistleblowerEvidenceCorrelator",
    "WhistleblowerProtection",
    "ContradictionType",
    "EvidenceStrength",
    "WhistleblowerClaim",
    "ContradictionMatch",
    "CorrelationMatrix",
    "ForensicDossierGenerator",
    "ForensicDossier",
    "ExecutiveSummary",
    "DetailedFindings",
    "EvidentExhibits",
    "LegalFramework",
    "MaterialityLevel",
    "ScienterStrength",
    "ConfigurationManager",
    "SECConfig",
    "GovInfoConfig",
    "SystemConfig",
    "get_config",
    "reload_config",
    # Phase 4: Temporal
    "ForensicTimelineReconstructor",
    "TemporalEvent",
    "ForensicTimeline",
    "TemporalContradiction",
    "TemporalAnomaly",
    "NarrativeSequence",
    "EventCorrelator",
    "EventCorrelation",
    "CausalChain",
    "TemporalParser",
    "TemporalExtractor",
    "DateExtractionResult",
    "TemporalAnomalyDetector",
    "GapAnomaly",
    "ClusterAnomaly",
    "PatternBreak",
    # Phase 5: Decision Engine
    "ProsecutionPathBuilder",
    "ProsecutionPath",
    "DecisionPath",
    "ProsecutionStrategy",
    "ForensicEvidenceEvaluator",
    "EvaluatedEvidence",
    "Admissibility",
    "DecisionTree",
    "DecisionNode",
    "DecisionBranch",
    "PathScore",
    "Evidence",
    "ProsecutionObjective",
    "EnforcementAction",
    # Phase 6: Contradiction
    "OmniscientContradictionDetector",
    "ContradictionReport",
    "Contradiction",
    "ContradictionNetwork",
    "Severity",
    # Phase 7: Reporting
    "ReportingEngine",
    "ProsecutionReportGenerator",
    "PDFReportGenerator",
    "CustodyReporter",
    "InteractiveDashboard",
    "EvidencePackager",
    "ExecutiveSummaryGenerator",
    # Phase 8: Orchestrator
    "MasterForensicController",
    "InvestigationConfig",
    "InvestigationResult",
    "FullSpectrumAnalysis",
    "SystemConfiguration",
    "PhaseConfig",
    "OutputConfig",
    "IntegrationTestSuite",
    "TestResult",
    "SystemHealth",
    # Phase 9: Deployment
    "HealthChecker",
    "DeploymentManager",
    "SystemOptimizer",
    # Multi-agent
    "AgentSECForensicAnalyzer",
    "AnthropicAgentAnalyzer",
    "MultiPassAnalysisStrategy",
    "MultiPassResult",
    # Enhancement modules
    "EntityResolver",
    "EntityMention",
    "ResolvedEntity",
    "ResolutionResult",
    "EntityType",
    "SourceType",
    "NarrativeAnalyzer",
    "NarrativeSegment",
    "NarrativeShift",
    "NarrativeAnalysisResult",
    "LinguisticMetrics",
    "ShiftSeverity",
    "NarrativeCategory"
]
