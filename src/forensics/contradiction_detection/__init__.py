"""
Phase 6: Advanced Contradiction Detection with Cross-Reference
Omniscient contradiction detector across all document types and time periods.
"""

from .omniscient_detector import (
    OmniscientContradictionDetector,
    ContradictionReport,
    Contradiction,
    ContradictionNetwork,
    ContradictionType,
    Severity,
    DocumentChunk,
    Claim,
    SpecificContradiction
)

from .semantic_analyzer import (
    SemanticContradictionAnalyzer,
    SemanticContradiction,
    SimilarityScore
)

from .logical_analyzer import (
    LogicalContradictionAnalyzer,
    LogicalContradiction,
    TemporalImpossibility,
    MathematicalInconsistency
)

from .cross_referencer import (
    CrossReferencer,
    CrossReference,
    ReferenceChain
)

__all__ = [
    'OmniscientContradictionDetector',
    'ContradictionReport',
    'Contradiction',
    'ContradictionNetwork',
    'ContradictionType',
    'Severity',
    'DocumentChunk',
    'Claim',
    'SpecificContradiction',
    'SemanticContradictionAnalyzer',
    'SemanticContradiction',
    'SimilarityScore',
    'LogicalContradictionAnalyzer',
    'LogicalContradiction',
    'TemporalImpossibility',
    'MathematicalInconsistency',
    'CrossReferencer',
    'CrossReference',
    'ReferenceChain'
]

