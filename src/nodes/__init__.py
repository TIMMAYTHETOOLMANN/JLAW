"""
JLAW Nodes Package - Unified Exports
====================================

Centralized exports for all 15 node modules in the JLAW system.
Each node is responsible for specific SEC filing analysis and violation detection.

Architecture:
- Nodes 1-6: Core SEC Filing Analysis (Phase 1)
- Nodes 7-12: Extended Intelligence (Phase 2)
- Nodes 13-14: Financial Health Prediction (Phase 3)
- Node 15: Market Correlation (Phase 4)
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
]

