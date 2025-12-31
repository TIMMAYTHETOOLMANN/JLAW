"""
Multi-Jurisdictional Compliance Framework
=========================================

DOJ-grade multi-jurisdictional legal compliance mapping for securities fraud prosecution.

This module provides comprehensive jurisdiction determination, state securities law analysis,
international compliance mapping, and forum shopping optimization.

Core Components:
- JurisdictionMapper: Determines all applicable jurisdictions with authority
- StateSecuritiesLawEngine: 50-state Blue Sky Law database and violation analysis
- InternationalComplianceAnalyzer: UK FCA, EU ESMA, IIROC, ASIC frameworks
- ForumShoppingOptimizer: Prosecution venue scoring and strategy generation

Legal Framework Coverage:
- Federal: SEC, DOJ, FINRA, CFTC
- State: All 50 states with Blue Sky Laws
- International: UK, EU (27 member states), Canada, Australia, Switzerland
"""

from .jurisdiction_mapper import (
    JurisdictionMapper,
    JurisdictionProfile,
    JurisdictionTrigger
)
from .state_securities_laws import (
    StateSecuritiesLawEngine,
    StateSecuritiesLaw
)
from .international_compliance import (
    InternationalComplianceAnalyzer,
    InternationalRegulation
)
from .forum_optimizer import (
    ForumShoppingOptimizer,
    ForumAnalysis
)

__all__ = [
    'JurisdictionMapper',
    'JurisdictionProfile',
    'JurisdictionTrigger',
    'StateSecuritiesLawEngine',
    'StateSecuritiesLaw',
    'InternationalComplianceAnalyzer',
    'InternationalRegulation',
    'ForumShoppingOptimizer',
    'ForumAnalysis',
]
