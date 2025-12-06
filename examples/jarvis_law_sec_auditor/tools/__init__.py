"""
JARVIS:LAW Forensic Analysis Tools
Modular enhancement suite for advanced fraud pattern detection
"""

from .zero_dollar_detector import detect_zero_dollar_risk, analyze_zero_dollar_patterns
from .verify_10b5_plan import check_10b5_plan, verify_cooling_off_period, analyze_plan_consistency
from .risk_weighting import weight_risk_score, extract_role_from_relationship, assess_role_specific_risk, rank_insiders_by_risk
from .earnings_window import is_within_earnings_window, analyze_earnings_proximity, detect_clustered_trading, load_earnings_calendar, correlate_all_transactions
from .batch_pattern_analysis import BatchPatternIntelligence, analyze_batch, quick_risk_assessment
from .financial_flow_tracer import (
    FinancialFlowTracer,
    trace_flows,
    trace_filings,
    quick_flow_risk,
    detect_enrichment,
    FlowType,
    FlowRiskLevel,
    TransactionFlow,
    FlowPattern,
    FlowAnalysisResult,
)

__all__ = [
    # Module 1: Zero-Dollar Detection
    'detect_zero_dollar_risk',
    'analyze_zero_dollar_patterns',
    
    # Module 2: 10b5-1 Compliance
    'check_10b5_plan',
    'verify_cooling_off_period',
    'analyze_plan_consistency',
    
    # Module 3: Risk Weighting
    'weight_risk_score',
    'extract_role_from_relationship',
    'assess_role_specific_risk',
    'rank_insiders_by_risk',
    
    # Module 4: Earnings Correlation
    'is_within_earnings_window',
    'analyze_earnings_proximity',
    'detect_clustered_trading',
    'load_earnings_calendar',
    
    # Module 5: Batch Pattern Intelligence (BPI)
    'BatchPatternIntelligence',
    'analyze_batch',
    'quick_risk_assessment',
    'correlate_all_transactions',
    
    # Module 6: Financial Flow Tracer
    'FinancialFlowTracer',
    'trace_flows',
    'trace_filings',
    'quick_flow_risk',
    'detect_enrichment',
    'FlowType',
    'FlowRiskLevel',
    'TransactionFlow',
    'FlowPattern',
    'FlowAnalysisResult',
]

