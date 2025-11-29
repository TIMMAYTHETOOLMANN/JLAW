"""Forensic analysis system with NIST-compliant cryptographic integrity."""

__version__ = "1.0.0"

from src.forensics.sec_edgar_analyzer import SECForensicAnalyzer, FilingAnalysis
from src.forensics.statute_mapper import StatuteMapper, StatuteViolation, StatuteTitle
from src.forensics.api_resilience import (
    CircuitBreaker, CircuitBreakerConfig, CircuitState,
    ResilientAPIClient, RetryConfig, FailureType,
    ExponentialBackoff, QueueManager,
    CircuitBreakerOpenError, MaxRetriesExceededError
)
from src.forensics.immutable_storage import (
    ImmutableStorage, StorageConfig, AppendOnlyLog
)
from src.forensics.forensic_orchestrator import (
    ForensicOrchestrator, ForensicCase, InvestigationStatus
)
from src.forensics.ml_fraud_detector import (
    AdvancedFraudDetector, FraudPrediction,
    FinancialFeatureExtractor, TextFeatureExtractor, TemporalFeatureExtractor
)
from src.forensics.sec_forensic_extraction_system import (
    UniversalDocumentExtractor, ForensicSECDocumentAnalyzer,
    ExtractionResult, DocumentFormat,
    ForensicSECAnalyzer, EnhancedDocumentFormat,
    ComprehensiveExtractionResult, SECPatternMatch
)
from src.forensics.multi_pass_compliance_analyzer import (
    MultiPassComplianceAnalyzer, ComplianceViolation,
    ComplianceAnalysisResult, ComplianceSeverity, RiskLevel
)
from src.forensics.nist_integrated_compliance_analyzer import (
    NISTIntegratedComplianceAnalyzer, XBRLParser, TransformerNLP,
    XGBoostAnomalyDetector, SECBulkDataFeed, CachedEDGARPipeline,
    IndustryPeerComparator, WhistleblowerEvidenceMatcher, ForensicAnalysisReport,
    XBRLFinancialData, PeerComparisonResult, WhistleblowerMatch,
    TemporalConsistencyResult
)
from src.forensics.forensic_statutory_mapper import (
    ForensicStatutoryMapper, StatuteJurisdiction, ViolationSeverity,
    StatuteReference, ForensicIndicatorResult, StatuteViolationMatch,
    ComprehensiveStatutoryAnalysis
)
from src.forensics.linguistic_deception_analyzer import (
    LinguisticDeceptionAnalyzer, DeceptionType, LinguisticCategory,
    CognitiveComplexityMetrics, PsychologicalDistancingMetrics,
    TemporalIndicators, ObfuscationMetrics, EmotionalToneMetrics,
    NarrativeStructureMetrics, DeceptionAnalysisResult
)
from src.forensics.temporal_forensic_reconciliation import (
    TemporalForensicReconciliation, ReconciliationSeverity, RestatementType,
    RatioAnomalyType, ReconciliationTest, RestatementEvent,
    RatioAnomaly, TemporalForensicAnalysis
)
from src.forensics.forensic_evidence_authenticator import (
    ForensicEvidenceAuthenticator, EvidenceType, AuthenticationMethod,
    HearsayException, ChainOfCustody, AuthenticationResult
)
from src.forensics.quantitative_forensic_analyzer import (
    QuantitativeForensicAnalyzer, FraudClassification, FinancialHealthStatus,
    BenfordAnalysis, AltmanZScore, PiotroskiFScore, ComprehensiveForensicScore
)
from src.forensics.whistleblower_evidence_correlator import (
    WhistleblowerEvidenceCorrelator, WhistleblowerProtection, ContradictionType,
    EvidenceStrength, WhistleblowerClaim, ContradictionMatch, CorrelationMatrix
)
from src.forensics.forensic_dossier_generator import (
    ForensicDossierGenerator, ForensicDossier, ExecutiveSummary,
    DetailedFindings, EvidentExhibits, LegalFramework,
    MaterialityLevel, ScienterStrength
)
from src.forensics.advanced_forensic_analytics import (
    SemanticContradictionGraph, EnhancedFinancialForensics,
    AdvancedForensicAnalyzer, ContradictionDetection,
    BeneishMScore, AdvancedForensicResult
)
from src.forensics.config_manager import (
    ConfigurationManager, SECConfig, GovInfoConfig, SystemConfig,
    get_config, reload_config
)

# Phase 4: Temporal Analysis & Timeline Reconstruction
from src.forensics.temporal_analysis import (
    ForensicTimelineReconstructor, TemporalEvent, ForensicTimeline,
    TemporalContradiction, TemporalAnomaly, NarrativeSequence,
    EventCorrelator, EventCorrelation, CausalChain,
    TemporalParser, TemporalExtractor, DateExtractionResult,
    TemporalAnomalyDetector, GapAnomaly, ClusterAnomaly, PatternBreak
)

# Phase 5: Decision Engine & Prosecution Path Builder
from src.forensics.decision_engine import (
    ProsecutionPathBuilder, ProsecutionPath, DecisionPath, ProsecutionStrategy,
    ForensicEvidenceEvaluator, EvaluatedEvidence, Admissibility, EvidenceStrength,
    DecisionTree, DecisionNode, DecisionBranch, PathScore,
    Evidence, EvidenceType, ProsecutionObjective, EnforcementAction
)

# Phase 6: Advanced Contradiction Detection
from src.forensics.contradiction_detection import (
    OmniscientContradictionDetector, ContradictionReport, Contradiction,
    ContradictionNetwork, ContradictionType, Severity
)

# Phase 7: Comprehensive Reporting & Visualization
# NOTE: Reporting module being refactored - temporarily disabled
# from src.forensics.reporting import (
#     ProsecutionReportGenerator, ProsecutionPackage, ExecutiveSummary,
#     VisualizationEngine, Visualizations,
#     RegulatoryFormGenerator, SECFormTCR, DOJReferral,
#     HTMLDashboardGenerator, DashboardConfig
# )

# Phase 8: Master Forensic Controller & Integration
# NOTE: Orchestrator module imports temporarily disabled
# from src.forensics.orchestrator import (
#     MasterForensicController, InvestigationConfig, InvestigationResult,
#     SystemConfiguration, IntegrationTestSuite, SystemHealth
# )

# Phase 9: Deployment & Optimization
# NOTE: Deployment module imports temporarily disabled
# from src.forensics.deployment import (
#     DeploymentManager, DeploymentConfig, DeploymentStatus,
#     SystemHealthCheck, HealthStatus, ComponentHealth,
#     SystemOptimizer, OptimizationProfile, PerformanceMetrics
# )

# Multi-Agent AI Components (Optional - require additional SDKs)
try:
    from src.forensics.agent_sec_analyzer import AgentSECForensicAnalyzer
except ImportError:
    AgentSECForensicAnalyzer = None

try:
    from src.forensics.anthropic_agent_analyzer import AnthropicAgentAnalyzer
except ImportError:
    AnthropicAgentAnalyzer = None

try:
    from src.forensics.multipass_strategy import MultiPassAnalysisStrategy, MultiPassResult
except ImportError:
    MultiPassAnalysisStrategy = None
    MultiPassResult = None

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
    "MultiPassResult"
]
