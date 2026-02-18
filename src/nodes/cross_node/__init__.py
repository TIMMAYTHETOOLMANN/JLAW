"""
Cross-Node Integration Module
=============================

Provides unified correlation and analysis across multiple forensic nodes.
"""

from .node_correlator import NodeCorrelator, CrossNodeAlert, UnifiedForensicAnalysis
from .beneficial_ownership_correlator import (
    BeneficialOwnershipCorrelator,
    OwnershipCorrelationReport,
    OwnershipCorrelationAlert,
    AsymmetryAlert,
    OwnershipAlertType,
    OwnershipSeverity
)

__all__ = [
    'NodeCorrelator',
    'CrossNodeAlert',
    'UnifiedForensicAnalysis',
    'BeneficialOwnershipCorrelator',
    'OwnershipCorrelationReport',
    'OwnershipCorrelationAlert',
    'AsymmetryAlert',
    'OwnershipAlertType',
    'OwnershipSeverity'
]
