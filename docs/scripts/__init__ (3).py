"""
Financial Forensics Module
==========================

Advanced financial fraud detection capabilities.

Components:
-----------
- BenfordAnalyzer: Multi-digit Benford's Law analysis for fraud detection
- RevenueRecognitionAnalyzer: Revenue recognition anomaly detection
- (future) RatioAnalyzer: Financial ratio anomaly detection
"""

from .benford_analyzer import (
    BenfordAnalyzer,
    BenfordAnalysis,
    BenfordDistribution,
    DigitAnomaly,
    analyze_financial_data
)

from .revenue_recognition_analyzer import (
    RevenueRecognitionAnalyzer,
    RevenueRecognitionAnalysis,
    QuarterlyFinancials,
    IndustryBenchmarks,
    RevenueAnomaly,
    AnomalyType,
    AnomalySeverity,
    DSOAnalysis,
    DeferredRevenueAnalysis,
    QuarterlyPattern
)

__all__ = [
    # Benford's Law
    "BenfordAnalyzer",
    "BenfordAnalysis",
    "BenfordDistribution",
    "DigitAnomaly",
    "analyze_financial_data",
    
    # Revenue Recognition
    "RevenueRecognitionAnalyzer",
    "RevenueRecognitionAnalysis",
    "QuarterlyFinancials",
    "IndustryBenchmarks",
    "RevenueAnomaly",
    "AnomalyType",
    "AnomalySeverity",
    "DSOAnalysis",
    "DeferredRevenueAnalysis",
    "QuarterlyPattern"
]
