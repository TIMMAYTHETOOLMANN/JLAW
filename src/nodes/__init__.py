"""
JLAW Nodes Package - Unified Exports
====================================

Centralized exports for JLAW node modules.
Each node is responsible for specific SEC filing analysis and violation detection.

This module currently provides unified exports for Nodes 2-5:
- Node 2: DEF 14A Compensation Analysis
- Node 3: 10-Q Temporal Consistency Validation
- Node 4: 10-K SOX Certification Analysis
- Node 5: IRC §83 Tax Exposure Calculation

Additional nodes (1, 6-15) are available but not yet unified in this export structure.
"""

# Node 1: Form 4 Insider Trading Analysis
from .node1_form4.form4_parser import Form4Parser
from .node1_form4.short_swing_calc import ShortSwingCalculator
from .node1_form4.gift_pattern_detector import GiftPatternDetector

# Node 2: DEF 14A Compensation Analysis
from .node2_def14a import (
    DEF14ACompensationAnalyzer,
    CompensationAnalysisResult,
    NEOCompensation,
    SayOnPayVote,
    CEOPayRatio,
    GoldenParachute,
    RelatedPartyTransaction,
    ClawbackPolicy,
    CompensationType,
    AwardVestingType,
    SayOnPayOutcome,
    CompensationViolationType,
    CompensationViolation
)

# Node 3: 10-Q Temporal Consistency
from .node3_10q import (
    TemporalConsistencyValidator,
    QuarterlyMetrics,
    TemporalViolation,
    TemporalViolationType
)

# Node 4: 10-K SOX Certification
from .node4_10k_sox import (
    SOXCertificationAnalyzer,
    SOXViolationType,
    AuditOpinionType,
    ICFROpinionType,
    Section302Certification,
    Section906Certification,
    MaterialWeakness,
    AuditOpinion,
    SOXViolation
)

# Node 5: IRC §83 Tax Exposure
from .node5_irs import (
    IRC83TaxCalculator,
    IRC83ViolationType,
    EquityAwardType,
    GrantType,
    EquityGrant,
    Section83bElection,
    TaxExposure,
    EquityDisposition,
    IRC83Violation
)

# Node 6: Enforcement Routing
from .node6_routing.enforcement_router import EnforcementRouter

# Node 7: 13F-HR Institutional Holdings
from .node7_13f_holdings import InstitutionalHoldingsAnalyzer

# Node 8: 13D/13G Beneficial Ownership
from .node8_13d_ownership import BeneficialOwnershipTracker

# Node 9: 8-K Material Event Correlator
from .node9_8k_events import MaterialEventCorrelator

# Node 10: Form 144 Restricted Sale Monitor
from .node10_form144 import (
    RestrictedSaleMonitor,
    RestrictedSaleMonitorV2,
    TackingCalculator,
    AffiliateVolumeAggregator
)

# Node 11: Executive Network Mapper
from .node11_network_mapper import (
    ExecutiveNetworkAnalyzer,
    ExecutiveNetworkAnalyzerV2,
    Neo4jGraphClient,
    MockNeo4jGraphClient
)

# Node 12: Earnings Call Transcript Analyzer
from .node12_earnings_calls import (
    TranscriptAnalyzerV2,
    DeBERTaContradictionDetector,
    EarningsCallCrossValidator
)

# Node 13: Z-Score Bankruptcy Predictor
from .node13_zscore import BankruptcyPredictorV2, Node13OutputV2

# Node 14: F-Score Financial Strength Analyzer
from .node14_fscore import FinancialStrengthAnalyzerV2, Node14OutputV2

# Node 15: Market Correlation Engine
from .node15_market_correlation import MarketCorrelationEngineV2, Node15OutputV2

# Cross-Node Integration
from .cross_node import NodeCorrelator, CrossNodeAlert, UnifiedForensicAnalysis

__all__ = [
    # Node 1
    'Form4Parser',
    'ShortSwingCalculator',
    'GiftPatternDetector',
    
    # Node 2
    'DEF14ACompensationAnalyzer',
    'CompensationAnalysisResult',
    'NEOCompensation',
    'SayOnPayVote',
    'CEOPayRatio',
    'GoldenParachute',
    'RelatedPartyTransaction',
    'ClawbackPolicy',
    'CompensationType',
    'AwardVestingType',
    'SayOnPayOutcome',
    'CompensationViolationType',
    'CompensationViolation',
    
    # Node 3
    'TemporalConsistencyValidator',
    'QuarterlyMetrics',
    'TemporalViolation',
    'TemporalViolationType',
    
    # Node 4
    'SOXCertificationAnalyzer',
    'SOXViolationType',
    'AuditOpinionType',
    'ICFROpinionType',
    'Section302Certification',
    'Section906Certification',
    'MaterialWeakness',
    'AuditOpinion',
    'SOXViolation',
    
    # Node 5
    'IRC83TaxCalculator',
    'IRC83ViolationType',
    'EquityAwardType',
    'GrantType',
    'EquityGrant',
    'Section83bElection',
    'TaxExposure',
    'EquityDisposition',
    'IRC83Violation',
    
    # Node 6
    'EnforcementRouter',
    
    # Node 7
    'InstitutionalHoldingsAnalyzer',
    
    # Node 8
    'BeneficialOwnershipTracker',
    
    # Node 9
    'MaterialEventCorrelator',
    
    # Node 10
    'RestrictedSaleMonitor',
    'RestrictedSaleMonitorV2',
    'TackingCalculator',
    'AffiliateVolumeAggregator',
    
    # Node 11
    'ExecutiveNetworkAnalyzer',
    'ExecutiveNetworkAnalyzerV2',
    'Neo4jGraphClient',
    'MockNeo4jGraphClient',
    
    # Node 12
    'TranscriptAnalyzerV2',
    'DeBERTaContradictionDetector',
    'EarningsCallCrossValidator',
    
    # Node 13
    'BankruptcyPredictorV2',
    'Node13OutputV2',
    
    # Node 14
    'FinancialStrengthAnalyzerV2',
    'Node14OutputV2',
    
    # Node 15
    'MarketCorrelationEngineV2',
    'Node15OutputV2',
    
    # Cross-Node Integration
    'NodeCorrelator',
    'CrossNodeAlert',
    'UnifiedForensicAnalysis',
]

