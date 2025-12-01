"""Forensic analysis system with NIST-compliant cryptographic integrity."""

__version__ = "1.0.0"

from .sec_edgar_analyzer import SECForensicAnalyzer, FilingAnalysis
from .statute_mapper import StatuteMapper, StatuteViolation, StatuteTitle
from .api_resilience import (
    CircuitBreaker, CircuitBreakerConfig, CircuitState,
    ResilientAPIClient, RetryConfig, FailureType,
    ExponentialBackoff, QueueManager,
    CircuitBreakerOpenError, MaxRetriesExceededError
)
from .immutable_storage import (
    ImmutableStorage, StorageConfig, AppendOnlyLog
)
from .forensic_orchestrator import (
    ForensicOrchestrator, ForensicCase, InvestigationStatus
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

# Phase 4: Temporal Analysis & Timeline Reconstruction
from .temporal_analysis import (
    ForensicTimelineReconstructor, TemporalEvent, ForensicTimeline,
    TemporalContradiction, TemporalAnomaly, NarrativeSequence,
    EventCorrelator, EventCorrelation, CausalChain,
    TemporalParser, TemporalExtractor, DateExtractionResult,
    TemporalAnomalyDetector, GapAnomaly, ClusterAnomaly, PatternBreak
)

# Phase 5: Decision Engine & Prosecution Path Builder
from .decision_engine import (
    ProsecutionPathBuilder, ProsecutionPath, DecisionPath, ProsecutionStrategy,
    ForensicEvidenceEvaluator, EvaluatedEvidence, Admissibility, EvidenceStrength,
    DecisionTree, DecisionNode, DecisionBranch, PathScore,
    Evidence, EvidenceType, ProsecutionObjective, EnforcementAction
)

# Phase 6: Advanced Contradiction Detection
from .contradiction_detection import (
    OmniscientContradictionDetector, ContradictionReport, Contradiction,
    ContradictionNetwork, ContradictionType, Severity
)

# Phase 7: Comprehensive Reporting & Visualization
# NOTE: Reporting module being refactored - temporarily disabled
# from .reporting import (
#     ProsecutionReportGenerator, ProsecutionPackage, ExecutiveSummary,
#     VisualizationEngine, Visualizations,
#     RegulatoryFormGenerator, SECFormTCR, DOJReferral,
#     HTMLDashboardGenerator, DashboardConfig
# )

# Phase 8: Master Forensic Controller & Integration
# NOTE: Orchestrator module imports temporarily disabled
# from .orchestrator import (
#     MasterForensicController, InvestigationConfig, InvestigationResult,
#     SystemConfiguration, IntegrationTestSuite, SystemHealth
# )

# Phase 9: Deployment & Optimization
# NOTE: Deployment module imports temporarily disabled
# from .deployment import (
#     DeploymentManager, DeploymentConfig, DeploymentStatus,
#     SystemHealthCheck, HealthStatus, ComponentHealth,
#     SystemOptimizer, OptimizationProfile, PerformanceMetrics
# )

# Multi-Agent AI Components (Optional - require additional SDKs)
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

# Enhancement Modules: Entity Resolution & Narrative Analysis
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

__all__ = [
    "__version__",
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
