"""
Enforcement Module - Phase 5
============================

Comprehensive enforcement routing and agency coordination module.

This module provides enhanced enforcement routing capabilities including:
- SEC investigation trigger threshold assessment
- Whistleblower program relevance flagging (Dodd-Frank §922)
- Multi-agency routing (SEC, DOJ, IRS, CFTC, FinCEN)
- Penalty range estimation
- Evidence-based recommendations

Components:
- EnforcementRoutingEngine: Primary routing engine with threshold assessment
- EnforcementRecommendation: Agency routing recommendations
- PenaltyRange: Estimated penalty ranges

Integration:
- Works with existing Node 6 enforcement router
- Leverages statutory binding engine
- Integrates with recursive analysis results
"""

from .routing_engine import (
    EnforcementRoutingEngine,
    EnforcementRecommendation,
    PenaltyRange,
    EnforcementAgency,
    CaseType,
    Priority,
    PenaltyType
)

__all__ = [
    'EnforcementRoutingEngine',
    'EnforcementRecommendation',
    'PenaltyRange',
    'EnforcementAgency',
    'CaseType',
    'Priority',
    'PenaltyType'
]
