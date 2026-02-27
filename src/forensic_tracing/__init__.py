"""
JLAW Forensic Tracing System
=============================

Six-domain forensic system for tracing insider economic benefit
through SEC EDGAR data, from $0 acquisition through entity transfer
to ultimate liquidation.

Domains:
    1. Form 4 Footnote Classification Engine
    2. Grant-to-Sale Transaction Tracing Engine
    3. Beneficial Ownership Chain Resolver (enhanced with parking detection)
    4. Form 144 Correlation Engine
    5. Two-Tier Documentation Framework (TCR / Work Product)
    6. Courtroom-Grade Visualization Specifications
"""

from src.forensic_tracing.domain1_footnote_classifier import (
    FootnoteClassifier,
    FootnoteRiskCategory,
)
from src.forensic_tracing.domain2_grant_to_sale import (
    GrantToSaleTracer,
    AcquisitionRecord,
    LiquidationChain,
)
from src.forensic_tracing.domain3_ownership_resolver import (
    EnhancedOwnershipResolver,
    ParkingDetector,
    BeneficialOwnershipTest,
)
from src.forensic_tracing.domain4_form144 import (
    Form144CorrelationEngine,
    Form144Notice,
)
from src.forensic_tracing.domain5_documentation import (
    TwoTierDocumentationFramework,
    DocumentTier,
    TCRSubmission,
)
from src.forensic_tracing.domain6_visualization import (
    CourtroomVisualizationSpec,
    OKABE_ITO_PALETTE,
)
from src.forensic_tracing.orchestrator import ForensicTracingOrchestrator

__all__ = [
    'FootnoteClassifier',
    'FootnoteRiskCategory',
    'GrantToSaleTracer',
    'AcquisitionRecord',
    'LiquidationChain',
    'EnhancedOwnershipResolver',
    'ParkingDetector',
    'BeneficialOwnershipTest',
    'Form144CorrelationEngine',
    'Form144Notice',
    'TwoTierDocumentationFramework',
    'DocumentTier',
    'TCRSubmission',
    'CourtroomVisualizationSpec',
    'OKABE_ITO_PALETTE',
    'ForensicTracingOrchestrator',
]
